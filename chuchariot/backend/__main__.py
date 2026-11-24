"""Explicit database maintenance commands; API startup never imports JSON."""
import argparse
import json
from pathlib import Path

from ..dataset_io import ROOT, TABLES, read_json, write_json
from .config import Settings
from .database import Repository, check, fingerprint, normalized


def main():
    parser = argparse.ArgumentParser(description="ChuChariot persistent knowledge database")
    parser.add_argument("command", choices=["dry-run", "import", "status", "export"])
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/candidates/knowledge.v0.11.json")
    parser.add_argument("--ontology", type=Path, default=ROOT / "data/ontology/ontology.v0.7.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command in {"dry-run", "import"}:
        data, ontology = read_json(args.dataset), read_json(args.ontology)
        check(data, ontology)
        report = {"valid": True, "counts": {t: len(data[t]) for t in TABLES},
                  "baseline_hash": fingerprint({"data": normalized(data), "ontology": ontology})}
        if args.command == "dry-run":
            print(json.dumps(report, ensure_ascii=True, indent=2))
            return
    repo = Repository(Settings.load())
    try:
        if args.command == "import":
            repo.initialize()
            report.update(repo.import_baseline(data, ontology))
        elif args.command == "status":
            data, ontology, state = repo.snapshot()
            report = {"ready": True, "graph_revision": repo.revision(state), "dataset_id": data["dataset_id"],
                      "ontology_version": ontology["version"], "counts": {t: len(data[t]) for t in TABLES}}
        else:
            if args.output is None:
                parser.error("export requires --output (choose a new release filename)")
            deleted, data, ontology, state = repo.recycle_bin()
            if args.output.exists():
                parser.error("output already exists; choose a new filename")
            write_json(args.output, {"dataset": data, "ontology": ontology, "deleted_records": deleted,
                                    "graph_revision": repo.revision(state)})
            report = {"exported": True, "graph_revision": repo.revision(state)}
        print(json.dumps(report, ensure_ascii=True, indent=2))
    finally:
        repo.close()


if __name__ == "__main__":
    main()
