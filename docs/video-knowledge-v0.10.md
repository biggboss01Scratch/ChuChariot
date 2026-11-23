# v0.10：现代复原视频知识

2026-11-23。按用户确认的原则：合理推测可以入库；记录来源、推理性质与适用范围，不以“百分之百确定”为入库前提。`review_status`记录项目审核进度，审核通过不会抹掉推测性质。

## 数据及增量

当前数据为[knowledge.v0.10.json](../data/candidates/knowledge.v0.10.json)，沿用本体0.6.0，契约升为0.3.0，支持视频定位与来源标注。队友v0.9所有记录完整保留，原文件未改。

新增1个视频来源、6条证据、6个案例、17条事实。其中6条是案例描述，11条是涉及构件的关联，不是17条独立的新历史结论。当前126实体、412条待复核事实、229条实体关系、54项尺寸、68段证据、5个来源、7组原有模型映射。

| 记录ID后缀（前缀`record:video1-`） | 定位 | 内容 | 描述的性质 |
| --- | --- | --- | --- |
| wheel-assembly | 26:04—26:52 | 辐条、轮辋对位与敲合 | 现代复原实验记录 |
| tenon-explanation | 25:28—26:46 | 长短榫有助于分批装配 | 现代复原推测；hypothesis |
| curved-frame | 31:54—32:45 | 天然弯曲木材加工框角 | 现代复原实验记录 |
| body-assembly | 32:49—33:08 | 车辀、车舆框架装配及相对轴位 | 现代复原实验记录 |
| woven-floor | 34:51—35:10 | 片中藤条编织车底方案 | 现代复原实验记录；材料名来自字幕 |
| hub-reinforcement | 35:48关键帧 | 复原者解释毂端铜件防止开裂 | 现代复原推测；inferred |

“实验记录”表示片中实际展示了现代制作或装配，不表示做过完整科学控制实验，也不表示古代原件必然采用同一方案。最后一项保存35:48—35:49关键帧窗口，不声称完整讲解只持续一秒。

原视频为用户提供的《战车视频1.mp4》，约53分32秒，1280×720，只有视频轨，无音轨，中英字幕烧录在画面里。本轮重点抽帧核对，未逐帧审阅整片。正式节目题名、制作信息、各标本归属未独立核实。来源中登记原件SHA256，文件名不是已核实的出版题名。

新描述挂在`ReferenceRecord`案例上，以`REFERS_TO_TYPE`关联现有构件。没有把藤条直接写为通用舆底或六号车的材料。长短榫解释保留“I think”的推测含义；英文hub对应毂，字幕误译为“轮轴”处在说明中指出。

## 字段与消费约定

- 视频来源：`format=mp4`、`source_type=modern_reconstruction_video`、`content_sha256`、`duration_seconds`。文件名相对于显式指定的资源目录，无本机绝对路径。
- 视频证据：`start_seconds`、`end_seconds`，满足`0 <= start < end <= duration`；不使用`pdf_page`。`transcription=video_frame`表示人工画面观察，`video_subtitle`表示人工核对烧录字幕。`quote`明确说明观察或字幕，`locator`保留重点帧，`scope_note`保留解释范围。
- 新事实的`knowledge_basis=modern_reconstruction_observation`显示“现代复原实验记录”；`modern_reconstruction_inference`显示“现代复原推测”，后者须保留`origin=inferred/hypothesis`及`rationale`，不能标为`documented`。
- `documented`表示来源里观察或记载了什么；`confirmed`表示项目审核接受该记录。二者都不是绝对历史真实性认证，审核不会改变推测性质。
- 旧PDF继续用页码。前端和AI问答不能假定所有证据都有`pdf_page`。回答应保留案例及时间，例如：“片中复原者推测长短榫有助于装配（25:28—26:46）。”

## 接入与复现

```powershell
python -m chuchariot --dataset data/candidates/knowledge.v0.10.json --ontology data/ontology/ontology.v0.6.json validate
python -m chuchariot --dataset data/candidates/knowledge.v0.10.json --ontology data/ontology/ontology.v0.6.json detail record:video1-tenon-explanation --include-pending
python -m chuchariot --dataset data/candidates/knowledge.v0.10.json --ontology data/ontology/ontology.v0.6.json evidence record:video1-tenon-explanation --include-pending
python -m chuchariot --dataset data/candidates/knowledge.v0.10.json --ontology data/ontology/ontology.v0.6.json preview --port 8770 --media-manifest data/sources/fusion-media.v0.10.json --resource-dir ..
```

在检查页搜索“长短榫”或“编织车底”，查看案例描述、来源性质与时间段。资源目录有原视频时可打开对应时间，服务支持HTTP Range定位读取；队友没有视频时仍可读取知识、字幕摘录和时间位置，原件另外准备。

回放`python -m scripts.add_video_knowledge_v010`，可选`--video 原视频路径`核对原件SHA256。回放无需原件，不执行自动字幕推断。媒体清单v0.10继承原PDF图块及模型图，视频通过来源链接打开。

验证：88项Python测试、9项Node测试通过。覆盖原包不变、时间越界、错误页码、来源字段、推测标签、审核不抹除推测、导入幂等、查询、页面显示和HTTP分段读取。没有新增三维映射或完整装配工序，没有覆盖未核实的伏兔支承位置；原视频未加入仓库。
