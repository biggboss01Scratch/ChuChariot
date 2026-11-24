"""Versioned, authenticated FastAPI service with runtime-checked DTO contracts."""
from __future__ import annotations

from contextlib import asynccontextmanager
import copy
import hmac
import logging
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import FastAPI, Depends, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jsonschema import Draft202012Validator
from neo4j.exceptions import Neo4jError, DriverError
from pydantic import BaseModel, ConfigDict, Field, model_validator
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..dataset_io import ROOT, KnowledgeError, read_json
from ..preview import FRONTEND, source_path
from .config import Settings
from .database import Repository, Conflict, Missing
from .service import View, pick, metadata

CONTRACT = read_json(ROOT / "docs/contracts/knowledge-api.v1.openapi.json")
bearer = HTTPBearer(auto_error=False, scheme_name="OperatorBearer")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Operation(StrictModel):
    table: Literal["sources", "evidence", "entities", "facts", "model_mappings"]
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]*:[a-z0-9][a-z0-9._-]*$")
    action: Literal["create", "update", "review", "delete", "restore"]
    record: dict | None = None
    review_status: Literal["pending", "confirmed", "disputed"] | None = None
    note: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def command_shape(self):
        if self.action in {"delete", "restore"}:
            if self.model_fields_set & {"record", "review_status", "note"}:
                raise ValueError("Delete/restore accepts only table, id and action; use the change set reason")
        elif self.action == "review":
            if self.table not in {"facts", "model_mappings"} or self.record is not None or self.review_status is None or not self.note:
                raise ValueError("Review needs a status and note, with no record")
        elif self.record is None or self.review_status is not None:
            raise ValueError("Create/update needs a complete record and no review_status")
        return self


class ChangeDraft(StrictModel):
    base_graph_revision: str = Field(min_length=1)
    ontology_version: str
    schema_version: Literal["0.4.0"]
    reason: str = Field(min_length=1, pattern=r"\S")
    operations: list[Operation] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def unique_records(self):
        keys = [(op.table, op.id) for op in self.operations]
        if len(keys) != len(set(keys)):
            raise ValueError("One operation per record per change set")
        return self


class Commit(StrictModel):
    expected_graph_revision: str = Field(min_length=1)


def create_app(settings=None, repository=None):
    settings = settings or Settings.load()
    repo = repository or Repository(settings)

    @asynccontextmanager
    async def lifespan(app):
        yield
        if repository is None:
            repo.close()

    app = FastAPI(title="ChuChariot knowledge API", version="1.1.0", lifespan=lifespan)
    app.state.repository = repo

    @app.middleware("http")
    async def request_context(request, call_next):
        request.state.request_id = uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def error(request, status, code, message, details=None):
        body = {"code": code, "message": message, "request_id": request.state.request_id}
        if details:
            body["details"] = details
        return JSONResponse({"error": body}, status_code=status,
                            headers={"WWW-Authenticate": "Bearer"} if status == 401 else None)

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return error(request, 422, "validation_error", "Invalid request", [
            {"path": ".".join(map(str, e["loc"])), "message": e["msg"]} for e in exc.errors()])

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        return error(request, exc.status_code, "http_error", str(exc.detail))

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        return error(request, 409, "conflict", str(exc))

    @app.exception_handler(Missing)
    async def missing(request, exc):
        return error(request, 404, "not_found", str(exc))

    @app.exception_handler(KnowledgeError)
    async def bad_knowledge(request, exc):
        return error(request, 422, "knowledge_validation", str(exc))

    async def database_error(request, exc):
        logging.getLogger(__name__).warning("Database unavailable: %s", type(exc).__name__)
        return error(request, 503, "database_unavailable", "Knowledge database is unavailable")
    app.add_exception_handler(Neo4jError, database_error)
    app.add_exception_handler(DriverError, database_error)

    @app.exception_handler(Exception)
    async def unexpected(request, exc):
        logging.getLogger(__name__).exception("Unhandled request %s", request.state.request_id)
        return error(request, 500, "internal_error", "Internal service error")

    def operator(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        if not settings.operators:
            raise HTTPException(503, "Internal access has not been configured")
        if credentials is None:
            raise HTTPException(401, "Operator authentication required")
        for actor, token in settings.operators.items():
            if hmac.compare_digest(credentials.credentials.encode(), token.encode()):
                return actor
        raise HTTPException(403, "Invalid operator credential")

    def query(request, allowed=(), repeated=()):
        for key in request.query_params:
            if key not in allowed or (key not in repeated and len(request.query_params.getlist(key)) != 1):
                raise HTTPException(422, "Unknown or repeated query parameter: " + key)

    def view(request, internal=False, include_pending=None):
        return View(repo, settings, request.state.request_id, internal=internal, include_pending=include_pending)

    def respond(schema, value, status=200):
        validator = Draft202012Validator({"$ref": "#/components/schemas/" + schema, "components": CONTRACT["components"]})
        validator.validate(value)
        return JSONResponse(value, status_code=status)

    def change_dto(value):
        return {**pick(value, {"id", "base_graph_revision", "result_graph_revision", "actor_id", "operation_count"}),
                "state": value["status"]}

    @app.get("/api/v1/health/live")
    def live(request: Request):
        query(request)
        return respond("Health", {"status": "ok", "database": "not_checked"})

    @app.get("/api/v1/health/ready")
    def ready(request: Request):
        query(request)
        if not repo.ready():
            return respond("Health", {"status": "not_ready", "database": "unavailable"}, 503)
        return respond("Health", {"status": "ok", "database": "ready"})

    @app.get("/api/v1/meta")
    def meta(request: Request):
        query(request)
        return respond("Meta", view(request).meta)

    @app.get("/api/v1/entities")
    def entities(request: Request, q: str = Query("", max_length=200), kind: str | None = None,
                 page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100)):
        query(request, {"q", "kind", "page", "page_size"})
        v = view(request)
        ids = [i for i, e in sorted(v.entities.items()) if (not kind or e["kind"] == kind)
               and (not q or any(q.casefold() in n.casefold() for n in [i, e["label"], *e["aliases"]]))]
        return respond("EntityPage", {"items": [v.entity(i) for i in ids[(page-1)*page_size:page*page_size]],
                                      "total": len(ids), "page": page, "page_size": page_size, "meta": v.meta})

    @app.get("/api/v1/entities/{entity_id}")
    def entity(entity_id: str, request: Request):
        query(request)
        return respond("EntityDetail", view(request).detail(entity_id))

    @app.get("/api/v1/graph")
    def graph(request: Request, center: str | None = None, depth: int = Query(1, ge=1, le=3),
              groups: Annotated[list[Literal["structure", "appearance", "reconstruction"]] | None, Query()] = None,
              limit: int = Query(500, ge=1, le=500)):
        query(request, {"center", "depth", "groups", "limit"}, {"groups"})
        return respond("Graph", view(request).graph(center, depth, groups, limit))

    @app.get("/api/v1/facts/{fact_id}")
    def fact(fact_id: str, request: Request):
        query(request)
        v = view(request)
        return respond("FactDetail", {"fact": v.fact(fact_id), "meta": v.meta})

    @app.get("/api/v1/facts/{fact_id}/evidence")
    def evidence(fact_id: str, request: Request):
        query(request)
        v = view(request)
        f = v.fact(fact_id)
        return respond("EvidencePage", {"fact_id": fact_id, "items": [v.proof(v.evidence[i]) for i in f["evidence_ids"]], "meta": v.meta})

    @app.get("/api/v1/entities/{entity_id}/model-mappings")
    def mappings(entity_id: str, request: Request):
        query(request)
        v = view(request)
        v.entity(entity_id)
        items = [pick(m, {"id", "entity_id", "model_version_id", "node_indices", "review_status", "note"})
                 for m in v.data["model_mappings"] if m["entity_id"] == entity_id and
                 (v.review or m["review_status"] == "confirmed")]
        return respond("MappingPage", {"entity_id": entity_id, "items": items, "meta": v.meta})

    @app.get("/api/v1/sources/{source_id}")
    def source(source_id: str, request: Request):
        query(request)
        return respond("Source", view(request).source(source_id))

    @app.get("/api/v1/internal/snapshot")
    def snapshot(request: Request, actor=Depends(operator)):
        query(request)
        v = view(request, True)
        return respond("Snapshot", {"dataset": v.data, "meta": v.meta})

    @app.get("/api/v1/internal/paths/teaching")
    def teaching(request: Request, from_id: str = Query(alias="from"), to_id: str = Query(alias="to"),
                 max_hops: int = Query(8, ge=1, le=16), include_pending: bool = False, actor=Depends(operator)):
        query(request, {"from", "to", "max_hops", "include_pending"})
        return respond("TeachingPath", view(request, True, include_pending).teaching(from_id, to_id, max_hops))

    @app.post("/api/v1/internal/change-sets", status_code=201)
    def create_change(request: Request, draft: ChangeDraft, idempotency_key: str = Header(min_length=8, max_length=200), actor=Depends(operator)):
        query(request)
        result = repo.create_change(draft.model_dump(exclude_none=True), actor, idempotency_key)
        return respond("ChangeSet", change_dto(result), 201)

    @app.post("/api/v1/internal/change-sets/{change_set_id}/validate")
    def validate_change(change_set_id: str, request: Request, actor=Depends(operator)):
        query(request)
        return respond("ValidationResult", repo.process_change(change_set_id, actor))

    @app.post("/api/v1/internal/change-sets/{change_set_id}/commit")
    def commit_change(change_set_id: str, request: Request, body: Commit, actor=Depends(operator)):
        query(request)
        result = repo.process_change(change_set_id, actor, commit=True, expected_revision=body.expected_graph_revision)
        return respond("ChangeSet", change_dto(result))

    @app.get("/api/v1/internal/export")
    def export(request: Request, actor=Depends(operator)):
        query(request)
        items, data, ontology, state = repo.recycle_bin()
        return respond("ExportBundle", {"dataset": data, "ontology": ontology, "deleted_records": items,
                                         "meta": metadata(data, ontology, state, request.state.request_id, "internal")})

    @app.get("/api/v1/internal/history/{record_id}")
    def history(record_id: str, request: Request, actor=Depends(operator)):
        query(request)
        v = view(request, True)
        return {"items": repo.history(record_id), "meta": v.meta}

    @app.get("/api/v1/internal/deleted")
    def deleted(request: Request, table: Literal["sources", "evidence", "entities", "facts", "model_mappings"] | None = None,
                page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100), actor=Depends(operator)):
        query(request, {"table", "page", "page_size"})
        items, data, ontology, state = repo.recycle_bin()
        items = [item for item in items if table is None or item["table"] == table]
        return respond("DeletedPage", {"items": items[(page-1)*page_size:page*page_size], "total": len(items),
                                       "page": page, "page_size": page_size,
                                       "meta": metadata(data, ontology, state, request.state.request_id, "internal")})

    @app.get("/api/v1/inspector")
    def inspector(request: Request, confirmed: bool = False):
        query(request, {"confirmed"})
        return view(request, include_pending=not confirmed).inspector()

    @app.get("/api/v1/internal/inspector")
    def internal_inspector(request: Request, confirmed: bool = False, actor=Depends(operator)):
        query(request, {"confirmed"})
        return view(request, True, not confirmed).inspector()

    @app.get("/api/v1/sources/{source_id}/content")
    def content(source_id: str, request: Request):
        query(request)
        v = view(request)
        v.source(source_id)
        file = source_path(v.sources[source_id], settings.resource_dirs)
        if file is None:
            raise Missing("Source content unavailable")
        return FileResponse(file, filename=file.name, content_disposition_type="inline")

    @app.get("/api/v1/internal/sources/{source_id}/content")
    def internal_content(source_id: str, request: Request, actor=Depends(operator)):
        query(request)
        v = view(request, True)
        v.source(source_id)
        file = source_path(v.sources[source_id], settings.resource_dirs)
        if file is None:
            raise Missing("Source content unavailable")
        return FileResponse(file, filename=file.name, content_disposition_type="inline")

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def index():
        text = (FRONTEND / "index.html").read_text(encoding="utf-8")
        text = text.replace('<script src="/app.js"', '<script>window.CHUCHARIOT_DATABASE_API=true;</script>\n  <script src="/app.js"')
        text = text.replace("临时测试 · 本地只读", "数据库版 · 只读浏览")
        text = text.replace("基于现有 JSON 知识层实时读取", "基于 Neo4j 知识库实时读取")
        text = text.replace('<button class="button" id="reload-button">', '<button class="button" id="operator-logout" hidden>退出内部访问</button><button class="button" id="reload-button">')
        text = text.replace('</body>', '''<dialog id="operator-login"><form method="dialog"><h2>内部访问验证</h2><p>输入本机配置的操作员凭据。凭据只在当前页面内存中使用。</p><label>操作员凭据 <input type="password" id="operator-token" autocomplete="off" required></label><p><button value="cancel" formnovalidate>取消</button> <button value="login">进入内部视图</button></p></form></dialog></body>''')
        return text

    @app.get("/app.js", include_in_schema=False)
    def script():
        return FileResponse(FRONTEND / "app.js", media_type="text/javascript")

    @app.get("/style.css", include_in_schema=False)
    def styles():
        return FileResponse(FRONTEND / "style.css", media_type="text/css")

    # Use the checked contract for core operations, and FastAPI's generated
    # schemas for the additional inspector/resource/history routes.
    generated_openapi = app.openapi
    def openapi():
        if app.openapi_schema:
            return app.openapi_schema
        actual = copy.deepcopy(generated_openapi())
        actual["info"].update(title="ChuChariot knowledge API", version="1.1.0",
                              description="Neo4j-backed API. Publication mode is configured on the server.")
        actual["components"]["schemas"].update(CONTRACT["components"]["schemas"])
        actual["components"].setdefault("responses", {}).update(CONTRACT["components"]["responses"])
        for path, operations in CONTRACT["paths"].items():
            actual["paths"][path] = copy.deepcopy(operations)
            for operation in actual["paths"][path].values():
                if isinstance(operation, dict):
                    operation["x-implementation-status"] = "implemented"
                    for response in operation.get("responses", {}).values():
                        if "$ref" not in response:
                            response["description"] = "Response"
        actual["x-storage"] = "neo4j"
        app.openapi_schema = actual
        return actual
    app.openapi = openapi
    return app


def app_factory():
    return create_app()
