"""Generate ignored local credentials once, without printing them."""
import json
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
local = root / ".local"
local.mkdir(exist_ok=True)
config = local / "backend.json"
if not config.exists():
    password = secrets.token_urlsafe(32)
    values = {
        "uri": "bolt://127.0.0.1:17687", "username": "neo4j", "password": password,
        "database": "neo4j", "publication_mode": "candidate_preview",
        "operators": {"local-operator": secrets.token_urlsafe(48)},
        "resource_dirs": [str(root.parent), str(root / "assets/references/local"),
                          str(root / "data/sources/terminology")],
    }
    config.write_text(json.dumps(values, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (local / "neo4j.env").write_text("NEO4J_AUTH=neo4j/" + password + "\n", encoding="utf-8")
    print("Created ignored local configuration; candidate preview is explicitly enabled.")
else:
    print("Kept existing local configuration.")
