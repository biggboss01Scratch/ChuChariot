# 尺寸属性迁移与建模检查

2026-11-23 · Codex第二主会话。本轮按用户要求调整数据表达，并提出其他实际建模问题；不是新一轮考古内容确认。

## 已完成的尺寸调整

| 项目 | 第五批 | 第六批 |
|---|---:|---:|
| 实体 | 149（含54个尺寸节点） | 95 |
| 实体之间的关系 | 163 | 109 |
| 尺寸属性 | 通过54个节点表达 | 54条结构化属性事实 |
| 全部事实 | 272 | 272 |
| 证据片段 / 模型映射 | 52 / 7 | 52 / 7 |

尺寸不是删除或仅在页面隐藏，而是从 `Measurement` 实体及 `HAS_MEASUREMENT` 边，迁移为所属主体的 `HAS_DIMENSION` 属性事实。事实ID、主体、数值、单位、原始表达、近似、范围、证据、依据性质、抽取记录和审核状态全部保留。主图和目录不再把尺寸当成独立对象；点选实体仍显示其全部尺寸及证据入口。

例如轮毂的通长、贤端径、壶中径、轵端径分别保留，轮标本的横径与竖径不合并；残长不改通长。同主体同项目的多个来源值允许并存，不按项目名称覆盖。一般部件类别不能直接接收具体器物的尺寸。

```json
{
  "id": "fact:pdf-147",
  "subject_id": "component:ch15-hub",
  "predicate": "HAS_DIMENSION",
  "value": {
    "quantity": "通长",
    "unit": "cm",
    "raw": "毂通长70、贤端径13.5、壶中径17、轵端径6厘米",
    "approximate": false,
    "value": 70
  },
  "evidence_ids": ["evidence:pdf-p06-t01"],
  "origin": "documented",
  "review_status": "pending",
  "extraction": {
    "method": "checked_pdf_atomic_extraction",
    "run_id": "run:20261123-teacher-pdf"
  }
}
```

第六批采用数据契约0.2.0、本体0.4.0。旧契约和旧候选包继续可读。逐项迁移索引及旧包哈希见[迁移摘要](../data/run-summaries/2026-11-23-dimension-properties.json)。所有事实仍待审核，迁移和测试不能证明历史真实性。

## 另外需要处理的建模问题

### 1. 描述区域与实物部件混用

`component:m1302-front`、`component:m1302-middle`、`component:m1302-rear` 是为限定红黑漆作用部位而建的辀身前、中、后段记录。备注已经说明不是可拆零件，但类型仍是 `Component`，关系仍为 `HAS_PART`。前端显示为“具体部件”，后续若直接拿它生成爆炸图或装配流程，会产生错误理解。

建议引入“描述区域”的类型和区域关系，或在髹饰事实中明确作用部位。区域不自动获得三维可拆零件身份。此次保留原记录与限定备注，未擅自重分全部组成关系。

### 2. 数量和重量仍是字符串

`HAS_RECORDED_QUANTITY` 的“5根”“登记33件；现存22件”和 `HAS_MASS_RECORD` 的“220克”等仍是文字。这样保存原意方便，但不利于数值筛选、单位转换，也难区分登记数、现存数与器物组数量。

建议分别表达数值、单位、统计口径和所指对象，并保留原文。470克是否包含所配辖仍不明确，不能为了结构化而给出未经支持的重量范围或分拆值。本轮未用正则猜测并替换历史统计。

### 3. 通用知识的适用范围不够结构化

目前部分关于商车、《考工记》及其他时代案例的说明，挂在通用部件类别上，通过描述文字保留作者和语境；年代、车型与适用范围尚不能作为独立条件查询。后续讲解和问答若只取主语与结论，可能把特定研究解释泛化为所有楚国战车的属性。

建议为事实增加经过来源支持的适用范围和观点归因，并建设通用知识覆盖清单。不能由某件木轮标本推出所有车轮均木质，不能由示意图认定六号车的全部实物连接。

### 4. 默认启动仍指向初版样例

`chuchariot/dataset_io.py` 的默认数据、本体仍是v0.1，现用数据、本体、媒体通过启动命令分别指定。README明确说明了这个兼容约定，但队友直接运行默认命令仍容易看到旧样例，或者手动搭配错版本。

建议增加集中管理的“当前数据集”配置或启动入口，统一绑定数据、本体、媒体和场景版本；把旧样例作为显式演示选项。本轮8769已明确切换第六批，未静默改变旧命令和旧样例测试的默认行为。

## 复现和验证

```powershell
python -X utf8 -m scripts.migrate_dimensions_v06
python -X utf8 -m chuchariot --dataset data/candidates/teacher-pdf.v0.6.json --ontology data/ontology/ontology.v0.4.json validate --model-report data/scenes/model-inspection.json
python -X utf8 -m chuchariot --dataset data/candidates/teacher-pdf.v0.6.json --ontology data/ontology/ontology.v0.4.json detail component:ch15-hub --include-pending
python -X utf8 -m unittest discover -s tests -v
node --test tests/inspector-layout.test.cjs
```

58项Python测试和6项前端布局测试通过。新增测试核对迁移前后每条事实与原始数值、证据及审核元数据，数值/单位约束、多个来源值不覆盖、审核过滤、媒体追溯、重复导入及冲突保护。浏览器检查原页证据、候选与确认模式及95个实体的地图。当前8769预览已切换第六批；完整启动命令见README。
