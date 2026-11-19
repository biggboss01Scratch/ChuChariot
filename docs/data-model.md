# 知识数据规范 v0.1.0

更新：2026-11-19。适用于当前三批候选数据。项目约束由 `chuchariot/validation.py` 与 `data/ontology/ontology.v0.1.json` 共同定义。

## 数据集与 ID

根字段：`schema_version`、`ontology_version`、`dataset_id`、`stage`、`description`，以及 `sources`、`evidence`、`entities`、`facts`、`model_mappings` 五个数组。

最新候选包名 `wheel-axle.v0.3.json` 表示数据批次，包内契约与本体版本仍为 `0.1.0`。实际入库关系和描述数量见[当前覆盖](coverage.md)。预审结论按事实 ID 保存在运行摘要，正式事实状态由 `review_status` 表达。

当前版本均为 `0.1.0`。`stage` 为 `candidate` 或 `reviewed`；后者不得含待审核事实或映射。未知字段报错，以避免拼写错误被忽略。导入包必须是完整、引用闭合的数据集，不接受孤立事实片段直接入库。

ID 格式为 `命名空间:稳定编号`，例如 `type:001`、`fact:001`；只能用小写英文字母、数字和规范允许的分隔符。一个数据集内全局唯一，不随名称变更。外部重复 JSON 字段被拒绝，不接受“最后一个同名字段覆盖前面字段”。

## 实体

共同字段：`id`、`kind`、`label`、`aliases`；可选 `scope_id`、`note`。具体类型及语义见本体文件。

- `ComponentType` 是类别；`Component` 是实物部件实例，必须通过 `scope_id` 声明所属 `Chariot` 或 `ReferenceSpecimen`。
- `ReferenceSpecimen` 专门保存对照标本；不能默认属于主展品，也不能因资料合订就合并不同标本。
- `Measurement` 的 `scope_id` 是尺寸所有者；必须与 `HAS_MEASUREMENT` 主体一致。允许所有者为战车、具体部件、对照标本或模型版本，彼此不可混用。
- `ModelVersion` 必须携带 `resource_id` 和 `content_sha256`，与对应 GLB 内容绑定；模型变化须使用新版本并重新核对映射。
- `Connection`、`Pose`、`AssemblyStep` 当前仅有基础实体与关系边界，没有完整空间/步骤执行格式。不能将它们的预留类型视为已实现演示。

`measurement` 字段只用于尺寸实体，包含 `quantity`、`unit`、`raw`、`approximate`，以及单值 `value` 或完整范围 `min`/`max`。数值必须是有限正数，未知值不填零；当前长度单位为 `mm`、`cm`、`m`。保留原始表达，不自动把非圆轮的横径/竖径合成一个“直径”。

当前没有经过核对的位姿数据。不能以文件格式的单位惯例替代模型实际采用单位的核验；坐标系、局部/世界空间和旋转表示在场景格式引入前另行固定。

## 事实与关系

每条事实包含 `id`、`subject_id`、`predicate`、`object_id` 或 `value`、`evidence_ids`、`origin`、`review_status`、`extraction`。目标实体与文字值二选一，关系允许类型在本体中逐项声明。

核心关系：类别层次、实例归类、直接组成、尺寸、参与连接、位姿、步骤涉及部件、步骤依赖和有证据的文字描述。

`HAS_PART` 的类别→类别只表达资料图示的通用结构；实例组成要求所属研究对象一致。不能由图中部件名推出具体实物数量或完整性。类别层次、直接组成、步骤依赖、推导依据链分别检查循环。

`SUPPORTED_BY` 由事实的 `evidence_ids` 投影；`REPRESENTED_BY` 由映射表投影，避免双份可修改记录。

| 字段 | 取值及含义 |
|---|---|
| `origin` | `documented` 资料明确记载；`inferred` 结构推导；`hypothesis` 复原假设 |
| `review_status` | `pending` 待审核；`confirmed` 按本项目规则已审核；`disputed` 有争议 |
| `basis_fact_ids` | 可选推导依据；不可引用自己或形成循环 |
| `rationale` | 推导/假设必须提供理由，并附证据或依据事实 |
| `extraction` | 必填 `method`、`run_id`，可选模型与提示词版本 |
| `review` | 已确认或有争议时必填审核者、ISO 日期和备注 |

`documented` 必须附有效证据。`confirmed` 不代表考古权威认证，也不改变 `hypothesis` 的性质。当前样例全部 `pending`，AI/程序不能因格式通过就自动提升状态。

## 来源与证据

来源记录保存稳定 ID、题名、资源 ID、资源文件名和格式；PDF 可保存总页数。当前具体证据格式只实现 PDF 页定位，DOCX 段落/OCR 坐标等后续扩展需要版本说明，不能滥用 PDF 页字段。

证据包含 `source_id`、从 1 开始的 `pdf_page`、`locator`、`quote`、`transcription`、`check_status`、`scope_note`，可选印刷页码和图号。PDF 页码、图号、印刷页码互不替代。

`embedded_text` 表示文本层抽取，`image_transcription` 表示依据页面图像转录或观察。`source_checked` 表示已对照来源，正式审核见对应事实的 `review_status`。第三批共登记 4 份 PDF 和 22 段证据，部分汇编图号待回查至原始报告。

## 模型映射与查询视图

映射保存 `id`、`entity_id`、`model_version_id`、`node_indices`、`review_status`、`note`；非待审核映射另附 `review`。允许一对多；类别映射不能冒充实物部件实例映射。

索引是绑定内容哈希的 glTF 节点数组下标，不是 Three.js 运行时对象 ID。模型中存在重名节点，不能只按名称绑定。索引/哈希检查只验证格式对应，不能确认几何语义。

检查页的图像索引位于 `data/sources/fusion-media.v0.1.json`，与候选包并列管理。资料裁片按实体、证据页和像素矩形定位，模型图按实体、映射 ID、节点索引和 GLB 哈希定位。关联须经过校验，并遵循事实或映射的审核可见性。查看[融合格式与重建](fusion.md)。

默认事实、关系、证据、映射查询仅返回 `confirmed`；审核视图 `--include-pending` 同时返回待审核及争议记录。实体目录始终可以浏览，但会附带 `fact_review_summary`；未确认尺寸值默认隐藏，返回 `measurement_visibility: hidden_until_reviewed`。目录元数据不能被前端直接包装成已确认解说。

## 导入与迁移

导入先完整校验，按 ID 去重；同 ID 同内容不重复写入，同 ID 不同内容拒绝整次操作，原文件保持不变。格式、数据集身份、阶段或说明冲突也需显式协调，不静默覆盖。

本版本是首个实现版本，无历史数据迁移。新增字段/语义需更新版本、验证器、样例、测试和本文；不支持的版本明确报错。
