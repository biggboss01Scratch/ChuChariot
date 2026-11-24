"""Check text proposals against the effective graph and build ordinary change sets."""

from dataclasses import dataclass, field
from decimal import Decimal
from difflib import SequenceMatcher
from hashlib import sha256
from pathlib import PurePath
import re
from typing import Literal
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..backend.database import fingerprint
from ..dataset_io import KnowledgeError
from ..validation import ID_PATTERN, _validate_measurement

MAX_TEXT = 80_000
IMPORT_KINDS = {"Chariot", "ReferenceSpecimen", "ReferenceRecord", "ComponentType", "Component",
                "StructuralRegionType", "ComponentRegion", "Material", "PreservationFeature",
                "SurfaceFinish", "DecorationMotif", "HarnessRole"}
IMPORT_PREDICATES = {"DESCRIPTION", "HAS_DIMENSION", "HAS_PART", "HAS_REGION", "HAS_MATERIAL",
                     "TENON_JOINT_WITH", "HAS_PRESERVED_FEATURE", "HAS_SURFACE_FINISH",
                     "HAS_ASSOCIATED_COMPONENT", "HAS_DECORATION_MOTIF", "INSTANCE_OF"}
UNITS_IN_MM = {"mm": Decimal(1), "cm": Decimal(10), "m": Decimal(1000)}
SPECIMEN_CODE = re.compile(r"(?i)[a-z][a-z0-9]*(?:[-:：][a-z0-9]+)*[-:：]\s*\d+[a-z0-9-]*")


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class UploadedText(Input):
    filename: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=MAX_TEXT)

    @model_validator(mode="after")
    def normalize_file(self):
        if (PurePath(self.filename).suffix.lower() not in {".md", ".txt"}
                or any(ch in self.filename for ch in "/\\:\x00\r\n")):
            raise ValueError("请选择 Markdown 或 TXT 文本文件")
        self.text = self.text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
        if not self.text.strip() or "\x00" in self.text:
            raise ValueError("文本为空或包含无效字符")
        self.text.encode("utf-8")
        return self


class EntityRef(Input):
    label: str = Field(min_length=1, max_length=180)
    id: str | None = Field(None, max_length=120, pattern=ID_PATTERN.pattern)
    kind: str | None = Field(None, max_length=64)
    scope_id: str | None = Field(None, max_length=120, pattern=ID_PATTERN.pattern)


class Proposal(Input):
    subject: EntityRef
    predicate: str = Field(min_length=1, max_length=80)
    object: EntityRef | None = None
    value: str | dict | None = None
    origin: Literal["documented", "inferred", "hypothesis"] = "documented"
    rationale: str = Field("", max_length=1000)
    quote: str = Field(min_length=1, max_length=2400)
    start_line: int | None = Field(None, ge=1)
    scope_confirmed: bool = False
    comparison: Literal["similar", "conflict"] | None = None
    related_fact_ids: list[str] = Field(default_factory=list, max_length=8)


class ReviewText(UploadedText):
    candidates: list[Proposal] = Field(max_length=100)


class Choice(Input):
    index: int = Field(ge=0)
    action: Literal["add", "evidence"]
    acknowledge_conflict: bool = False


class CommitText(ReviewText):
    base_graph_revision: str = Field(pattern=r"^rev:[0-9]+$")
    selections: list[Choice] = Field(min_length=1, max_length=100)


def normalized(text):
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", text).casefold())


def uploaded_source(upload):
    digest = sha256(upload.text.encode("utf-8")).hexdigest()
    return {"id": "source:upload-" + digest, "title": upload.filename,
            "resource_id": "resource:upload-" + digest, "filename": upload.filename,
            "format": PurePath(upload.filename).suffix[1:].lower(), "source_type": "uploaded_text",
            "content_sha256": digest, "text_content": upload.text}


def locate(text, quote, requested_line=None):
    quote = quote.strip().replace("\r\n", "\n")
    if not quote:
        raise KnowledgeError("缺少原文摘录")
    positions = []
    offset = text.find(quote)
    while offset >= 0:
        line = text.count("\n", 0, offset) + 1
        if requested_line is None or requested_line == line:
            positions.append(line)
        offset = text.find(quote, offset + len(quote))
    if len(positions) != 1:
        raise KnowledgeError("找不到对应原句或原句出现多次，请提供准确原文和起始行")
    start = positions[0]
    return quote, start, start + quote.count("\n")


def measurement_key(value):
    unit = value["unit"]
    scale = UNITS_IN_MM.get(unit, Decimal(1))
    values = [value["value"]] if "value" in value else [value["min"], value["max"]]
    return ("mm" if unit in UNITS_IN_MM else unit, tuple((Decimal(str(n)) * scale).normalize() for n in values))


@dataclass
class Assessment:
    status: str
    message: str
    matches: list = field(default_factory=list)
    fact: dict | None = None
    evidence: dict | None = None
    new_entities: list = field(default_factory=list)

    def response(self, index):
        return {"index": index, "status": self.status, "message": self.message, "matches": self.matches,
                "new_entities": self.new_entities, "evidence": self.evidence,
                "subject_id": self.fact.get("subject_id") if self.fact else None,
                "object_id": self.fact.get("object_id") if self.fact else None}


class ImportReview:
    def __init__(self, data, ontology, upload):
        self.ontology = ontology
        self.entities = {e["id"]: e for e in data["entities"]}
        self.facts = data["facts"]
        self.evidence = {e["id"]: e for e in data["evidence"]}
        self.source = uploaded_source(upload)
        self.source_exists = any(s["id"] == self.source["id"] for s in data["sources"])

    def resolve(self, ref):
        label = normalized(ref.label)
        def match(entity):
            return (label in {normalized(name) for name in [entity["label"], *entity["aliases"]]}
                    and (ref.kind is None or entity["kind"] == ref.kind)
                    and (ref.scope_id is None or entity.get("scope_id") == ref.scope_id))

        if ref.id:
            entity = self.entities.get(ref.id)
            if entity is None or not match(entity):
                raise KnowledgeError("所选实体与名称、类型或归属不一致：" + ref.label)
            return entity, False
        matches = [entity for entity in self.entities.values() if match(entity)]
        if len(matches) == 1:
            return matches[0], False
        if matches:
            options = "、".join(f"{item['label']}（{item['id']}）" for item in matches[:6])
            raise KnowledgeError("多个实体匹配，请选择具体对象：" + options)
        if not label or ref.kind not in IMPORT_KINDS or ref.kind not in self.ontology["entity_kinds"]:
            raise KnowledgeError("实体归属待确认：" + ref.label)
        if ref.scope_id and ref.scope_id not in self.entities:
            raise KnowledgeError("所属对象不存在：" + ref.scope_id)
        if ref.kind in {"Component", "ComponentRegion"} and (
                not ref.scope_id or self.entities[ref.scope_id]["kind"] not in {"Chariot", "ReferenceSpecimen"}):
            raise KnowledgeError("具体部件需选择所属战车或标本：" + ref.label)
        ident = "entity:text-" + fingerprint([label, ref.kind, ref.scope_id])[:32]
        record = {"id": ident, "kind": ref.kind, "label": ref.label.strip(), "aliases": []}
        if ref.scope_id:
            record["scope_id"] = ref.scope_id
        return record, True

    def existing(self, fact):
        same, alternatives = [], []
        for previous in self.facts:
            if (previous["subject_id"], previous["predicate"]) != (fact["subject_id"], fact["predicate"]):
                continue
            if "object_id" in fact:
                if previous.get("object_id") == fact["object_id"]:
                    same.append(previous)
            elif fact["predicate"] == "HAS_DIMENSION":
                left, right = previous["value"], fact["value"]
                if normalized(left["quantity"]) == normalized(right["quantity"]):
                    (same if measurement_key(left) == measurement_key(right) else alternatives).append(previous)
            else:
                left, right = normalized(previous["value"]), normalized(fact["value"])
                if left == right:
                    same.append(previous)
                elif min(len(left), len(right)) >= 8 and SequenceMatcher(None, left, right).ratio() >= 0.82:
                    alternatives.append(previous)
        return same, alternatives

    def assess(self, proposal):
        try:
            return self._assess(proposal)
        except KnowledgeError as exc:
            return Assessment("needs_review", str(exc))

    def _assess(self, proposal):
        predicate = self.ontology["predicates"].get(proposal.predicate)
        if predicate is None or proposal.predicate not in IMPORT_PREDICATES:
            raise KnowledgeError("请选择首版支持的事实或部件关系")
        quote, start, end = locate(self.source["text_content"], proposal.quote, proposal.start_line)
        subject_ref = proposal.subject
        code = SPECIMEN_CODE.search(subject_ref.label)
        if (not subject_ref.id and not subject_ref.kind and code
                and any(term in subject_ref.label for term in ("标本", "样件"))
                and normalized(code.group()) in normalized(quote)):
            subject_ref = subject_ref.model_copy(update={"kind": "ReferenceSpecimen"})
        subject, is_new = self.resolve(subject_ref)
        if (subject["kind"] == "ReferenceRecord" and "未编号" in subject["label"]
                and normalized(subject["label"]) not in normalized(quote)
                and not proposal.scope_confirmed):
            raise KnowledgeError("未编号对象不能仅凭尺寸或相似描述归到已有记录，请确认归属")
        if proposal.origin != "documented" and not proposal.rationale.strip():
            raise KnowledgeError("推断或假设需要说明依据和理由")
        new_entities = [subject] if is_new else []
        fact = {"subject_id": subject["id"], "predicate": proposal.predicate,
                "origin": proposal.origin, "review_status": "pending"}
        if proposal.rationale.strip():
            fact["rationale"] = proposal.rationale.strip()
        if predicate["object_kind"] == "entity":
            if proposal.object is None or proposal.value is not None:
                raise KnowledgeError("关系需要选择目标实体")
            target, new_target = self.resolve(proposal.object)
            if [subject["kind"], target["kind"]] not in predicate["endpoint_pairs"]:
                raise KnowledgeError("本体不允许这两种实体使用所选关系")
            if new_target:
                new_entities.append(target)
            fact["object_id"] = target["id"]
        else:
            if proposal.object is not None or subject["kind"] not in predicate["subject_kinds"]:
                raise KnowledgeError("本体不允许该实体保存此属性")
            if predicate["object_kind"] == "dimension":
                if not isinstance(proposal.value, dict):
                    raise KnowledgeError("尺寸必须有项目、单位和数值")
                errors = []
                _validate_measurement(proposal.value, self.ontology, proposal.predicate,
                                      lambda _path, message: errors.append(message))
                if errors:
                    raise KnowledgeError("、".join(errors))
                values = [proposal.value["value"]] if "value" in proposal.value else [proposal.value["min"], proposal.value["max"]]
                quoted_numbers = {Decimal(number) for number in re.findall(r"\d+(?:\.\d+)?", unicodedata.normalize("NFKC", quote))}
                if any(Decimal(str(value)) not in quoted_numbers for value in values):
                    raise KnowledgeError("尺寸数值需逐项出现在原文引句；请核对数值或改选支持它的引句")
            elif not isinstance(proposal.value, str) or not proposal.value.strip():
                raise KnowledgeError("请填写文字事实")
            fact["value"] = proposal.value

        evidence_id = "evidence:text-" + fingerprint([self.source["id"], start, end, quote])[:32]
        evidence = {"id": evidence_id, "source_id": self.source["id"], "start_line": start, "end_line": end,
                    "locator": f"第 {start} 行" if start == end else f"第 {start}–{end} 行",
                    "quote": quote, "transcription": "embedded_text", "check_status": "pending",
                    "scope_note": f"上传文本《{self.source['title']}》，按所引段落及标本语境理解。"}
        same, alternatives = self.existing(fact)
        if same:
            message = "已有同一事实"
            if evidence_id not in same[0]["evidence_ids"]:
                message += "，可为原事实补充本段证据"
            else:
                message += "，已有相同的上传证据"
            return Assessment("duplicate", message, same + alternatives, fact, evidence, new_entities)
        if alternatives:
            is_dimension = proposal.predicate == "HAS_DIMENSION"
            return Assessment("conflict" if is_dimension else "possible_duplicate",
                              "同标本同项目已有不同尺寸" if is_dimension else "已有相近描述，需核对是否同义",
                              alternatives, fact, evidence, new_entities)
        related = [item for item in self.facts if item["id"] in proposal.related_fact_ids
                   and item["subject_id"] == fact["subject_id"] and item["predicate"] == fact["predicate"]]
        if proposal.comparison and related:
            conflict = proposal.comparison == "conflict"
            return Assessment("conflict" if conflict else "possible_duplicate",
                              "模型提示可能冲突，请核对同一对象的原文" if conflict else "模型找到可能同义的已有记录",
                              related, fact, evidence, new_entities)
        return Assessment("new", "可新增，需管理员确认", [], fact, evidence, new_entities)

    def check(self, candidates):
        assessments = [self.assess(proposal) for proposal in candidates]
        grouped = {}
        for item in assessments:
            if item.fact and item.fact["predicate"] == "HAS_DIMENSION":
                key = (item.fact["subject_id"], normalized(item.fact["value"]["quantity"]))
                grouped.setdefault(key, []).append(item)
        for items in grouped.values():
            if len({measurement_key(item.fact["value"]) for item in items}) > 1:
                for item in items:
                    if item.status == "new":
                        item.status, item.message = "conflict", "同一份材料对同标本同一尺寸给出不同记录"
        return assessments

    def operations(self, candidates, selections, run_id):
        results = self.check(candidates)
        operations = {}
        selected_facts = set()
        indices = [choice.index for choice in selections]
        if len(indices) != len(set(indices)) or any(index >= len(results) for index in indices):
            raise KnowledgeError("勾选条目编号重复或不存在")
        for choice in selections:
            result = results[choice.index]
            if result.fact is None or result.evidence is None:
                raise KnowledgeError("请先修正待确认的条目")
            if choice.action == "add":
                if result.status == "duplicate":
                    raise KnowledgeError("重复事实可补证，不可再次新增")
                if result.status in {"conflict", "possible_duplicate"} and not choice.acknowledge_conflict:
                    raise KnowledgeError("请先确认可能冲突或相近的记录")
                fact = result.fact
                signature = fingerprint([fact["subject_id"], fact["predicate"], fact.get("object_id"),
                                         measurement_key(fact["value"])[0] if fact["predicate"] == "HAS_DIMENSION" else None,
                                         [normalized(fact["value"]["quantity"]), *map(str, measurement_key(fact["value"])[1])]
                                         if fact["predicate"] == "HAS_DIMENSION" else normalized(fact.get("value", ""))])
                if signature in selected_facts:
                    raise KnowledgeError("当批勾选中存在重复事实，请保留一条")
                selected_facts.add(signature)
                for entity in result.new_entities:
                    operations.setdefault(entity["id"], operation("entities", entity))
                record = {**fact, "id": "fact:text-" + signature[:32],
                          "evidence_ids": [result.evidence["id"]],
                          "extraction": {"method": "reviewed_text_import", "run_id": run_id}}
                operations[record["id"]] = operation("facts", record)
            else:
                if result.status != "duplicate":
                    raise KnowledgeError("只有确认重复的事实可选择补充证据")
                original = result.matches[0]
                ident = original["id"]
                record = dict(operations.get(ident, {}).get("record", original))
                if result.evidence["id"] in record["evidence_ids"]:
                    continue
                record["evidence_ids"] = [*record["evidence_ids"], result.evidence["id"]]
                record["review_status"] = "pending"
                record.pop("review", None)
                operations[ident] = operation("facts", record, "update")
            if not self.source_exists:
                operations.setdefault(self.source["id"], operation("sources", self.source))
            if result.evidence["id"] not in self.evidence:
                operations.setdefault(result.evidence["id"], operation("evidence", result.evidence))
        if not operations:
            raise KnowledgeError("没有需要写入的变更")
        return list(operations.values())


def operation(table, record, action="create"):
    return {"table": table, "id": record["id"], "action": action, "record": record}
