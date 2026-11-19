# 楚国战车专题交互导览系统

面向博物馆专题介绍场景，以知识图谱组织有来源的知识，结合三维模型和专题讲解展示楚国战车。AI 问答作为加分项。

## 当前状态

2026-11-19：已开始 P1，知识层初版可通过命令行运行，使用 Python 标准库，不需要 AI 密钥或数据库。

第二批有 15 个实体、19 条候选事实、14 段证据和 7 组候选模型映射。新增的 10 条由首轮提取和一次拾遗产生，全部候选仍为 `pending`。独立预审的逐条结论见 [预审记录](data/run-summaries/2026-11-19-wheel-axle-review.json)。命令行默认读取初版样例，使用 `--dataset` 可选择第二批，使用 `--include-pending` 可查看候选事实。正式业务 API、三维运行时和 Neo4j 尚未接入。

补充资料已保存到本地：**3份PDF（含1份出版社样章）和4篇机构网页正文**，从[资料下载索引](docs/downloads.md)直接打开。下载缓存被Git忽略，下载记录与原站链接随项目文档维护。

已完成这7项资料的[任务相关性核查](docs/source-relevance.md)：优先使用结构连接和轮辋制造内容，区分九连墩背景、比较实例与目标车直接证据。

## 打开临时知识检查页

在仓库根目录执行：

```powershell
python -m chuchariot --dataset data/candidates/wheel-axle.v0.2.json preview --port 8766 --resource-dir .. --resource-dir assets/references/local
```

然后访问 [本地检查页](http://127.0.0.1:8766/)。前台运行时按 `Ctrl+C` 停止。端口占用时可换一个端口并访问对应地址。证据原文分别从教师资料目录和本地下载目录读取。

- 左侧按名称、别名或 ID 搜索，按实体类型筛选。
- 中间点击图谱节点、拖动或缩放，支持只看当前对象的关联。
- 右侧查看事实、资料页码、原文和模型节点索引；配置资源目录后可打开已登记的原 PDF。
- 页面默认明确标记为“候选检查”；切换“已确认知识”会隐藏候选关系、证据和尺寸。当前确认事实为 0，因此为空是预期结果。
- 这是只读检查工具，不会修改候选、提交审核或播放三维模型。点击“重新加载”会从文件重新校验和读取。

`--resource-dir` 可省略，此时知识检查正常，原 PDF 链接不可用。若资料不在父目录，请换成实际资源目录。服务只提供检查页和已登记 PDF，不开放仓库/父目录文件列表。

## 快速运行

在仓库根目录使用 Python 3.11+；本轮实际验证环境为 Windows、Python 3.12.4。无需 `pip install`，不要求使用 Codex 的专用运行环境。

```powershell
python -m chuchariot validate
python -m chuchariot list --q 轮毂
python -m chuchariot detail measurement:001
python -m chuchariot detail measurement:001 --include-pending
python -m chuchariot relations type:001 --include-pending
python -m chuchariot evidence measurement:001 --include-pending
python -m chuchariot mappings type:001 --include-pending
python -X utf8 -m unittest discover -s tests -v
```

不传 `--dataset` 时，`validate` 检查初版的 14 个实体、9 条待审核事实。第二批的校验、证据查询和导入命令见 [知识构建流程](docs/pipeline.md)。

CLI 命令执行后立即退出，无需停止服务。失败返回退出码 1 和 JSON 错误；成功返回退出码 0。全局 `--dataset`、`--ontology` 参数放在子命令前。

### 重复导入候选包

```powershell
python -m chuchariot import --input data/candidates/wheel-axle.v0.1.json --output data/local/knowledge.json
python -m chuchariot import --input data/candidates/wheel-axle.v0.1.json --output data/local/knowledge.json
python -m chuchariot --dataset data/local/knowledge.json validate
```

同 ID 同内容不会增加重复记录；同 ID 不同内容报错并保持目标不变，不会静默覆盖或自动确认事实。`data/local/` 是被忽略的派生目录。

## 组员阅读入口

1. [软件计划设计书](docs/software-plan.md)：项目定位、架构、范围、阶段交付与验收。
2. [最新交接记录](docs/handover.md)：接手状态和下一项任务。
3. [决策记录](docs/decisions.md)：区分已确认方向、实施建议和待定事项。
4. [进度记录](docs/progress.md)：实际改动及执行过的检查。
5. [原始构建说明](docs/AGENT_BUILD_BRIEF.md)：保留原始要求，不能把计划写成已完成。
6. [数据规范](docs/data-model.md)、[构建管线](docs/pipeline.md)、[来源说明](docs/sources.md)：P1 实际数据与命令。
7. [实际架构](docs/architecture.md)、[覆盖与问题](docs/coverage.md)、[接口状态](docs/api.md)。
8. [补充研究资料清单](docs/research-sources.md)：10项主要来源、4条追查线索、阅读状态与适用范围；不是已导入的事实。
9. [装配与制作资料专题](docs/assembly-sources.md)：复原项目、制车工艺和局部连接依据；未核实到主展品完整装配手册。

## 开发方式

采用串行接力，每次一名开发者修改共享开发线。接手先复现前一阶段检查；交出前同步代码、数据、规范、进度和交接记录。具体流程见设计书第 8 节。

当前仍在知识层第一阶段：来源登记、格式和工具已建立，下一步是组员复核候选及追查原报告，再形成首批正式知识。尚未达到整个 P1 的交接完成条件。

## 环境、资源与运行

- 核心代码为 `chuchariot/`；当前没有第三方运行依赖。后端框架版本在 P2 实际接入时记录。
- 命令行查询和测试只依赖入仓的小样例，不需要原始 PDF/GLB。重新检查来源和模型时需要另外准备资源。
- 资源清单为 `data/sources/resources.json`，准备方式见来源说明；原文件目前在父目录，未复制或上传。
- 已有 HTML 仅静态查看、GLB 仅元数据检查；不能据此声称网站或动画已通过交互测试。
- 当前是 JSON/内存读取适配，未建立图数据库或 AI 服务连接。最终 Neo4j 要求待组内确认。
- 不要上传密钥、真实 `.env`、本地数据库和未确认可共享的资料。运行资源是否入 Git、LFS 或外部准备另行记录。

## 重新检查资源

把来源说明中的 8 个文件放在同一个资源目录，将 `..` 换成该目录。资源命令只读原件，输出文件由参数指定。

```powershell
python -m chuchariot inventory --resource-dir .. --output data/sources/resources.json --model-report data/scenes/model-inspection.json
python -m chuchariot validate --model-report data/scenes/model-inspection.json
```

缺失资源会标为 `missing`。模型内容哈希变化或节点索引越界时，映射检查失败；检查通过也不代表几何语义正确。

## Git 与常见问题

在仓库根目录查看改动：

```powershell
git status --short --branch
git diff --check
```

- `No module named chuchariot`：先进入包含本 README 的仓库根目录。
- 查询没有事实：当前事实均待审核，正常默认视图为空；复核时显式添加 `--include-pending`。
- 无原始资料：可运行 CLI 和测试，但不能重新核对图片证据或播放模型；不能把已有资源快照当作本机文件存在证明。
- `git diff --check` 不检查未跟踪文件，提交前还要审查新增文件。本文档和代码尚未由 Agent 自动提交或推送。
