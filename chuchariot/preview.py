"""Local, read-only inspection UI. This is not the planned production backend."""

from __future__ import annotations

import json
import mimetypes
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from .dataset_io import DEFAULT_DATASET, DEFAULT_ONTOLOGY, ROOT, read_json
from .queries import KnowledgeStore

FRONTEND = ROOT / "frontend/inspector"
ResourceDirectories = Path | list[Path] | tuple[Path, ...] | None


def preview_data(dataset=DEFAULT_DATASET, ontology=DEFAULT_ONTOLOGY, review=False,
                 resource_dir: ResourceDirectories = None) -> dict:
    definitions = read_json(ontology)
    store = KnowledgeStore(read_json(dataset), definitions)
    snapshot = store.snapshot(include_pending=review)
    for source in snapshot["sources"]:
        source["available"] = source_path(source, resource_dir) is not None
    model = ROOT / "data/scenes/model-inspection.json"
    snapshot["meta"].update(review_mode=review, validation="passed")
    snapshot["ontology"] = definitions
    snapshot["model_report"] = read_json(model) if model.exists() else None
    return snapshot


def source_path(source: dict, resource_dir: ResourceDirectories) -> Path | None:
    if resource_dir is None or source["format"] != "pdf":
        return None
    directories = (resource_dir,) if isinstance(resource_dir, Path) else resource_dir
    for directory in directories:
        root = directory.resolve()
        path = (root / source["filename"]).resolve()
        if path.parent == root and path.is_file():
            return path
    return None


def make_server(port=8765, dataset=DEFAULT_DATASET, ontology=DEFAULT_ONTOLOGY,
                resource_dir: ResourceDirectories = None) -> ThreadingHTTPServer:
    # Validate before starting, then reload data on each request for manual review.
    KnowledgeStore.load(dataset, ontology)

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
            try:
                if path == "/api/health":
                    self.json_response({"status": "ok", "mode": "local_read_only_preview"})
                elif path == "/api/preview":
                    review = parse_qs(parsed.query).get("review", ["0"]) == ["1"]
                    self.json_response(preview_data(dataset, ontology, review, resource_dir))
                elif path.startswith("/api/sources/"):
                    source_id = path.removeprefix("/api/sources/")
                    source = KnowledgeStore.load(dataset, ontology).source(source_id)
                    file = source_path(source, resource_dir) if source else None
                    if file is None:
                        self.json_response({"error": "原文未配置、缺失或来源不存在"}, 404)
                        return
                    self.send_response(200)
                    self.send_header("Content-Type", "application/pdf")
                    self.send_header("Content-Length", str(file.stat().st_size))
                    self.send_header("Content-Disposition", 'inline; filename="source.pdf"')
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    with file.open("rb") as stream:
                        shutil.copyfileobj(stream, self.wfile)
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


def serve(port=8765, dataset=DEFAULT_DATASET, ontology=DEFAULT_ONTOLOGY, resource_dir=None):
    server = make_server(port, dataset, ontology, resource_dir)
    print(f"Knowledge preview: http://127.0.0.1:{server.server_port}", flush=True)
    print("Local read-only preview. Stop with Ctrl+C.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Preview stopped.", flush=True)
    finally:
        server.server_close()
