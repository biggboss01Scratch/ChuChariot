"""Neo4j record storage, atomic migration and optimistic change sets.

Domain records are flattened into queryable scalar/list properties, not JSON
blobs. Only immutable audit snapshots, pending commands and ontology metadata
use JSON. Small-course-project snapshots serialize on GraphState to avoid
mixing records from different revisions under read-committed isolation.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from uuid import uuid4

from neo4j import GraphDatabase

from ..dataset_io import TABLES, KnowledgeError
from ..validation import validate

LABELS = {"entities": "Entity", "facts": "Fact", "evidence": "Evidence",
          "sources": "Source", "model_mappings": "ModelMapping"}


class Conflict(KnowledgeError):
    pass


class Missing(KnowledgeError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def normalized(data):
    result = copy.deepcopy(data)
    for table in TABLES:
        result[table].sort(key=lambda r: r["id"])
    return result


def flatten(record):
    result = {}
    def visit(value, path):
        if isinstance(value, dict):
            if not value:
                result.setdefault("empty_maps", []).append(path)
            for key, child in value.items():
                if "__" in key:
                    raise KnowledgeError("Unsupported field name")
                visit(child, path + "__" + key)
        else:
            result[path] = value
    for key, value in record.items():
        visit(value, "data__" + key)
    return result


def unflatten(properties):
    result = {}
    for key, value in properties.items():
        if not key.startswith("data__"):
            continue
        node = result
        parts = key.split("__")[1:]
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    for key in properties.get("empty_maps", []):
        node = result
        for part in key.split("__")[1:]:
            node = node.setdefault(part, {})
    return result


def check(data, ontology):
    try:
        errors = validate(data, ontology)
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise KnowledgeError("Invalid record structure") from exc
    if errors:
        raise KnowledgeError("\n".join(errors))
    ids = [r["id"] for table in TABLES for r in data[table]]
    if len(ids) != len(set(ids)):
        raise KnowledgeError("Record IDs must be globally unique")


def references(record):
    """Business references only; resource IDs and run IDs are external registries."""
    result = {record[k] for k in ("subject_id", "object_id", "scope_id", "source_id",
                                  "entity_id", "model_version_id") if isinstance(record.get(k), str)}
    for key in ("evidence_ids", "basis_fact_ids"):
        if isinstance(record.get(key), list):
            result.update(value for value in record[key] if isinstance(value, str))
    return result


def apply_operations(data, operations, actor, timestamp, *, deleted_records=None):
    """Pure command reducer. Caller validates the complete resulting graph."""
    result = copy.deepcopy(data)
    changed = {}
    deleted_records = deleted_records or {}
    now = timestamp[:10]
    for op in operations:
        table, ident, action = op["table"], op["id"], op["action"]
        index = {r["id"]: i for i, r in enumerate(result[table])}
        before = copy.deepcopy(result[table][index[ident]]) if ident in index else None
        archived = deleted_records.get(ident)
        if archived and archived["table"] != table:
            raise Conflict("Record ID is reserved in a different table: " + ident)
        if action == "create" and archived:
            raise Conflict("Deleted record ID is reserved; use restore: " + ident)
        if action == "restore":
            if before is not None:
                raise Conflict("Record is already active: " + ident)
            if archived is None:
                raise Missing("Deleted record not found: " + ident)
            record = copy.deepcopy(archived["record"])
            if table in {"facts", "model_mappings"}:
                record["review_status"] = "pending"
                record.pop("review", None)
            if table == "entities":
                record["publication_status"] = "draft"
            if table == "facts":
                record["publication_managed"] = True
            result[table].append(record)
            changed[(table, ident)] = (None, record)
            continue
        if action == "create" and before is not None:
            raise Conflict("Record already exists: " + ident)
        if action != "create" and before is None:
            if archived:
                raise Conflict("Record is deleted; restore it before editing: " + ident)
            raise Missing("Record not found: " + ident)
        if action == "delete":
            result[table].pop(index[ident])
            changed[(table, ident)] = (before, None)
            continue
        if action == "review":
            record = copy.deepcopy(before)
            if table == "entities":
                record["publication_status"] = "published" if op["review_status"] == "confirmed" else "draft"
            else:
                record.update(review_status=op["review_status"], review={"reviewer": actor, "date": now, "note": op["note"]})
        else:
            record = copy.deepcopy(op["record"])
            if record.get("id") != ident:
                raise KnowledgeError("record.id does not match operation.id")
            if table in {"facts", "model_mappings"}:
                # Content commands cannot supply trusted review state or identity.
                if record.get("review_status", "pending") != "pending" or "review" in record:
                    raise KnowledgeError("Use a review operation to assign review status")
                record["review_status"] = "pending"
            if table == "entities":
                record["publication_status"] = "draft"
            if table == "facts":
                record["publication_managed"] = True
        if before is None:
            result[table].append(record)
        else:
            result[table][index[ident]] = record
        changed[(table, ident)] = (before, record)

    removed = {ident for (_, ident), (_, after) in changed.items() if after is None}
    blockers = [(record["id"], sorted(references(record) & removed))
                for table in TABLES for record in result[table] if references(record) & removed]
    if blockers:
        raise Conflict("Cannot delete referenced records; update or explicitly delete dependents in the same change set: "
                       + canonical(blockers))

    # Re-open reviewed assertions when evidence/source/terms or premises change.
    impacted_entities = {op["id"] for op in operations if op["table"] == "entities" and op["action"] != "review"}
    impacted_sources = {i for (t, i) in changed if t == "sources"}
    impacted_evidence = {i for (t, i) in changed if t == "evidence"}
    impacted_evidence |= {e["id"] for e in result["evidence"] if e["source_id"] in impacted_sources}
    impacted_facts = {op["id"] for op in operations if op["table"] == "facts" and op["action"] != "review"}
    affected = set()
    while True:
        prior = len(impacted_facts)
        for fact in result["facts"]:
            if (set(fact["evidence_ids"]) & impacted_evidence or
                {fact["subject_id"], fact.get("object_id")} & impacted_entities or
                set(fact.get("basis_fact_ids", [])) & impacted_facts):
                affected.add(fact["id"])
                impacted_facts.add(fact["id"])
        if len(impacted_facts) == prior:
            break
    for table in ("facts", "model_mappings"):
        for record in result[table]:
            reopen = record["id"] in affected if table == "facts" else bool(
                {record["entity_id"], record["model_version_id"]} & impacted_entities)
            if reopen:
                changed.setdefault((table, record["id"]), (copy.deepcopy(record), None))
                record["review_status"] = "pending"
                record.pop("review", None)
                if table == "facts":
                    record["publication_managed"] = True
                changed[(table, record["id"])] = (changed[(table, record["id"])][0], copy.deepcopy(record))

    hidden_entities, hidden_facts = publication_blocks(result)
    for op in operations:
        if op["action"] != "review" or op["review_status"] != "confirmed":
            continue
        ident = op["id"]
        if op["table"] == "entities" and ident in hidden_entities:
            raise KnowledgeError("请先发布该实体的所属对象：" + ident)
        if op["table"] == "facts" and ident in hidden_facts:
            raise KnowledgeError("请先发布该事实的关联实体或依据，内容刚修改的事实需另次发布：" + ident)
    return normalized(result), changed, sorted(affected)


def publication_blocks(data):
    entities = {entity["id"] for entity in data["entities"] if entity.get("publication_status") == "draft"}
    while True:
        scoped = {entity["id"] for entity in data["entities"] if entity.get("scope_id") in entities}
        if scoped <= entities:
            break
        entities.update(scoped)
    facts = {fact["id"] for fact in data["facts"]
             if (fact.get("publication_managed") and fact["review_status"] != "confirmed")
             or bool({fact["subject_id"], fact.get("object_id")} & entities)}
    while True:
        dependent = {fact["id"] for fact in data["facts"] if facts.intersection(fact.get("basis_fact_ids", []))}
        if dependent <= facts:
            return entities, facts
        facts.update(dependent)


class Repository:
    def __init__(self, settings):
        self.database = settings.database
        self.driver = GraphDatabase.driver(settings.uri, auth=(settings.username, settings.password),
                                          connection_timeout=5, max_transaction_retry_time=10)

    def close(self):
        self.driver.close()

    def ready(self):
        self.driver.verify_connectivity()
        with self.driver.session(database=self.database) as session:
            row = session.run("MATCH (s:GraphState {id:'main'}) RETURN s.revision AS revision").single()
        return bool(row and row["revision"])

    def current_revision(self):
        with self.driver.session(database=self.database) as session:
            row = session.run("MATCH (s:GraphState {id:'main'}) RETURN s.revision AS revision").single()
        if not row or not row["revision"]:
            raise Missing("Knowledge baseline has not been imported")
        return self.revision(row)

    def initialize(self):
        with self.driver.session(database=self.database) as session:
            for label in ("Record", "GraphState", "ChangeSet", "RecordRevision"):
                session.run(f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE").consume()
            session.run("CREATE CONSTRAINT command_key IF NOT EXISTS FOR (n:ChangeSet) REQUIRE n.command_key IS UNIQUE").consume()
            for label, field in (("Entity", "kind"), ("Entity", "label"), ("Fact", "predicate"), ("Fact", "review_status")):
                session.run(f"CREATE INDEX {label.lower()}_{field} IF NOT EXISTS FOR (n:{label}) ON (n.data__{field})").consume()
            session.run("MERGE (s:GraphState {id:'main'}) ON CREATE SET s.guard=0, s.revision=0").consume()
            session.run("MATCH (r:Record) WHERE r.deleted IS NULL SET r.deleted=false").consume()

    @staticmethod
    def _lock(tx):
        row = tx.run("MATCH (s:GraphState {id:'main'}) SET s.guard=s.guard+1 RETURN properties(s) AS state").single()
        if not row:
            raise Missing("Database has not been initialized")
        return dict(row["state"])

    @staticmethod
    def _read(tx, state):
        if not state.get("revision"):
            raise Missing("Knowledge baseline has not been imported")
        data = json.loads(state["metadata_json"])
        for table in TABLES:
            data[table] = []
        for row in tx.run("MATCH (r:Record) WHERE coalesce(r.deleted,false)=false "
                          "RETURN r.table AS table, properties(r) AS properties ORDER BY r.id"):
            data[row["table"]].append(unflatten(row["properties"]))
        return data, json.loads(state["ontology_json"]), state

    def snapshot(self):
        with self.driver.session(database=self.database) as session:
            return session.execute_write(lambda tx: self._read(tx, self._lock(tx)))

    @staticmethod
    def _deleted(tx):
        records = {}
        for row in tx.run("MATCH (r:Record) WHERE r.deleted=true RETURN properties(r) AS r ORDER BY r.id"):
            props = row["r"]
            records[props["id"]] = {"id": props["id"], "table": props["table"], "record": unflatten(props),
                                    **{k: props[k] for k in ("deleted_at", "deleted_by", "deleted_reason", "deleted_revision")}}
        return records

    def recycle_bin(self):
        def read(tx):
            data, ontology, state = self._read(tx, self._lock(tx))
            return list(self._deleted(tx).values()), data, ontology, state
        with self.driver.session(database=self.database) as session:
            return session.execute_write(read)

    @staticmethod
    def _write_records(tx, data):
        for table, label in LABELS.items():
            rows = [{"id": r["id"], "props": {**flatten(r), "id": r["id"], "table": table, "deleted": False,
                      "content_hash": fingerprint(r)}} for r in data[table]]
            tx.run(f"UNWIND $rows AS row MERGE (n:Record:{label} {{id:row.id}}) SET n = row.props", rows=rows).consume()
        # Rebuild only the owned projection; audit history has no Record endpoints.
        tx.run("MATCH (:Record)-[r]->(:Record) DELETE r").consume()
        relations = []
        for fact in data["facts"]:
            relations.append((fact["id"], fact["subject_id"], "SUBJECT", fact["id"]))
            if "object_id" in fact:
                relations += [(fact["id"], fact["object_id"], "OBJECT", fact["id"]),
                              (fact["subject_id"], fact["object_id"], fact["predicate"], fact["id"])]
            relations += [(fact["id"], eid, "SUPPORTED_BY", fact["id"]) for eid in fact["evidence_ids"]]
            relations += [(fact["id"], bid, "BASED_ON", fact["id"]) for bid in fact.get("basis_fact_ids", [])]
        relations += [(e["id"], e["source_id"], "SOURCE", e["id"]) for e in data["evidence"]]
        relations += [(e["id"], e["scope_id"], "IN_SCOPE", e["id"]) for e in data["entities"] if "scope_id" in e]
        relations += [(e["id"], e["source_id"], "TERM_SOURCE", e["id"]) for e in data["entities"] if "source_id" in e]
        for m in data["model_mappings"]:
            relations += [(m["id"], m["entity_id"], "MAPS_ENTITY", m["id"]),
                          (m["id"], m["model_version_id"], "MAPS_MODEL", m["id"])]
        groups = {}
        for source, target, rel, fact_id in relations:
            if not re.fullmatch(r"[A-Z][A-Z_]*", rel):
                raise KnowledgeError("Invalid relationship type")
            groups.setdefault(rel, []).append({"source": source, "target": target, "fact_id": fact_id})
        for rel, rows in groups.items():
            tx.run(f"UNWIND $rows AS row MATCH (a:Record {{id:row.source}}), (b:Record {{id:row.target}}) "
                   f"CREATE (a)-[:{rel} {{fact_id:row.fact_id}}]->(b)", rows=rows).consume()

    def import_baseline(self, data, ontology):
        check(data, ontology)
        data = normalized(data)
        digest = fingerprint({"data": data, "ontology": ontology})
        timestamp = datetime.now(timezone.utc).isoformat()
        def write(tx):
            state = self._lock(tx)
            if state["revision"]:
                if state.get("baseline_hash") == digest and state["revision"] == 1:
                    return {"changed": False, "graph_revision": "rev:00000001"}
                raise Conflict("Baseline differs or database has later revisions; use change sets")
            self._write_records(tx, data)
            metadata = {k: v for k, v in data.items() if k not in TABLES}
            tx.run("MATCH (s:GraphState {id:'main'}) SET s.revision=1, s.metadata_json=$meta, "
                   "s.ontology_json=$ontology, s.baseline_hash=$hash, s.imported_at=$at",
                   meta=canonical(metadata), ontology=canonical(ontology), hash=digest, at=timestamp).consume()
            return {"changed": True, "graph_revision": "rev:00000001"}
        with self.driver.session(database=self.database) as session:
            return session.execute_write(write)

    @staticmethod
    def _archive_records(tx, ids, actor, reason, timestamp, revision):
        tx.run("UNWIND $ids AS id MATCH (r:Record {id:id}) "
               "SET r.deleted=true, r.deleted_at=$at, r.deleted_by=$actor, "
               "r.deleted_reason=$reason, r.deleted_revision=$revision",
               ids=ids, at=timestamp, actor=actor, reason=reason, revision=revision).consume()

    @staticmethod
    def revision(state):
        return f"rev:{state['revision']:08d}"

    @staticmethod
    def _command(row):
        result = json.loads(row["payload_json"])
        result.update(id=row["id"], actor_id=row["actor_id"], status=row["status"],
                      operation_count=len(result["operations"]))
        if row.get("result_revision"):
            result["result_graph_revision"] = row["result_revision"]
        return result

    def create_change(self, draft, actor, key):
        ident = "change:" + uuid4().hex
        command_key = fingerprint([actor, key])
        payload = canonical(draft)
        timestamp = datetime.now(timezone.utc).isoformat()
        def write(tx):
            state = self._lock(tx)
            existing = tx.run("MATCH (c:ChangeSet {command_key:$key}) RETURN properties(c) AS c", key=command_key).single()
            if existing:
                if existing["c"]["payload_json"] != payload:
                    raise Conflict("Idempotency key was used for different content")
                return self._command(existing["c"])
            if draft["base_graph_revision"] != self.revision(state):
                raise Conflict("Graph revision changed")
            tx.run("CREATE (c:ChangeSet {id:$id, command_key:$key, payload_json:$payload, actor_id:$actor, "
                   "status:'draft', created_at:$at})", id=ident, key=command_key, payload=payload, actor=actor, at=timestamp).consume()
            return {**draft, "id": ident, "actor_id": actor, "status": "draft", "operation_count": len(draft["operations"])}
        with self.driver.session(database=self.database) as session:
            return session.execute_write(write)

    def process_change(self, ident, actor, *, commit=False, expected_revision=None):
        timestamp = datetime.now(timezone.utc).isoformat()
        def write(tx):
            state = self._lock(tx)
            row = tx.run("MATCH (c:ChangeSet {id:$id}) RETURN properties(c) AS c", id=ident).single()
            if not row:
                raise Missing("Change set not found")
            props = row["c"]
            if props["actor_id"] != actor:
                raise Missing("Change set not found")
            command = self._command(props)
            def validation_result(valid, errors=(), affected=()):
                return {"change_set_id": ident, "valid": valid,
                        "base_graph_revision": command["base_graph_revision"],
                        "errors": [{"path": "operations", "message": message} for message in errors],
                        "impacted_fact_ids": list(affected)}
            if command["status"] == "committed":
                if commit and expected_revision != command["base_graph_revision"]:
                    raise Conflict("Commit revision differs from original request")
                return command if commit else validation_result(True)
            revision = self.revision(state)
            if command["base_graph_revision"] != revision or (commit and expected_revision != revision):
                raise Conflict("Graph revision changed; rebase and validate a new change set")
            data, ontology, _ = self._read(tx, state)
            if command["ontology_version"] != ontology["version"] or command["schema_version"] != data["schema_version"]:
                raise Conflict("Ontology or schema version changed")
            affected = []
            try:
                updated, changes, affected = apply_operations(data, command["operations"], actor, timestamp,
                                                              deleted_records=self._deleted(tx))
                check(updated, ontology)
            except KnowledgeError as exc:
                if commit:
                    raise
                return validation_result(False, str(exc).splitlines(), affected)
            if not commit:
                tx.run("MATCH (c:ChangeSet {id:$id}) SET c.status='validated'", id=ident).consume()
                return validation_result(True, affected=affected)
            if command["status"] != "validated":
                raise Conflict("Validate the change set before committing")
            self._write_records(tx, updated)
            next_revision = f"rev:{state['revision'] + 1:08d}"
            deleted_ids = [rid for (_, rid), (_, after) in changes.items() if after is None]
            self._archive_records(tx, deleted_ids, actor, command["reason"], timestamp, next_revision)
            audit = [{"id": ident + ":" + str(i), "record_id": rid, "table": table,
                      "before_json": canonical(before), "after_json": canonical(after), "actor_id": actor,
                      "change_set_id": ident, "reason": command["reason"], "at": timestamp, "revision": next_revision}
                     for i, ((table, rid), (before, after)) in enumerate(changes.items())]
            actions = {(op["table"], op["id"]): op["action"] for op in command["operations"]}
            for entry in audit:
                entry["action"] = actions.get((entry["table"], entry["record_id"]), "reopen_review")
            tx.run("UNWIND $rows AS row CREATE (r:RecordRevision) SET r=row", rows=audit).consume()
            tx.run("MATCH (s:GraphState {id:'main'}), (c:ChangeSet {id:$id}) "
                   "SET s.revision=s.revision+1, c.status='committed', c.result_revision=$revision, c.committed_at=$at",
                   id=ident, revision=next_revision, at=timestamp).consume()
            return {**command, "status": "committed", "result_graph_revision": next_revision}
        with self.driver.session(database=self.database) as session:
            return session.execute_write(write)

    def history(self, ident):
        with self.driver.session(database=self.database) as session:
            return [dict(r["r"]) for r in session.run(
                "MATCH (r:RecordRevision {record_id:$id}) RETURN properties(r) AS r ORDER BY r.revision, r.id", id=ident)]
