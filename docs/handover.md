# 最新交接记录

更新：2026-11-19。当前工作包：P1 知识层与临时检查页；状态：CLI 和只读页面可运行，内容待复核，整个 P1 尚未完成。

最新一批完成知识层职责拆分、车轮与车轴专题提取、一次拾遗和独立预审。候选包在 `data/candidates/wheel-axle.v0.2.json`。旧样例仍用于默认命令和兼容验证。

装配方向另补 `docs/assembly-sources.md` 与 `data/sources/assembly-catalogue.json`：6项来源、1条待追查线索。样章PDF第9页已渲染检查，可作商车轴端固定局部先后的候选依据；尚未取得九连墩六号车完整工序，不要自行写入正式装配步骤。

## 1. 工作权与基线

- 由项目发起者在本主会话开始知识层实现；尚未向另一名组员转移工作权，也未发生接收验收。
- 本轮开始时分支 `master`、无提交，P0 文档为未跟踪状态。本轮保留并更新这些文档，未自动提交/推送。
- 数据契约、本体、Python 包版本均为 `0.1.0`；增加临时检查 HTTP 接口，正式 API 契约尚未固定。
- 接手者实际同步后执行 `git rev-parse HEAD` 记录收到的提交号；无首次提交时如实记录“尚无提交”。

## 2. 本轮交付与关键文件

| 内容 | 入口 |
|---|---|
| 运行说明 | `README.md` |
| JSON 读写、校验、查询、导入 | `chuchariot/dataset_io.py`、`validation.py`、`queries.py`、`importer.py` |
| 资源/GLB检查、映射索引检查 | `chuchariot/resources.py` |
| CLI | `python -m chuchariot --help` |
| 本地检查页 | `chuchariot/preview.py`、`frontend/inspector/` |
| 本体 | `data/ontology/ontology.v0.1.json` |
| 候选包 | `data/candidates/wheel-axle.v0.2.json`，旧样例为 `wheel-axle.v0.1.json` |
| 资源规格/本轮快照 | `data/sources/` |
| 模型元数据报告 | `data/scenes/model-inspection.json` |
| 首轮、拾遗、预审与执行器契约 | `data/run-summaries/`、`data/pipeline/` |
| 必要检查 | `tests/test_knowledge.py` |

第二批共有 15 个实体、19 条候选事实、14 段证据、4 份证据 PDF 和 7 组候选映射。全部待正式审核。独立预审支持 16 条表述，3 条图示组成关系的适用范围待复核。

## 3. 阅读和复现

阅读顺序：README → 本文件 → data-model → sources/coverage → architecture/pipeline → 软件计划和 decisions。

在仓库根目录使用 Python 3.11+，本轮实际为 Windows / Python 3.12.4；不需安装第三方库、启动数据库或配置 AI。

```powershell
python -m chuchariot validate --model-report data/scenes/model-inspection.json
python -m chuchariot detail measurement:001
python -m chuchariot evidence measurement:001 --include-pending
python -m chuchariot relations type:001 --include-pending
python -X utf8 -m unittest discover -s tests -v
```

预期：校验统计 14/9/9；默认尺寸详情隐藏数值；审核证据可回溯到 PDF 第 6 页的 CH1：5 对照标本；测试通过。CLI 执行即退出，不存在服务停止步骤。

当前候选的 `source_checked` 是本轮 Agent 查看页面后的对应检查，**不是组员审核**。默认查询没有事实是预期行为，不是数据加载失败。

知识层原26项检查通过；新增检查服务后共31项测试通过。浏览器已检查搜索、节点选择、尺寸、证据、原PDF、审核切换、筛选、缩放及桌面/手机布局，未发现页面错误或横向溢出。最终结果见 progress；组员接手复现尚未执行，三维渲染/拾取/动画、Neo4j 和 AI 仍未验证。

## 临时页面启动/停止

```powershell
python -m chuchariot preview --port 8765 --resource-dir ..
```

访问 `http://127.0.0.1:8765/`，按 `Ctrl+C` 停止；换端口用 `--port`。不需安装前端依赖。省略资源目录仍可看数据，但原PDF链接不可用。页面默认候选检查并醒目标记状态；切换已确认视图将隐藏候选。

当前会话为用户查看而保留的预览进程不保证在关闭 Codex/终端后继续运行；接手时按上面的命令自行启动，不依赖旧进程。该页只读，不能替代内容审核或正式三维前端。

## 4. 资源与重跑

原始8个文件仍在仓库父目录，未上传。克隆者通过组内授权渠道取得资料，文件名见 sources；不把本轮快照当作本机已存在的证明。普通查询和测试不依赖原件。

```powershell
python -m chuchariot inventory --resource-dir .. --output data/sources/resources.json --model-report data/scenes/model-inspection.json
python -m chuchariot import --input data/candidates/wheel-axle.v0.1.json --output data/local/knowledge.json
```

`data/local/`、`tmp/`、`data/runs/` 为本地派生产物，不默认入仓。重跑导入不重复记录；冲突不会静默覆盖。模型变化不能沿用旧哈希与映射。

## 5. 下一项任务：内容复核

重构后的模块依赖和剩余扩展工作见 [架构文档](architecture.md)。临时前端仍使用样例布局。当前 Git 尚无首个提交，交接提交基线待建立。

下一位先查看 [独立预审记录](../data/run-summaries/2026-11-19-wheel-axle-review.json)。正式确认应优先核对 3 条图示关系的范围，再追查 CH1：3、CH1：5、M1：201-1 的原始报告归属。启动第二批检查页和导入快照的命令见 [README](../README.md) 与 [知识构建流程](pipeline.md)。

已对下载的7项资料完成[任务相关性核查](source-relevance.md)，机器映射见 `data/sources/source-relevance.json`。优先精读/抽取刘永华样章PDF第8—9页（商车连接比较）和张万辉论文PDF第3—6页（轮辋制造）；邵朋飞论文PDF第5—6页用于检验与功能专题。国博为系驾原论文线索，北大为复原方法案例，湖北省博物馆为九连墩背景，故宫为比较器物。它们均未提供六号车部件级直接证据。不要把工艺类比、检验分类、项目成果介绍写成目标车完整安装次序；本轮未新增或确认事实。

先查看补充资料清单及[下载索引](downloads.md)。本地已有张万辉轮辋论文7页、邵朋飞工匠精神/制轮论文9页及刘永华公开样章9页，另有4篇机构网页正文副本；完整性、哈希和检查页见 `data/sources/download-manifest.json`。新论文仅完成文件与首末页核对，尚未逐事实审核。邵朋飞论文PDF题名与期刊HTML不同，已保留两者。优先通过学校/老师获取《九连墩楚墓》（ISBN 9787501085583）的车马坑章节；正文仍未取得，CH1归属问题仍未解决。陕西木轮车调查PDF及吴晓筠论文均未成功下载。

1. 打开 sources 指定 PDF 第 4—6 页，复核四段证据和9条候选；核对组成关系的一般化边界。
2. 追查 CH1：3/CH1：5 的原始报告及归属；不要把它们的尺寸分配给主展品。
3. 确认主展品范围，建立第一批正式 `reviewed` 知识；逐条记录审核者、日期和备注，保留冲突。
4. 补局部连接知识或明确资料缺口；随后再核模型实际几何对应。
5. 重跑检查，更新覆盖、数据规范和交接，满足 P1 交付条件后交给 P2 后端开发者。

## 6. 仍待定的范围

截止时间、人数与后续负责人、R06—R09 动画深度、最终 Neo4j 要求、断网/部署、资料共享、报告分工。它们不阻止当前候选复核，但需要按软件计划的节点确定。

本轮没有对外 AI 调用、网络发布、远程仓库创建或推送。Gleaning 只有契约与明确的跳过记录，不能宣称真实补抽已实现。

资料搜集阶段访问了公开机构/期刊/出版社网页，已保存2份完整论文、1份公开样章和4篇网页正文作本地阅读；网页图片/视频未离线打包。未向外部上传老师提供的原始资料。本地阅读缓存目录已忽略，组员通过记录的原站入口自行获取，不默认将下载文件随Git再发布。

后续每轮记录：交出者/接手者、日期、基线提交、数据/API版本、变更、环境、检查命令与真实结果、未完成项、第一项任务、接收复现及工作权转移状态。
