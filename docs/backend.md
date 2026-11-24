# 持久化知识库与后端 API

2026-11-23用户要求开始后已实施；2026-11-24增加[删除、回收站和恢复](deletion.md)，接口版本1.1.0。运行版本：Neo4j Community 5.26.33、Python驱动6.4.1、FastAPI 0.135.3。知识仍为v0.11、本体0.7.0、数据契约0.4.0，主库修订`rev:00000001`。

## 已完成

- Docker命名卷持久化保存128个实体、423条事实、72段证据、7个来源和7组模型映射。54项尺寸保留为属性，全部事实仍待审核。
- Record.id唯一约束及类型、名称、谓词、审核索引。实体、事实、证据、来源、映射为分别可查询的节点；嵌套字段展开为标量属性，原始表达保留。Fact为断言主记录，直接关系携带fact_id且可重建。
- 版本化查询、内部鉴权、教学路径、完整导出、增量变更、审核、冲突保护、修订历史和原件读取。
- 数据库版复用图谱页面，支持搜索、属性、关系筛选及证据定位。内部凭据只留在页面内存，退出内部视图清除凭据与内部图数据。

本机入口：图谱`http://127.0.0.1:8780/`，接口文档`http://127.0.0.1:8780/docs`，真实就绪检查`http://127.0.0.1:8780/api/v1/health/ready`。原8770等临时服务保持独立。

## 从仓库启动

仓库根目录、PowerShell、Python 3.11+及Docker Desktop。本次验证Python 3.13.11。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-backend.lock
.\.venv\Scripts\python.exe scripts/configure_backend.py
docker desktop start
docker compose up -d
.\.venv\Scripts\python.exe -m chuchariot.backend dry-run
.\.venv\Scripts\python.exe -m chuchariot.backend import
.\.venv\Scripts\python.exe -m uvicorn chuchariot.backend.api:app_factory --factory --host 127.0.0.1 --port 8780
```

首次启动容器需要数秒，确认Bolt连接可用后再import；失败时看`docker compose logs --tail 60 neo4j`。API启动不会自动导入JSON；数据库异常返回503。

已有数据库日常重启只需compose up和最后的uvicorn命令，不重新导入。相同基线重复导入不新增；已有增量修订后，基线导入会拒绝覆盖。主卷`chuchariot_knowledge-data`不随Python退出或容器停止而删除。

配置脚本首次生成`.local/backend.json`及`.local/neo4j.env`，后续保留原配置，不重置密码；两者被Git忽略。当前后台API启动PID记在`.local/backend.pid`，日志位于`.local/backend.stdout.log`和`.local/backend.stderr.log`。手动前台启动可Ctrl+C停止，不要按模糊进程名终止其他Python项目。

## 公众、内部和候选

默认Settings为confirmed_only。本机配置脚本**显式启用candidate_preview以供课堂检查**，页面持续显示候选、推测和审核状态。正式发布时在本机配置改为confirmed_only并重启；不因导入自动确认知识。

公众不接受audience=internal、review或Cypher。内部需要`Authorization: Bearer <operator token>`，无鉴权配置则拒绝；缺凭据401、错误凭据403。操作员身份及审核日期由服务端确定。页面使用密码输入框，凭据不进入URL或localStorage。

凭据位于本机配置operators字段；项目持有人可本机查看并按需授权。不要把整个配置发给队友，其中还含数据库密码；队友可本机重新生成独立凭据。首版操作员具有相同内部维护能力，尚无多角色账号管理。

## 队友接入

查看[正式契约](contracts/knowledge-api.v1.openapi.json)或服务`/openapi.json`。原16个计划接口全部实现，另有6个图谱适配、历史、回收站及资源路由，实时OpenAPI列出全部22个操作。

| 接口 | 用途 |
| --- | --- |
| GET /api/v1/meta | 数据基线、当前修订、本体／契约和发布模式 |
| GET /api/v1/entities?q=轮&page=1&page_size=30 | 名称、别名、ID检索与分页 |
| GET /api/v1/entities/{id} | 实体、尺寸properties、文字descriptions、relations |
| GET /api/v1/graph?center=type:001&depth=2 | 周边图；省略center为受上限限制的全图 |
| GET /api/v1/graph?groups=structure&groups=appearance | 关系组筛选，返回nodes、edges及truncated |
| GET /api/v1/facts/{id}/evidence | PDF页、视频起止秒或辞书义项及来源 |
| GET /api/v1/entities/{id}/model-mappings | 当前发布模式允许的模型映射，保留审核状态 |
| GET /api/v1/sources/{id} | 来源元信息及受控content_url |
| GET /api/v1/internal/paths/teaching?from=type:001&to=type:body&include_pending=true | 有向教学导航，逐跳带依据和性质 |
| GET /api/v1/internal/history/{record_id} | 修改前后快照、操作人、原因和修订 |

前端只访问API，不持有Neo4j密码。跨源前端应配置同源反向代理；首版未开放任意CORS。实体及事实ID沿用JSON，不能依赖Neo4j内部ID。

baseline_dataset_id指首批输入，graph_revision随成功提交变化。正式发行新知识交接版时从数据库导出，并明确新的数据版本。运行时以数据库为唯一写入入口；JSON作为交接及备份，不能各自独立编辑后假定已同步。

## 增量维护

POST`/api/v1/internal/change-sets`时带Bearer及Idempotency-Key。以下是占位结构，不作为史料导入：

```json
{
  "base_graph_revision": "rev:00000001",
  "ontology_version": "0.7.0",
  "schema_version": "0.4.0",
  "reason": "修改原因及核对方式",
  "operations": [{
    "table": "entities",
    "id": "type:example",
    "action": "create",
    "record": {"id": "type:example", "kind": "ComponentType", "label": "占位示例", "aliases": []}
  }]
}
```

随后POST`internal/change-sets/{id}/validate`，查看valid、错误和impacted_fact_ids；通过后POST`internal/change-sets/{id}/commit`，请求体`{"expected_graph_revision":"rev:00000001"}`。

同操作员同幂等键同内容返回原变更集，同键不同内容409。校验后他人抢先提交会409，需读新修订并新建变更集。提交后的同请求重试不重复写入。缺证据、跨标本、循环或类型不符不能通过；写入失败整批回滚。

一个变更集对同一记录只允许一次操作。update提供完整记录，不冒填review或confirmed。审核另用action=review、review_status和note，仅支持facts及model_mappings；接受推测不改变其origin。关键证据、实体或依据事实变化会重开受影响的审核；需要下一次修订重新审核。

错误记录可以通过delete撤下，使用内部回收站及restore恢复；disputed仅表示有争议，不等同删除。删除会检查引用，恢复事实／映射会重新待审核，详见[删除流程](deletion.md)。恢复有效记录的旧内容仍可从历史before_json取出，走update形成新修订。本体外的新类型／谓词需显式迁移，首版不提供在线本体编辑器。

## 备份、恢复及验证

本轮生成`.local/backups/baseline-2026-11-23.json`及离线`neo4j.dump`；已恢复到**独立测试库**并逐条比较知识、本体及修订，一致。原PDF、视频、GLB需另备份。

后续导出可用内部export或CLI，CLI要求新文件名，避免覆盖备份：

```powershell
.\.venv\Scripts\python.exe -m chuchariot.backend export --output .local/backups/manual-new-release.json
```

Community离线dump需先停本项目数据库，用锁定镜像挂载数据卷和备份目录执行`neo4j-admin database dump neo4j --to-path=/backups`，完成再启动。恢复前先备份现库，优先恢复到独立环境验证后切换。不要执行`docker compose down -v`删除知识卷。

测试使用独立compose.test.yaml与27687端口；只有显式设置以下环境变量才会重置**测试库**，其他URI会拒绝：

```powershell
docker compose -f compose.test.yaml up -d
$env:CHUCHARIOT_TEST_URI='bolt://127.0.0.1:27687'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --test tests/inspector-layout.test.cjs tests/inspector-video.test.cjs tests/inspector-normalization.test.cjs tests/inspector-filters.test.cjs
```

118项Python及16项Node通过：真实导入、响应契约、三种证据、候选隔离、鉴权、Range、并发冲突、回滚及历史恢复。未装后端依赖时跳过后端测试，原知识工具仍支持标准库运行。

本轮版本、数量、主库未变及备份恢复结果见[机器可读验收记录](audits/2026-11-23-backend-acceptance.json)。测试容器已停止，主数据库及8780接口继续运行；未推送GitHub。

页面实查公众76条关系、标本横径／竖径、内部凭据入口及返回公众成功加载。当前为小规模课程项目，API从数据库读取一致快照后复用查询与展示规则，快照和写入通过GraphState串行，未做大规模性能优化。

剩余：三维展厅全面联调、新区域GLB高亮、裁剪图片媒体服务、内容人工复核、AI问答、在线本体迁移及公网部署。7组映射仍未完成几何语义审核。数据库可用不代表整个博物馆系统完成。

设计核对：[Neo4j Docker](https://neo4j.com/docs/operations-manual/current/docker/introduction/)、[事务与重试](https://neo4j.com/docs/python-manual/current/transactions/)、[FastAPI安全依赖](https://fastapi.tiangolo.com/tutorial/security/first-steps/)。具体版本已锁定在compose及requirements文件。
