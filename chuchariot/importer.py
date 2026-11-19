"""Merge complete candidate bundles and commit the result atomically."""

import copy
from pathlib import Path

from .dataset_io import TABLES, KnowledgeError, read_json, write_json
from .validation import validate


def import_dataset(incoming: dict, output: Path, ontology: dict) -> dict:
    """Import full candidate packages; conflicts require explicit human reconciliation."""
    errors = validate(incoming, ontology)
    if errors:
        raise KnowledgeError("\n".join(errors))
    if not output.exists():
        result = copy.deepcopy(incoming)
    else:
        result = read_json(output)
        errors = validate(result, ontology)
        if errors:
            raise KnowledgeError("目标数据集不合法：\n" + "\n".join(errors))
        for field in ("schema_version", "ontology_version", "dataset_id", "stage", "description"):
            if result[field] != incoming[field]:
                raise KnowledgeError(f"导入元数据冲突：{field}；请先显式迁移或合并")
        for table in TABLES:
            index = {r["id"]: r for r in result[table]}
            for record in incoming[table]:
                if record["id"] in index and index[record["id"]] != record:
                    raise KnowledgeError(f"冲突记录：{record['id']}；未覆盖原数据")
                index[record["id"]] = copy.deepcopy(record)
            result[table] = sorted(index.values(), key=lambda r: r["id"])
    errors = validate(result, ontology)
    if errors:
        raise KnowledgeError("合并结果不合法：\n" + "\n".join(errors))
    # Normalize ordering on the first import as well, making replay byte-identical.
    for table in TABLES:
        result[table] = sorted(result[table], key=lambda r: r["id"])
    write_json(output, result)
    return result
