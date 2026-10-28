"""The studio's HTTP routes: the static page, the JSON API and the file download.

Every body is JSON except the upload and the file download; a refusal is ``{"error": text}`` with
the ``ApiError`` status, any other failure a 500. A JSON POST must carry ``Content-Type:
application/json`` and at most MAX_JSON bytes, which also makes a cross-site request need a CORS
preflight the server never grants.
"""

from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from henryk_media.studio import prompts
from henryk_media.studio.app import UPLOAD_LIMIT, ApiError, Studio

STATIC = Path(__file__).with_name("static")
MAX_JSON = 1_000_000
TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".md": "text/markdown; charset=utf-8",
}
H3_FIELDS = ("action", "camera", "hold", "soundscape", "music")


def handler(studio: Studio) -> type[BaseHTTPRequestHandler]:
    """Return the request handler class serving one studio."""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass  # the page polls every second

        def send(self, code: int, content_type: str, body: bytes) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, code: int, payload: dict) -> None:
            self.send(code, "application/json; charset=utf-8", json.dumps(payload).encode())

        def send_file(self, path: Path) -> None:
            self.send(
                200, TYPES.get(path.suffix.lower(), "application/octet-stream"), path.read_bytes()
            )

        def length(self, limit: int) -> int:
            try:
                length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                length = -1
            if not 0 < length <= limit:
                raise ApiError(400, f"the body needs a Content-Length from 1 to {limit} bytes")
            return length

        def body(self) -> dict:
            if not self.headers.get("Content-Type", "").startswith("application/json"):
                raise ApiError(400, "the body must be application/json")
            try:
                body = json.loads(self.rfile.read(self.length(MAX_JSON)))
            except ValueError as error:
                raise ApiError(400, "the body is not JSON") from error
            if not isinstance(body, dict):
                raise ApiError(400, "the body must be a JSON object")
            return body

        def do_GET(self) -> None:
            self.dispatch("GET")

        def do_POST(self) -> None:
            self.dispatch("POST")

        def dispatch(self, method: str) -> None:
            url = urlsplit(self.path)
            query = {key: values[0] for key, values in parse_qs(url.query).items()}
            try:
                self.route(method, url.path, query)
            except ApiError as error:
                self.send_json(error.status, {"error": str(error)})
            except Exception as error:  # noqa: BLE001 - the page shows the failure
                self.send_json(500, {"error": f"{type(error).__name__}: {error}"})

        def route(self, method: str, path: str, query: dict) -> None:
            parts = path.strip("/").split("/")
            if method == "GET" and path in ("", "/", "/index.html"):
                self.send_file(STATIC / "index.html")
            elif method == "GET" and len(parts) == 2 and parts[0] == "static":
                file = STATIC / parts[1]
                if not (file.is_file() and file.resolve().parent == STATIC.resolve()):
                    raise ApiError(404, "not found")
                self.send_file(file)
            elif method == "GET" and path == "/api/gpus":
                self.send_json(200, studio.gpu_list())
            elif method == "POST" and path == "/api/gpu":
                self.send_json(200, studio.select_gpu(self.body().get("index")))
            elif method == "GET" and path == "/api/images":
                self.send_json(200, {"images": studio.images()})
            elif method == "GET" and path == "/api/file":
                self.send_file(studio.resolve(query.get("ref")))
            elif method == "POST" and path == "/api/uploads":
                data = self.rfile.read(self.length(UPLOAD_LIMIT))
                self.send_json(201, studio.upload(query.get("name", ""), data))
            elif method == "GET" and path == "/api/prompts":
                self.send_json(200, studio.prompts(query.get("ref"), query.get("kind")))
            elif method == "POST" and path == "/api/h3-prompt":
                body = self.body()
                fields = [body.get(name, "") for name in H3_FIELDS]
                if not all(isinstance(value, str) for value in fields):
                    raise ApiError(400, f"every field of {list(H3_FIELDS)} must be text")
                self.send_json(200, {"prompt": prompts.h3_prompt(*fields)})
            elif method == "POST" and path == "/api/jobs":
                self.send_json(201, {"job": studio.view(studio.submit(self.body()))})
            elif method == "GET" and path == "/api/jobs":
                self.send_json(200, {"jobs": studio.job_list()})
            elif method == "GET" and len(parts) == 3 and parts[:2] == ["api", "jobs"]:
                self.send_json(200, {"job": studio.view(studio.job(parts[2]))})
            elif method == "POST" and len(parts) == 4 and parts[:2] == ["api", "jobs"]:
                if parts[3] != "cancel":
                    raise ApiError(404, "not found")
                self.body()
                self.send_json(200, {"job": studio.view(studio.cancel(parts[2]))})
            else:
                raise ApiError(404, "not found")

    return Handler
