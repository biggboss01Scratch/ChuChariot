"""Authenticated administration endpoints; imports reuse the existing change sets."""

from pathlib import Path
from threading import BoundedSemaphore
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import FileResponse

from ..ai_client import AIUnavailable, DeepSeekSettings
from ..backend.database import Conflict, Repository, fingerprint
from ..backend.service import metadata
from ..dataset_io import KnowledgeError, ROOT
from ..presentation import browsing_regions
from .extractor import DeepSeekExtractor
from .ingestion import CommitText, ImportReview, ReviewText, UploadedText, locate

ASSETS = ROOT / "frontend/admin"
CSP = "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"


def router(repo, operator, extractor=None):
    routes = APIRouter()
    slot = BoundedSemaphore(1)

    @routes.get("/admin", include_in_schema=False)
    def page():
        return FileResponse(ASSETS / "index.html", headers={"Content-Security-Policy": CSP})

    @routes.get("/admin/{asset}", include_in_schema=False)
    def assets(asset: Literal["app.js", "graph.js", "network.js", "style.css"]):
        return FileResponse(ASSETS / asset)

    @routes.get("/api/v1/internal/admin/state")
    def state(request: Request, _actor=Depends(operator)):
        data, ontology, revision = repo.snapshot()
        sources = [{key: value for key, value in source.items() if key != "text_content"} for source in data["sources"]]
        return {"dataset": {**data, "sources": sources}, "ontology": ontology,
                "regions": browsing_regions(data, data["entities"]),
                "meta": metadata(data, ontology, revision, request.state.request_id, "internal")}

    def review(data, ontology, rev, upload, candidates):
        checker = ImportReview(data, ontology, upload)
        return {"graph_revision": Repository.revision(rev),
                "items": [item.response(index) for index, item in enumerate(checker.check(candidates))]}

    @routes.post("/api/v1/internal/admin/imports/analyze")
    def analyze(upload: UploadedText, _actor=Depends(operator)):
        if not slot.acquire(blocking=False):
            raise HTTPException(429, "已有材料正在分析，请稍后重试")
        try:
            provider = extractor
            if provider is None:
                try:
                    provider = DeepSeekExtractor(DeepSeekSettings.load(ROOT / ".local/ai.json"))
                except (OSError, ValueError, TypeError):
                    raise HTTPException(503, "AI 配置不可用") from None
            data, ontology, rev = repo.snapshot()
            candidates, unrelated, warnings = provider.extract(data, ontology, upload)
            if repo.current_revision() != Repository.revision(rev):
                raise Conflict("分析期间图谱已更新，请重新分析")
            evidence = []
            for item in unrelated:
                if (not isinstance(item, dict) or not isinstance(item.get("quote"), str)
                        or not isinstance(item.get("reason"), str)):
                    continue
                try:
                    quote, start, end = locate(upload.text, item["quote"])
                except KnowledgeError:
                    continue
                evidence.append({"quote": quote, "reason": item["reason"][:300], "start_line": start, "end_line": end})
            return {**review(data, ontology, rev, upload, candidates),
                    "candidates": [item.model_dump(exclude_none=True) for item in candidates],
                    "unrelated": evidence, "warnings": warnings}
        except AIUnavailable as exc:
            raise HTTPException(503, str(exc)) from None
        finally:
            slot.release()

    @routes.post("/api/v1/internal/admin/imports/check")
    def check(upload: ReviewText, _actor=Depends(operator)):
        data, ontology, rev = repo.snapshot()
        return review(data, ontology, rev, upload, upload.candidates)

    @routes.post("/api/v1/internal/admin/imports/commit")
    def commit(upload: CommitText, idempotency_key: str = Header(min_length=8, max_length=200),
               actor=Depends(operator)):
        data, ontology, rev = repo.snapshot()
        if Repository.revision(rev) != upload.base_graph_revision:
            raise Conflict("图谱已更新，请先重新检查建议")
        run_id = "run:text-" + fingerprint([actor, idempotency_key])[:32]
        changes = ImportReview(data, ontology, upload).operations(upload.candidates, upload.selections, run_id)
        draft = {"base_graph_revision": upload.base_graph_revision, "ontology_version": ontology["version"],
                 "schema_version": data["schema_version"], "reason": "文本导入审核：" + upload.filename,
                 "operations": changes}
        command = repo.create_change(draft, actor, idempotency_key)
        checked = repo.process_change(command["id"], actor)
        if not checked["valid"]:
            raise KnowledgeError("\n".join(error["message"] for error in checked["errors"]))
        result = repo.process_change(command["id"], actor, commit=True, expected_revision=upload.base_graph_revision)
        return {"change_set_id": result["id"], "graph_revision": result["result_graph_revision"],
                "record_count": len(changes),
                "fact_ids": [op["id"] for op in changes if op["table"] == "facts"]}

    return routes
