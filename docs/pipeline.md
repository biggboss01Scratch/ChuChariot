# 知识构建与重跑

2026-11-23第七批：执行 `python -X utf8 -m scripts.apply_source_audit_v07`，按已记录的272条原页判定回放修正，生成候选v0.7、本体0.5、媒体v0.7、审计报告和运行摘要。脚本检查第六批输入哈希、原事实快照及本地原件哈希；它不是自动内容审核器，不自动确认事实。审计记录由同一Codex会话作出，仍需组员复核。前置尺寸迁移仍使用 `scripts.migrate_dimensions_v06`；各旧批次保留。查看[逐条审计](audits/2026-11-23-source-audit.md)。

2026-11-23补充：第五批用 `python -X utf8 -m scripts.extract_teacher_pdf_v05` 从已对照原页的转录输入确定性构建候选包、本体和摘要。此脚本不执行OCR，不自动判断历史真伪。本轮未做独立Agent预审，全部新增事实仍待组员复核。详见[逐页记录及命令](extraction-2026-11-23.md)。以下保留既有管线和历史运行说明。

更新：2026-11-19。当前实现资源登记、候选格式、校验、查询和幂等导入。第二、三批已执行来源页提取、Codex 子 Agent 拾遗与独立预审，结果保存在可查询的 JSON 候选包中。

## 1. 环境和来源

核心工具使用 Python 3.11+ 标准库，本轮在 Python 3.12.4 验证，无安装依赖。资源登记见 README 和 sources。原始资源通过参数定位，查询和测试不要求原件在场。

本轮辅助阅读使用了 Codex 打包的 PDF 工具和 Python `pypdf`，它们不是项目运行依赖。图片文字未被文本层抽取覆盖；已在本地渲染并查看 PDF 第 4—6 页。临时文本和 PNG 位于被忽略的 `tmp/inspection/`，不是入仓的来源替代品。

有 Poppler 的组员可以用以下方式重新生成这几页的阅读图像；先创建临时目录，将输入路径换成自己的资料位置：

```powershell
New-Item -ItemType Directory -Force tmp/inspection
pdftoppm -f 4 -l 6 -scale-to 1800 -png "../obP5c-1787891799145-马车复原及示意图及相关器具尺寸数据6.28.-刘逸鑫.pdf" tmp/inspection/report
```

渲染不修改原文件。Poppler 未安装时可直接用本机 PDF 阅读器按 PDF 页号查看，不影响核心校验工具运行。

## 2. 人工候选整理

参考 `data/candidates/wheel-axle.v0.1.json`：先登记来源和证据，再建实体及事实；每条记载附证据 ID，资料不足或归属不明时只记问题，不补造数值。保留待审核、冲突、推导和假设。

候选格式目前为引用闭合的完整包；增加新事实时保留它引用的实体、来源、证据等记录。禁止把主展品、一般类别和对照标本合并为一个对象。

## 3. 校验、查询和导入

```powershell
python -m chuchariot validate --model-report data/scenes/model-inspection.json
python -m chuchariot evidence measurement:001 --include-pending
python -m chuchariot relations type:001 --include-pending
python -m chuchariot import --input data/candidates/wheel-axle.v0.1.json --output data/local/knowledge.json
python -m chuchariot --dataset data/local/knowledge.json validate
python -X utf8 -m unittest discover -s tests -v
```

`validate` 默认读仓库中的候选包。额外模型报告只检查绑定哈希和节点范围，不渲染也不确认语义。原始 PDF 是否存在与文字是否准确仍需要单独核对。

同一个包重复导入后，输出字节保持一致。遇到同 ID 不同内容，整次拒绝，不改目标；需要负责人整理冲突后显式更新源数据。输出不能与输入为同一文件。`data/local/knowledge.json` 是派生产物，不是另一个编辑入口。

## 4. 审核与正式知识

第三批的 28 条事实均为 `pending`，含旧版 19 条和 9 条经新增预审的候选。第二批独立预审支持 16 条表述，另外 3 条图示组成关系仍需复核适用范围。正式审核时逐条填写 `review` 和状态，争议保留为 `disputed`，并检查正式包的引用闭合。

默认查询只显示已确认事实；审核视图显式开启待审核和争议内容。事实被确认不代表推导/假设变成原始记载，也不表示模型几何获得核验。

## 5. AI 抽取和 Gleaning 边界

当前采用[拾遗契约 v0.2](../data/pipeline/gleaning-contract.v0.2.json)。它适用于本地逐段复查，自动执行器仍待实现。输入为原片段、来源定位、本体、首轮结果和已有实体。

逐句核查实体、可独立验证的属性和关系，分辨具体标本、类别与修饰对象。优先复用标本、材质或术语，同一句中已写进 `DESCRIPTION` 的内容也要检查能否结构化。记录每段的新增、已有、待核和范围缺口，以覆盖结果和溯源判断完成度。新增带上证据及限定条件并保持待审核。

例如，马具组的原文提到某件马镳及骨帽上的黑漆勾连云纹。按「组包含残件」「残件有髹饰」「残件有纹饰」分别赋予关系，效果可以从「黑漆」反查车辀和马镳，并回到各自不同的原文页。见[第四批拾遗记录](../data/run-summaries/2026-11-20-structured-gleaning.json)。

额外补抽默认最多一轮；无新增有效记录停止。歧义与冲突不得静默覆盖；调用失败保留首轮结果。真实处理原始资料前确认授权，密钥仅通过环境配置，不进入日志。

`2026-11-19-local01.json` 是初版跳过记录。第二批的首轮、拾遗与预审分别保存在 [首轮](../data/run-summaries/2026-11-19-wheel-axle-first-pass.json)、[拾遗](../data/run-summaries/2026-11-19-wheel-axle-gleaning.json)、[预审](../data/run-summaries/2026-11-19-wheel-axle-review.json)。实际执行了一轮子 Agent 拾遗，随后由另一个子 Agent 对照原页预审。以上是一次 Codex 会话内执行记录，自动执行器仍为接口约定。

第二批使用同一批固定来源页。教师资料汇编第 4—6 页用于复核旧记录及补充保存状态与对照器物，刘永华样章第 8—9 页、张万辉论文第 5—6 页、邵朋飞论文第 5—6 页用于术语、功能和研究解释。所有新增断言附来源和定位，其中作者的观点保留归因。

第三批开展了扩展页拾遗，新增 5 条文献候选和 4 条媒体索引候选，随后对照原页独立预审。详见[第三批摘要](../data/run-summaries/2026-11-19-fusion-gleaning.json)。

在仓库根目录可导入第四批并反查拾遗结果。不同阶段的派生快照保留各自路径。

```powershell
python -m chuchariot --ontology data/ontology/ontology.v0.2.json import --input data/candidates/wheel-axle.v0.4.json --output data/local/wheel-axle-structured.v0.4.json
python -m chuchariot --ontology data/ontology/ontology.v0.2.json --dataset data/local/wheel-axle-structured.v0.4.json validate --model-report data/scenes/model-inspection.json
python -m chuchariot --ontology data/ontology/ontology.v0.2.json --dataset data/local/wheel-axle-structured.v0.4.json relations finish:002 --include-pending
```

## 6. 批次记录与交接

完整机器可读运行记录放 `data/runs/`（本地、默认忽略）；脱敏后需共享的摘要放 `data/run-summaries/`。记录 run_id、片段/证据、模型与提示词/本体版本、轮次、新增/拒绝/冲突、失败信息和可获得的用量耗时。不可获得的值使用空值，不填虚构数字。

每次更新源包后重跑校验与必要测试；更新 data-model、覆盖问题、progress 和 handover。当前 CLI 不会自动生成每次查询/导入的批次日志，重要离线操作由开发者记录摘要；未来自动化时另补实现。
