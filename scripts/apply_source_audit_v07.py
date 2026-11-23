"""Replay Codex's recorded source audit and build a revised candidate.

This script is NOT an automated content reviewer. It consumes the 272 manually
adjudicated rows in data/audits, tied to an exact sixth-batch input hash.
It neither marks claims confirmed nor claims an independent human review.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter

from chuchariot.dataset_io import ROOT, read_json, write_json
from chuchariot.validation import validate


AUDIT_PATH = ROOT / "data/audits/2026-11-23-source-audit.json"


def build():
    audit = read_json(AUDIT_PATH)
    source_path = ROOT / audit["input_path"]
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != audit["input_sha256"]:
        raise ValueError("Audit input changed; source judgments must be rechecked.")
    source = read_json(source_path)
    rows = {row["fact_id"]: row for row in audit["fact_reviews"]}
    if len(rows) != len(audit["fact_reviews"]) or set(rows) != {fact["id"] for fact in source["facts"]}:
        raise ValueError("Audit must cover every input fact exactly once.")
    for fact in source["facts"]:
        if rows[fact["id"]]["fact_before"] != fact:
            raise ValueError("Audit row no longer matches " + fact["id"])
    if any(row["verdict"] not in {"source_supported", "needs_correction", "insufficient_evidence", "conflict"}
           or not row["reason"] or not row["references"] for row in rows.values()):
        raise ValueError("Audit has unadjudicated or unsupported review records.")
    for reviewed in audit["source_reviews"]:
        original = next((path for path in [ROOT.parent / reviewed["filename"], ROOT / "assets/references/local" / reviewed["filename"]] if path.is_file()), None)
        if original and hashlib.sha256(original.read_bytes()).hexdigest() != reviewed["sha256"]:
            raise ValueError("Audited PDF changed: " + reviewed["filename"])

    data = copy.deepcopy(source)
    ontology = read_json(ROOT / "data/ontology/ontology.v0.4.json")
    ontology["version"] = "0.5.0"
    ontology["entity_kinds"]["ComponentRegion"] = "资料描述的局部区域，不等同于独立零件或可拆件"
    ontology["predicates"]["HAS_REGION"] = {
        "label": "主体包含描述区域；不表示可拆卸组成或装配步骤", "object_kind": "entity",
        "endpoint_pairs": [[kind, "ComponentRegion"] for kind in ["ReferenceSpecimen", "Chariot", "Component"]],
    }
    for predicate in ["HAS_MATERIAL", "HAS_PRESERVED_FEATURE", "HAS_SURFACE_FINISH", "HAS_DECORATION_MOTIF"]:
        target = ontology["predicates"][predicate]["endpoint_pairs"][0][1]
        ontology["predicates"][predicate]["endpoint_pairs"].append(["ComponentRegion", target])
    for predicate in ["DESCRIPTION", "HAS_PATTERN_DETAIL", "HAS_DIMENSION"]:
        ontology["predicates"][predicate]["subject_kinds"].append("ComponentRegion")
    region_ids = {"component:m1302-front", "component:m1302-middle", "component:m1302-rear"}
    for entity in data["entities"]:
        if entity["id"] in region_ids:
            entity["kind"] = "ComponentRegion"
            entity["note"] = "原文针对M1：302所存残件的描述区域，用于限定髹饰；不代表独立可拆零件或完整车辀的分件。"
    facts = {fact["id"]: fact for fact in data["facts"]}
    for ident in ["fact:001", "fact:002", "fact:003"]:
        facts[ident].update(subject_id="record:wheel-axle-labels", predicate="DEPICTS")
    for ident in ["fact:pdf-074", "fact:pdf-076", "fact:pdf-078"]:
        facts[ident]["predicate"] = "HAS_REGION"
    facts["fact:pdf-089"]["value"] = "原文记33件；现存22件（33件的统计口径未注明）"
    uncertain = facts["fact:pdf-217"]
    uncertain.update(origin="inferred", rationale="依据同页7号车图的红线文字注释与8号车图类似红线进行的图像解释；8号车图无独立“靷”标签，仍待原始报告核实，不作为六号车依据。")
    uncertain["evidence_ids"] = ["evidence:pdf-figure-03", "evidence:pdf-figure-02"]

    merges = []
    for keep, remove in [("fact:035", "fact:pdf-192"), ("fact:038", "fact:pdf-191")]:
        kept, redundant = facts[keep], facts[remove]
        kept["subject_id"] = "component:m1257-bone-cap"
        if kept["predicate"] != redundant["predicate"] or kept["object_id"] != redundant["object_id"]:
            raise ValueError("Proposed merge is not the same scoped claim.")
        if kept["review_status"] != redundant["review_status"] or kept["review_status"] != "pending":
            raise ValueError("Reviewed facts require explicit review reconciliation.")
        kept["evidence_ids"] = list(dict.fromkeys(kept["evidence_ids"] + redundant["evidence_ids"]))
        merges.append({"removed_fact_id": remove, "retained_fact_id": keep,
                       "reason": "原页限定为骨帽；将旧的整件边定位到骨帽后，与已有局部事实重复。",
                       "removed_fact": copy.deepcopy(redundant)})
    removed_ids = {row["removed_fact_id"] for row in merges}
    if any(removed_ids & set(fact.get("basis_fact_ids", [])) for fact in data["facts"]):
        raise ValueError("A removed duplicate is referenced as a derivation basis.")
    data["facts"] = [fact for fact in data["facts"] if fact["id"] not in removed_ids]

    expanded_quotes = {
        "evidence:002": "标本 CH1：5-轮，轮为木质，木质已腐烂，现仅存表面深褐色漆皮。右轮横径132、竖径119厘米",
        "evidence:003": "标本 CH1：3-轴……轴通长272、粗径9.7、细径2.6厘米",
        "evidence:007": "在毂穿进车轴后，为了不使毂掉落，伸出的轴末要安装青铜车軎。",
        "evidence:011": "图二四〇 一号墓出土车器——铜双箍云纹圆筒形车軎（M1：201-1）",
        "evidence:016": "图三一七 一号车马坑——6号车复原图；图内标注：围栏局部",
        "evidence:019": "标本 M1：257……存一只漆骨帽马镳，骨帽黑漆绘勾连云纹。",
    }
    for evidence in data["evidence"]:
        if evidence["id"] in expanded_quotes:
            evidence["quote"] = expanded_quotes[evidence["id"]]
            if "……" in evidence["quote"]:
                evidence["locator"] += "；为补足主体作非连续摘录，省略处用省略号标示"
    data.update(dataset_id="dataset:teacher-pdf-007", ontology_version=ontology["version"],
                description="第七批：依据Codex逐条原页预审修订区域/零件边界、局部髹饰和统计措辞，合并2条重复断言；保留54项尺寸属性，8号车红线解释仍待原报告核实。全部为待审核候选。")
    errors = validate(data, ontology)
    if errors:
        raise ValueError("\n".join(errors))
    claims = [(f["subject_id"], f["predicate"], f.get("object_id"),
               json.dumps(f.get("value"), ensure_ascii=False, sort_keys=True)) for f in data["facts"]]
    if len(claims) != len(set(claims)):
        raise ValueError("Duplicate scoped claims remain.")
    manifest = read_json(ROOT / "data/sources/fusion-media.v0.6.json")
    manifest["dataset_id"] = data["dataset_id"]
    old = {f["id"]: f for f in source["facts"]}
    verdicts = Counter(row["verdict"] for row in rows.values())
    summary = {
        "run_id": "run:20261123-source-audit", "date": audit["date"], "auditor": "Codex",
        "input_dataset": source["dataset_id"], "output_dataset": data["dataset_id"],
        "audit_file": str(AUDIT_PATH.relative_to(ROOT)).replace("\\", "/"),
        "audit_sha256": hashlib.sha256(AUDIT_PATH.read_bytes()).hexdigest(),
        "reviewed_facts": len(rows),
        "verdicts": {key: verdicts[key] for key in ["source_supported", "needs_correction", "insufficient_evidence", "conflict"]},
        "independent_review": False, "formal_confirmations": 0,
        "output_counts": {"entities": len(data["entities"]), "facts": len(data["facts"]),
                          "entity_relations": sum("object_id" in f for f in data["facts"]),
                          "dimension_properties": sum(f["predicate"] == "HAS_DIMENSION" for f in data["facts"]),
                          "evidence": len(data["evidence"]), "model_mappings": len(data["model_mappings"])},
        "changed_fact_ids": [f["id"] for f in data["facts"] if old[f["id"]] != f],
        "changed_entity_ids": sorted(region_ids), "expanded_evidence_ids": list(expanded_quotes),
        "merged_duplicates": merges,
        "unsupported_claims_still_pending": ["fact:pdf-217"],
        "note": "来源支持只表示在当前直接来源和限定内得到支持，包含作者推断与图示观察；不是考古真实性认证。",
    }
    return data, ontology, manifest, summary, audit


def reports(summary, audit):
    labels = {"source_supported": "来源支持", "needs_correction": "需修正", "insufficient_evidence": "证据不足", "conflict": "有冲突"}
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    def claim(row):
        f = row["fact_before"]
        value = row["target_label"] if f.get("object_id") else json.dumps(f["value"], ensure_ascii=False)
        return f'{row["subject_label"]} — {f["predicate"]} — {value}'
    lines = ["# 第六批272条事实的原页审计", "", "2026-11-23 · 审计者：Codex。对象为审计记录锁定哈希的teacher-pdf.v0.6。",
             "", "本轮是同一Codex会话对自己及旧批次整理结果的逐条原页复查，不是独立Agent、老师或组员复核。未提升任何事实为confirmed。",
             "", "## 结论", "", "| 判定 | 原第六批事实数 |", "|---|---:|"]
    lines += [f"| {labels[key]} | {count} |" for key, count in summary["verdicts"].items()]
    lines += ["", "上述分类覆盖全部272条原事实。来源支持包含原文推断、图像观察与目录性说明，不能理解为独立考古结论的数量或准确率。54项尺寸逐项对照原页，数值、单位、范围、近似及所有者未发现不一致。276与272分别属于不同记录，不当作冲突。",
              "", "修订候选v0.7：95个实体、270条待审核事实、107条实体关系、54项尺寸属性、52段证据和7组未审核模型映射。两条骨帽髹饰/纹饰重复边已合并，完整迁移关系和被合并记录保存在运行摘要；没有删除独立来源断言。",
              "", "## 本轮修正与待核", "", "| 原事实ID | 判定 | 问题与处理 |", "|---|---|---|"]
    for row in audit["fact_reviews"]:
        if row["verdict"] != "source_supported":
            lines.append(f'| `{row["fact_id"]}` | {labels[row["verdict"]]} | {cell(row["reason"] + " " + row["recommended_action"])} |')
    lines += ["", "另外补全6段过短证据摘录的主体、标本号或图中标注，非连续摘录显式使用省略号。仅涉及来源表达完整性，不改变尺寸数值。",
              "", "## 来源与检查范围", "", "| 来源ID | 文件 | PDF页序 |", "|---|---|---|"]
    for source in audit["source_reviews"]:
        pages = "、".join(str(row["pdf_page"]) for row in source["reviewed_pages"])
        lines.append(f'| `{source["source_id"]}` | {source["filename"]} | {pages} |')
    lines += ["", "教师汇编10页全部重新渲染，其中第10页空白；三份补充PDF检查的是8条既有事实涉及的5个PDF页，并非重新全文提取。四份文件内容哈希、页面复查备注、52段证据及逐条输入事实完整保存在[机器可读审计表](../../data/audits/2026-11-23-source-audit.json)。",
              "", "[覆盖与缺口](2026-11-23-coverage.md) · [修订摘要与合并索引](../../data/run-summaries/2026-11-23-source-audit.json) · [修订候选v0.7](../../data/candidates/teacher-pdf.v0.7.json)",
              "", "## 全部272条逐条判定", "", "表中是修订前第六批的原断言及其审计结论；修订后数值、范围和审核元数据可通过摘要追溯。不是把当前270条重新编号为272条。",
              "", "| 原事实ID | 原断言 | 出处与证据ID | 判定 | 核对说明 |", "|---|---|---|---|---|"]
    for row in audit["fact_reviews"]:
        refs = "；".join(f'{ref["source_id"]} PDF第{ref["pdf_page"]}页 / {ref["evidence_id"]}' for ref in row["references"])
        lines.append(f'| `{row["fact_id"]}` | {cell(claim(row))} | {refs} | {labels[row["verdict"]]} | {cell(row["reason"])} |')
    coverage = ["# 本轮审计覆盖与知识缺口", "", "2026-11-23 · 审计范围和知识完备度分开记录。本轮覆盖272/272条既有事实，不代表资料提取召回率100%，也不代表楚国战车知识已完备。",
                "", "## 实际查看的原页", "", "| 来源 | PDF页 | 页内核对范围 |", "|---|---:|---|"]
    for source in audit["source_reviews"]:
        for page in source["reviewed_pages"]:
            coverage.append(f'| {source["source_id"]} | {page["pdf_page"]} | {cell(page["review_note"])} |')
    coverage += ["", "## 尚未闭合的缺口", ""] + [f"- {gap}" for gap in audit["remaining_gaps"]]
    coverage += ["", "## 后续处理顺序", "", "1. 复核第七批修正及8号车图的解释，保留实际审核者和理由；AI自查不能冒充独立审核。",
                 "2. 获取或查阅原始发掘报告，核实车号、标本号、图号、未编号轴/辀以及M1：257镳的同一性。",
                 "3. 对已选资料逐段建立部件名称、功能、组成、连接、材质、尺寸、加工和适用范围的覆盖矩阵，补提有依据的通用知识。",
                 "4. 对原资料只有标题、字形不清或缺少归属的内容继续保留空缺，不用模型尺寸或图形比例填补。",
                 "", "尚未重新核验GLB几何与7组模型映射，未验证论文所述力学解释的实验正确性；作者观点只按来源归因保存。"]
    return "\n".join(lines) + "\n", "\n".join(coverage) + "\n"


if __name__ == "__main__":
    data, ontology, manifest, summary, audit = build()
    for path, value in [("data/candidates/teacher-pdf.v0.7.json", data),
                        ("data/ontology/ontology.v0.5.json", ontology),
                        ("data/sources/fusion-media.v0.7.json", manifest),
                        ("data/run-summaries/2026-11-23-source-audit.json", summary)]:
        write_json(ROOT / path, value)
    report, coverage = reports(summary, audit)
    directory = ROOT / "docs/audits"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "2026-11-23-source-audit.md").write_text(report, encoding="utf-8")
    (directory / "2026-11-23-coverage.md").write_text(coverage, encoding="utf-8")
    print(json.dumps({"verdicts": summary["verdicts"], "output_counts": summary["output_counts"]}, ensure_ascii=False, indent=2))
