# 项目文档索引

2026-11-20 · P1 知识层与本地临时检查原型，当前数据批次为 `wheel-axle.v0.4`。

第一次接手建议按顺序阅读 [README 与启动命令](../README.md)、[项目交接索引](handover.md)、[知识覆盖与待核事项](coverage.md)。需要了解最终交付范围时看[软件计划设计书](software-plan.md)的需求和验收表。

## 这一版交付到哪里

| 模块 | 当前结果 | 查阅入口 |
|---|---|---|
| 知识层 | JSON 数据与内存查询支持校验、查询、证据追溯和重复导入 | [实际架构](architecture.md) · [数据规范](data-model.md) |
| 候选知识 | 24 个实体、38 条 `pending` 事实、22 段证据、4 份登记的证据 PDF。图上 19 条关系，另有 19 条文字描述 | [最新候选包](../data/candidates/wheel-axle.v0.4.json) · [覆盖情况](coverage.md) |
| 临时检查页 | 本地只读开发工具。可搜索实体、点选图谱和检查证据，配置本地资源后可看原页、8 张资料截图及 7 组模型静态图 | [运行方式](../README.md#启动临时检查页) · [临时 HTTP 接口](api.md) |
| 多媒体与模型 | 截图关联 PDF 页和裁剪范围，静态图关联 GLB 版本、节点和实体。已检查七组局部几何，记录了拼装片段的缩放和行进片段的循环跳变问题 | [融合与模型核对](fusion.md) · [媒体关联清单](../data/sources/fusion-media.v0.1.json) · [GLB 元数据](../data/scenes/model-inspection.json) |
| 拾遗与预审 | 第二、三批有 Codex 会话中的拾遗及独立预审记录。项目内的自动执行器仍为契约，正式已确认事实为零 | [构建管线](pipeline.md) · [第二批预审](../data/run-summaries/2026-11-19-wheel-axle-review.json) · [第三批拾遗与复核](../data/run-summaries/2026-11-19-fusion-gleaning.json) |
| 验证 | 38 项自动测试通过。第四批实测材质及髹饰反查、证据页和审核过滤，融合页的桌面与移动检查见第三批验证 | [进度与验证记录](progress.md) |

待开发项包括生产 API、正式展陈前端、实时三维拾取与图谱联动、动画交互、专题导览、Neo4j 和 AI 问答。六号车的部件、尺寸和连接归属仍依赖原始报告核对。现有页面上的节点和图块是核对入口，模型位姿及动画演示的历史适用性另行审核。

## 按任务找资料

| 我想做什么 | 打开哪里 |
|---|---|
| 了解老师和小组的项目要求 | [原始构建说明](AGENT_BUILD_BRIEF.md) · [软件计划与验收](software-plan.md) · [决策记录](decisions.md) |
| 本地启动、交给下一位或准备 GitHub | [README](../README.md) · [项目交接索引](handover.md) · [项目进度](progress.md) |
| 写代码、扩字段或接后端 | [实际架构](architecture.md) · [数据规范](data-model.md) · [接口和 Python 调用](api.md) |
| 复核事实、补提取或导入候选 | [覆盖与待核问题](coverage.md) · [教师原件逐项核查](source-coverage-audit.md) · [构建管线](pipeline.md) · [拾遗契约 v0.2](../data/pipeline/gleaning-contract.v0.2.json) |
| 查截图、证据页和三维节点对应 | [融合检查](fusion.md) · [媒体清单](../data/sources/fusion-media.v0.1.json) |
| 找老师原件、已有 GLB 或旧展件 | [来源文件、用途和共享位置](sources.md) · [资源哈希清单](../data/sources/resources.json) |
| 找补充文献或查它能支持什么 | [研究资料清单](research-sources.md) · [装配与制作资料专题](assembly-sources.md) · [原站与本地保存索引](downloads.md) · [任务相关性核查](source-relevance.md) |

## 数据版本

| 数据批次 | 用法 |
|---|---|
| [v0.1](../data/candidates/wheel-axle.v0.1.json) | 默认 CLI 启动样例，14 个实体、9 条候选 |
| [v0.2](../data/candidates/wheel-axle.v0.2.json) | 第二批提取及预审，15 个实体、19 条候选 |
| [v0.3](../data/candidates/wheel-axle.v0.3.json) | 第三批融合候选，17 个实体、28 条候选 |
| [v0.4](../data/candidates/wheel-axle.v0.4.json) | 当前交接批次，24 个实体、38 条候选，新增材质、保存特征、髹饰、组成和纹饰边 |

JSON 字段契约为 `0.1.0`。第四批使用[本体 `0.2.0`](../data/ontology/ontology.v0.2.json)，前三批使用本体 `0.1.0`。
