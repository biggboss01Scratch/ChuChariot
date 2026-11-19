"""JSON file handling and shared dataset paths."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "data/candidates/wheel-axle.v0.1.json"
DEFAULT_ONTOLOGY = ROOT / "data/ontology/ontology.v0.1.json"
TABLES = ("sources", "evidence", "entities", "facts", "model_mappings")


class KnowledgeError(ValueError):
    """Invalid knowledge input; messages are safe to display to local users."""


def read_json(path: str | Path) -> dict:
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise KnowledgeError(f"重复 JSON 字段：{key}")
            result[key] = value
        return result

    with Path(path).open(encoding="utf-8-sig") as stream:
        return json.load(stream, object_pairs_hook=unique_pairs)


def write_json(path: str | Path, value: dict) -> None:
    """Replace only after successful serialization; identical imports do not rewrite."""
    path = Path(path)
    content = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent,
                                delete=False, suffix=".tmp") as stream:
            temp_path = Path(stream.name)
            stream.write(content)
        temp_path.replace(path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
