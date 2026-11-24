"""Shared server-side transport and configuration for the DeepSeek API."""

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


class AIUnavailable(Exception):
    """The external model is unavailable or returned unusable data."""


@dataclass(frozen=True)
class DeepSeekSettings:
    generation_key: str = field(default="", repr=False)
    generation_model: str = "deepseek-flash"
    timeout_seconds: float = 60

    def __post_init__(self):
        if not isinstance(self.generation_key, str) or not isinstance(self.generation_model, str):
            raise ValueError("Invalid DeepSeek credentials or model")
        if not self.generation_model.strip() or not 1 <= self.timeout_seconds <= 60:
            raise ValueError("Invalid DeepSeek model or timeout")

    @classmethod
    def load(cls, default_path):
        path = Path(os.environ.get("CHUCHARIOT_AI_CONFIG", default_path))
        config = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        if not isinstance(config, dict):
            raise ValueError("AI configuration must be an object")
        if "DEEPSEEK_API_KEY" in os.environ:
            config["generation_key"] = os.environ["DEEPSEEK_API_KEY"]
        return cls(**config)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def post(url, key, payload, timeout, provider):
    if not key:
        raise AIUnavailable(f"{provider} credential is not configured")
    req = Request(url, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                  {"Content-Type": "application/json", "Authorization": "Bearer " + key}, method="POST")
    try:
        with build_opener(NoRedirect()).open(req, timeout=timeout) as result:
            raw = result.read(2_000_001)
            if len(raw) > 2_000_000:
                raise AIUnavailable(f"{provider} response exceeded the size limit")
            return json.loads(raw)
    except HTTPError as exc:
        status = exc.code
        exc.close()
        raise AIUnavailable(f"{provider} request failed (HTTP {status})") from None
    except (URLError, TimeoutError, OSError, ValueError):
        raise AIUnavailable(f"{provider} returned no usable response") from None
