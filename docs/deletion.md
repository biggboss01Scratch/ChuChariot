# 删除、回收站与恢复

2026-11-24已实现，API版本1.1.0。实体、事实、证据、来源、模型映射均支持删除和恢复，沿用已鉴权的变更集流程。

## 删除的实际效果

提交删除后，记录从普通查询、实体详情、图谱、教学路径、内部有效快照和有效数据导出中移除；依赖它派生的图关系也移除。Neo4j保留被删除记录的原内容、操作人、时间、原因和修订，供内部回收站及历史查询使用。删除知识记录与清理原PDF／视频／GLB文件分开管理。

这与disputed不同：disputed表示观点有争议，候选视图仍可显示；delete表示当前知识已撤下，候选视图也不显示。

仍有有效引用时不能单独删除。校验会列出引用记录ID；应先修改引用，或在同一个变更集中明确删除相应依赖。系统不自动级联。检查覆盖事实主客体、推导依据、证据及来源、实体作用范围／词义来源、模型映射与版本。

## 操作步骤

先GET`/api/v1/meta`取得当前graph_revision。在`/docs`输入本机操作员Bearer凭据后，POST`/api/v1/internal/change-sets`，提供Idempotency-Key。下面ID仅是格式示例，实际操作应使用要纠正的记录ID：

```json
{
  "base_graph_revision": "rev:00000001",
  "ontology_version": "0.7.0",
  "schema_version": "0.4.0",
  "reason": "说明哪条知识错误，以及删除依据",
  "operations": [
    {"table": "facts", "id": "fact:example", "action": "delete"}
  ]
}
```

然后依次POST`/api/v1/internal/change-sets/{id}/validate`和`/api/v1/internal/change-sets/{id}/commit`。commit请求体是`{"expected_graph_revision":"rev:00000001"}`，应使用该变更集对应的实际基线修订。validate不删除记录，只有commit成功才生效。

版本过期或引用未处理时409，目标不存在时404，非法操作字段422。validate会以valid=false及错误列表报告业务问题；必须解决问题后再提交。相同变更集的提交重试不会重复删除或增加修订。

## 回收站与恢复

GET`/api/v1/internal/deleted?page=1&page_size=30`查看回收站；可用`table=facts`等筛选。响应含原record及deleted_at、deleted_by、deleted_reason、deleted_revision。接口需要内部凭据，公众不能通过查询参数访问。

恢复仍创建新的变更集，把action改为restore：

```json
{"table": "facts", "id": "fact:example", "action": "restore"}
```

delete／restore只提交table、id和action，原因写在变更集reason中，不接受客户端提供原record、审核状态或操作人。恢复使用服务端回收站保存的内容；如需纠正内容，恢复后另提交update。

恢复会再次校验完整知识。被引用的主体、证据或来源尚未恢复时，需要先恢复它们或同批恢复。原本已审核的事实、模型映射恢复后重新成为pending，保留origin及理由；重新审核后再按发布规则展示。

删除后的ID继续保留，create不能复用成另一条记录，update／review不能绕过恢复；restore也不能覆盖已有有效记录。操作历史中的action区分delete、restore、update和依赖重审，旧历史不被抹除。

## 导出与边界

内部export和CLI导出的dataset只含有效记录，另附deleted_records保存回收站。同一导出中的有效数据、回收站和graph_revision来自同一个事务快照。完整数据库备份应继续使用Neo4j dump，以同时保留修订历史。

当前通过后端API／Swagger操作；图谱页面仍是只读浏览，尚无管理删除按钮。运行中的原标准库JSON预览仍读取独立的发行文件；要查看数据库删除效果，应使用8780数据库版页面并重新加载。

本轮删除测试在独立27687测试库执行，覆盖五张记录表、引用阻止、显式批量删除和恢复、撤下后不可见、ID保留、重复提交、失败回滚、恢复重审及旧版本冲突。正式主库与v0.11／本体v0.7原文件保留。
