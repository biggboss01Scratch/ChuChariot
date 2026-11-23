"""Read-only knowledge queries and review visibility."""

import copy
from collections import defaultdict, deque

from .dataset_io import DEFAULT_DATASET, DEFAULT_ONTOLOGY, TABLES, KnowledgeError, read_json
from .validation import validate


def _visible(record, include_pending):
    return include_pending or record["review_status"] == "confirmed"


class KnowledgeStore:
    """Read-only adapter; reloading replaces the snapshot rather than appending."""

    def __init__(self, data: dict, ontology: dict):
        errors = validate(data, ontology)
        if errors:
            raise KnowledgeError("\n".join(errors))
        self._data = copy.deepcopy(data)
        self._indices = {name: {r["id"]: r for r in self._data[name]} for name in TABLES}
        self._facts_by_entity = defaultdict(list)
        for fact in self._data["facts"]:
            for ident in {fact["subject_id"], fact.get("object_id")} - {None}:
                self._facts_by_entity[ident].append(fact)
        self._mappings_by_entity = defaultdict(list)
        for mapping in self._data["model_mappings"]:
            self._mappings_by_entity[mapping["entity_id"]].append(mapping)

    @classmethod
    def load(cls, dataset=DEFAULT_DATASET, ontology=DEFAULT_ONTOLOGY):
        return cls(read_json(dataset), read_json(ontology))

    def list_entities(self, query="", kind=None, include_pending=False):
        query = query.casefold()
        matched = sorted((e for e in self._data["entities"]
            if (kind is None or e["kind"] == kind) and
            (not query or any(query in name.casefold() for name in [e["label"], *e["aliases"]]))),
            key=lambda e: e["id"])
        return [self.entity(e["id"], include_pending) for e in matched]

    def entity(self, ident, include_pending=False):
        self._require_entity(ident)
        result = copy.deepcopy(self._indices["entities"][ident])
        related = self._facts_by_entity.get(ident, [])
        result["fact_review_summary"] = {status: sum(f["review_status"] == status for f in related)
                                         for status in ("confirmed", "pending", "disputed")}
        if result["kind"] == "Measurement" and not include_pending:
            confirmed = any(f["predicate"] == "HAS_MEASUREMENT" and f.get("object_id") == ident
                            and _visible(f, False) for f in related)
            if not confirmed:
                result.pop("measurement", None)
                result["measurement_visibility"] = "hidden_until_reviewed"
        return result

    def facts(self, ident, include_pending=False):
        self._require_entity(ident)
        visible = (f for f in self._facts_by_entity.get(ident, []) if _visible(f, include_pending))
        return copy.deepcopy(sorted(visible, key=lambda f: f["id"]))

    def relations(self, ident, include_pending=False):
        return [{"fact": f, "direction": "outgoing" if f["subject_id"] == ident else "incoming",
                 "neighbor": self.entity(f["object_id"] if f["subject_id"] == ident else f["subject_id"], include_pending)}
                for f in self.facts(ident, include_pending) if "object_id" in f]

    def evidence(self, ident, include_pending=False):
        result = []
        for fact in self.facts(ident, include_pending):
            for eid in fact["evidence_ids"]:
                record = copy.deepcopy(self._indices["evidence"][eid])
                result.append({"fact_id": fact["id"], "review_status": fact["review_status"],
                               "evidence": record, "source": copy.deepcopy(self._indices["sources"][record["source_id"]])})
        return result

    def mappings(self, ident, include_pending=False):
        self._require_entity(ident)
        return copy.deepcopy([m for m in self._mappings_by_entity.get(ident, []) if _visible(m, include_pending)])

    def connection_path(self, from_id, to_id, include_pending=False, max_hops=8):
        """Shortest directed teaching path, preserving each hop's distinct basis.

        Only SCHEMATIC_NEXT participates. Classification, composition and shared
        materials must never create shortcuts or imply physical connectivity.
        """
        self._require_entity(from_id)
        self._require_entity(to_id)
        if type(max_hops) is not int or not 1 <= max_hops <= 16:
            raise KnowledgeError("max_hops 必须为1至16的整数")
        visible = [f for f in self._data["facts"] if _visible(f, include_pending)]
        metadata = defaultdict(dict)
        for fact in visible:
            if fact["predicate"] in {"CONNECTION_FROM", "CONNECTION_TO", "HAS_EVIDENCE_BASIS"}:
                metadata[fact["subject_id"]][fact["predicate"]] = fact
        edges = defaultdict(list)
        for fact in sorted(visible, key=lambda f: f["id"]):
            if fact["predicate"] != "SCHEMATIC_NEXT":
                continue
            for connection_id, fields in sorted(metadata.items()):
                if set(fields) != {"CONNECTION_FROM", "CONNECTION_TO", "HAS_EVIDENCE_BASIS"}:
                    continue
                if (fields["CONNECTION_FROM"]["object_id"] != fact["subject_id"]
                        or fields["CONNECTION_TO"]["object_id"] != fact["object_id"]
                        or any(fact["id"] not in item.get("basis_fact_ids", []) for item in fields.values())):
                    continue
                evidence_ids = sorted({eid for item in [fact, *fields.values()] for eid in item["evidence_ids"]})
                edges[fact["subject_id"]].append({
                    "fact": fact, "connection": self.entity(connection_id, include_pending),
                    "from": self.entity(fact["subject_id"], include_pending),
                    "to": self.entity(fact["object_id"], include_pending),
                    "evidence_basis": self.entity(fields["HAS_EVIDENCE_BASIS"]["object_id"], include_pending),
                    "metadata_facts": list(fields.values()),
                    "evidence": [{"evidence": self._indices["evidence"][eid],
                                  "source": self._indices["sources"][self._indices["evidence"][eid]["source_id"]]}
                                 for eid in evidence_ids],
                })
        result = {"from_id": from_id, "to_id": to_id, "found": False, "hops": [],
                  "view": "review" if include_pending else "confirmed_only",
                  "note": "这是有向教学导航路径，各跳可来自不同标本、复原图或教学方案；不是同车物理连接、受力链或装配顺序证明。"}
        queue = deque([(from_id, [])])
        seen = {from_id}
        while queue:
            current, hops = queue.popleft()
            if current == to_id:
                result.update(found=True, hops=hops)
                break
            if len(hops) >= max_hops:
                continue
            for hop in edges.get(current, []):
                target = hop["fact"]["object_id"]
                if target not in seen:
                    seen.add(target)
                    queue.append((target, [*hops, hop]))
        return copy.deepcopy(result)

    def _require_entity(self, ident):
        if ident not in self._indices["entities"]:
            raise KnowledgeError(f"实体不存在：{ident}")

    def source(self, ident):
        return copy.deepcopy(self._indices["sources"].get(ident))

    def snapshot(self, include_pending=False):
        """Project the small dataset for the inspector with the same visibility as queries."""
        facts = self._data["facts"]
        visible_facts = [fact for fact in facts if _visible(fact, include_pending)]
        evidence_ids = {eid for fact in visible_facts for eid in fact["evidence_ids"]}
        return {
            "meta": {key: self._data[key] for key in ("dataset_id", "stage", "schema_version", "description")},
            "stats": {
                "entities": len(self._data["entities"]), "facts": len(facts),
                "confirmed": sum(_visible(f, False) for f in facts),
                "pending": sum(f["review_status"] == "pending" for f in facts),
                "evidence": len(self._data["evidence"]), "visible_facts": len(visible_facts),
                "dimension_properties": sum(f["predicate"] == "HAS_DIMENSION" for f in facts),
                "mappings": len(self._data["model_mappings"]),
            },
            "entities": self.list_entities(include_pending=include_pending),
            "facts": copy.deepcopy(visible_facts),
            "evidence": copy.deepcopy([item for item in self._data["evidence"] if item["id"] in evidence_ids]),
            "sources": copy.deepcopy(self._data["sources"]),
            "mappings": copy.deepcopy([m for m in self._data["model_mappings"] if _visible(m, include_pending)]),
        }
