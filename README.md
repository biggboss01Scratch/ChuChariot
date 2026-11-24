# 楚国战车专题交互导览系统

面向博物馆专题介绍场景，以可追溯的知识图谱组织楚国战车资料，规划结合三维模型和专题讲解提供交互导览。AI 问答是规划中的加分项。

2026-11-24新增[删除、回收站与恢复](docs/deletion.md)：通过内部API撤下错误知识，检查引用并保留历史，支持恢复；数据库版接口版本1.1.0。

队友接入这版数据库和接口，请先看[API v1.1阶段性交接](docs/handovers/Codex-API-v1.1-交接文档-2026-11-24.md)。

**当前已具备 P1 知识层与首版本地 Neo4j／FastAPI 后端。** 数据库支持持久化查询、证据追溯、增量变更、审核及历史记录；数据库图谱入口为`http://127.0.0.1:8780/`，接口文档为`http://127.0.0.1:8780/docs`，见[后端启动与队友接入](docs/backend.md)。正式展陈页面、实时三维联动和AI问答仍待完成。

当前为 **v0.11**，统一构件区域和“辔／马勒”的语境词义。数据配本体0.7.0、格式0.4.0，详见[规范与接入说明](docs/normalization-v0.11.md)。[视频知识v0.10](docs/video-knowledge-v0.10.md)及[队友v0.9](docs/teammate-quickstart-v0.9.md)作为历史交付保留，完整记录见[文档索引](docs/index.md)。

本次GitHub交付见[v0.11交接文档](docs/handovers/Codex-v0.11-交接文档-2026-11-23.md)。综合展厅与三维原型尚未完整接入新版知识，新区域高亮及双向联动待合并适配。

检查页新增[公众／内部视图及关系筛选](docs/presentation-views.md)：默认公众预览，隐藏管理及分类。原标准库临时服务的用途切换不含鉴权；新数据库服务的内部访问需要操作员凭据。

## 从仓库复现

在包含本 README 的目录运行，要求 Python 3.11+。知识查询、校验、临时页面及测试均可在纯 Python 标准库环境运行。

```powershell
python -m chuchariot --dataset data/candidates/knowledge.v0.11.json --ontology data/ontology/ontology.v0.7.json validate --model-report data/scenes/model-inspection.json
python -m chuchariot --dataset data/candidates/knowledge.v0.11.json --ontology data/ontology/ontology.v0.7.json detail component:ch15-hub --include-pending
python -X utf8 -m unittest discover -s tests -v
```

数据已包含在仓库中，直接运行上述命令即可。若需回放v0.5—v0.7的历史整理过程，再依次执行 `python -m scripts.extract_teacher_pdf_v05`、`python -m scripts.migrate_dimensions_v06` 和 `python -m scripts.apply_source_audit_v07`。

第十一批为 **128个实体、233条实体关系、54项尺寸、423条待复核事实、72段证据、7组候选模型映射**。股、骹及窄篆以区域表达，原有尺寸、两处榫卯和视频知识保留；马勒为规范讲解对象，辔按老师用法、缰绳义及合称义分别记录。合理推测可入库并保留来源、性质及范围。新增三维高亮仍待映射。不指定 `--dataset` 的CLI继续读取初版样例。

查询逐跳依据：

```powershell
python -m chuchariot --dataset data/candidates/knowledge.v0.11.json --ontology data/ontology/ontology.v0.7.json connection-path type:001 type:body --include-pending
```

该命令返回“车轮→毂→车轴→伏兔→舆”，逐跳保留对照标本或教学方案依据、推断性质和证据。只查询有向教学导航边，不通过材质、类别等关系拼凑机械路径。

## 启动临时检查页

```powershell
python -m chuchariot --dataset data/candidates/knowledge.v0.11.json --ontology data/ontology/ontology.v0.7.json preview --port 8770 --media-manifest data/sources/fusion-media.v0.11.json --resource-dir .. --resource-dir data/sources/terminology
```

浏览器访问 `http://127.0.0.1:8770/`，在运行命令的终端按 `Ctrl+C` 停止。候选检查模式可搜索「股」「篆」「辔」「马勒」或「长短榫」并查看属性、证据位置和媒体索引。切换到已确认视图时，当前正式确认数为零。

点击图谱节点或目录实体，右侧「全部属性」汇总当前实体的尺寸、材质、保存特征等直接属性，并列出实体字段、文字描述和结构关系。每项属性保留审核状态及证据入口；具体标本的属性不自动归给通用类别。小屏会定位到详情，可用「返回关系图」回到图谱。

图谱默认使用「大地图」。内部完整核对保留128个实体、233条实体关系及54项尺寸；公众预览按展示规则筛选，可勾选结构、外观及复原案例关系，默认隐藏无连线节点。节点按轮系、牵引与车体、轴与軎辖、马具与系驾、材质与髹饰、图示与资料目录分区。分区仅用于浏览，不是新增知识关系。选择实体只高亮关联，勾选筛选时重新排布；复杂全图不保证所有跨区连线完全无交叉。

访问 `http://127.0.0.1:8770/?view=map` 直接进入大屏。顶部可跳转分区；搜索后按回车定位，继续按回车查看下一个匹配；滚轮围绕鼠标缩放，拖动平移，右下位置导航可跳转。点击节点打开可收起的属性面板。「全图总览」回到整图，「局部关联」保留原先的逐个实体核对方式。按Esc先收起详情，再退出大屏。

前端布局检查可用Node运行 `node --test tests/inspector-layout.test.cjs tests/inspector-video.test.cjs tests/inspector-normalization.test.cjs`，检查全量覆盖、节点不重叠、尺寸不再进入主图、关系无增删和布局稳定。运行知识工具及Python测试仍无需Node。

如需打开原 PDF 或查看从原件生成的图片，请按[来源与资源登记](docs/sources.md)准备本地资料，再执行[融合检查复现命令](docs/fusion.md#本地复现)。从 GitHub 获取的版本包含索引和生成脚本，原件与缓存由组内渠道另行准备。

## 开发交接

小组按[软件计划设计书](docs/software-plan.md)串行接力。接手后记录收到的提交号，按[交接记录](docs/handover.md)复现当前批次，完成后同步更新[数据规范](docs/data-model.md)、[覆盖与待核问题](docs/coverage.md)和[进度记录](docs/progress.md)。
