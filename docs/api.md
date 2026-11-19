# 接口状态与后端对接

更新：2026-11-19。当前增加临时本地只读检查接口，正式后端实体查询等计划路由尚未实现；路由草案见软件计划设计书第 6 节。

## 临时检查接口

运行 `python -m chuchariot preview --port 8765 --resource-dir ..` 后可访问：

| 路由 | 行为 |
|---|---|
| `GET /` | 检查页，另提供 `/style.css`、`/app.js` |
| `GET /api/health` | 返回 `status: ok`、`mode: local_read_only_preview`；不是数据库/AI健康证明 |
| `GET /api/preview` | 元数据、统计、实体目录、已确认事实/证据/映射、本体及模型初查报告 |
| `GET /api/preview?review=1` | 显式审核视图，包含候选及争议记录，保留各条状态 |
| `GET /api/sources/{id}` | 可选原 PDF；需要配置资源目录且文件存在，否则 404 |

API 返回的来源对象附 `available` 表示本机原文是否可打开。普通视图仍可看到目录及审核数量，但不含候选事实/证据/映射和未审核尺寸值。JSON、样式和脚本响应禁用缓存；重新请求将重新校验数据。未定义路由返回 404，读取/校验失败返回 500 和 JSON 错误，POST 返回 405。

这组接口服务于开发检查，无编辑/审核写入功能，不代表计划中的完整 REST 服务已完成。

## 后端 Python 对接

P2 可以先复用 `chuchariot.knowledge.KnowledgeStore`：

```python
from chuchariot.knowledge import KnowledgeStore

store = KnowledgeStore.load()
entities = store.list_entities(query="轮毂", kind="ComponentType")
detail = store.entity("type:003")
relations = store.relations("type:001")
proof = store.evidence("measurement:001", include_pending=True)
```

查询返回深拷贝。未知 ID 抛 `KnowledgeError`，后端可转换为 404；实体存在但没有已确认关系/证据/映射时返回空集合，不能当作实体不存在。

基础查询的 `include_pending` 默认为 `False`。后端审核模式若允许开启，必须明确标记；普通展陈页面不能无提示地使用候选。实体元数据带 `fact_review_summary`；未确认尺寸默认隐藏。

HTTP 参数、分页、错误模型、正式响应和框架依赖需 P2 实际实现后补齐。本页记录的是 Python 调用接口，不宣称满足计划中的 REST 接口验收。
