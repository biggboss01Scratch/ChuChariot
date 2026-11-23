# 接口状态与后端对接

2026-11-23更新：第七批继续使用契约0.2.0。`HAS_DIMENSION` 的 `value` 是结构化尺寸对象，含 `quantity`、`unit`、`raw`、`approximate` 和 `value` 或 `min`/`max`；归属为事实的 `subject_id`，不提供 `object_id`。尺寸参与属性、证据和审核查询，不参与实体邻接关系。`stats.dimension_properties` 单列总数，审核视图由可见事实判断，不可用总数绕过过滤。旧契约0.1.0仍支持旧节点式尺寸。本体0.5增加 `ComponentRegion`（描述区域）和 `HAS_REGION`；推断保留 `rationale`，不能按来源记载展示。

更新：2026-11-19。当前增加临时本地只读检查接口，正式后端实体查询等计划路由尚未实现；路由草案见软件计划设计书第 6 节。

## 临时检查接口

在本机按 [README](../README.md#启动临时检查页) 启动服务。以下接口均用于组内临时测试。

| 路由 | 行为 |
|---|---|
| `GET /` | 检查页，另提供 `/style.css`、`/app.js` |
| `GET /api/health` | 返回 `status: ok`、`mode: local_read_only_preview`；不是数据库/AI健康证明 |
| `GET /api/preview` | 元数据、统计、实体目录、已确认事实/证据/映射、本体及模型初查报告；配置媒体清单时返回可见的 `media` |
| `GET /api/preview?review=1` | 显式审核视图，包含候选及争议记录，保留各条状态 |
| `GET /api/sources/{id}` | 可选原 PDF；需要配置资源目录且文件存在，否则 404 |
| `GET /api/media/{id}` | 可选 PNG；需要媒体清单、可见关联和本地图片。候选图块显式使用 `?review=1`，其他情况返回 404 |

来源和媒体对象附 `available` 表示对应本机文件能否打开。普通视图保留目录与审核数量，并按审核状态过滤事实、证据、尺寸、映射和媒体。JSON、样式和脚本响应禁用缓存，重新请求会重新校验数据。未定义路由返回 404，读取或校验失败返回 500 和 JSON 错误，POST 返回 405。预览服务仅绑定回环地址，审核参数用于切换本地视图。

这组接口服务于开发检查，无编辑/审核写入功能，不代表计划中的完整 REST 服务已完成。

## 后端 Python 对接

P2 可以先复用 `chuchariot.knowledge.KnowledgeStore`：

```python
from chuchariot.knowledge import KnowledgeStore

store = KnowledgeStore.load(
    "data/candidates/teacher-pdf.v0.7.json",
    "data/ontology/ontology.v0.5.json",
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
