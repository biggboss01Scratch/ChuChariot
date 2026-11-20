# 当前交接与 GitHub 准备

2026-11-20 · P1 知识层。第四批把已有描述拆成可查询的材质、组成、保存特征、髹饰和纹饰关系。完整导航见[项目文档索引](index.md)。

## 收到的版本

| 项目 | 当前情况 |
|---|---|
| Git | 本地开发分支为 `master`，基线为 `228591c`。`origin` 已指向 [GitHub 仓库](https://github.com/biggboss01Scratch/ChuChariot)，交付目标分支为 `main` |
| 候选批次 | `dataset:wheel-axle-004`，对应 [wheel-axle.v0.4.json](../data/candidates/wheel-axle.v0.4.json) 和 [ontology.v0.2.json](../data/ontology/ontology.v0.2.json) |
| 接力 | 项目发起者维护当前阶段，组员尚未完成接收复现。接手时用 `git rev-parse HEAD` 记录实际收到的提交号 |
| 环境 | Python 3.11+，核心查询、校验、预览及测试使用标准库。媒体重建另需 Pillow、NumPy 和 Poppler |

当前 24 个实体、38 条待审核事实、22 段证据、7 组候选映射、8 张原文图块和 7 组节点静态图。图块和静态图须从本地原件生成。临时页面用于开发、展示候选和核对来源。正式展陈、实时三维浏览、审核写入以及生产 API 属于后续阶段。

## 接手复现

在仓库根目录运行以下命令。第一条预期返回 24 个实体、38 条事实和 38 条待审核事实。两条命令均可在没有本地原件的情况下运行。

```powershell
python -m chuchariot --dataset data/candidates/wheel-axle.v0.4.json --ontology data/ontology/ontology.v0.2.json validate --model-report data/scenes/model-inspection.json
python -X utf8 -m unittest discover -s tests -v
```

运行结果与 38 项测试覆盖见[进度记录](progress.md)。检查页启动和停止方式见 [README](../README.md)。原 PDF、图块与 GLB 节点图的查看方式见[融合检查](fusion.md)。

## 准备提交到 GitHub

| 随仓库交接 | 在本地另行准备 |
|---|---|
| `chuchariot/`、`frontend/inspector/`、`tests/`、`scripts/`、`pyproject.toml` | 教师原始 DOCX、PDF、GLB、旧展件和其他原件，按[来源登记](sources.md)从组内渠道取得 |
| `data/ontology/`、`data/candidates/`、`data/scenes/`、`data/sources/`、`data/pipeline/`、`data/run-summaries/` | 公开文献与网页本地副本，下载地址和哈希见[资料索引](downloads.md) |
| `README.md`、`docs/`、`.gitignore` | `assets/references/local/` 提取图和静态渲染、`data/local/` 派生快照、`data/runs/` 临时记录及 `tmp/` 文件 |

提交前从 `ChuChariot/` 根目录检查 `git status --short --branch`，同时查看尚未跟踪的文件。暂存后用 `git diff --cached --stat` 和 `git diff --cached --check` 检查提交内容。GitHub 仓库主页读取 README，其他入口使用仓库相对链接。检查页地址是本机回环地址，访问时需要先运行 Python 服务。

## 接力任务

1. 查看[第二批逐条预审](../data/run-summaries/2026-11-19-wheel-axle-review.json)和[第三批拾遗与预审](../data/run-summaries/2026-11-19-fusion-gleaning.json)。先核对 3 条图示组成关系的适用范围。
2. 通过学校或老师查阅《九连墩楚墓》车马坑章节，ISBN 9787501085583。核实 CH1：3、CH1：5、M1：201-1 等标本归属，再决定哪些记录可对应六号车。
3. 为先行核实的候选记录审核人、日期、意见和冲突，形成第一批正式 `reviewed` 知识。更新[数据规范](data-model.md)和[覆盖情况](coverage.md)。
4. 根据证据推进部件定位与模型联动。当前 GLB 已做静态几何和动画轨道核查，已知问题见[模型核对](fusion.md#模型核对)。
5. 复现通过后再接实装后端与正式展陈，按[软件计划](software-plan.md)确认动画深度、数据库要求、部署和分工。

逐轮记录交出者、接手者、日期、基线、契约版本、环境、运行命令、验证结果及下一项任务。
