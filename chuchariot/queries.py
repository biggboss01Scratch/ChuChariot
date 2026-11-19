"""Read-only knowledge queries and review visibility."""

import copy
from collections import defaultdict

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
                "mappings": len(self._data["model_mappings"]),
            },
            "entities": self.list_entities(include_pending=include_pending),
            "facts": copy.deepcopy(visible_facts),
            "evidence": copy.deepcopy([item for item in self._data["evidence"] if item["id"] in evidence_ids]),
            "sources": copy.deepcopy(self._data["sources"]),
            "mappings": copy.deepcopy([m for m in self._data["model_mappings"] if _visible(m, include_pending)]),
        }
