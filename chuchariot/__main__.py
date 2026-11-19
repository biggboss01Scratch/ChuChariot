"""Run with: python -m chuchariot --help (Python standard library only)."""

import argparse
import json
import sys
from pathlib import Path

from .dataset_io import DEFAULT_DATASET, DEFAULT_ONTOLOGY, ROOT, KnowledgeError, read_json, write_json
from .importer import import_dataset
from .queries import KnowledgeStore
from .resources import check_mapping_indices, inspect_glb, inventory
from .validation import validate


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="楚国战车知识层工具；候选事实默认不作为已确认知识返回。")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--ontology", type=Path, default=DEFAULT_ONTOLOGY)
    sub = parser.add_subparsers(dest="command", required=True)
    checking = sub.add_parser("validate", help="检查格式、引用、证据、尺寸归属和循环")
    checking.add_argument("--model-report", type=Path, help="额外检查映射的模型哈希和节点范围")
    listing = sub.add_parser("list", help="检索实体目录；实体目录不等于事实已确认")
    listing.add_argument("--q", default="")
    listing.add_argument("--type", dest="kind")
    listing.add_argument("--include-pending", action="store_true")
    for command in ("detail", "relations", "evidence", "mappings"):
        query = sub.add_parser(command)
        query.add_argument("entity_id")
        query.add_argument("--include-pending", action="store_true", help="开发/审核视图，同时返回待审核或有争议记录")
    importing = sub.add_parser("import", help="幂等导入候选包；同 ID 不同内容报错，不覆盖")
    importing.add_argument("--input", type=Path, required=True)
    importing.add_argument("--output", type=Path, required=True)
    resources = sub.add_parser("inventory", help="只读登记资源并生成 GLB 结构报告")
    resources.add_argument("--resource-dir", type=Path, required=True)
    resources.add_argument("--specs", type=Path, default=ROOT / "data/sources/resource-specs.json")
    resources.add_argument("--output", type=Path, required=True)
    resources.add_argument("--model-report", type=Path)
    preview = sub.add_parser("preview", help="打开本地只读知识检查页，无第三方依赖")
    preview.add_argument("--port", type=int, default=8765)
    preview.add_argument("--resource-dir", type=Path, action="append",
                         help="可重复指定原始PDF目录，只提供已登记的PDF")
    preview.add_argument("--media-manifest", type=Path, help="截图与模型图像关联清单")
    preview.add_argument("--media-dir", type=Path, help="从原件生成的本地图像目录")
    args = parser.parse_args(argv)
    try:
        if args.command == "preview":
            from .preview import serve
            serve(args.port, args.dataset, args.ontology, args.resource_dir,
                  media_manifest=args.media_manifest, media_dir=args.media_dir)
            return 0
        elif args.command == "inventory":
            specs = read_json(args.specs)
            result = inventory(args.resource_dir, specs)
            model_report = None
            if args.model_report:
                model = next(r for r in result["resources"] if r["id"] == "res:005")
                if model["availability"] == "present":
                    model_report = inspect_glb(args.resource_dir / model["filename"])
                else:
                    model_report = {"model_resource_id": "res:005", "availability": "missing"}
            write_json(args.output, result)
            if args.model_report:
                write_json(args.model_report, model_report)
            result = {"registered": len(result["resources"]),
                      "missing": [r["id"] for r in result["resources"] if r["availability"] == "missing"]}
        elif args.command == "import":
            if args.input.resolve() == args.output.resolve():
                raise KnowledgeError("输入和输出不能是同一文件；保留原始候选包")
            result = import_dataset(read_json(args.input), args.output, read_json(args.ontology))
            result = {"dataset_id": result["dataset_id"], "facts": len(result["facts"]), "output": str(args.output)}
        else:
            data, ontology = read_json(args.dataset), read_json(args.ontology)
            if args.command == "validate":
                errors = validate(data, ontology)
                if not errors and args.model_report:
                    errors.extend(check_mapping_indices(data, read_json(args.model_report)))
                if errors:
                    raise KnowledgeError("\n".join(errors))
                result = {"valid": True, "stage": data["stage"], "entities": len(data["entities"]),
                          "facts": len(data["facts"]),
                          "pending_facts": sum(f["review_status"] == "pending" for f in data["facts"]),
                          "note": "格式校验不等于历史真实性核验；未检查原始资源文件是否齐全。"}
            else:
                store = KnowledgeStore(data, ontology)
                if args.command == "list":
                    if args.kind and args.kind not in ontology["entity_kinds"]:
                        raise KnowledgeError(f"未知实体类型：{args.kind}")
                    result = store.list_entities(args.q, args.kind, args.include_pending)
                elif args.command == "detail":
                    result = {"entity": store.entity(args.entity_id, args.include_pending),
                              "facts": store.facts(args.entity_id, args.include_pending),
                              "view": "review" if args.include_pending else "confirmed_only"}
                else:
                    result = getattr(store, args.command)(args.entity_id, args.include_pending)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (KnowledgeError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
