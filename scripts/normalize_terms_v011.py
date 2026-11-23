"""Normalize component regions and contextual senses while retaining old IDs."""

import copy
import hashlib

from chuchariot.dataset_io import ROOT, TABLES, read_json, write_json
from chuchariot.validation import validate


DATASET = ROOT / "data/candidates/knowledge.v0.11.json"
ONTOLOGY = ROOT / "data/ontology/ontology.v0.7.json"
REGIONS = {
    "type:spoke-inner": ("component:ch15-spoke-inner", "股", "辐靠近毂的内段", "fact:pdf-134", "fact:v09-tree-04"),
    "type:spoke-outer": ("component:ch15-spoke-outer", "骹", "辐靠近轮牙的外段", "fact:pdf-136", "fact:v09-tree-05"),
    "type:hub-ridge": ("component:ch15-hub-ridges", "篆（毂上窄篆）", "毂轵部的环棱状特征区域", "fact:pdf-151", None),
}


def excerpt_source(key, title, filename, url):
    path = ROOT / "data/sources/terminology" / filename
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return {"id": f"source:moe-{key}", "title": title, "resource_id": f"res:moe-{key}",
            "filename": filename, "format": "md", "source_type": "dictionary_excerpt",
            "url": url, "accessed_on": "2026-11-23", "content_sha256": hashlib.sha256(raw).hexdigest(),
            "note": "官方辞书条目的人工摘录，非原网页副本；只解释词义，不充当六号车实物构造证据。"}


def build_ontology():
    ontology = copy.deepcopy(read_json(ROOT / "data/ontology/ontology.v0.6.json"))
    ontology["version"] = "0.7.0"
    ontology["entity_kinds"]["ComponentRegion"] = "具体构件的描述部位或形态特征区域；不是独立分件，保留标本归属"
    ontology["entity_kinds"]["StructuralRegionType"] = "构件部位或形态特征区域的类别；可来自文献或教学，实测范围由实例及证据确定"
    ontology["entity_kinds"]["TermSense"] = "特定来源、语境或义项中的词义记录；不代表独立实物构件，不作全局同义归并"
    predicates = ontology["predicates"]
    predicates["INSTANCE_OF"]["endpoint_pairs"].append(["ComponentRegion", "StructuralRegionType"])
    predicates["HAS_REGION"]["endpoint_pairs"].append(["ComponentType", "StructuralRegionType"])
    predicates["HAS_REGION"]["acyclic"] = True
    predicates["HAS_REGION"]["label"] = "包含描述部位或形态特征区域，不表示独立分件或装配步骤"
    predicates["TENON_JOINT_WITH"]["endpoint_pairs"] += [["ComponentRegion", "Component"], ["Component", "ComponentRegion"]]
    predicates["TENON_JOINT_WITH"]["label"] = "构件或其明确部位与构件榫卯相接；部位不因此成为独立零件"
    for name in ("HAS_SHAPE", "HAS_RECORDED_QUANTITY", "HAS_POSITION", "HAS_PROCESSING"):
        if "ComponentRegion" not in predicates[name]["subject_kinds"]:
            predicates[name]["subject_kinds"].append("ComponentRegion")
    predicates["DESCRIPTION"]["subject_kinds"].append("TermSense")
    predicates["IN_SUBSYSTEM"]["endpoint_pairs"].append(["TermSense", "Subsystem"])
    predicates["IN_SUBSYSTEM"]["label"] = "构件类别、区域类别或来源词项归入教学栏目，可跨栏目"
    predicates["USES_TERM"] = {"label": "来源记录使用特定语境词项，不代表增加一个实物部件",
                                "object_kind": "entity", "endpoint_pairs": [["ReferenceRecord", "TermSense"]]}
    predicates["TERM_DENOTES"] = {"label": "该来源词义在明确语境下指称规范概念，非全局同义",
                                  "object_kind": "entity", "endpoint_pairs": [["TermSense", "ComponentType"]]}
    predicates["TERM_RELATED_TO"] = {"label": "该词义涉及某概念，不断言同义、上下位或整体部分关系",
                                     "object_kind": "entity", "endpoint_pairs": [["TermSense", "ComponentType"]]}
    return ontology


def build():
    base = read_json(ROOT / "data/candidates/knowledge.v0.10.json")
    data = copy.deepcopy(base)
    ontology = build_ontology()
    data.update(schema_version="0.4.0", ontology_version=ontology["version"], dataset_id="dataset:knowledge-011",
                description="继承v0.10，统一股骹与窄篆的区域表达，规范马勒并保留辔的来源语境及多义；尺寸、视频与模型映射保留。")
    entities = {e["id"]: e for e in data["entities"]}
    facts = {f["id"]: f for f in data["facts"]}
    extraction = {"method": "evidence_based_terminology_normalization", "run_id": "run:20261123-normalize-v011"}

    for type_id, (instance, label, meaning, part_fact, type_fact) in REGIONS.items():
        entities[type_id].update(kind="StructuralRegionType", label=label,
                                 note=f"本项目中指{meaning}；用区域关系表达，不据此认定为可拆装零件。")
        entities[instance].update(kind="ComponentRegion", note=f"CH1：5对照轮的{meaning}，保留原尺寸与标本范围；不是独立分件。")
        facts[part_fact]["predicate"] = "HAS_REGION"
        if type_fact:
            facts[type_fact]["predicate"] = "HAS_REGION"
            facts[type_fact]["rationale"] += "统一为部位类别，不表示辐由可拆的股、骹两件拼成。"
        if type_id == "type:hub-ridge":
            entities[type_id]["aliases"] = ["篆", "窄篆"]
            entities[instance]["note"] += "只记录环棱形态，制作方式及是否使用附加材料未由这段资料说明。"

    entities["type:bridle"].update(
        kind="TermSense", label="辔（教师资料中的马勒用法）", lexeme="辔", source_id="source:001",
        scope_id="record:m2432-reconstruction",
        note="保留旧ID以兼容交接。本节点记录教师资料第7页小节名“辔”及第8页马勒图的语境，不是另一件独立马具，也不代表所有辔都等于马勒。")
    entities["type:horse-bridle"]["aliases"] = ["勒", "马勒"]
    entities["type:horse-bridle"]["note"] = "马勒的规范讲解概念。教师资料“辔”小节的图题称马勒，原词另存为词义节点；不将缰绳义的辔全局并入本节点，也不据此确定六号车具体构造。"
    entities["type:reins"]["aliases"] = ["缰绳"]
    facts["fact:pdf-195"].update(predicate="USES_TERM", evidence_ids=["evidence:v11-pei-heading", "evidence:pdf-figure-16"])
    facts["fact:v09-functional-03"].update(
        subject_id="type:bridle", predicate="TERM_DENOTES", object_id="type:horse-bridle", origin="inferred",
        evidence_ids=["evidence:v11-pei-heading", "evidence:pdf-figure-16"],
        rationale="依据教师资料第7页“辔”小节接续第8页“马勒推测复原图”，在本来源图示语境下对齐到马勒；不是全局同义、上下位或实物组成断言。")
    path_suffixes = ("cheekpiece-bridle", "bridle-reins")
    for fact in data["facts"]:
        if fact["predicate"] in {"SCHEMATIC_NEXT", "CONNECTION_FROM", "CONNECTION_TO"}:
            for key in ("subject_id", "object_id"):
                if fact.get(key) == "type:bridle":
                    fact[key] = "type:horse-bridle"
        if any(fact["id"].startswith(prefix + suffix) for prefix in ("fact:v09-path-", "fact:v09-connection-") for suffix in path_suffixes):
            fact["rationale"] += " 本来源原称辔，现依马勒图统一到规范马勒概念；保持教学导航性质。"
            fact["evidence_ids"] = list(dict.fromkeys([*fact["evidence_ids"], "evidence:v11-pei-heading", "evidence:pdf-figure-16"]))
    for suffix, label in [("cheekpiece-bridle", "镳 → 马勒（连接路径）"), ("bridle-reins", "马勒 → 缰（连接路径）")]:
        connection = entities[f"connection:v09-{suffix}"]
        connection.update(label=label, note=connection.get("note", "") + " 原ID保留；教师原称辔已按马勒图统一为规范讲解对象。")

    data["sources"] += [
        excerpt_source("pei", "教育部《重编国语辞典修订本》“轡”条（项目摘录）", "moe-pei-20261123.md",
                       "https://dict.revised.moe.edu.tw/dictView.jsp?ID=669&la=0&powerMode=0"),
        excerpt_source("le", "教育部《重编国语辞典修订本》“勒”条（项目摘录）", "moe-le-20261123.md",
                       "https://dict.revised.moe.edu.tw/dictView.jsp?ID=3203"),
    ]
    data["evidence"] += [
        {"id": "evidence:v11-pei-heading", "source_id": "source:001", "pdf_page": 7,
         "locator": "PDF第7页下半部小节标题，接续第8页马勒推测复原图", "quote": "（二）辔",
         "transcription": "image_transcription", "check_status": "source_checked",
         "scope_note": "这里只记录来源原称；与下一页图题的对齐是本来源语境解释，不把辔的所有义项等同马勒。"},
        {"id": "evidence:v11-pei-reins", "source_id": "source:moe-pei", "locator": "“轡”条，名词义项1",
         "quote": "控制牛、馬等牲口的韁繩。", "transcription": "embedded_text", "check_status": "source_checked",
         "scope_note": "现代辞书对词义的解释，非某辆出土车的构件材质、安装或数量证据。"},
        {"id": "evidence:v11-pei-broad", "source_id": "source:moe-pei", "locator": "“轡”条，名词义项2",
         "quote": "指韁繩與套在牲口嘴中的銜勒。", "transcription": "embedded_text", "check_status": "source_checked",
         "scope_note": "保留合称义，不由此建立辔与马勒固定的全局同义或上下位关系。"},
        {"id": "evidence:v11-le-definition", "source_id": "source:moe-le", "locator": "“勒”条，lè名词义项1",
         "quote": "有嚼口的馬絡頭。", "transcription": "embedded_text", "check_status": "source_checked",
         "scope_note": "仅采用马具义；不混入动词、书法、姓氏等义项，不据辞书确定六号车的构造。"},
    ]
    for ident, label, note in [
        ("term:pei-reins", "辔（缰绳义）", "辞书“轡”名词义项1，指御者操控牲口的缰绳。"),
        ("term:pei-broad", "辔（缰绳与衔勒合称义）", "辞书“轡”名词义项2，涉及缰绳与衔勒；不定义为某个独立分件。"),
    ]:
        data["entities"].append({"id": ident, "kind": "TermSense", "label": label, "aliases": [],
                                 "lexeme": "辔", "source_id": "source:moe-pei", "note": note})

    def add(key, subject, predicate, evidence_ids, *, value=None, object_id=None, origin="documented", rationale=None):
        fact = {"id": f"fact:v11-{key}", "subject_id": subject, "predicate": predicate,
                "evidence_ids": evidence_ids, "origin": origin, "review_status": "pending", "extraction": copy.deepcopy(extraction)}
        fact["value" if value is not None else "object_id"] = value if value is not None else object_id
        if rationale:
            fact["rationale"] = rationale
        data["facts"].append(fact)

    add("pei-teacher-description", "type:bridle", "DESCRIPTION", ["evidence:v11-pei-heading", "evidence:pdf-figure-16"],
        value="教师资料以辔为小节名，接续M2：432马勒推测复原图；本项目在这一图示语境下用马勒作为规范讲解对象，保留辔为来源用词。",
        origin="inferred", rationale="根据连续小节和图题进行来源内词义对齐，不把该用法外推到其他文献的辔。")
    add("pei-reins-description", "term:pei-reins", "DESCRIPTION", ["evidence:v11-pei-reins"], value="现代辞书中，辔有控制牛马等牲口的缰绳这一义项。")
    add("pei-reins-denotes", "term:pei-reins", "TERM_DENOTES", ["evidence:v11-pei-reins"], object_id="type:reins")
    add("pei-broad-description", "term:pei-broad", "DESCRIPTION", ["evidence:v11-pei-broad"], value="现代辞书中，辔另有缰绳与衔勒的合称义，不等于一个独立分件。")
    for suffix, target in [("reins", "type:reins"), ("bridle", "type:horse-bridle")]:
        add(f"pei-broad-related-{suffix}", "term:pei-broad", "TERM_RELATED_TO", ["evidence:v11-pei-broad", "evidence:v11-le-definition"],
            object_id=target, origin="inferred", rationale="按辞书合称义关联缰绳及马勒讲解概念，只表达涉及，不建立全局同义或构件包含关系。")
    add("le-description", "type:horse-bridle", "DESCRIPTION", ["evidence:v11-le-definition"], value="《重编国语辞典修订本》以有嚼口的马络头解释勒的马具义；本项目采用该义规范马勒概念。")
    for type_id, (_, _, meaning, _, _) in REGIONS.items():
        add(f"region-{type_id.split(':')[1]}", type_id, "DESCRIPTION", ["evidence:pdf-p06-t01"], value=f"在CH1：5对照轮描述语境中，这里指{meaning}；该部位类别不表示独立可拆零件。")
    add("hub-has-ridge-region", "type:003", "HAS_REGION", ["evidence:pdf-p06-t01"], object_id="type:hub-ridge",
        origin="inferred", rationale="依据CH1：5对照轮毂轵部窄篆的记载设置部位类别关联，只用于该资料语境的讲解，不断言所有毂都有窄篆。")

    # Changed records keep their IDs and evidence. Record the new operation too.
    old_indices = {table: {r["id"]: r for r in base[table]} for table in TABLES}
    for fact in data["facts"]:
        old = old_indices["facts"].get(fact["id"])
        if old is not None and old != fact:
            fact["extraction"] = copy.deepcopy(extraction)
    errors = validate(data, ontology)
    if errors:
        raise ValueError("\n".join(errors))
    changes = {}
    for table in TABLES:
        index = {r["id"]: r for r in data[table]}
        changes[table] = {
            "added_ids": [ident for ident in index if ident not in old_indices[table]],
            "modified": [{"id": ident, "before": old_indices[table][ident], "after": record}
                         for ident, record in index.items() if ident in old_indices[table] and record != old_indices[table][ident]],
            "removed_ids": [ident for ident in old_indices[table] if ident not in index],
        }
    summary = {"dataset_id": data["dataset_id"], "baseline": base["dataset_id"], "ontology_version": ontology["version"],
               "baseline_sha256": hashlib.sha256((ROOT / "data/candidates/knowledge.v0.10.json").read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
               "schema_version": data["schema_version"], "changes": changes,
               "totals": {table: len(data[table]) for table in TABLES},
               "dimension_properties": sum(f["predicate"] == "HAS_DIMENSION" for f in data["facts"]),
               "entity_relations": sum("object_id" in f for f in data["facts"]),
               "formal_confirmations": 0,
               "notes": ["旧ID保留，但type:bridle现为来源词义，机械/教学导航端点统一为type:horse-bridle。",
                         "部位与部件均可高亮；本次未新增模型映射。", "原v0.10及队友v0.9快照保持不变。"]}
    return data, ontology, summary


def main():
    data, ontology, summary = build()
    write_json(ONTOLOGY, ontology)
    write_json(DATASET, data)
    write_json(ROOT / "data/run-summaries/2026-11-23-normalization-v011.json", summary)
    media = copy.deepcopy(read_json(ROOT / "data/sources/fusion-media.v0.10.json"))
    media["dataset_id"] = data["dataset_id"]
    write_json(ROOT / "data/sources/fusion-media.v0.11.json", media)
    print({"dataset_id": data["dataset_id"], "totals": summary["totals"],
           "dimensions": summary["dimension_properties"], "relations": summary["entity_relations"]})


if __name__ == "__main__":
    main()
