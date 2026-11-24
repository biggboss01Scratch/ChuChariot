"""Local configuration. Secrets are never serialized into API responses."""
from dataclasses import dataclass, field
import json
import os
from pathlib import Path

from ..dataset_io import ROOT


@dataclass
class Settings:
    uri: str = "bolt://127.0.0.1:17687"
    username: str = "neo4j"
    password: str = field(default="", repr=False)
    database: str = "neo4j"
    publication_mode: str = "confirmed_only"
    operators: dict = field(default_factory=dict, repr=False)
    resource_dirs: tuple = ()

    def __post_init__(self):
        if self.publication_mode not in {"confirmed_only", "candidate_preview"}:
            raise ValueError("Invalid publication mode")
        if not isinstance(self.operators, dict) or any(
            not isinstance(actor, str) or not actor.strip() or not isinstance(token, str) or len(token) < 32
            for actor, token in self.operators.items()
        ) or len(set(self.operators.values())) != len(self.operators):
            raise ValueError("Operators require distinct tokens of at least 32 characters")

    @classmethod
    def load(cls, path=None):
        path = Path(path or os.environ.get("CHUCHARIOT_CONFIG", ROOT / ".local/backend.json"))
        values = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        values["resource_dirs"] = tuple(Path(p).resolve() for p in values.get("resource_dirs", []))
        for name in ("uri", "username", "password", "database", "publication_mode"):
            key = "CHUCHARIOT_" + name.upper()
            if key in os.environ:
                values[name] = os.environ[key]
        return cls(**values)
