# 接口状态与后端对接

2026-11-24：API1.1.0在变更集中支持delete／restore，新增已鉴权回收站`GET /api/v1/internal/deleted`。删除记录从有效查询和候选图谱中移除，保留可恢复内容及审计；引用未处理时阻止删除。见[完整操作说明](deletion.md)。

## 当前正式接口（本地首版已实现）

2026-11-23用户要求开始后已实现Neo4j及FastAPI，运行于`http://127.0.0.1:8780`，实时文档`/docs`和`/openapi.json`。见[正式契约](contracts/knowledge-api.v1.openapi.json)、[启动、鉴权与变更集](backend.md)。16个原计划及5个适配／资源／历史接口可用。知识、本体版本不变，数据库修订单列。下文保留准备及临时接口记录，“尚未实现”描述的是当时状态。

## 正式数据库API准备稿（尚未实现）

2026-11-23：按“先做好准备、不开始”的要求，新增[数据库与迁移方案](plans/database-api-preparation-2026-11-23.md)及[OpenAPI 3.1契约草案](contracts/knowledge-api.v1.draft.openapi.json)，规划16个`/api/v1`接口。实体属性、图数据、事实证据、模型映射、教学路径、增量变更及导出均有拟定响应；公众与内部访问分开。接口草案不表示当前服务已提供这些路由。本轮未安装依赖、启动数据库、导入或实现后端；下文仍记录实际可用的临时接口及Python查询。

2026-11-23更新：当前第十一批使用契约0.4.0、本体0.7.0，增加词义节点、语境指称和词典条目定位，详见[规范接入](normalization-v0.11.md)。历史第十批使用契约0.3.0，新增视频时间段与现代复原来源标注，见[视频知识接入](video-knowledge-v0.10.md)。第九批契约0.2.0继续兼容。`HAS_DIMENSION` 的 `value` 是结构化尺寸对象，含 `quantity`、`unit`、`raw`、`approximate` 和 `value` 或 `min`/`max`；归属为事实的 `subject_id`，不提供 `object_id`。尺寸参与属性、证据和审核查询，不参与实体邻接关系。`stats.dimension_properties` 单列总数，审核视图由可见事实判断，不可用总数绕过过滤。旧契约0.1.0仍支持旧节点式尺寸。本体0.5增加 `ComponentRegion`（描述区域）和 `HAS_REGION`；推断保留 `rationale`，不能按来源记载展示。

更新：2026-11-19。当前增加临时本地只读检查接口，正式后端实体查询等计划路由尚未实现；路由草案见软件计划设计书第 6 节。

## 临时检查接口

新增用途投影：`/api/preview?review=1&audience=public`隐藏管理及分类关系，`audience=internal`返回完整核对视图；默认internal兼容旧调用，未知或重复参数400。用途与审核状态独立，见[公众／内部视图](presentation-views.md)。这不是身份鉴权。

在本机按 [README](../README.md#启动临时检查页) 启动服务。以下接口均用于组内临时测试。

| 路由 | 行为 |
|---|---|
| `GET /` | 检查页，另提供 `/style.css`、`/app.js` |
| `GET /api/health` | 返回 `status: ok`、`mode: local_read_only_preview`；不是数据库/AI健康证明 |
| `GET /api/preview` | 元数据、统计、实体目录、已确认事实/证据/映射、本体及模型初查报告；配置媒体清单时返回可见的 `media` |
| `GET /api/preview?review=1` | 显式审核视图，包含候选及争议记录，保留各条状态 |
| `GET /api/sources/{id}` | 可选原PDF、MP4或已登记词典摘录MD；资源目录配置且文件存在时返回，支持Range及206/416；否则404 |
| `GET /api/media/{id}` | 可选 PNG；需要媒体清单、可见关联和本地图片。候选图块显式使用 `?review=1`，其他情况返回 404 |

来源和媒体对象附 `available` 表示对应本机文件能否打开。普通视图保留目录与审核数量，并按审核状态过滤事实、证据、尺寸、映射和媒体。JSON、样式和脚本响应禁用缓存，重新请求会重新校验数据。未定义路由返回 404，读取或校验失败返回 500 和 JSON 错误，POST 返回 405。预览服务仅绑定回环地址，审核参数用于切换本地视图。

这组接口服务于开发检查，无编辑/审核写入功能，不代表计划中的完整 REST 服务已完成。

## 后端 Python 对接

P2 可以先复用 `chuchariot.knowledge.KnowledgeStore`：

```python
from chuchariot.knowledge import KnowledgeStore

store = KnowledgeStore.load(
    "data/candidates/knowledge.v0.11.json",
    "data/ontology/ontology.v0.7.json",
)
entities = store.list_entities(query="轮毂", kind="ComponentType")
detail = store.entity("type:003")
relations = store.relations("component:ch15-hub", include_pending=True)
facts = store.facts("component:ch15-hub", include_pending=True)
proof = store.evidence("component:ch15-hub", include_pending=True)
```

查询返回深拷贝。未知 ID 抛 `KnowledgeError`，后端可转换为 404；实体存在但没有已确认关系/证据/映射时返回空集合，不能当作实体不存在。

基础查询的 `include_pending` 默认为 `False`。后端审核模式若允许开启，必须明确标记；普通展陈页面不能无提示地使用候选。实体元数据带 `fact_review_summary`；未确认尺寸默认隐藏。

HTTP 参数、分页、错误模型、正式响应和框架依赖需 P2 实际实现后补齐。本页记录的是 Python 调用接口，不宣称满足计划中的 REST 接口验收。

## v0.9教学路径查询

`KnowledgeStore.connection_path(from_id, to_id, include_pending=False, max_hops=8)` 返回一个最短有向教学路径，包含 `found`、`hops`、`view`、`note`。每跳含 `fact`、`from`、`to`、`connection`、`evidence_basis`、`metadata_facts`和带来源的 `evidence`。不走组成、分类或共享材质边；不自动反向查询；max_hops为1—16整数。找不到时found为false，hops为空；未知实体抛KnowledgeError。

本地只读接口：`GET /api/connection-path?from=type:001&to=type:body&review=1&max_hops=8`。from/to必须各出现一次；参数错误400，实体不存在404，数据读取或校验失败500。review省略时仅使用确认事实，当前找不到候选路径。未提供跨域或正式服务部署。

CLI：`python -m chuchariot --dataset data/candidates/knowledge.v0.11.json --ontology data/ontology/ontology.v0.7.json connection-path type:001 type:body --include-pending`。展示时保留各跳性质和警示，不把教学导航描述为真实装配确认。
