"""Join local images to knowledge evidence and versioned model mappings."""

import re
from collections import defaultdict
from pathlib import Path

from .dataset_io import KnowledgeError


def image_path(filename: str, directory: Path | None) -> Path | None:
    if directory is None or not re.fullmatch(r"[a-z0-9-]+\.png", filename):
        return None
    root = directory.resolve()
    path = (root / filename).resolve()
    return path if path.parent == root and path.is_file() else None


def _evidence_targets(facts):
    targets = defaultdict(set)
    for fact in facts:
        entities = {fact["subject_id"], fact.get("object_id")} - {None}
        for evidence_id in fact["evidence_ids"]:
            targets[evidence_id].update(entities)
    return targets


def project_media(dataset, snapshot, manifest, directory=None):
    """Validate catalog links against the full data, then apply query visibility."""
    if manifest["version"] != "0.1.0" or manifest["dataset_id"] != dataset["dataset_id"]:
        raise KnowledgeError("媒体清单版本或对应数据集不匹配")

    visible_mappings = {item["id"] for item in snapshot["mappings"]}
    evidence = {item["id"]: item for item in dataset["evidence"]}
    mappings = {item["id"]: item for item in dataset["model_mappings"]}
    entities = {item["id"]: item for item in dataset["entities"]}
    evidence_entities = _evidence_targets(snapshot["facts"])
    all_evidence_entities = _evidence_targets(dataset["facts"])

    records = []
    seen = set()
    for item in manifest["items"]:
        ident = item["id"]
        targets = set(item["entity_ids"])
        if (ident in seen or not re.fullmatch(r"media:[a-z0-9-]+", ident) or not targets or
                not targets <= entities.keys() or not re.fullmatch(r"[a-z0-9-]+\.png", item["filename"])):
            raise KnowledgeError(f"无效的媒体编号、文件名或实体引用：{ident}")
        seen.add(ident)

        if item["kind"] == "source_clip":
            evidence_id = item["evidence_id"]
            original = evidence.get(evidence_id)
            if (original is None or item["pdf_page"] != original["pdf_page"] or
                    not targets <= all_evidence_entities[evidence_id]):
                raise KnowledgeError(f"截图与证据页或实体关系不一致：{ident}")
            left, top, right, bottom = item["rect_px"]
            width, height = item["page_size_px"]
            if not (0 <= left < right <= width and 0 <= top < bottom <= height):
                raise KnowledgeError(f"截图坐标超出原页：{ident}")
            targets &= evidence_entities[evidence_id]
            if not targets:
                continue
        elif item["kind"] == "model_view":
            mapping_id = item["mapping_id"]
            mapping = mappings.get(mapping_id)
            if (mapping is None or targets != {mapping["entity_id"]} or
                    item["node_indices"] != mapping["node_indices"] or
                    item["model_sha256"] != entities[mapping["model_version_id"]]["content_sha256"]):
                raise KnowledgeError(f"模型图像的节点或版本已变更：{ident}")
            if mapping_id not in visible_mappings:
                continue
        else:
            raise KnowledgeError(f"未知媒体类型：{ident}")

        records.append({**item, "entity_ids": sorted(targets),
                        "available": image_path(item["filename"], directory) is not None})
    return records
