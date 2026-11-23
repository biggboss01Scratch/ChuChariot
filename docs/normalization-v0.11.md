# v0.11：构件区域与“辔／马勒”统一

2026-11-23。当前数据[knowledge.v0.11.json](../data/candidates/knowledge.v0.11.json)，本体[ontology.v0.7.json](../data/ontology/ontology.v0.7.json)，数据格式0.4.0。旧v0.10、队友v0.9和各旧本体保持不变。

## 已完成的两项规范

1. **股、骹和毂上窄篆统一为部位／特征区域。** 三个具体节点从`Component`改为`ComponentRegion`，对应类别从`ComponentType`改为`StructuralRegionType`，所属关系改用`HAS_REGION`。保留原ID、CH1：5归属、全部尺寸及篆的13道数量。股、骹仍分别与毂、轮牙榫卯相接，部位不是独立分件。窄篆只记录环棱特征，不补造制作方法或附加环件。
2. **马勒作为规范讲解对象，辔按语境和词义保存。** `type:horse-bridle`继续代表马勒；旧`type:bridle`改为`TermSense`，记录老师“辔”小节接续马勒图的特定用法，不再作为另一个部件。另保存辞书的缰绳义与缰绳／衔勒合称义，避免全局同义合并。

资料依据：老师汇编PDF第6页明确记辐的内外两段、过渡平滑无明显界线及毂上窄篆；第7页“（二）辔”接续第8页马勒推测复原图。辞书原条目为[轡](https://dict.revised.moe.edu.tw/dictView.jsp?ID=669&la=0&powerMode=0)、[勒](https://dict.revised.moe.edu.tw/dictView.jsp?ID=3203)。项目保存带URL、访问日期及内容哈希的人工摘录，明确不是原网页副本。对老师用词与马勒图的对齐保留`inferred`及理由。

## 数据及版本

| 项目 | v0.10 | v0.11 |
| --- | ---: | ---: |
| 实体 | 126 | 128 |
| 事实 | 412 | 423 |
| 实体关系 | 229 | 233 |
| 尺寸属性 | 54 | 54 |
| 证据 | 68 | 72 |
| 来源 | 5 | 7 |
| 模型映射 | 7 | 7 |

新增11条事实包括词义描述、语境关系及区域类别说明，不代表11条新的考古实物结论。所有旧记录ID保留；修改前后完整快照见[迁移清单](../data/run-summaries/2026-11-23-normalization-v011.json)。没有删除原记录，没有提升任何审核状态。视频知识及原有54项尺寸逐条保持不变。

本次涉及概念分类和关系端点，因此**本体升为0.7.0，数据升为v0.11**。格式0.4.0增加词义节点的`lexeme`、`source_id`及词典来源的`url`、`accessed_on`；校验继续兼容旧0.1—0.3格式与各自本体。

## 查询与展示约定

- `INSTANCE_OF`现在允许`ComponentRegion → StructuralRegionType`；`HAS_REGION`允许具体构件到具体区域，以及构件类别到区域类别。区域形态、数量、尺寸可独立查询和展示。
- `TENON_JOINT_WITH`允许同一标本中的`ComponentRegion ↔ Component`，不将区域变成独立零件，不允许跨标本。
- `USES_TERM`：来源记录使用该语境词项。`TERM_DENOTES`：该来源语境指称规范概念，非全局同义。两种关系都校验词义所属来源的证据。
- `TERM_RELATED_TO`：广义词义涉及某概念；不表示同义、上下位或整体部分。
- `type:bridle`现在是老师用法的词义节点；`term:pei-reins`指缰绳义；`term:pei-broad`保留合称义。`source_id`约束解释来源，老师用法另用`scope_id`限定到马勒图记录。
- 13段教学路径完整保留，其中原“镳→辔→缰”统一为“镳→马勒→缰”；路径及连接记录ID保留，起终点与依据同步更新，仍是教学导航。不能沿词义关系拼接机械路径。
- 图谱显示“描述区域”“部位或特征类别”“语境词义”，词典证据显示义项并打开官方URL，不伪造PDF页码。部位仍可高亮；本轮未新增GLB映射，实际三维高亮仍须队友实现对应。

## 当前启动命令

```powershell
python -m chuchariot --dataset data/candidates/knowledge.v0.11.json --ontology data/ontology/ontology.v0.7.json validate --model-report data/scenes/model-inspection.json
python -m chuchariot --dataset data/candidates/knowledge.v0.11.json --ontology data/ontology/ontology.v0.7.json detail component:ch15-spoke-inner --include-pending
python -m chuchariot --dataset data/candidates/knowledge.v0.11.json --ontology data/ontology/ontology.v0.7.json connection-path type:bit type:body --include-pending
python -m chuchariot --dataset data/candidates/knowledge.v0.11.json --ontology data/ontology/ontology.v0.7.json preview --port 8770 --resource-dir .. --resource-dir data/sources/terminology --media-manifest data/sources/fusion-media.v0.11.json
```

检查页搜索“股”“篆”“辔”“马勒”，查看属性、区域关系、词义与证据。回放脚本为`python -m scripts.normalize_terms_v011`，读取固定旧版及仓库内词典摘录，不依赖网络或原视频。

## 验证与剩余问题

98项Python与13项Node测试通过：旧ID保留、全部尺寸及视频事实不变、两处榫卯同标本约束、区域不能接回独立部件关系、词义分离、来源校验、13段导航、媒体、导入幂等，以及128个地图节点无重叠。

此次关闭[一致性检查](audits/2026-11-23-consistency-v010.md)中的区域粒度及辔／马勒语义处理两项。仍未统一全部研究观点的结构化表示，也未补齐所有通用关系的车型、时代及适用范围；不因此宣称知识库已无任何潜在冲突。
