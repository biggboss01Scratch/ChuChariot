"""DeepSeek proposal generation for a text and the complete effective knowledge graph."""

import json
from pathlib import Path

from pydantic import ValidationError

from ..ai_client import AIUnavailable, post
from .ingestion import IMPORT_KINDS, IMPORT_PREDICATES, Proposal

PROMPT = (Path(__file__).parent / "extract.zh.md").read_text(encoding="utf-8")


class DeepSeekExtractor:
    def __init__(self, settings, send=post):
        self.settings = settings
        self.send = send

    def extract(self, data, ontology, upload):
        graph = {
            "entities": data["entities"],
            "facts": [{key: value for key, value in fact.items() if key not in {"review", "extraction"}}
                      for fact in data["facts"]],
            "evidence": data["evidence"],
            "sources": [{key: value for key, value in source.items() if key not in {"filename", "text_content"}}
                        for source in data["sources"]],
        }
        schema = {"kinds": sorted(IMPORT_KINDS & ontology["entity_kinds"].keys()),
                  "predicates": {key: value for key, value in ontology["predicates"].items() if key in IMPORT_PREDICATES},
                  "units": ontology["units"]}
        payload = {"graph": graph, "allowed": schema,
                   "upload": {"filename": upload.filename, "text": upload.text}}
        response = self.send(
            "https://api.deepseek.com/chat/completions", self.settings.generation_key,
            {"model": self.settings.generation_model, "thinking": {"type": "disabled"}, "temperature": 0.1,
             "response_format": {"type": "json_object"}, "max_tokens": 12_000,
             "messages": [{"role": "system", "content": PROMPT},
                          {"role": "user", "content": json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}]},
            self.settings.timeout_seconds, "DeepSeek",
        )
        try:
            choice = response["choices"][0]
            if choice["finish_reason"] != "stop":
                raise ValueError("Incomplete extraction")
            result = json.loads(choice["message"]["content"])
            proposals, unrelated = result["candidates"], result["unrelated"]
            if not isinstance(proposals, list) or not isinstance(unrelated, list):
                raise ValueError("Invalid extraction")
        except (KeyError, TypeError, ValueError, IndexError):
            raise AIUnavailable("模型未返回完整提取结果。请尝试上传较短的材料。") from None
        candidates = []
        rejected = 0
        for value in proposals[:100]:
            try:
                candidates.append(Proposal.model_validate(value).model_copy(update={"scope_confirmed": False}))
            except ValidationError:
                rejected += 1
        warnings = []
        if rejected:
            warnings.append(f"模型有 {rejected} 条建议格式无效，请对照原文检查遗漏。")
        if len(proposals) > 100 or len(unrelated) > 100:
            warnings.append("本次建议条数达到显示上限，请分段检查余下材料。")
        return candidates, unrelated[:100], warnings
