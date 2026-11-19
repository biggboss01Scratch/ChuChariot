"""Read-only source inventory and structural GLB inspection; no geometry claims."""

from __future__ import annotations

import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

from .dataset_io import KnowledgeError


def inspect_glb(path: Path) -> dict:
    raw = path.read_bytes()
    if len(raw) < 20:
        raise KnowledgeError("GLB 文件过短")
    magic, version, length = struct.unpack_from("<4sII", raw)
    size, kind = struct.unpack_from("<II", raw, 12)
    if magic != b"glTF" or version != 2 or length != len(raw) or kind != 0x4E4F534A or 20 + size > length:
        raise KnowledgeError("GLB 头部或 JSON 块不合法")
    gltf = json.loads(raw[20:20 + size])
    nodes = gltf.get("nodes", [])
    named = [{"node_index": i, "name": n["name"], "children": n.get("children", [])}
             for i, n in enumerate(nodes) if n.get("name")]
    counts = Counter(n["name"] for n in named)
    animations = []
    for index, animation in enumerate(gltf.get("animations", [])):
        animations.append({"index": index, "name": animation.get("name"),
                           "channel_count": len(animation.get("channels", [])),
                           "target_node_count": len({c.get("target", {}).get("node")
                                                     for c in animation.get("channels", [])})})
    return {"model_resource_id": "res:005", "sha256": hashlib.sha256(raw).hexdigest(),
            "asset": gltf.get("asset", {}), "node_count": len(nodes),
            "mesh_count": len(gltf.get("meshes", [])), "named_nodes": named,
            "duplicate_names": sorted(name for name, count in counts.items() if count > 1),
            "animations": animations,
            "inspection_scope": "结构元数据；未渲染、未核验几何正确性和动画播放效果。"}


def inventory(resource_dir: Path, specs: dict) -> dict:
    result = []
    root = resource_dir.resolve()
    for spec in specs["resources"]:
        path = (root / spec["filename"]).resolve()
        if path.parent != root:
            raise KnowledgeError("资源文件必须直接位于指定资源目录内")
        record = dict(spec)
        record["availability"] = "present" if path.is_file() else "missing"
        if path.is_file():
            record["bytes"] = path.stat().st_size
            with path.open("rb") as stream:
                record["sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
        result.append(record)
    return {"schema_version": "0.1.0", "path_policy": "文件名相对于显式指定的资源目录；不保存本机绝对路径。",
            "resources": result}


def check_mapping_indices(data: dict, report: dict) -> list[str]:
    """Check hash and index bounds only; this does not verify semantic geometry."""
    errors = []
    entities = {e["id"]: e for e in data["entities"]}
    for mapping in data["model_mappings"]:
        model = entities[mapping["model_version_id"]]
        if model.get("resource_id") != report.get("model_resource_id"):
            errors.append(f"{mapping['id']}: 报告资源与模型不匹配")
        elif model.get("content_sha256") != report.get("sha256"):
            errors.append(f"{mapping['id']}: 模型内容 SHA256 已变化，映射必须重新核验")
        elif any(index >= report.get("node_count", 0) for index in mapping["node_indices"]):
            errors.append(f"{mapping['id']}: 模型节点索引越界")
    return errors
