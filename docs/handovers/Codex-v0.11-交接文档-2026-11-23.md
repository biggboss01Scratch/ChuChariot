# 知识库v0.11／本体v0.7交接 · 2026-11-23

从基线`aadfdf8`继续，当前知识数据为`knowledge.v0.11.json`，配`ontology.v0.7.json`及`fusion-media.v0.11.json`，数据格式为0.4.0。交付提交号以包含本文件的Git提交为准。

## 本次知识更新

- 在队友v0.9基础上纳入视频知识：车轮拼装、长短榫便于装配的推测、弯木框角、车舆框架装配、藤编车底和毂端加固解释。逐项保存视频时间段，区分现代复原记录与推测。
- 股、骹和毂上窄篆统一为部位或形态特征区域；保留原ID、全部54项尺寸、13道窄篆数量和两处榫卯关系。区域不再被表达成独立分件。
- 马勒作为规范讲解对象；旧`type:bridle`保留ID但改为来源语境词义，另存辔的缰绳义和合称义。教学导航统一到马勒，不把所有辔全局归为同一对象。
- 当前128实体、423条待复核事实、233条实体关系、54项尺寸、72段证据、7个来源、7组候选模型映射。新增条目包含来源、词义及关联说明，数量不等于新的考古实物结论数。
- 本体因类别与关系端点规范而升至0.7.0；格式0.4.0支持词义来源及词典条目定位。旧v0.9、v0.10及旧本体完整保留，不能用新本体直接校验旧包。

## 队友如何使用

拉取仓库后，在项目根目录运行（Python 3.11+）：

```powershell
python -m chuchariot --dataset data/candidates/knowledge.v0.11.json --ontology data/ontology/ontology.v0.7.json validate --model-report data/scenes/model-inspection.json
python -m chuchariot --dataset data/candidates/knowledge.v0.11.json --ontology data/ontology/ontology.v0.7.json preview --port 8770 --media-manifest data/sources/fusion-media.v0.11.json --resource-dir .. --resource-dir data/sources/terminology
```

打开`http://127.0.0.1:8770/`，可搜索“股”“篆”“辔”“马勒”“长短榫”。原PDF和视频需要组内另行准备；仓库包含知识、证据摘录、定位、辞书摘录及复现代码，没有上传原视频和本机截图缓存。缺少原件时仍可读取知识与时间／页码，辞书可通过官方URL查看。

下游应按证据来源格式显示PDF页、视频时间段或词典义项；不能假设所有证据都有`pdf_page`。构件区域使用`HAS_REGION`，词义使用`USES_TERM`、`TERM_DENOTES`和`TERM_RELATED_TO`；`type:bridle`已不是独立构件类别，旧系驾导航端点须改为`type:horse-bridle`。

完整说明：[v0.11规范与迁移](../normalization-v0.11.md)、[视频知识v0.10](../video-knowledge-v0.10.md)。修改前后每条记录见`data/run-summaries/2026-11-23-normalization-v011.json`。

## 综合项目合并状态

**本次发布知识层、数据契约、检查页及交接资料，综合展厅和三维原型尚未完整合并接入新版知识。**此前本机8767展厅入口仍使用v0.9数据／v0.6本体，8770检查页使用本次新版；本机地址不是队友可直接访问的公网服务。

新区域及系驾部件的三维网格映射、完整双向联动、展厅接口适配和AI问答仍待后续实现。现有7组候选模型映射没有增加；图谱节点可查询不等于三维已可分别高亮。合理推测可以入库，保留来源、理由与适用范围；尚未替组员提升审核状态。

## 验证

98项Python与13项Node测试通过，覆盖历史快照兼容、尺寸及视频知识保留、区域与榫卯归属、词义分离、来源完整性、教学路径、幂等导入、媒体、页面属性和全图节点布局。

```powershell
python -X utf8 -m unittest discover -s tests -v
node --test tests/inspector-layout.test.cjs tests/inspector-video.test.cjs tests/inspector-normalization.test.cjs
```

当前仍有通用知识适用范围和研究观点表达方式待进一步统一；本次处理不等于全部史实已独立核验。
