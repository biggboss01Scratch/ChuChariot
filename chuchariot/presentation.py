"""Exhibition projections; visibility here is not user authentication."""

import copy

from .dataset_io import KnowledgeError


RELATION_GROUPS = (
    ("structure", "结构与连接", True, {"HAS_PART", "HAS_REGION", "HAS_ASSOCIATED_COMPONENT", "TENON_JOINT_WITH", "PARTICIPATES_IN_CONNECTION"}),
    ("appearance", "材质与外观", True, {"HAS_MATERIAL", "HAS_PRESERVED_FEATURE", "HAS_SURFACE_FINISH", "HAS_DECORATION_MOTIF"}),
    ("reconstruction", "复原示意与案例", True, {"SCHEMATIC_ASSEMBLY_WITH", "SCHEMATIC_HAS_REGION", "REGION_NEAR_COMPONENT", "INVOLVES_COMPONENT", "DEPENDS_ON"}),
    ("classification", "分类与教学栏目", False, {"INSTANCE_OF", "SUBCLASS_OF", "IN_SUBSYSTEM", "TEACHING_GROUPS_TYPE"}),
    ("references", "资料与语境词义", False, {"REFERS_TO_TYPE", "DEPICTS", "USES_TERM", "TERM_DENOTES", "TERM_RELATED_TO"}),
    ("navigation", "路径与模型元数据", False, {"SCHEMATIC_NEXT", "CONNECTION_FROM", "CONNECTION_TO", "HAS_EVIDENCE_BASIS", "HAS_POSE"}),
    ("other", "其他内部关系", False, set()),
)
PUBLIC_KINDS = {"ComponentType", "Chariot", "ReferenceSpecimen", "Component", "ComponentRegion", "StructuralRegionType",
                "Material", "PreservationFeature", "SurfaceFinish", "DecorationMotif", "HarnessRole", "AssemblyStep"}
REGION_TYPES = {
    "wheel": {"type:001", "type:003", "type:004", "type:005", "type:spoke-inner", "type:spoke-outer", "type:hub-ridge", "type:wheel-strip", "type:binding-strip"},
    "axle": {"type:002", "type:006", "type:007"},
    "traction": {"type:yoke", "type:trace", "type:beam", "type:yi", "type:beam-cap", "type:pole", "type:pole-head", "type:body", "type:futu", "type:body-floor", "type:railing", "regiontype:floor-support"},
    "harness": {"type:bit", "type:cheekpiece", "type:horse-bridle", "type:reins", "type:bridle", "type:yi-ring", "type:you-ring", "type:buckle", "type:rope-family"},
}


def browsing_regions(dataset, visible_entities):
    """Return display-only groups, including groups inherited by specimens."""
    index = {entity["id"]: entity for entity in dataset["entities"]}
    categories = {fact["subject_id"]: fact["object_id"] for fact in dataset["facts"]
                  if fact["predicate"] in {"INSTANCE_OF", "REFERS_TO_TYPE"}}
    direct = {ident: region for region, ids in REGION_TYPES.items() for ident in ids}

    def region(ident, visited):
        if ident in direct:
            return direct[ident]
        if ident in visited or ident not in index:
            return "reference"
        visited.add(ident)
        entity = index[ident]
        if entity["kind"] in {"Material", "PreservationFeature", "SurfaceFinish", "DecorationMotif"}:
            return "shared"
        if entity["kind"] == "HarnessRole":
            return "harness"
        if "scope_id" in entity:
            return region(entity["scope_id"], visited)
        if ident in categories:
            return region(categories[ident], visited)
        if "马具" in entity["label"]:
            return "harness"
        return "reference"

    return {entity["id"]: region(entity["id"], set()) for entity in visible_entities}


def project_presentation(dataset, snapshot, audience="internal"):
    """Filter one read-only snapshot, retaining source evidence and review states.

    Uses the full validated dataset to classify case records and place nodes,
    but never emits hidden edges as layout metadata. Unknown relations default
    to internal. The optional review flag is handled before this projection.
    """
    if audience not in {"public", "internal"}:
        raise KnowledgeError("audience必须为public或internal")
    result = copy.deepcopy(snapshot)
    index = {e["id"]: e for e in dataset["entities"]}
    cases = {f["subject_id"] for f in dataset["facts"] if f.get("knowledge_basis")
             and index[f["subject_id"]]["kind"] == "ReferenceRecord"}
    group_by_predicate = {p: key for key, _, _, predicates in RELATION_GROUPS for p in predicates}

    def group(fact):
        if fact["predicate"] == "REFERS_TO_TYPE" and fact["subject_id"] in cases:
            return "reconstruction"
        return group_by_predicate.get(fact["predicate"], "other")

    if audience == "public":
        result["entities"] = [e for e in result["entities"] if e["kind"] in PUBLIC_KINDS or e["id"] in cases]
        allowed = {e["id"] for e in result["entities"]}
        groups = {key for key, _, public, _ in RELATION_GROUPS if public}
        result["facts"] = [f for f in result["facts"] if f["subject_id"] in allowed and
                           ("object_id" not in f or (f["object_id"] in allowed and group(f) in groups))]
        evidence_ids = {eid for fact in result["facts"] for eid in fact["evidence_ids"]}
        result["evidence"] = [e for e in result["evidence"] if e["id"] in evidence_ids]
        source_ids = {e["source_id"] for e in result["evidence"]}
        result["sources"] = [s for s in result["sources"] if s["id"] in source_ids]
        result["mappings"] = []
        result["model_report"] = None
        if "media" in result:
            result["media"] = [{**m, "entity_ids": [ident for ident in m["entity_ids"] if ident in allowed]}
                               for m in result["media"] if m["kind"] == "source_clip" and
                               m.get("evidence_id") in evidence_ids and any(ident in allowed for ident in m["entity_ids"])]
        # Counts in public mode describe this projection, not the full dataset.
        result["stats"].update(entities=len(result["entities"]), facts=len(result["facts"]),
                               visible_facts=len(result["facts"]), evidence=len(result["evidence"]), mappings=0,
                               confirmed=sum(f["review_status"] == "confirmed" for f in result["facts"]),
                               pending=sum(f["review_status"] == "pending" for f in result["facts"]),
                               dimension_properties=sum(f["predicate"] == "HAS_DIMENSION" for f in result["facts"]))
        for entity in result["entities"]:
            related = [f for f in result["facts"] if entity["id"] in {f["subject_id"], f.get("object_id")}]
            entity["fact_review_summary"] = {status: sum(f["review_status"] == status for f in related)
                                               for status in ("pending", "confirmed", "disputed")}

    edges = [f for f in result["facts"] if "object_id" in f]
    result["presentation"] = {
        "audience": audience,
        "groups": [{"id": key, "label": label, "public": public,
                    "fact_ids": [f["id"] for f in edges if group(f) == key]}
                   for key, label, public, _ in RELATION_GROUPS if audience == "internal" or public],
        "regions": browsing_regions(dataset, result["entities"]) if audience == "public" else {},
        "note": "本地展示筛选，不是登录或权限控制；复原推测和审核状态保持原样。",
    }
    return result
