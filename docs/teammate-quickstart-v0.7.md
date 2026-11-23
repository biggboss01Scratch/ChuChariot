# 队友接入说明 · 知识图谱 v0.7

2026-11-23。本批可供前后端对接和展示开发，95个实体、270条待审核事实，其中107条实体关系、54项尺寸属性；52段证据、7组候选模型映射。契约0.2.0，本体0.5.0。全部事实仍为pending，不能无提示地展示成已确认结论。

## 获取与运行

拉取仓库main分支，或解压同版本源码ZIP。在含README的目录运行，要求Python 3.11+；直接使用已提交的候选文件即可，无需先安装OCR、重跑提取或准备PDF/GLB。

```powershell
python -m chuchariot --dataset data/candidates/teacher-pdf.v0.7.json --ontology data/ontology/ontology.v0.5.json validate
python -m chuchariot --dataset data/candidates/teacher-pdf.v0.7.json --ontology data/ontology/ontology.v0.5.json preview --port 8769 --media-manifest data/sources/fusion-media.v0.7.json
```

打开 `http://127.0.0.1:8769/?view=map` 查看全图，按Ctrl+C停止服务。已有8769服务时可改端口；127.0.0.1只指向运行服务的电脑，队友需要在自己电脑启动。

## 配套文件

| 文件 | 用途 |
|---|---|
| [teacher-pdf.v0.7.json](../data/candidates/teacher-pdf.v0.7.json) | 完整候选知识：实体、事实、证据、来源和模型映射 |
| [ontology.v0.5.json](../data/ontology/ontology.v0.5.json) | 实体类型、谓词、端点和值类型约束 |
| [fusion-media.v0.7.json](../data/sources/fusion-media.v0.7.json) | 可选媒体索引，图片文件需另外准备 |
| [数据规范](data-model.md) · [接口说明](api.md) | 字段含义、过滤和只读查询接口 |
| [审计表](audits/2026-11-23-source-audit.md) · [覆盖缺口](audits/2026-11-23-coverage.md) | 原272条的逐条核对、修正与未解决问题 |

不要将v0.7数据与旧本体混用；不指定版本的CLI默认值仍是旧样例，请使用上面的完整命令。数据库接入由队友实现，当前交付是JSON知识快照和只读适配器，不是已部署的Neo4j数据库。

## Python接入

在仓库根目录运行：

```python
from chuchariot.knowledge import KnowledgeStore

store = KnowledgeStore.load(
    "data/candidates/teacher-pdf.v0.7.json",
    "data/ontology/ontology.v0.5.json",
)
entity_id = "component:ch15-hub"
entity = store.entity(entity_id, include_pending=True)
facts = store.facts(entity_id, include_pending=True)
attributes = [f for f in facts if f["subject_id"] == entity_id and "value" in f]
relations = store.relations(entity_id, include_pending=True)
proof = store.evidence(entity_id, include_pending=True)
snapshot = store.snapshot(include_pending=True)
```

`facts`包含主体和客体与该实体有关的事实。全部属性面板应汇总主体为当前实体的文字/尺寸属性，以及材质、髹饰、纹饰、保存特征等概念关系；不要把传入关系当成该实体自身属性，也不要把具体标本尺寸继承给通用类别。

HTTP读取可用 `GET /api/preview?review=1` 获取候选全图。`GET /api/preview`默认仅返回已确认内容，因此本批的可见事实为零。开发时启用候选视图并明确标示状态；正式接口、跨域配置、分页和数据库写入仍需后端实现。

## 前端与建库注意事项

- `entities`用于实体目录和图节点；只有带 `object_id` 的事实才是实体之间的边。用稳定ID关联，不要按显示名称合并对象。
- `HAS_DIMENSION`为属性，结构化 `value`含 `quantity`、`unit`、`raw`、`approximate`和单值 `value` 或范围 `min`/`max`。本批没有独立尺寸节点，不要把对象强转字符串或再生成54个尺寸实体。
- `ComponentRegion`是描述区域，`HAS_REGION`不表示可拆卸零件。`ReferenceSpecimen`、未编号 `ReferenceRecord`、复原图和六号车要保持区分，不能都挂成六号车的实物部件。
- 保留 `origin`、`rationale`、`review_status`、`evidence_ids`及来源页。8号车图红线认作靷属于证据不足的推断候选；图示观察和作者解释不能显示成无条件结论。
- `scope_id`是归属字段；前端按它分组不等于新增历史关系。大地图六个分区也只是浏览布局。
- 7组模型映射仍待核验；GLB节点索引绑定模型版本和哈希，不要把知识实体或描述区域自动当成可爆炸拆件。队友旧版展陈包尚未合并，本批未验证其新爆炸图。
- 两条重复事实已合并，旧ID去向见[运行摘要](../data/run-summaries/2026-11-23-source-audit.json)的 `merged_duplicates`。旧批次保留用于追溯，不要把多个版本叠加导入。

## 资源与复现

源码包含数据、证据文字、审核记录和预览程序。原PDF、GLB、图片缓存、本地数据库及运行日志不在源码ZIP或Git中；缺少它们仍可浏览图谱和属性，原页/图片入口会不可用。准备方法见[来源登记](sources.md)和[融合说明](fusion.md)。

如需回放整理过程，再按序运行 `python -m scripts.extract_teacher_pdf_v05`、`python -m scripts.migrate_dimensions_v06`、`python -m scripts.apply_source_audit_v07`。这些脚本回放已记录的整理与判断，不是重新进行独立内容审核。

检查命令：`python -X utf8 -m unittest discover -s tests -q`；有Node时可另跑 `node --test tests/inspector-layout.test.cjs`。测试验证程序和数据一致性，内容确认仍需项目组员复核。
