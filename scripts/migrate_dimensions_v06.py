"""Migrate dimension nodes to evidence-bearing structured property facts.

This changes representation, never extracts or confirms new historical claims.
The fifth batch remains immutable and every removed node is mapped to its fact.
"""

from __future__ import annotations

import copy
import hashlib
from collections import Counter

from chuchariot.dataset_io import ROOT, read_json, write_json
from chuchariot.validation import validate


def build():
    source_path = ROOT / "data/candidates/teacher-pdf.v0.5.json"
    source = read_json(source_path)
    data = copy.deepcopy(source)
    ontology = read_json(ROOT / "data/ontology/ontology.v0.3.json")
    ontology["version"] = "0.4.0"
    del ontology["entity_kinds"]["Measurement"]
    previous = ontology["predicates"].pop("HAS_MEASUREMENT")
    ontology["predicates"]["HAS_DIMENSION"] = {
        "label": "具有尺寸或距离属性；保留项目、数值、单位及原文",
        "object_kind": "dimension",
        "subject_kinds": list(dict.fromkeys(pair[0] for pair in previous["endpoint_pairs"])),
    }
    dimensions = {entity["id"]: entity for entity in source["entities"] if entity["kind"] == "Measurement"}
    migrations = []
    for fact in data["facts"]:
        if fact["predicate"] == "HAS_MEASUREMENT":
            dimension = dimensions[fact.pop("object_id")]
            if dimension["scope_id"] != fact["subject_id"]:
                raise ValueError(f"Dimension ownership mismatch: {fact['id']}")
            fact["predicate"] = "HAS_DIMENSION"
            fact["value"] = copy.deepcopy(dimension["measurement"])
            migrations.append({"legacy_entity_id": dimension["id"], "legacy_label": dimension["label"],
                               "subject_id": fact["subject_id"], "fact_id": fact["id"]})
    counts = Counter(row["legacy_entity_id"] for row in migrations)
    if set(counts) != set(dimensions) or any(count != 1 for count in counts.values()):
        raise ValueError("Migration requires exactly one owner fact per dimension node; resolve ambiguity first.")
    data["entities"] = [entity for entity in data["entities"] if entity["id"] not in dimensions]
    if any(fact["subject_id"] in dimensions or fact.get("object_id") in dimensions for fact in data["facts"]):
        raise ValueError("Other relations refer to a dimension node; resolve before removing it.")
    if any(mapping["entity_id"] in dimensions for mapping in data["model_mappings"]):
        raise ValueError("Dimension has a model mapping; resolve before removing it.")
    data.update(schema_version="0.2.0", ontology_version=ontology["version"], dataset_id="dataset:teacher-pdf-006",
                description="第六批：继承v0.5全部272条候选断言，将54个尺寸节点迁移为所属实体的结构化属性；不增加或确认历史知识。")
    errors = validate(data, ontology)
    if errors:
        raise ValueError("\n".join(errors))
    manifest = read_json(ROOT / "data/sources/fusion-media.v0.5.json")
    manifest["dataset_id"] = data["dataset_id"]
    manifest.pop("compatible_dataset_ids", None)
    for item in manifest["items"]:
        item["entity_ids"] = sorted({dimensions[ident]["scope_id"] if ident in dimensions else ident for ident in item["entity_ids"]})
    summary = {
        "run_id": "run:20261123-dimension-properties", "date": "2026-11-23",
        "source_dataset": source["dataset_id"], "dataset_id": data["dataset_id"],
        "source_dataset_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "schema_version": data["schema_version"], "ontology_version": data["ontology_version"],
        "counts": {"entities": len(data["entities"]), "facts": len(data["facts"]),
                   "dimension_properties": len(migrations), "entity_relations": sum("object_id" in fact for fact in data["facts"]),
                   "evidence": len(data["evidence"]), "model_mappings": len(data["model_mappings"])},
        "new_historical_claims": 0, "review_status_changes": 0,
        "migrations": migrations,
        "notes": ["尺寸仍逐项保留原事实ID、证据、来源性质、审核状态和抽取记录。",
                  "保留横径/竖径、残长/通长、近似、范围及原始表达；不自动平均、覆盖或换算原始值。",
                  "同主体同项目可有多个来源的属性事实，需逐条核对，不能按项目名覆盖。"],
    }
    return data, ontology, manifest, summary


if __name__ == "__main__":
    data, ontology, manifest, summary = build()
    for path, value in [("data/candidates/teacher-pdf.v0.6.json", data),
                        ("data/ontology/ontology.v0.4.json", ontology),
                        ("data/sources/fusion-media.v0.6.json", manifest),
                        ("data/run-summaries/2026-11-23-dimension-properties.json", summary)]:
        write_json(ROOT / path, value)
    print(summary["counts"])
