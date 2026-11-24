"""Local, read-only inspection UI. This is not the planned production backend."""

from __future__ import annotations

import json
import mimetypes
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from .dataset_io import DEFAULT_DATASET, DEFAULT_ONTOLOGY, ROOT, KnowledgeError, read_json
from .media import image_path, project_media
from .queries import KnowledgeStore
from .presentation import project_presentation

FRONTEND = ROOT / "frontend/inspector"
ResourceDirectories = Path | list[Path] | tuple[Path, ...] | None


def preview_data(dataset=DEFAULT_DATASET, ontology=DEFAULT_ONTOLOGY, review=False,
                 resource_dir: ResourceDirectories = None, *, media_manifest=None, media_dir=None, audience="internal") -> dict:
    definitions = read_json(ontology)
    data = read_json(dataset)
    store = KnowledgeStore(data, definitions)
    snapshot = store.snapshot(include_pending=review)
    for source in snapshot["sources"]:
        source["available"] = source_path(source, resource_dir) is not None
    model = ROOT / "data/scenes/model-inspection.json"
    snapshot["meta"].update(review_mode=review, validation="passed")
    snapshot["ontology"] = definitions
    snapshot["model_report"] = read_json(model) if model.exists() else None
    if media_manifest is not None:
        snapshot["media"] = project_media(data, snapshot, read_json(media_manifest), media_dir)
    return project_presentation(data, snapshot, audience)


def source_path(source: dict, resource_dir: ResourceDirectories) -> Path | None:
    if resource_dir is None or source["format"] not in {"pdf", "mp4", "md"}:
        return None
    directories = (resource_dir,) if isinstance(resource_dir, Path) else resource_dir
    for directory in directories:
        root = directory.resolve()
        path = (root / source["filename"]).resolve()
        if path.parent == root and path.is_file():
            return path
    return None


def make_server(port=8765, dataset=DEFAULT_DATASET, ontology=DEFAULT_ONTOLOGY,
                resource_dir: ResourceDirectories = None, *, media_manifest=None, media_dir=None) -> ThreadingHTTPServer:
    # Validate before starting, then reload data on each request for manual review.
    def snapshot(review, audience="internal"):
        return preview_data(dataset, ontology, review, resource_dir,
                            media_manifest=media_manifest, media_dir=media_dir, audience=audience)

    snapshot(False)

    class Handler(BaseHTTPRequestHandler):
        def respond(self, body: bytes, status=200, content_type="application/json; charset=utf-8"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def json_response(self, value, status=200):
            self.respond(json.dumps(value, ensure_ascii=False).encode("utf-8"), status)

        def do_GET(self):
            parsed = urlsplit(self.path)
            path = unquote(parsed.path)
            review = parse_qs(parsed.query).get("review", ["0"]) == ["1"]
            try:
                if path == "/api/health":
                    self.json_response({"status": "ok", "mode": "local_read_only_preview"})
                elif path == "/api/preview":
                    audience = parse_qs(parsed.query, keep_blank_values=True).get("audience", ["internal"])
                    if len(audience) != 1 or audience[0] not in {"internal", "public"}:
                        self.json_response({"error": "audience必须为public或internal且只能提供一次"}, 400)
                        return
                    self.json_response(snapshot(review, audience[0]))
                elif path == "/api/connection-path":
                    parameters = parse_qs(parsed.query, keep_blank_values=True)
                    try:
                        if any(len(parameters.get(key, [])) != 1 or not parameters[key][0]
                               for key in ("from", "to")):
                            raise ValueError("from和to必须各提供一个实体ID")
                        limit = parameters.get("max_hops", ["8"])
                        if len(limit) != 1 or not limit[0].isascii() or not limit[0].isdigit() or not 1 <= int(limit[0]) <= 16:
                            raise ValueError("max_hops必须为1至16的整数")
                    except ValueError as exc:
                        self.json_response({"error": str(exc)}, 400)
                        return
                    store = KnowledgeStore.load(dataset, ontology)
                    try:
                        result = store.connection_path(parameters["from"][0], parameters["to"][0], review, int(limit[0]))
                    except KnowledgeError as exc:
                        self.json_response({"error": str(exc)}, 404)
                        return
                    self.json_response(result)
                elif path.startswith("/api/media/") and media_manifest is not None:
                    ident = path.removeprefix("/api/media/")
                    item = next((entry for entry in snapshot(review)["media"] if entry["id"] == ident), None)
                    file = image_path(item["filename"], media_dir) if item else None
                    if file is None:
                        self.json_response({"error": "媒体未登记、未配置或当前视图不可用"}, 404)
                    else:
                        self.respond(file.read_bytes(), content_type="image/png")
                elif path.startswith("/api/sources/"):
                    source_id = path.removeprefix("/api/sources/")
                    source = KnowledgeStore.load(dataset, ontology).source(source_id)
                    file = source_path(source, resource_dir) if source else None
                    if file is None:
                        self.json_response({"error": "原文未配置、缺失或来源不存在"}, 404)
                        return
                    size = file.stat().st_size
                    start, end, status = 0, size - 1, 200
                    requested = self.headers.get("Range")
                    if requested:
                        match = re.fullmatch(r"bytes=(\d*)-(\d*)", requested)
                        valid = bool(match and size and any(match.groups()))
                        if valid:
                            first, last = match.groups()
                            if first:
                                start = int(first)
                                end = min(int(last), size - 1) if last else size - 1
                            else:
                                valid = int(last) > 0
                                start = max(0, size - int(last))
                            valid = valid and 0 <= start <= end < size
                        if not valid:
                            self.send_response(416)
                            self.send_header("Content-Range", f"bytes */{size}")
                            self.send_header("Content-Length", "0")
                            self.end_headers()
                            return
                        status = 206
                    self.send_response(status)
                    source_types = {"mp4": "video/mp4", "pdf": "application/pdf", "md": "text/markdown; charset=utf-8"}
                    self.send_header("Content-Type", source_types[source["format"]])
                    self.send_header("Content-Length", str(max(0, end - start + 1)))
                    self.send_header("Accept-Ranges", "bytes")
                    if status == 206:
                        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                    self.send_header("Content-Disposition", f'inline; filename="source.{source["format"]}"')
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    with file.open("rb") as stream:
                        stream.seek(start)
                        remaining = end - start + 1
                        while remaining > 0:
                            block = stream.read(min(65536, remaining))
                            if not block:
                                break
                            self.wfile.write(block)
                            remaining -= len(block)
                elif path in {"/", "/index.html", "/style.css", "/app.js"}:
                    file = FRONTEND / ("index.html" if path == "/" else path[1:])
                    content_type = mimetypes.guess_type(str(file))[0] or "text/plain"
                    self.respond(file.read_bytes(), content_type=content_type + "; charset=utf-8")
                elif path == "/favicon.ico":
                    self.respond(b"", 204, "image/x-icon")
                else:
                    self.json_response({"error": "页面或接口不存在"}, 404)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                self.json_response({"error": f"读取或校验数据失败：{exc}"}, 500)

        def do_POST(self):
            self.json_response({"error": "检查页为只读，不支持修改或审核提交"}, 405)

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(port=8765, dataset=DEFAULT_DATASET, ontology=DEFAULT_ONTOLOGY, resource_dir=None, *,
          media_manifest=None, media_dir=None):
    server = make_server(port, dataset, ontology, resource_dir, media_manifest=media_manifest, media_dir=media_dir)
    print(f"Knowledge preview: http://127.0.0.1:{server.server_port}", flush=True)
    print("Local read-only preview. Stop with Ctrl+C.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Preview stopped.", flush=True)
    finally:
        server.server_close()
