# 知识数据规范 v0.4.0

更新：2026-11-23。当前v0.11使用本体0.7.0、格式0.4.0，区域类别及词义关系见[规范说明](normalization-v0.11.md)。校验继续兼容旧版。以下为历史第十批`knowledge.v0.10.json`使用契约0.3.0及本体0.6.0，增加视频时间段、现代复原标注；详见[视频知识入库](video-knowledge-v0.10.md)。旧PDF规范仍适用。以下第九批 `teacher-pdf.v0.9.json` 使用本体 `ontology.v0.6.json`；旧批次保留原契约0.1.0和对应旧本体。校验实现位于 `chuchariot/validation.py`。本轮修改见[原页审计](audits/2026-11-23-source-audit.md)及[尺寸迁移与建模检查](model-review-2026-11-23.md)。

## 数据集与标识

根字段为 `schema_version`、`ontology_version`、`dataset_id`、`stage`、`description`，以及 `sources`、`evidence`、`entities`、`facts`、`model_mappings` 五个数组。候选包引用必须闭合。未知字段、重复JSON键和不支持的契约版本报错。

ID采用稳定命名空间格式，例如 `type:001`、`fact:pdf-147`，全包唯一。实体、事实、证据ID不随名称变化。`stage` 为 `candidate` 或 `reviewed`；后者不得含待审核事实或映射。具体记录数量见[当前覆盖](coverage.md)。

## 实体

共同字段为 `id`、`kind`、`label`、`aliases`，可选 `scope_id`、`note`；0.4.0的TermSense另须`lexeme`和有效来源`source_id`。类型约束以所选本体为准。

- `ComponentType` 为通用部件类别，不代表某辆车上的具体对象。
- `Chariot` 为具体战车或研究对象。
- `ReferenceSpecimen` 为资料中的对照标本，不能默认归属于六号车。
- `Component` 通过 `scope_id` 声明所属 `Chariot` 或 `ReferenceSpecimen`。
- `ComponentRegion` 表示部件的描述区域，通过同范围的 `HAS_REGION` 关联，用于局部属性限定，不表示可拆卸零件。当前M1：302辀身前、中、后段使用此类型。
- `ReferenceRecord` 保存未编号描述、统计及复原图记录，不冒充已确定身份的实物。
- `HarnessRole` 保存服马、骖马等系驾角色，不是已识别的某匹马。
- `Material`、`SurfaceFinish`、`PreservationFeature`、`DecorationMotif` 是可复用的概念，支持反查关联器物。
- `ModelVersion` 必须绑定 `resource_id` 与 `content_sha256`；模型变化使用新版本并重新核对节点。
- `Connection`、`Pose`、`AssemblyStep` 为预留类型，不能据其存在声称已完成空间或步骤演示。

## 尺寸作为结构化属性

第六批不再创建独立 `Measurement` 实体。`HAS_DIMENSION` 事实以所属对象为 `subject_id`，`value` 为结构化对象：

```json
{
  "quantity": "通长",
  "unit": "cm",
  "raw": "毂通长70、贤端径13.5、壶中径17、轵端径6厘米",
  "approximate": false,
  "value": 70
}
```

必填 `quantity`、`unit`、`raw`、`approximate`，并提供单值 `value` 或完整范围 `min`/`max`，两者不能混用。数值必须为有限正数，拒绝零、布尔值和无穷值。长度单位为 `mm`、`cm`、`m`，不擅自替换原始单位或以零表示未知。

属性归属由事实主体唯一表达，不在实体元数据重复保存另一份可编辑尺寸。允许主体为具体部件、对照标本、战车、来源记录或模型版本；不允许通用类别直接接收标本尺寸。同一主体同一项目可有多条来源断言，每条拥有独立事实ID、证据和审核状态，不按项目名覆盖。

横径/竖径、残长/通长、局部尺寸/总体尺寸保持区别；不自动合成平均直径。数量与重量目前仍为文字属性，尚未采用上述长度对象；相对位置距离虽然保留原项目名，也不能被解释成轴自身通长。

旧契约0.1.0仍支持尺寸实体、`measurement` 数值对象、`scope_id` 和 `HAS_MEASUREMENT` 边，原有所有者一致性检查不变。旧包继续可读，迁移生成新包，不原地覆盖。对应ID索引见[迁移摘要](../data/run-summaries/2026-11-23-dimension-properties.json)。

## 事实、范围与审核

事实共同字段为 `id`、`subject_id`、`predicate`、`evidence_ids`、`origin`、`review_status`、`extraction`。目标二选一：实体关系提供 `object_id`，属性提供 `value`。一般文字属性的值必须为字符串；只有本体声明 `object_kind: dimension` 的尺寸属性可使用结构化数值对象，旧契约不接受该扩展。

- `HAS_PART` 为直接组成；类别组成需明确适用范围。原3条图示结构已收窄为 `DEPICTS`。实例组成要求归属一致，不能跨车或标本。
- `INSTANCE_OF` 表示实例归类。`REFERS_TO_TYPE` 表示来源记录涉及某类别，`DEPICTS` 表示图中描绘，两者不等于实物组成。
- `TENON_JOINT_WITH` 要求部件同属一个器物范围；`HAS_ASSOCIATED_COMPONENT` 要求所配部件归属于主体标本。
- 材质、保存特征、髹饰、纹饰关系保留作用范围。局部红黑漆不自动成为所有同类部件的属性。
- 类别层次、组成、步骤依赖和推导依据分别检查循环。`SUPPORTED_BY` 与 `REPRESENTED_BY` 从证据引用和映射投影，避免重复编辑。

| 字段 | 含义 |
|---|---|
| `origin` | `documented` 来源记载或图像观察；`inferred` 推断；`hypothesis` 复原假设 |
| `review_status` | `pending` 待审核；`confirmed` 已按项目规则审核；`disputed` 有争议 |
| `basis_fact_ids` | 可选依据事实，不能引用自身或形成循环 |
| `rationale` | 推断和假设必填理由，并附证据或依据事实 |
| `extraction` | 必填 `method`、`run_id`，可选模型和提示词版本 |
| `review` | 非pending记录必填审核者、ISO日期、备注 |

来源记载必须附有效证据；已确认不改变推断或假设的性质。当前423条事实均待审核。原272条的来源支持/需修正/证据不足判定单独保存在审计记录，不替代 `review_status`。`documented` 不意味着逐字照录或已经独立核实。年代、车型和适用范围尚未充分结构化，需保留描述中的限定词。

## 来源、媒体与模型

来源保存题名、资源ID、文件名和格式；PDF可带页数。PDF证据支持PDF页定位，视频证据改用start_seconds/end_seconds（不能假设每条都有pdf_page）。PDF证据包含 `source_id`、`pdf_page`、`locator`、`quote`、`transcription`、`check_status`、`scope_note`，可选印刷页码、图号；三者不能互相替代。

`embedded_text` 为文本层，`image_transcription` 为页面图像转录或观察。`source_checked` 表示Codex已对照页面，不能当作老师、组员或独立人员审核。教师汇编也不替代原始发掘报告。

媒体v0.9沿用18个资料图块和7组模型图，按实体、事实证据和来源页关联。模型映射保存实体、模型版本、节点索引、状态和说明；索引绑定GLB哈希，不采用运行时对象ID。模型几何不自动成为历史尺寸。详见[融合记录](fusion.md)。

## 查询、导入与版本

默认查询仅返回已确认事实、证据和映射，审核模式显式启用候选和争议。尺寸属性随整条事实过滤，不从实体字段绕过。目录保留并附审核数量，这些数量不是已确认内容。`stats.dimension_properties` 单列尺寸属性总数，不能代替当前可见事实。

候选数据为唯一编辑入口；本地导入快照只作派生产物。幂等导入同ID同内容不重写，同ID不同内容拒绝整次操作，元数据版本冲突也不静默合并。新增语义须同步本体、校验、查询消费者、测试和文档。

## v0.9教学分组与路径

本体0.6新增 `Subsystem`（教师栏目）、`StructuralRegionType`（教学结构区域）、`EvidenceBasisClass`（路径依据类别）。前端六分区仍是浏览布局，和四个教师栏目不是同一套分类；“转动装置”沿用资料标题，不表示机械学分类。

`IN_SUBSYSTEM`为栏目归属，允许同一类别进入多个栏目；`SCHEMATIC_HAS_REGION`、`REGION_NEAR_COMPONENT`、`TEACHING_GROUPS_TYPE`、`SCHEMATIC_ASSEMBLY_WITH`保存教学区域、邻近、功能集合和示意装配，不能当作已确认实物组成。来件7条类别层 `HAS_PART`均为inferred，保留理由和待审核状态；尤其舆底不能直接解释为已证独立可拆件。

`SCHEMATIC_NEXT`是有向导航边；每跳用一个 `Connection`实体记录 `CONNECTION_FROM`、`CONNECTION_TO`、`HAS_EVIDENCE_BASIS`。三条元数据各自通过 `basis_fact_ids`引用同一条路径事实，校验起终点一致和一对一完整性。依据类别为对照标本/复原图/教学方案，它与origin、review_status分别保存。路径可混合来源，不作为同一标本的连续机械链或安装顺序。

查询只使用可见导航边及完整可见的连接元数据；默认确认模式不会泄漏候选依据。详见[同步检查](teammate-sync-v0.9.md)。
