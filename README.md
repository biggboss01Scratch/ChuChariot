# 楚国战车专题交互导览系统

面向博物馆专题介绍场景，以可追溯的知识图谱组织楚国战车资料，规划结合三维模型和专题讲解提供交互导览。AI 问答是规划中的加分项。

**当前交付是 P1 知识层候选与临时检查工具。** 页面在本机只读运行，用于组内开发测试和证据复核。正式展陈页面、实时三维浏览与生产后端属于后续阶段。

队友接入请先看[知识图谱v0.9接入说明](docs/teammate-quickstart-v0.9.md)，可直接使用仓库内的最新数据启动检查和开发。完整资料位置与历史记录见[项目文档索引](docs/index.md)。

## 从仓库复现

在包含本 README 的目录运行，要求 Python 3.11+。知识查询、校验、临时页面及测试均可在纯 Python 标准库环境运行。

```powershell
python -m chuchariot --dataset data/candidates/teacher-pdf.v0.9.json --ontology data/ontology/ontology.v0.6.json validate --model-report data/scenes/model-inspection.json
python -m chuchariot --dataset data/candidates/teacher-pdf.v0.9.json --ontology data/ontology/ontology.v0.6.json detail component:ch15-hub --include-pending
python -X utf8 -m unittest discover -s tests -v
```

数据已包含在仓库中，直接运行上述命令即可。若需回放v0.5—v0.7的历史整理过程，再依次执行 `python -m scripts.extract_teacher_pdf_v05`、`python -m scripts.migrate_dimensions_v06` 和 `python -m scripts.apply_source_audit_v07`。

第九批为 **120个实体、218条实体关系、54项结构化尺寸属性、395条待审核事实、62段证据、7组候选模型映射**。完整保留v0.7；v0.8新增轮辋研究记录，v0.9增加教师栏目、教学区域和13段带依据分类的导航路径。新增内容未经完整独立审核，教学路径不证明同车实物连接或装配顺序；模型映射未增加，新增三维高亮尚未完成。查看[本次同步检查](docs/teammate-sync-v0.9.md)、[v0.7原页审计](docs/audits/2026-11-23-source-audit.md)及[覆盖缺口](docs/audits/2026-11-23-coverage.md)。不指定 `--dataset` 的CLI继续读取初版样例。

查询逐跳依据：

```powershell
python -m chuchariot --dataset data/candidates/teacher-pdf.v0.9.json --ontology data/ontology/ontology.v0.6.json connection-path type:001 type:body --include-pending
```

该命令返回“车轮→毂→车轴→伏兔→舆”，逐跳保留对照标本或教学方案依据、推断性质和证据。只查询有向教学导航边，不通过材质、类别等关系拼凑机械路径。

## 启动临时检查页

```powershell
python -m chuchariot --dataset data/candidates/teacher-pdf.v0.9.json --ontology data/ontology/ontology.v0.6.json preview --port 8769 --media-manifest data/sources/fusion-media.v0.9.json
```

浏览器访问 `http://127.0.0.1:8769/`，在运行命令的终端按 `Ctrl+C` 停止。候选检查模式可搜索「CH1：5轮毂」「轭」或「木材」并查看属性、证据位置和媒体索引。切换到已确认视图时，当前正式确认数为零。

点击图谱节点或目录实体，右侧「全部属性」汇总当前实体的尺寸、材质、保存特征等直接属性，并列出实体字段、文字描述和结构关系。每项属性保留审核状态及证据入口；具体标本的属性不自动归给通用类别。小屏会定位到详情，可用「返回关系图」回到图谱。

图谱默认使用「大地图」，同时保留120个实体、218条实体关系，54项尺寸在所属实体的属性面板展示，按轮系、牵引与车体、轴与軎辖、马具与系驾、材质与髹饰、图示与资料目录分区。分区仅用于浏览，不是新增知识关系。点击实体只高亮关联，不移走其他节点，也不重排地图；完整文字属性仍在详情中查看。复杂全图通过排布和曲线减少遮挡，不保证所有跨区连线完全无交叉。

访问 `http://127.0.0.1:8769/?view=map` 直接进入大屏。顶部可跳转分区；搜索后按回车定位，继续按回车查看下一个匹配；滚轮围绕鼠标缩放，拖动平移，右下位置导航可跳转。点击节点打开可收起的属性面板。「全图总览」回到整图，「局部关联」保留原先的逐个实体核对方式。按Esc先收起详情，再退出大屏。

前端布局检查可用Node运行 `node --test tests/inspector-layout.test.cjs`，检查全量覆盖、节点不重叠、尺寸不再进入主图、关系无增删和布局稳定。运行知识工具及Python测试仍无需Node。

如需打开原 PDF 或查看从原件生成的图片，请按[来源与资源登记](docs/sources.md)准备本地资料，再执行[融合检查复现命令](docs/fusion.md#本地复现)。从 GitHub 获取的版本包含索引和生成脚本，原件与缓存由组内渠道另行准备。

## 开发交接

小组按[软件计划设计书](docs/software-plan.md)串行接力。接手后记录收到的提交号，按[交接记录](docs/handover.md)复现当前批次，完成后同步更新[数据规范](docs/data-model.md)、[覆盖与待核问题](docs/coverage.md)和[进度记录](docs/progress.md)。
