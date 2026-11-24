"""Dataset schema, reference integrity and domain validation."""

import math
import hashlib
import re
from collections import defaultdict
from datetime import date
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from urllib.parse import urlsplit

from .dataset_io import TABLES


ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*:[a-z0-9][a-z0-9._-]*$")
RECORD_SHAPES = {
    "sources": ({"id": str, "title": str, "resource_id": str, "filename": str,
                 "format": str}, {"page_count": int, "note": str}),
    "evidence": ({"id": str, "source_id": str, "pdf_page": int, "locator": str,
                  "quote": str, "transcription": str, "check_status": str,
                  "scope_note": str}, {"figure": str, "printed_page": str}),
    "entities": ({"id": str, "kind": str, "label": str, "aliases": list},
                 {"scope_id": str, "measurement": dict, "resource_id": str,
                  "content_sha256": str, "note": str}),
    "facts": ({"id": str, "subject_id": str, "predicate": str, "evidence_ids": list,
               "origin": str, "review_status": str, "extraction": dict},
              {"object_id": str, "value": str, "basis_fact_ids": list, "rationale": str,
               "review": dict}),
    "model_mappings": ({"id": str, "entity_id": str, "model_version_id": str,
                        "node_indices": list, "review_status": str, "note": str}, {"review": dict}),
}


def validate(data: dict, ontology: dict) -> list[str]:
    """Return shape and semantic errors. Historical review is separate."""
    errors = []

    def error(path, message):
        errors.append(f"{path}: {message}")

    _validate_shape(data, error)
    if errors:
        return errors

    if data["schema_version"] not in {"0.1.0", "0.2.0", "0.3.0", "0.4.0"}:
        error("schema_version", "不支持的版本；请先迁移")
    if data["ontology_version"] != ontology["version"]:
        error("ontology_version", "与本体版本不一致")
    if data["stage"] not in {"candidate", "reviewed"}:
        error("stage", "必须为 candidate 或 reviewed")

    indices = _index_records(data, error)
    _validate_sources(indices["sources"], error)
    _validate_evidence(indices["evidence"], indices["sources"], error)
    _validate_entities(indices["entities"], ontology, error, indices["sources"])
    _validate_facts(indices, ontology, data["stage"], error)
    if not errors:
        _validate_teaching_paths(indices, error)
    _validate_mappings(indices["model_mappings"], indices["entities"], data["stage"], error)
    return errors


def _validate_teaching_paths(indices, error):
    """A schematic hop must have exactly one complete, consistent basis record."""
    predicates = {"CONNECTION_FROM", "CONNECTION_TO", "HAS_EVIDENCE_BASIS"}
    fields = defaultdict(lambda: defaultdict(list))
    paths = {f["id"]: f for f in indices["facts"].values() if f["predicate"] == "SCHEMATIC_NEXT"}
    for fact in indices["facts"].values():
        if fact["predicate"] in predicates:
            fields[fact["subject_id"]][fact["predicate"]].append(fact)
    counts = defaultdict(int)
    for connection_id, group in fields.items():
        if set(group) != predicates or any(len(items) != 1 for items in group.values()):
            error(connection_id, "教学连接必须各有一条起点、终点和依据类别事实")
            continue
        group = {key: items[0] for key, items in group.items()}
        anchors = [set(item.get("basis_fact_ids", [])) & paths.keys() for item in group.values()]
        if any(len(anchor) != 1 for anchor in anchors) or any(anchor != anchors[0] for anchor in anchors):
            error(connection_id, "教学连接的起点、终点和依据类别必须引用同一条路径事实")
            continue
        path_id = next(iter(anchors[0]))
        hop = paths[path_id]
        if (group["CONNECTION_FROM"]["object_id"] != hop["subject_id"]
                or group["CONNECTION_TO"]["object_id"] != hop["object_id"]):
            error(connection_id, "教学连接的起止点与路径事实不一致")
        counts[path_id] += 1
    for path_id in paths:
        if counts[path_id] != 1:
            error(path_id, "教学路径必须恰好对应一组完整的连接依据")


def shape(record, required, optional, path, error):
    if not isinstance(record, dict):
        error(path, "必须为对象")
        return False
    valid = True
    for key, kind in required.items():
        if key not in record or not isinstance(record[key], kind):
            valid = False
            error(f"{path}.{key}", "缺失或类型不合法")
    for key, kind in optional.items():
        if key in record and not isinstance(record[key], kind):
            valid = False
            error(f"{path}.{key}", "类型不合法")
    for key in record.keys() - required.keys() - optional.keys():
        valid = False
        error(f"{path}.{key}", "未定义字段")
    return valid


def _validate_shape(data, error):
    if not shape(data, {"schema_version": str, "ontology_version": str, "dataset_id": str,
                        "stage": str, "description": str, **{name: list for name in TABLES}}, {}, "dataset", error):
        return
    for table, (required, optional) in RECORD_SHAPES.items():
        if table == "facts" and data["schema_version"] in {"0.2.0", "0.3.0", "0.4.0"}:
            optional = {**optional, "value": (str, dict)}
        if data["schema_version"] in {"0.3.0", "0.4.0"}:
            if table == "sources":
                optional = {**optional, "duration_seconds": (int, float),
                            "content_sha256": str, "source_type": str}
            elif table == "evidence":
                required = {key: value for key, value in required.items() if key != "pdf_page"}
                optional = {**optional, "pdf_page": int, "start_seconds": (int, float),
                            "end_seconds": (int, float)}
            elif table == "facts":
                optional = {**optional, "knowledge_basis": str}
        if data["schema_version"] == "0.4.0":
            if table == "sources":
                optional = {**optional, "url": str, "accessed_on": str, "text_content": str}
            elif table == "entities":
                optional = {**optional, "lexeme": str, "source_id": str, "publication_status": str}
            elif table == "evidence":
                optional = {**optional, "start_line": int, "end_line": int}
            elif table == "facts":
                optional = {**optional, "publication_managed": bool}
        if isinstance(data.get(table), list):
            for index, record in enumerate(data[table]):
                shape(record, required, optional, f"{table}[{index}]", error)


def _index_records(data, error):
    indices = {}
    all_ids = set()
    for table in TABLES:
        indices[table] = {}
        for record in data[table]:
            ident = record["id"]
            if not ID_PATTERN.fullmatch(ident) or ident in all_ids:
                error(ident, "ID 格式错误或不唯一")
            all_ids.add(ident)
            indices[table][ident] = record
    return indices


def _validate_sources(sources, error):
    for source in sources.values():
        if source["format"] not in {"pdf", "docx", "md", "mp4", "txt"}:
            error(source["id"], "不支持的文献格式")
        if Path(source["filename"]).name != source["filename"] or ":" in source["filename"] or "\\" in source["filename"]:
            error(source["id"], "filename 必须是相对于资源目录的文件名")
        if "page_count" in source and (type(source["page_count"]) is not int or source["page_count"] < 1):
            error(source["id"], "page_count 必须为正整数")
        if source["format"] == "mp4":
            duration = source.get("duration_seconds")
            if type(duration) not in {int, float} or not math.isfinite(duration) or duration <= 0:
                error(source["id"], "视频 duration_seconds 必须为有限正数")
            if not re.fullmatch(r"[0-9a-f]{64}", source.get("content_sha256", "")):
                error(source["id"], "视频来源必须保存内容 SHA256")
            if source.get("source_type") != "modern_reconstruction_video":
                error(source["id"], "当前视频须标明来源类型 modern_reconstruction_video")
            if "page_count" in source:
                error(source["id"], "视频不能使用 PDF 页数")
        elif source["format"] in {"md", "txt"} and source.get("source_type") == "uploaded_text":
            content = source.get("text_content", "")
            if not content.strip() or len(content) > 80_000 or "\x00" in content:
                error(source["id"], "上传文本不能为空、超过 80000 字符或包含空字符")
            if hashlib.sha256(content.encode("utf-8")).hexdigest() != source.get("content_sha256"):
                error(source["id"], "文本内容与保存的 SHA256 不一致")
            if any(key in source for key in ("page_count", "duration_seconds", "url", "accessed_on")):
                error(source["id"], "上传文本不能使用页数、视频时长或外部词典链接字段")
        elif source["format"] == "md" and source.get("source_type") == "dictionary_excerpt":
            try:
                url = urlsplit(source.get("url", ""))
            except ValueError:
                url = urlsplit("")
            if url.scheme != "https" or not url.hostname or url.username or url.password:
                error(source["id"], "词典摘录必须提供HTTPS官方条目URL，不能包含登录凭据")
            if not re.fullmatch(r"[0-9a-f]{64}", source.get("content_sha256", "")):
                error(source["id"], "词典摘录必须保存内容 SHA256")
            try:
                date.fromisoformat(source.get("accessed_on", ""))
            except ValueError:
                error(source["id"], "词典摘录必须保存ISO访问日期")
            if "duration_seconds" in source or "page_count" in source:
                error(source["id"], "词典条目不能使用视频时长或PDF页数")
        elif any(key in source for key in ("duration_seconds", "content_sha256", "source_type", "url", "accessed_on")):
            error(source["id"], "来源元数据与格式不兼容")
        if source["format"] == "mp4" and any(key in source for key in ("url", "accessed_on")):
            error(source["id"], "本地视频不能使用词典摘录字段")
        if source.get("source_type") != "uploaded_text" and ("text_content" in source or source["format"] == "txt"):
            error(source["id"], "普通文本字段需要 uploaded_text 来源类型")


def _validate_evidence(evidence, sources, error):
    for item in evidence.values():
        ident = item["id"]
        source = sources.get(item["source_id"])
        if source is None or source["format"] not in {"pdf", "mp4", "md", "txt"}:
            error(ident, "证据必须引用已登记PDF、视频或文本")
        if source and source["format"] == "mp4":
            if "pdf_page" in item or "printed_page" in item or "figure" in item:
                error(ident, "视频证据不能使用 PDF 页码或图号")
            start, end = item.get("start_seconds"), item.get("end_seconds")
            if any(type(n) not in {int, float} or not math.isfinite(n) for n in (start, end)):
                error(ident, "视频必须提供有限数值 start_seconds 和 end_seconds")
            elif (type(source.get("duration_seconds")) not in {int, float}
                  or not 0 <= start < end <= source["duration_seconds"]):
                error(ident, "视频时间段越界或起止顺序错误")
            transcriptions = {"video_frame", "video_subtitle"}
        elif source and source.get("source_type") == "uploaded_text":
            if any(key in item for key in ("pdf_page", "printed_page", "figure", "start_seconds", "end_seconds")):
                error(ident, "文本证据不能使用PDF页码或视频时间段")
            lines = source.get("text_content", "").split("\n")
            start, end = item.get("start_line"), item.get("end_line")
            if (type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines)
                    or item["quote"] not in "\n".join(lines[start - 1:end])):
                error(ident, "文本引文必须出现在指定行范围")
            transcriptions = {"embedded_text"}
        elif source and source["format"] == "md":
            if source.get("source_type") != "dictionary_excerpt":
                error(ident, "文字条目证据须引用已登记的词典摘录")
            if any(key in item for key in ("pdf_page", "printed_page", "figure", "start_seconds", "end_seconds")):
                error(ident, "词典条目不能使用PDF页码或视频时间段")
            transcriptions = {"embedded_text"}
        else:
            page = item.get("pdf_page")
            if type(page) is not int or page < 1:
                error(ident, "pdf_page 必须为从 1 开始的正整数")
            elif source and page > source.get("page_count", math.inf):
                error(ident, "PDF 页码越界")
            if "start_seconds" in item or "end_seconds" in item:
                error(ident, "PDF 证据不能使用视频时间段")
            transcriptions = {"embedded_text", "image_transcription"}
        if not item["quote"].strip() or not item["locator"].strip():
            error(ident, "证据原文和定位不能为空")
        if item["transcription"] not in transcriptions:
            error(ident, "未知的转录方式")
        if item["check_status"] not in {"source_checked", "pending"}:
            error(ident, "未知的原文检查状态")
        if (not source or source.get("source_type") != "uploaded_text") and {"start_line", "end_line"} & item.keys():
            error(ident, "行号仅适用于上传文本")


def _validate_measurement(measurement, ontology, ident, error):
    if not shape(measurement, {"quantity": str, "unit": str, "raw": str, "approximate": bool},
                 {"value": (int, float), "min": (int, float), "max": (int, float)}, ident, error):
        return
    scalar = "value" in measurement
    interval = "min" in measurement and "max" in measurement
    if scalar == interval or (scalar and ("min" in measurement or "max" in measurement)):
        error(ident, "尺寸必须为单值或完整范围，不能混用")
    for key in ("value", "min", "max"):
        if key in measurement and (type(measurement[key]) not in {int, float} or
                                   not math.isfinite(measurement[key]) or measurement[key] <= 0):
            error(ident, "尺寸数值必须是有限正数，不能以零或布尔值填空")
    if interval and measurement["min"] > measurement["max"]:
        error(ident, "尺寸范围上下界颠倒")
    if measurement["unit"] not in ontology["units"]:
        error(ident, "未定义的尺寸单位")
    if not measurement["raw"].strip() or not measurement["quantity"].strip():
        error(ident, "尺寸类型和原始表达不能为空")


def _validate_entities(entities, ontology, error, sources=None):
    for item in entities.values():
        ident, kind = item["id"], item["kind"]
        if item.get("publication_status", "published") not in {"draft", "published"}:
            error(ident, "实体发布状态无效")
        if kind not in ontology["entity_kinds"]:
            error(ident, "未定义的实体类型")
        if kind == "ModelVersion" and (not item.get("resource_id") or
                not re.fullmatch(r"[0-9a-f]{64}", item.get("content_sha256", ""))):
            error(ident, "模型版本必须绑定资源 ID 与内容 SHA256")
        if not item["label"].strip() or any(not isinstance(a, str) or not a.strip() for a in item["aliases"]):
            error(ident, "名称/别名必须为非空字符串")
        scope = entities.get(item.get("scope_id"))
        if "scope_id" in item and scope is None:
            error(ident, "scope_id 引用不存在")
        if kind == "TermSense":
            if not item.get("lexeme", "").strip() or item.get("source_id") not in (sources or {}):
                error(ident, "词义节点必须保存原词lexeme及有效来源source_id")
            if "scope_id" in item and (scope is None or scope["kind"] != "ReferenceRecord"):
                error(ident, "词义语境必须指向来源记录，不能当作实物归属")
        elif "lexeme" in item or "source_id" in item:
            error(ident, "lexeme/source_id只用于词义节点")
        if kind in {"Component", "ComponentRegion"} and (scope is None or scope["kind"] not in {"Chariot", "ReferenceSpecimen"}):
            error(ident, "具体部件必须声明所属战车或对照标本")
        if kind == "Measurement":
            measurement = item.get("measurement")
            if measurement is None:
                error(ident, "尺寸实体缺少 measurement")
                continue
            _validate_measurement(measurement, ontology, ident + ".measurement", error)
            if scope is None or scope["kind"] not in {"ReferenceSpecimen", "ReferenceRecord", "Component", "Chariot", "ModelVersion"}:
                error(ident, "尺寸必须声明归属对象")
        elif "measurement" in item:
            error(ident, "只有 Measurement 可携带尺寸值")


def _validate_facts(indices, ontology, stage, error):
    entities, evidence, facts = (indices[name] for name in ("entities", "evidence", "facts"))
    adjacency = defaultdict(lambda: defaultdict(list))
    for fact in facts.values():
        ident = fact["id"]
        subject = entities.get(fact["subject_id"])
        predicate = ontology["predicates"].get(fact["predicate"])
        if subject is None or predicate is None:
            error(ident, "subject_id 或 predicate 未定义")
            continue
        object_id = fact.get("object_id")
        if ("object_id" in fact) == ("value" in fact):
            error(ident, "object_id 和 value 必须且只能提供一个")
        if predicate["object_kind"] == "entity":
            obj = entities.get(object_id)
            if obj is None or [subject["kind"], obj["kind"]] not in predicate["endpoint_pairs"]:
                error(ident, "关系目标不存在或两端类型不允许")
            else:
                if predicate.get("acyclic"):
                    adjacency[fact["predicate"]][subject["id"]].append(object_id)
                if fact["predicate"] == "HAS_MEASUREMENT" and obj.get("scope_id") != subject["id"]:
                    error(ident, "尺寸归属与关系主体不一致")
                if fact["predicate"] == "HAS_PART" and obj["kind"] == "Component":
                    expected = subject["id"] if subject["kind"] in {"Chariot", "ReferenceSpecimen"} else subject.get("scope_id")
                    if obj.get("scope_id") != expected:
                        error(ident, "具体部件跨研究对象组成")
                if fact["predicate"] == "HAS_REGION" and obj["kind"] == "ComponentRegion":
                    expected = subject["id"] if subject["kind"] in {"Chariot", "ReferenceSpecimen"} else subject.get("scope_id")
                    if obj.get("scope_id") != expected:
                        error(ident, "描述区域不能跨标本或研究对象")
                if fact["predicate"] == "HAS_ASSOCIATED_COMPONENT" and obj.get("scope_id") != subject["id"]:
                    error(ident, "所配部件必须归属于当前标本记录")
                if fact["predicate"] == "TENON_JOINT_WITH" and subject.get("scope_id") != obj.get("scope_id"):
                    error(ident, "榫卯连接不能跨标本或研究对象")
                if fact["predicate"] == "TERM_DENOTES":
                    term_source = subject.get("source_id")
                    if not any(evidence.get(eid, {}).get("source_id") == term_source
                               for eid in fact["evidence_ids"] if isinstance(eid, str)):
                        error(ident, "词义指称必须引用该词义所属来源的证据")
                if fact["predicate"] == "USES_TERM":
                    term_source = obj.get("source_id")
                    if not any(evidence.get(eid, {}).get("source_id") == term_source
                               for eid in fact["evidence_ids"] if isinstance(eid, str)):
                        error(ident, "来源用词必须引用该词义所属来源的证据")
        elif predicate["object_kind"] == "dimension":
            if not isinstance(fact.get("value"), dict) or subject["kind"] not in predicate["subject_kinds"]:
                error(ident, "尺寸属性必须为结构化数值，且不能归给通用部件类别")
            else:
                _validate_measurement(fact["value"], ontology, ident + ".value", error)
        elif not isinstance(fact.get("value"), str) or subject["kind"] not in predicate["subject_kinds"]:
            error(ident, "文字事实的主体类型或 value 不合法")
        elif not fact["value"].strip():
            error(ident, "文字事实不能为空")
        if fact["origin"] not in {"documented", "inferred", "hypothesis"}:
            error(ident, "未知的 origin")
        video_backed = any(
            indices["sources"].get(evidence.get(eid, {}).get("source_id"), {}).get("format") == "mp4"
            for eid in fact["evidence_ids"] if isinstance(eid, str))
        knowledge_basis = fact.get("knowledge_basis")
        if video_backed or knowledge_basis is not None:
            if knowledge_basis not in {"modern_reconstruction_observation", "modern_reconstruction_inference"}:
                error(ident, "视频知识必须标注现代复原实验记录或现代复原推测")
            if not video_backed:
                error(ident, "现代复原来源标注必须引用视频证据")
            if knowledge_basis == "modern_reconstruction_inference" and fact["origin"] == "documented":
                error(ident, "现代复原推测不能标为 documented")
        if fact["review_status"] not in {"pending", "confirmed", "disputed"}:
            error(ident, "未知的 review_status")
        if stage == "reviewed" and fact["review_status"] == "pending":
            error(ident, "待审核事实不能进入 reviewed 数据集")
        if not isinstance(fact["evidence_ids"], list) or any(not isinstance(e, str) or e not in evidence for e in fact["evidence_ids"]):
            error(ident, "证据引用不存在或类型错误")
        if fact["origin"] == "documented" and not fact["evidence_ids"]:
            error(ident, "资料记载事实必须附证据")
        basis = fact.get("basis_fact_ids", [])
        if not isinstance(basis, list) or any(not isinstance(b, str) or b not in facts or b == ident for b in basis):
            error(ident, "推导依据引用不合法")
        elif basis:
            adjacency["basis_fact_ids"][ident].extend(basis)
        if fact["origin"] in {"inferred", "hypothesis"} and (not fact.get("rationale", "").strip() or not (basis or fact["evidence_ids"])):
            error(ident, "推导/假设必须说明理由及依据")
        extraction = fact["extraction"]
        shape(extraction, {"method": str, "run_id": str},
              {"model": str, "prompt_version": str}, ident + ".extraction", error)
        if fact["review_status"] != "pending":
            _validate_review(fact.get("review", {}), ident, "缺少审核者", error)

    for relation, graph in adjacency.items():
        try:
            TopologicalSorter(graph).prepare()
        except CycleError:
            error(relation, "发现循环依赖")


def _validate_mappings(mappings, entities, stage, error):
    for mapping in mappings.values():
        model = entities.get(mapping["model_version_id"])
        if mapping["entity_id"] not in entities or model is None or model["kind"] != "ModelVersion":
            error(mapping["id"], "实体或模型版本引用不合法")
        nodes = mapping["node_indices"]
        if not nodes or any(type(n) is not int or n < 0 for n in nodes) or len(set(str(n) for n in nodes)) != len(nodes):
            error(mapping["id"], "节点索引必须为不重复的非负整数")
        if mapping["review_status"] not in {"pending", "confirmed", "disputed"}:
            error(mapping["id"], "映射状态不合法")
        if stage == "reviewed" and mapping["review_status"] == "pending":
            error(mapping["id"], "待审核映射不能进入 reviewed 数据集")
        if mapping["review_status"] != "pending":
            _validate_review(mapping.get("review", {}), mapping["id"], "缺少映射审核者", error)


def _validate_review(review, ident, missing_reviewer, error):
    if not shape(review, {"reviewer": str, "date": str, "note": str}, {}, ident + ".review", error):
        return
    try:
        date.fromisoformat(review["date"])
    except ValueError:
        error(ident, "审核日期必须为 ISO 日期")
    if not review["reviewer"].strip():
        error(ident, missing_reviewer)
