"""Public DTOs and presentation derived exclusively from a database snapshot."""
import copy
from urllib.parse import quote
from neo4j.exceptions import ServiceUnavailable

from ..queries import KnowledgeStore
from ..presentation import project_presentation
from ..preview import source_path
from .database import Missing, Repository


def pick(record, keys):
    return {k: copy.deepcopy(v) for k, v in record.items() if k in keys}


def metadata(data, ontology, state, request_id, mode):
    return {"graph_revision": Repository.revision(state), "baseline_dataset_id": data["dataset_id"],
            "ontology_version": ontology["version"], "schema_version": data["schema_version"],
            "publication_mode": mode, "request_id": request_id}


class View:
    def __init__(self, repo, settings, request_id, *, internal=False, include_pending=None):
        try:
            self.data, self.ontology, self.state = repo.snapshot()
        except Missing as exc:
            raise ServiceUnavailable("Knowledge database is not initialized") from exc
        self.settings = settings
        self.store = KnowledgeStore(self.data, self.ontology)
        mode = "internal" if internal else settings.publication_mode
        review = internal or mode == "candidate_preview"
        if include_pending is not None:
            review = review and include_pending
        self.review = review
        self.internal = internal
        self.meta = metadata(self.data, self.ontology, self.state, request_id, mode)
        self.snapshot = project_presentation(self.data, self.store.snapshot(review), "internal" if internal else "public")
        self.entities = {e["id"]: e for e in self.snapshot["entities"]}
        self.facts = {f["id"]: f for f in self.snapshot["facts"]}
        self.sources = {s["id"]: s for s in self.snapshot["sources"]}
        self.evidence = {e["id"]: e for e in self.snapshot["evidence"]}

    def entity(self, ident):
        if ident not in self.entities:
            raise Missing("Entity not found")
        return pick(self.entities[ident], {"id", "kind", "label", "aliases", "scope_id", "note"})

    def fact(self, ident):
        if ident not in self.facts:
            raise Missing("Fact not found")
        return pick(self.facts[ident], {"id", "subject_id", "predicate", "object_id", "value", "evidence_ids",
                                       "origin", "review_status", "rationale", "knowledge_basis", "basis_fact_ids"})

    @staticmethod
    def edge(fact):
        return {**pick(fact, {"subject_id", "object_id", "predicate", "origin", "review_status", "knowledge_basis", "rationale"}),
                "fact_id": fact["id"], "evidence_count": len(fact["evidence_ids"])}

    def source(self, ident):
        if ident not in self.sources:
            raise Missing("Source not found")
        source = self.sources[ident]
        available = source_path(source, self.settings.resource_dirs) is not None
        prefix = "/api/v1/internal" if self.internal else "/api/v1"
        return {**pick(source, {"id", "title", "format", "resource_id", "url", "note"}),
                "content_available": available,
                "content_url": prefix + "/sources/" + quote(ident, safe="") + "/content" if available else None}

    def proof(self, evidence):
        source = self.source(evidence["source_id"])
        result = pick(evidence, {"id", "locator", "quote", "scope_note", "pdf_page", "printed_page", "figure",
                                "start_seconds", "end_seconds"})
        result.update(source=source, type={"pdf": "pdf", "mp4": "video", "md": "dictionary_excerpt"}[source["format"]])
        if source["format"] == "md":
            result["entry_url"] = source["url"]
        return result

    def detail(self, ident):
        entity = self.entity(ident)
        facts = [f for f in self.facts.values() if ident in {f["subject_id"], f.get("object_id")}]
        return {"entity": entity,
                "properties": [self.fact(f["id"]) for f in facts if isinstance(f.get("value"), dict)],
                "descriptions": [self.fact(f["id"]) for f in facts if isinstance(f.get("value"), str)],
                "relations": [self.edge(f) for f in facts if "object_id" in f], "meta": self.meta}

    def graph(self, center=None, depth=1, groups=None, limit=500):
        permitted = {g["id"]: set(g["fact_ids"]) for g in self.snapshot["presentation"]["groups"]}
        selected = set().union(*(permitted[g] for g in (groups or permitted)))
        edges = [f for f in self.facts.values() if "object_id" in f and f["id"] in selected]
        ids = set(self.entities)
        if center:
            self.entity(center)
            ids = frontier = {center}
            for _ in range(depth):
                next_ids = {i for f in edges if {f["subject_id"], f["object_id"]} & frontier
                            for i in (f["subject_id"], f["object_id"])} - ids
                ids = ids | next_ids
                frontier = next_ids
        ordered = sorted(ids, key=lambda i: (i != center, i))
        truncated = len(ordered) > limit
        ids = set(ordered[:limit])
        return {"nodes": [self.entity(i) for i in ordered[:limit]],
                "edges": [self.edge(f) for f in edges if {f["subject_id"], f["object_id"]} <= ids],
                "truncated": truncated, "meta": self.meta}

    def teaching(self, from_id, to_id, max_hops):
        result = self.store.connection_path(from_id, to_id, self.review, max_hops)
        hops = []
        for hop in result["hops"]:
            hops.append({"fact": self.fact(hop["fact"]["id"]),
                         **{k: self.entity(hop[k]["id"]) for k in ("from", "to", "connection", "evidence_basis")},
                         "metadata_facts": [self.fact(f["id"]) for f in hop["metadata_facts"]],
                         "evidence": [self.proof(e["evidence"]) for e in hop["evidence"]]})
        return {"path_kind": "teaching", "found": result["found"], "hops": hops,
                "note": result["note"], "meta": self.meta}

    def inspector(self):
        result = copy.deepcopy(self.snapshot)
        result["meta"].update(self.meta, review_mode=self.review, validation="passed", storage="neo4j")
        result.update(ontology=self.ontology, model_report=None, media=[])
        for source in result["sources"]:
            dto = self.source(source["id"])
            source.update(available=dto["content_available"], content_url=dto["content_url"])
            source.pop("filename", None)
        result["presentation"]["note"] = "Database-backed projection; internal access requires server authentication."
        return result
