# 第六批272条事实的原页审计

2026-11-23 · 审计者：Codex。对象为审计记录锁定哈希的teacher-pdf.v0.6。

本轮是同一Codex会话对自己及旧批次整理结果的逐条原页复查，不是独立Agent、老师或组员复核。未提升任何事实为confirmed。

## 结论

| 判定 | 原第六批事实数 |
|---|---:|
| 来源支持 | 258 |
| 需修正 | 13 |
| 证据不足 | 1 |
| 有冲突 | 0 |

上述分类覆盖全部272条原事实。来源支持包含原文推断、图像观察与目录性说明，不能理解为独立考古结论的数量或准确率。54项尺寸逐项对照原页，数值、单位、范围、近似及所有者未发现不一致。276与272分别属于不同记录，不当作冲突。

修订候选v0.7：95个实体、270条待审核事实、107条实体关系、54项尺寸属性、52段证据和7组未审核模型映射。两条骨帽髹饰/纹饰重复边已合并，完整迁移关系和被合并记录保存在运行摘要；没有删除独立来源断言。

## 本轮修正与待核

| 原事实ID | 判定 | 问题与处理 |
|---|---|---|
| `fact:001` | 需修正 | 原页第5页展示的是一幅辐式车轮结构图。当前把图示的毂、辐、牙直接写成无范围的车轮类别组成，容易被解释成所有车轮的通用结论；旧批次预审也曾保留适用范围问题。 将关系收窄为已有轮轴图示记录DEPICTS对应部件类别，保留原事实ID和图像证据；通用结构待显式建适用范围。 |
| `fact:002` | 需修正 | 原页第5页展示的是一幅辐式车轮结构图。当前把图示的毂、辐、牙直接写成无范围的车轮类别组成，容易被解释成所有车轮的通用结论；旧批次预审也曾保留适用范围问题。 将关系收窄为已有轮轴图示记录DEPICTS对应部件类别，保留原事实ID和图像证据；通用结构待显式建适用范围。 |
| `fact:003` | 需修正 | 原页第5页展示的是一幅辐式车轮结构图。当前把图示的毂、辐、牙直接写成无范围的车轮类别组成，容易被解释成所有车轮的通用结论；旧批次预审也曾保留适用范围问题。 将关系收窄为已有轮轴图示记录DEPICTS对应部件类别，保留原事实ID和图像证据；通用结构待显式建适用范围。 |
| `fact:035` | 需修正 | 原页只明确骨帽绘勾连云纹，现有边挂在整件马镳上，需定位到骨帽，并与已存在fact:pdf-192合并。 移到component:m1257-bone-cap，合并同义重复事实。 |
| `fact:038` | 需修正 | 黑漆明确记在骨帽上，现有边作用部位过宽；骨帽已另有fact:pdf-191。 移到骨帽并合并重复，保留全部证据和旧ID迁移记录。 |
| `fact:pdf-074` | 需修正 | 原页支持辀身前中后段的局部漆饰，但这些段是描述区域。当前Component/HAS_PART表达容易被后续应用当作独立零件。 将三段改为ComponentRegion，组成边改HAS_REGION；保留红黑漆和后段纹饰事实。 |
| `fact:pdf-075` | 需修正 | 原页支持辀身前中后段的局部漆饰，但这些段是描述区域。当前Component/HAS_PART表达容易被后续应用当作独立零件。 将三段改为ComponentRegion，组成边改HAS_REGION；保留红黑漆和后段纹饰事实。 |
| `fact:pdf-076` | 需修正 | 原页支持辀身前中后段的局部漆饰，但这些段是描述区域。当前Component/HAS_PART表达容易被后续应用当作独立零件。 将三段改为ComponentRegion，组成边改HAS_REGION；保留红黑漆和后段纹饰事实。 |
| `fact:pdf-077` | 需修正 | 原页支持辀身前中后段的局部漆饰，但这些段是描述区域。当前Component/HAS_PART表达容易被后续应用当作独立零件。 将三段改为ComponentRegion，组成边改HAS_REGION；保留红黑漆和后段纹饰事实。 |
| `fact:pdf-078` | 需修正 | 原页支持辀身前中后段的局部漆饰，但这些段是描述区域。当前Component/HAS_PART表达容易被后续应用当作独立零件。 将三段改为ComponentRegion，组成边改HAS_REGION；保留红黑漆和后段纹饰事实。 |
| `fact:pdf-079` | 需修正 | 原页支持辀身前中后段的局部漆饰，但这些段是描述区域。当前Component/HAS_PART表达容易被后续应用当作独立零件。 将三段改为ComponentRegion，组成边改HAS_REGION；保留红黑漆和后段纹饰事实。 |
| `fact:pdf-080` | 需修正 | 原页支持辀身前中后段的局部漆饰，但这些段是描述区域。当前Component/HAS_PART表达容易被后续应用当作独立零件。 将三段改为ComponentRegion，组成边改HAS_REGION；保留红黑漆和后段纹饰事实。 |
| `fact:pdf-089` | 需修正 | 原页为“轴33件，现存22件”，未出现“登记”或说明33件统计口径；数值正确，但“登记33件”加了解释。 改为“原文记33件；现存22件（33件的统计口径未注明）”。 |
| `fact:pdf-217` | 证据不足 | 同页7号车图红字明确标注靷，8号车仅画类似红线，无独立靷标签；相似性不足以当作明文记载。 保留候选并标inferred，补同页对照依据及理由，待原始报告核实。 |

另外补全6段过短证据摘录的主体、标本号或图中标注，非连续摘录显式使用省略号。仅涉及来源表达完整性，不改变尺寸数值。

## 来源与检查范围

| 来源ID | 文件 | PDF页序 |
|---|---|---|
| `source:001` | obP5c-1787891799145-马车复原及示意图及相关器具尺寸数据6.28.-刘逸鑫.pdf | 1、2、3、4、5、6、7、8、9、10 |
| `source:002` | liu-2013-chariot-excerpt.pdf | 9 |
| `source:003` | shao-2022-wheel-craft.pdf | 5、6 |
| `source:004` | zhang-2022-wheel-rim.pdf | 5、6 |

教师汇编10页全部重新渲染，其中第10页空白；三份补充PDF检查的是8条既有事实涉及的5个PDF页，并非重新全文提取。四份文件内容哈希、页面复查备注、52段证据及逐条输入事实完整保存在[机器可读审计表](../../data/audits/2026-11-23-source-audit.json)。

[覆盖与缺口](2026-11-23-coverage.md) · [修订摘要与合并索引](../../data/run-summaries/2026-11-23-source-audit.json) · [修订候选v0.7](../../data/candidates/teacher-pdf.v0.7.json)

## 全部272条逐条判定

表中是修订前第六批的原断言及其审计结论；修订后数值、范围和审核元数据可通过摘要追溯。不是把当前270条重新编号为272条。

| 原事实ID | 原断言 | 出处与证据ID | 判定 | 核对说明 |
|---|---|---|---|---|
| `fact:001` | 车轮 — HAS_PART — 毂 | source:001 PDF第5页 / evidence:001 | 需修正 | 原页第5页展示的是一幅辐式车轮结构图。当前把图示的毂、辐、牙直接写成无范围的车轮类别组成，容易被解释成所有车轮的通用结论；旧批次预审也曾保留适用范围问题。 |
| `fact:002` | 车轮 — HAS_PART — 辐 | source:001 PDF第5页 / evidence:001 | 需修正 | 原页第5页展示的是一幅辐式车轮结构图。当前把图示的毂、辐、牙直接写成无范围的车轮类别组成，容易被解释成所有车轮的通用结论；旧批次预审也曾保留适用范围问题。 |
| `fact:003` | 车轮 — HAS_PART — 牙 | source:001 PDF第5页 / evidence:001 | 需修正 | 原页第5页展示的是一幅辐式车轮结构图。当前把图示的毂、辐、牙直接写成无范围的车轮类别组成，容易被解释成所有车轮的通用结论；旧批次预审也曾保留适用范围问题。 |
| `fact:004` | CH1：5轮标本 — INSTANCE_OF — 车轮 | source:001 PDF第6页 / evidence:002 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：5轮标本”归类为“车轮”；不据编号相近合并不同对象。 |
| `fact:005` | CH1：3轴标本 — INSTANCE_OF — 车轴 | source:001 PDF第4页 / evidence:003 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：3轴标本”归类为“车轴”；不据编号相近合并不同对象。 |
| `fact:006` | CH1：5轮标本 — HAS_DIMENSION — {"quantity": "右轮横径", "value": 132, "unit": "cm", "raw": "右轮横径132、竖径119厘米", "approximate": false} | source:001 PDF第6页 / evidence:002 | 来源支持 | 逐项对照原页：CH1：5轮标本的右轮横径为132cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:007` | CH1：5轮标本 — HAS_DIMENSION — {"quantity": "右轮竖径", "value": 119, "unit": "cm", "raw": "右轮横径132、竖径119厘米", "approximate": false} | source:001 PDF第6页 / evidence:002 | 来源支持 | 逐项对照原页：CH1：5轮标本的右轮竖径为119cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:008` | CH1：3轴标本 — HAS_DIMENSION — {"quantity": "通长", "value": 272, "unit": "cm", "raw": "轴通长272、粗径9.7、细径2.6厘米", "approximate": false} | source:001 PDF第4页 / evidence:003 | 来源支持 | 逐项对照原页：CH1：3轴标本的通长为272cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:009` | CH1：5轮标本 — DESCRIPTION — "资料记载该轮为木质，木质已腐烂，现仅存表面深褐色漆皮。" | source:001 PDF第6页 / evidence:004 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:010` | CH1：3轴标本 — DESCRIPTION — "汇编将 CH1：3 轴描述为木质，木质已腐朽，仅见表面深褐色漆皮。" | source:001 PDF第4页 / evidence:005 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:011` | 车轴 — DESCRIPTION — "刘永华在商车讨论中将车轴解释为承载车上重量的关键部件。" | source:002 PDF第9页 / evidence:006 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:012` | 軎 — DESCRIPTION — "刘永华在商车讨论中将车軎描述为轴端防止车毂脱落的部件。" | source:002 PDF第9页 / evidence:007 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:013` | 辐 — DESCRIPTION — "邵朋飞将辐解释为车轮中连接毂与轮圈的木质部件。" | source:003 PDF第5页 / evidence:008 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:014` | 车轮 — DESCRIPTION — "邵朋飞把车轮的正圆、平整与均衡分别作为《考工记》制轮质量的解释主题。" | source:003 PDF第5页 / evidence:009 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:015` | 牙 — DESCRIPTION — "张万辉将江苏淮安运河村出土的战国中晚期车辆列为先秦木质轮辋研究的实物案例。" | source:004 PDF第6页 / evidence:010 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:016` | M1：201-1 车軎 — DESCRIPTION — "教师汇编图二四〇将 M1：201-1 标为一号墓出土的铜双箍云纹圆筒形车軎。" | source:001 PDF第5页 / evidence:011 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:017` | 毂 — DESCRIPTION — "刘永华在商车讨论中将车毂两端分别称为贤端和轵端。" | source:002 PDF第9页 / evidence:012 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:018` | 车轮 — DESCRIPTION — "邵朋飞将《考工记》制轮语境中的“三材”解释为毂、辐、牙的用材。" | source:003 PDF第6页 / evidence:013 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:019` | 牙 — DESCRIPTION — "张万辉转述了考古研究者利用铜枒饰的对称分布推测西周车辆轮辋拼合情况的做法。" | source:004 PDF第5页 / evidence:014 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:020` | 九连墩一号车马坑6号车 — DESCRIPTION — "教师汇编把九连墩一号车马坑6号车作为复原的主要模板。" | source:001 PDF第1页 / evidence:015 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:021` | 九连墩一号车马坑6号车 — DESCRIPTION — "教师汇编收录一号车马坑6号车复原图，图三一七标出围栏局部。" | source:001 PDF第9页 / evidence:016 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:022` | M1：302 车辀残件 — DESCRIPTION — "汇编记载 M1：302 车辀出自南室第二层西部中间靠西壁处，残存前段。" | source:001 PDF第3页 / evidence:017 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:023` | M1：302 车辀残件 — DESCRIPTION — "汇编记载 M1：302 车辀考古记录中有红、黑两种漆饰。" | source:001 PDF第3页 / evidence:018 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:024` | M1：257 马具组 — DESCRIPTION — "汇编记载 M1：257 马具组留存一只漆骨帽马镳，骨帽有黑漆勾连云纹。" | source:001 PDF第7页 / evidence:019 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:025` | 车轴 — DESCRIPTION — "教师汇编的车轮示意图标出了车轴。" | source:001 PDF第5页 / evidence:020 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:026` | 辖 — DESCRIPTION — "教师汇编记载 M1：201-1 所配辖的顶端为兽面。" | source:001 PDF第5页 / evidence:021 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:027` | 车轮 — DESCRIPTION — "教师汇编第6页左上角有一幅辐式车轮的正面图。" | source:001 PDF第6页 / evidence:022 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:028` | M1：201-1 车軎 — INSTANCE_OF — 軎 | source:001 PDF第5页 / evidence:011 | 来源支持 | 原页标本名称、图注或正文用词支持“M1：201-1 车軎”归类为“軎”；不据编号相近合并不同对象。 |
| `fact:029` | CH1：5轮标本 — HAS_MATERIAL — 木材 | source:001 PDF第6页 / evidence:004 | 来源支持 | 原页对该对象或部位记有“木材”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:030` | CH1：3轴标本 — HAS_MATERIAL — 木材 | source:001 PDF第4页 / evidence:005 | 来源支持 | 原页对该对象或部位记有“木材”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:031` | M1：201-1 车軎 — HAS_MATERIAL — 铜 | source:001 PDF第5页 / evidence:011 | 来源支持 | 原页对该对象或部位记有“铜”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:032` | CH1：5轮标本 — HAS_PRESERVED_FEATURE — 残存深褐色漆皮 | source:001 PDF第6页 / evidence:004 | 来源支持 | 原页对该对象或部位记有“残存深褐色漆皮”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:033` | CH1：3轴标本 — HAS_PRESERVED_FEATURE — 残存深褐色漆皮 | source:001 PDF第4页 / evidence:005 | 来源支持 | 原页对该对象或部位记有“残存深褐色漆皮”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:034` | M1：257 马具组 — HAS_PART — M1：257 残存漆骨帽马镳 | source:001 PDF第7页 / evidence:019 | 来源支持 | 原页对应图示或正文明确支持“M1：257 马具组”与“M1：257 残存漆骨帽马镳”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:035` | M1：257 残存漆骨帽马镳 — HAS_DECORATION_MOTIF — 勾连云纹 | source:001 PDF第7页 / evidence:019 | 需修正 | 原页只明确骨帽绘勾连云纹，现有边挂在整件马镳上，需定位到骨帽，并与已存在fact:pdf-192合并。 |
| `fact:036` | M1：302 车辀残件 — HAS_SURFACE_FINISH — 红漆 | source:001 PDF第3页 / evidence:018 | 来源支持 | 原页对该对象或部位记有“红漆”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:037` | M1：302 车辀残件 — HAS_SURFACE_FINISH — 黑漆 | source:001 PDF第3页 / evidence:018 | 来源支持 | 原页对该对象或部位记有“黑漆”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:038` | M1：257 残存漆骨帽马镳 — HAS_SURFACE_FINISH — 黑漆 | source:001 PDF第7页 / evidence:019 | 需修正 | 黑漆明确记在骨帽上，现有边作用部位过宽；骨帽已另有fact:pdf-191。 |
| `fact:pdf-001` | 车茵 — DESCRIPTION — "原第9页标题列出“车茵”，该小节无展开内容。" | source:001 PDF第9页 / evidence:pdf-heading-p09-floor-mat | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:pdf-002` | 车蔽衣 — DESCRIPTION — "原第9页标题列出“车蔽衣”，该小节无展开内容。" | source:001 PDF第9页 / evidence:pdf-heading-p09-body-cover | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:pdf-003` | 伞 — DESCRIPTION — "原第9页标题列出“伞”，该小节无展开内容。" | source:001 PDF第9页 / evidence:pdf-heading-p09-umbrella | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:pdf-004` | 盖 — DESCRIPTION — "原第9页标题列出“盖”，该小节无展开内容。" | source:001 PDF第9页 / evidence:pdf-heading-p09-canopy | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:pdf-005` | CH1：3轭标本 — INSTANCE_OF — 轭 | source:001 PDF第1页 / evidence:pdf-p01-t03 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：3轭标本”归类为“轭”；不据编号相近合并不同对象。 |
| `fact:pdf-006` | CH1：3轭标本 — HAS_MATERIAL — 木材 | source:001 PDF第1页 / evidence:pdf-p01-t03 | 来源支持 | 原页对该对象或部位记有“木材”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-007` | CH1：3轭标本 — HAS_PRESERVED_FEATURE — 残存深褐色漆皮 | source:001 PDF第1页 / evidence:pdf-p01-t03 | 来源支持 | 原页对该对象或部位记有“残存深褐色漆皮”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-008` | CH1：3轭标本 — HAS_SURFACE_FINISH — 红漆 | source:001 PDF第1页 / evidence:pdf-p01-t03 | 来源支持 | 原页对该对象或部位记有“红漆”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-009` | CH1：3轭标本 — HAS_DIMENSION — {"quantity": "通宽", "unit": "cm", "raw": "通宽49、高52厘米", "approximate": false, "value": 49} | source:001 PDF第1页 / evidence:pdf-p01-t03 | 来源支持 | 逐项对照原页：CH1：3轭标本的通宽为49cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-010` | CH1：3轭标本 — HAS_DIMENSION — {"quantity": "高", "unit": "cm", "raw": "通宽49、高52厘米", "approximate": false, "value": 52} | source:001 PDF第1页 / evidence:pdf-p01-t03 | 来源支持 | 逐项对照原页：CH1：3轭标本的高为52cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-011` | CH1：1靷标本 — INSTANCE_OF — 靷 | source:001 PDF第1页 / evidence:pdf-p01-t05 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：1靷标本”归类为“靷”；不据编号相近合并不同对象。 |
| `fact:pdf-012` | CH1：1靷标本 — HAS_MATERIAL — 麻或丝（原文未定） | source:001 PDF第1页 / evidence:pdf-p01-t05 | 来源支持 | 原页对该对象或部位记有“麻或丝（原文未定）”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-013` | CH1：1靷标本 — HAS_PRESERVED_FEATURE — 炭化后仅存深褐色痕迹 | source:001 PDF第1页 / evidence:pdf-p01-t05 | 来源支持 | 原页对该对象或部位记有“炭化后仅存深褐色痕迹”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-014` | CH1：1靷标本 — HAS_PRESERVED_FEATURE — 残留少量深褐色漆痕迹 | source:001 PDF第1页 / evidence:pdf-p01-t05 | 来源支持 | 原页对该对象或部位记有“残留少量深褐色漆痕迹”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-015` | CH1：1靷标本 — HAS_DIMENSION — {"quantity": "可见部分长", "unit": "cm", "raw": "可见部分长163、宽约1.5厘米", "approximate": false, "value": 163} | source:001 PDF第1页 / evidence:pdf-p01-t05 | 来源支持 | 逐项对照原页：CH1：1靷标本的可见部分长为163cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-016` | CH1：1靷标本 — HAS_DIMENSION — {"quantity": "宽", "unit": "cm", "raw": "可见部分长163、宽约1.5厘米", "approximate": true, "value": 1.5} | source:001 PDF第1页 / evidence:pdf-p01-t05 | 来源支持 | 逐项对照原页：CH1：1靷标本的宽为1.5cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-017` | CH1：1靷标本 — HAS_PROCESSING — "三根合并对折而成" | source:001 PDF第1页 / evidence:pdf-p01-t05 | 来源支持 | 逐项对照原页中该主体的记载，HAS_PROCESSING所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-018` | CH1：1靷标本 — HAS_SHAPE — "分成左右两股，前端结小套环" | source:001 PDF第1页 / evidence:pdf-p01-t05 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-019` | CH1：4靷标本 — INSTANCE_OF — 靷 | source:001 PDF第1页 / evidence:pdf-p01-t07 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：4靷标本”归类为“靷”；不据编号相近合并不同对象。 |
| `fact:pdf-020` | CH1：4靷标本 — HAS_MATERIAL — 皮质 | source:001 PDF第1页 / evidence:pdf-p01-t07 | 来源支持 | 原页对该对象或部位记有“皮质”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-021` | CH1：4靷标本 — HAS_PRESERVED_FEATURE — 炭化后仅存深褐色痕迹 | source:001 PDF第1页 / evidence:pdf-p01-t07 | 来源支持 | 原页对该对象或部位记有“炭化后仅存深褐色痕迹”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-022` | CH1：4靷标本 — HAS_PRESERVED_FEATURE — 残留少量深褐色漆痕迹 | source:001 PDF第1页 / evidence:pdf-p01-t07 | 来源支持 | 原页对该对象或部位记有“残留少量深褐色漆痕迹”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-023` | CH1：4靷标本 — HAS_DIMENSION — {"quantity": "可见部分长", "unit": "cm", "raw": "可见部分长177、宽约3厘米", "approximate": false, "value": 177} | source:001 PDF第1页 / evidence:pdf-p01-t07 | 来源支持 | 逐项对照原页：CH1：4靷标本的可见部分长为177cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-024` | CH1：4靷标本 — HAS_DIMENSION — {"quantity": "宽", "unit": "cm", "raw": "可见部分长177、宽约3厘米", "approximate": true, "value": 3} | source:001 PDF第1页 / evidence:pdf-p01-t07 | 来源支持 | 逐项对照原页：CH1：4靷标本的宽为3cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-025` | CH1：4靷标本 — HAS_SHAPE — "前端小套环，后端大套环" | source:001 PDF第1页 / evidence:pdf-p01-t07 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-026` | CH1：4靷标本 — HAS_POSITION — "从前轸下引出双股，由辀的两侧前引至左右服马后脊处" | source:001 PDF第1页 / evidence:pdf-p01-t07 | 来源支持 | 逐项对照原页中该主体的记载，HAS_POSITION所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-027` | 麻或丝靷统计记录 — REFERS_TO_TYPE — 靷 | source:001 PDF第1页 / evidence:pdf-p01-t04 | 来源支持 | 逐项核对该图题、正文主题或明确标注，来源记录涉及“靷”；保留来源记录语境。 |
| `fact:pdf-028` | 麻或丝靷统计记录 — HAS_RECORDED_QUANTITY — "5根" | source:001 PDF第1页 / evidence:pdf-p01-t04 | 来源支持 | 逐项对照原页中该主体的记载，HAS_RECORDED_QUANTITY所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-029` | 麻或丝靷统计记录 — HAS_ORIGINAL_IDENTIFIERS — "CH1：1、6、12、14、22" | source:001 PDF第1页 / evidence:pdf-p01-t04 | 来源支持 | 逐项对照原页中该主体的记载，HAS_ORIGINAL_IDENTIFIERS所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-030` | 皮靷统计记录 — REFERS_TO_TYPE — 靷 | source:001 PDF第1页 / evidence:pdf-p01-t06 | 来源支持 | 逐项核对该图题、正文主题或明确标注，来源记录涉及“靷”；保留来源记录语境。 |
| `fact:pdf-031` | 皮靷统计记录 — HAS_RECORDED_QUANTITY — "14根" | source:001 PDF第1页 / evidence:pdf-p01-t06 | 来源支持 | 逐项对照原页中该主体的记载，HAS_RECORDED_QUANTITY所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-032` | 皮靷统计记录 — HAS_ORIGINAL_IDENTIFIERS — "CH1：2~5、7~10、13、15、16、20、24、33" | source:001 PDF第1页 / evidence:pdf-p01-t06 | 来源支持 | 逐项对照原页中该主体的记载，HAS_ORIGINAL_IDENTIFIERS所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-033` | CH1：4衡标本 — INSTANCE_OF — 衡 | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：4衡标本”归类为“衡”；不据编号相近合并不同对象。 |
| `fact:pdf-034` | CH1：4衡标本 — HAS_MATERIAL — 木材 | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 原页对该对象或部位记有“木材”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-035` | CH1：4衡标本 — HAS_PRESERVED_FEATURE — 残存深褐色漆皮 | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 原页对该对象或部位记有“残存深褐色漆皮”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-036` | CH1：4衡标本 — HAS_SHAPE — "波浪形，中粗两端细" | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-037` | CH1：4衡标本 — HAS_SHAPE — "横截面扁方形" | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-038` | CH1：4衡标本 — HAS_DIMENSION — {"quantity": "残长", "unit": "cm", "raw": "衡残长136、宽4.2、厚3.6厘米", "approximate": false, "value": 136} | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 逐项对照原页：CH1：4衡标本的残长为136cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-039` | CH1：4衡标本 — HAS_DIMENSION — {"quantity": "宽", "unit": "cm", "raw": "衡残长136、宽4.2、厚3.6厘米", "approximate": false, "value": 4.2} | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 逐项对照原页：CH1：4衡标本的宽为4.2cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-040` | CH1：4衡标本 — HAS_DIMENSION — {"quantity": "厚", "unit": "cm", "raw": "衡残长136、宽4.2、厚3.6厘米", "approximate": false, "value": 3.6} | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 逐项对照原页：CH1：4衡标本的厚为3.6cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-041` | CH1：4衡标本 — HAS_PART — CH1：4衡的轙（合组记录） | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 原页对应图示或正文明确支持“CH1：4衡标本”与“CH1：4衡的轙（合组记录）”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:pdf-042` | CH1：4衡的轙（合组记录） — INSTANCE_OF — 轙 | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：4衡的轙（合组记录）”归类为“轙”；不据编号相近合并不同对象。 |
| `fact:pdf-043` | CH1：4衡的轙（合组记录） — HAS_RECORDED_QUANTITY — "4个" | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_RECORDED_QUANTITY所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-044` | CH1：4衡的轙（合组记录） — HAS_SHAPE — "长方形" | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-045` | CH1：4衡标本 — HAS_PART — CH1：4衡两端骨衡帽 | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 原页对应图示或正文明确支持“CH1：4衡标本”与“CH1：4衡两端骨衡帽”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:pdf-046` | CH1：4衡两端骨衡帽 — INSTANCE_OF — 骨衡帽 | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：4衡两端骨衡帽”归类为“骨衡帽”；不据编号相近合并不同对象。 |
| `fact:pdf-047` | CH1：4衡两端骨衡帽 — HAS_MATERIAL — 骨质 | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 原页对该对象或部位记有“骨质”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-048` | CH1：4衡两端骨衡帽 — HAS_POSITION — "套于衡两端" | source:001 PDF第2页 / evidence:pdf-p02-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_POSITION所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-049` | 第2页未编号辀记录 — REFERS_TO_TYPE — 辀 | source:001 PDF第2页 / evidence:pdf-p02-t02 | 来源支持 | 逐项核对该图题、正文主题或明确标注，来源记录涉及“辀”；保留来源记录语境。 |
| `fact:pdf-050` | 第2页未编号辀记录 — HAS_DIMENSION — {"quantity": "长", "unit": "cm", "raw": "辀长328、厚3.1厘米", "approximate": false, "value": 328} | source:001 PDF第2页 / evidence:pdf-p02-t02 | 来源支持 | 逐项对照原页：第2页未编号辀记录的长为328cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-051` | 第2页未编号辀记录 — HAS_DIMENSION — {"quantity": "厚", "unit": "cm", "raw": "辀长328、厚3.1厘米", "approximate": false, "value": 3.1} | source:001 PDF第2页 / evidence:pdf-p02-t02 | 来源支持 | 逐项对照原页：第2页未编号辀记录的厚为3.1cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-052` | 第2页未编号辀记录 — HAS_DIMENSION — {"quantity": "前轸处宽", "unit": "cm", "raw": "辀在前轸处较宽，宽13厘米，近衡处较窄，宽6厘米", "approximate": false, "value": 13} | source:001 PDF第2页 / evidence:pdf-p02-t02 | 来源支持 | 逐项对照原页：第2页未编号辀记录的前轸处宽为13cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-053` | 第2页未编号辀记录 — HAS_DIMENSION — {"quantity": "近衡处宽", "unit": "cm", "raw": "辀在前轸处较宽，宽13厘米，近衡处较窄，宽6厘米", "approximate": false, "value": 6} | source:001 PDF第2页 / evidence:pdf-p02-t02 | 来源支持 | 逐项对照原页：第2页未编号辀记录的近衡处宽为6cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-054` | 第2页未编号辀记录 — HAS_DIMENSION — {"quantity": "踵外露部分长", "unit": "cm", "raw": "外露部分长4.5、宽7.3、厚4.2厘米", "approximate": false, "value": 4.5} | source:001 PDF第2页 / evidence:pdf-p02-t02 | 来源支持 | 逐项对照原页：第2页未编号辀记录的踵外露部分长为4.5cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-055` | 第2页未编号辀记录 — HAS_DIMENSION — {"quantity": "踵外露部分宽", "unit": "cm", "raw": "外露部分长4.5、宽7.3、厚4.2厘米", "approximate": false, "value": 7.3} | source:001 PDF第2页 / evidence:pdf-p02-t02 | 来源支持 | 逐项对照原页：第2页未编号辀记录的踵外露部分宽为7.3cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-056` | 第2页未编号辀记录 — HAS_DIMENSION — {"quantity": "踵外露部分厚", "unit": "cm", "raw": "外露部分长4.5、宽7.3、厚4.2厘米", "approximate": false, "value": 4.2} | source:001 PDF第2页 / evidence:pdf-p02-t02 | 来源支持 | 逐项对照原页：第2页未编号辀记录的踵外露部分厚为4.2cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-057` | 第2页未编号辀记录 — HAS_SHAPE — "前端上扬，后段贴于地面；横截面扁方形" | source:001 PDF第2页 / evidence:pdf-p02-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-058` | 第2页未编号辀记录 — HAS_POSITION — "纵向置于舆下轴上中轴纬线上；踵露于轮后（原文用语照录）" | source:001 PDF第2页 / evidence:pdf-p02-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_POSITION所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-059` | M1：302 车辀残件 — INSTANCE_OF — 辀 | source:001 PDF第3页 / evidence:pdf-p03-t01 | 来源支持 | 原页标本名称、图注或正文用词支持“M1：302 车辀残件”归类为“辀”；不据编号相近合并不同对象。 |
| `fact:pdf-060` | M1：302 车辀残件 — HAS_FIND_POSITION — "南室第二层西部中间靠西壁处" | source:001 PDF第3页 / evidence:pdf-p03-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_FIND_POSITION所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-061` | M1：302 车辀残件 — HAS_PRESERVED_FEATURE — 残存前段 | source:001 PDF第3页 / evidence:pdf-p03-t01 | 来源支持 | 原页对该对象或部位记有“残存前段”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-062` | M1：302 车辀残件 — HAS_SHAPE — "辀身长方体，前粗后细" | source:001 PDF第3页 / evidence:pdf-p03-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-063` | M1：302 车辀残件 — HAS_DIMENSION — {"quantity": "残长", "unit": "cm", "raw": "残长39.6、前宽7.6、最高7.6、身前宽4、高5.2厘米", "approximate": false, "value": 39.6} | source:001 PDF第3页 / evidence:pdf-p03-t01 | 来源支持 | 逐项对照原页：M1：302 车辀残件的残长为39.6cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-064` | M1：302 车辀残件 — HAS_DIMENSION — {"quantity": "前宽", "unit": "cm", "raw": "残长39.6、前宽7.6、最高7.6、身前宽4、高5.2厘米", "approximate": false, "value": 7.6} | source:001 PDF第3页 / evidence:pdf-p03-t01 | 来源支持 | 逐项对照原页：M1：302 车辀残件的前宽为7.6cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-065` | M1：302 车辀残件 — HAS_DIMENSION — {"quantity": "最高", "unit": "cm", "raw": "残长39.6、前宽7.6、最高7.6、身前宽4、高5.2厘米", "approximate": false, "value": 7.6} | source:001 PDF第3页 / evidence:pdf-p03-t01 | 来源支持 | 逐项对照原页：M1：302 车辀残件的最高为7.6cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-066` | M1：302 车辀残件 — HAS_DIMENSION — {"quantity": "身前宽", "unit": "cm", "raw": "残长39.6、前宽7.6、最高7.6、身前宽4、高5.2厘米", "approximate": false, "value": 4} | source:001 PDF第3页 / evidence:pdf-p03-t01 | 来源支持 | 逐项对照原页：M1：302 车辀残件的身前宽为4cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-067` | M1：302 车辀残件 — HAS_DIMENSION — {"quantity": "身前高", "unit": "cm", "raw": "残长39.6、前宽7.6、最高7.6、身前宽4、高5.2厘米", "approximate": false, "value": 5.2} | source:001 PDF第3页 / evidence:pdf-p03-t01 | 来源支持 | 逐项对照原页：M1：302 车辀残件的身前高为5.2cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-068` | M1：302 车辀残件 — HAS_PART — M1：302辀首 | source:001 PDF第3页 / evidence:pdf-p03-t01 | 来源支持 | 原页对应图示或正文明确支持“M1：302 车辀残件”与“M1：302辀首”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:pdf-069` | M1：302辀首 — INSTANCE_OF — 辀首 | source:001 PDF第3页 / evidence:pdf-p03-t01 | 来源支持 | 原页标本名称、图注或正文用词支持“M1：302辀首”归类为“辀首”；不据编号相近合并不同对象。 |
| `fact:pdf-070` | M1：302辀首 — HAS_SHAPE — "前上部中间有长方形穿孔" | source:001 PDF第3页 / evidence:pdf-p03-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-071` | M1：302辀首 — HAS_SHAPE — "下部成“凹”字形" | source:001 PDF第3页 / evidence:pdf-p03-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-072` | M1：302辀首 — HAS_SHAPE — "后部横穿圆孔" | source:001 PDF第3页 / evidence:pdf-p03-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-073` | M1：302辀首 — HAS_SURFACE_FINISH — 红漆 | source:001 PDF第3页 / evidence:pdf-p03-t01 | 来源支持 | 原页对该对象或部位记有“红漆”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-074` | M1：302 车辀残件 — HAS_PART — M1：302辀身前段 | source:001 PDF第3页 / evidence:pdf-p03-t01 | 需修正 | 原页支持辀身前中后段的局部漆饰，但这些段是描述区域。当前Component/HAS_PART表达容易被后续应用当作独立零件。 |
| `fact:pdf-075` | M1：302辀身前段 — HAS_SURFACE_FINISH — 红漆 | source:001 PDF第3页 / evidence:pdf-p03-t01 | 需修正 | 原页支持辀身前中后段的局部漆饰，但这些段是描述区域。当前Component/HAS_PART表达容易被后续应用当作独立零件。 |
| `fact:pdf-076` | M1：302 车辀残件 — HAS_PART — M1：302辀身中段 | source:001 PDF第3页 / evidence:pdf-p03-t01 | 需修正 | 原页支持辀身前中后段的局部漆饰，但这些段是描述区域。当前Component/HAS_PART表达容易被后续应用当作独立零件。 |
| `fact:pdf-077` | M1：302辀身中段 — HAS_SURFACE_FINISH — 黑漆 | source:001 PDF第3页 / evidence:pdf-p03-t01 | 需修正 | 原页支持辀身前中后段的局部漆饰，但这些段是描述区域。当前Component/HAS_PART表达容易被后续应用当作独立零件。 |
| `fact:pdf-078` | M1：302 车辀残件 — HAS_PART — M1：302辀身后段 | source:001 PDF第3页 / evidence:pdf-p03-t01 | 需修正 | 原页支持辀身前中后段的局部漆饰，但这些段是描述区域。当前Component/HAS_PART表达容易被后续应用当作独立零件。 |
| `fact:pdf-079` | M1：302辀身后段 — HAS_SURFACE_FINISH — 黑漆 | source:001 PDF第3页 / evidence:pdf-p03-t01 | 需修正 | 原页支持辀身前中后段的局部漆饰，但这些段是描述区域。当前Component/HAS_PART表达容易被后续应用当作独立零件。 |
| `fact:pdf-080` | M1：302辀身后段 — HAS_PATTERN_DETAIL — "黑漆上有一周红漆" | source:001 PDF第3页 / evidence:pdf-p03-t01 | 需修正 | 原页支持辀身前中后段的局部漆饰，但这些段是描述区域。当前Component/HAS_PART表达容易被后续应用当作独立零件。 |
| `fact:pdf-081` | 第4页未编号轴记录 — REFERS_TO_TYPE — 车轴 | source:001 PDF第4页 / evidence:pdf-p04-t02 | 来源支持 | 逐项核对该图题、正文主题或明确标注，来源记录涉及“车轴”；保留来源记录语境。 |
| `fact:pdf-082` | 第4页未编号轴记录 — HAS_DIMENSION — {"quantity": "通长", "unit": "cm", "raw": "轴通长276、粗径5、细径3.5厘米", "approximate": false, "value": 276} | source:001 PDF第4页 / evidence:pdf-p04-t02 | 来源支持 | 逐项对照原页：第4页未编号轴记录的通长为276cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-083` | 第4页未编号轴记录 — HAS_DIMENSION — {"quantity": "粗径", "unit": "cm", "raw": "轴通长276、粗径5、细径3.5厘米", "approximate": false, "value": 5} | source:001 PDF第4页 / evidence:pdf-p04-t02 | 来源支持 | 逐项对照原页：第4页未编号轴记录的粗径为5cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-084` | 第4页未编号轴记录 — HAS_DIMENSION — {"quantity": "细径", "unit": "cm", "raw": "轴通长276、粗径5、细径3.5厘米", "approximate": false, "value": 3.5} | source:001 PDF第4页 / evidence:pdf-p04-t02 | 来源支持 | 逐项对照原页：第4页未编号轴记录的细径为3.5cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-085` | 第4页未编号轴记录 — HAS_DIMENSION — {"quantity": "相对舆中轴经线向前距离", "unit": "cm", "raw": "轴置于舆下的中轴经线前2厘米处", "approximate": false, "value": 2} | source:001 PDF第4页 / evidence:pdf-p04-t02 | 来源支持 | 逐项对照原页：第4页未编号轴记录的相对舆中轴经线向前距离为2cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-086` | 第4页未编号轴记录 — HAS_SHAPE — "长条形，横截面下圆上方，末端锥形贯毂" | source:001 PDF第4页 / evidence:pdf-p04-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-087` | 第4页未编号轴记录 — HAS_POSITION — "位于舆下的中轴经线前2厘米处" | source:001 PDF第4页 / evidence:pdf-p04-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_POSITION所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-088` | 第4页轴数量记录 — REFERS_TO_TYPE — 车轴 | source:001 PDF第4页 / evidence:pdf-p04-t03 | 来源支持 | 逐项核对该图题、正文主题或明确标注，来源记录涉及“车轴”；保留来源记录语境。 |
| `fact:pdf-089` | 第4页轴数量记录 — HAS_RECORDED_QUANTITY — "登记33件；现存22件" | source:001 PDF第4页 / evidence:pdf-p04-t03 | 需修正 | 原页为“轴33件，现存22件”，未出现“登记”或说明33件统计口径；数值正确，但“登记33件”加了解释。 |
| `fact:pdf-090` | CH1：3轴标本 — HAS_DIMENSION — {"quantity": "粗径", "unit": "cm", "raw": "轴通长272、粗径9.7、细径2.6厘米", "approximate": false, "value": 9.7} | source:001 PDF第4页 / evidence:pdf-p04-t04 | 来源支持 | 逐项对照原页：CH1：3轴标本的粗径为9.7cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-091` | CH1：3轴标本 — HAS_DIMENSION — {"quantity": "细径", "unit": "cm", "raw": "轴通长272、粗径9.7、细径2.6厘米", "approximate": false, "value": 2.6} | source:001 PDF第4页 / evidence:pdf-p04-t04 | 来源支持 | 逐项对照原页：CH1：3轴标本的细径为2.6cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-092` | CH1：3轴标本 — HAS_PROCESSING — "一根整木砍刨打磨光滑而成" | source:001 PDF第4页 / evidence:pdf-p04-t04 | 来源支持 | 逐项对照原页中该主体的记载，HAS_PROCESSING所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-093` | CH1：3轴标本 — HAS_SHAPE — "中部较粗，贯毂部分内粗外细，呈圆锥体" | source:001 PDF第4页 / evidence:pdf-p04-t04 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-094` | CH1：3轴标本 — HAS_SHAPE — "轴上部应为平面，下部为圆弧形（原文推测）" | source:001 PDF第4页 / evidence:pdf-p04-t04 | 来源支持 | 原页确有这项来源推断；原文根据所述连接或范线痕作解释。仅支持“来源提出该推断”，不提升为实测或确定工艺。 |
| `fact:pdf-095` | CH1：3轴标本 — HAS_SHAPE — "末端有长方形榫钉孔，套軎后辖插入其中" | source:001 PDF第4页 / evidence:pdf-p04-t04 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-096` | 伏兔 — DESCRIPTION — "汇编在轴的参考段中讨论轴与伏兔的连接；部件图另标“伏兔”。" | source:001 PDF第4页 / evidence:pdf-p04-t04 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:pdf-097` | 双箍云纹圆筒形车軎组记录 — REFERS_TO_TYPE — 軎 | source:001 PDF第5页 / evidence:pdf-p05-t01 | 来源支持 | 逐项核对该图题、正文主题或明确标注，来源记录涉及“軎”；保留来源记录语境。 |
| `fact:pdf-098` | 双箍云纹圆筒形车軎组记录 — HAS_RECORDED_QUANTITY — "2件，1对" | source:001 PDF第5页 / evidence:pdf-p05-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_RECORDED_QUANTITY所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-099` | 双箍云纹圆筒形车軎组记录 — HAS_FIND_POSITION — "南室第一层东段中部偏南处" | source:001 PDF第5页 / evidence:pdf-p05-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_FIND_POSITION所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-100` | 双箍云纹圆筒形车軎组记录 — HAS_SHAPE — "末端平，正中有小圆孔；首端口部斜折，宽沿方唇" | source:001 PDF第5页 / evidence:pdf-p05-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-101` | 双箍云纹圆筒形车軎组记录 — HAS_SHAPE — "双凸箍，箍下有垫片" | source:001 PDF第5页 / evidence:pdf-p05-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-102` | 双箍云纹圆筒形车軎组记录 — HAS_SHAPE — "外箍一侧下伸长嘴鸟首形钩；内箍与口部间有对称长方形穿" | source:001 PDF第5页 / evidence:pdf-p05-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-103` | 双箍云纹圆筒形车軎组记录 — HAS_PROCESSING — "鸟首形钩范线痕被原文解释为双范合铸、嵌入軎体叠铸的依据" | source:001 PDF第5页 / evidence:pdf-p05-t01 | 来源支持 | 原页确有这项来源推断；原文根据所述连接或范线痕作解释。仅支持“来源提出该推断”，不提升为实测或确定工艺。 |
| `fact:pdf-104` | 双箍云纹圆筒形车軎组记录 — HAS_PATTERN_DETAIL — "通体错金银带纹和勾连云纹；末端面四蒂状卷云纹；双箍外壁勾连云纹；箍间四组方块夹对三角勾连云纹" | source:001 PDF第5页 / evidence:pdf-p05-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_PATTERN_DETAIL所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-105` | M1：201-1 车軎 — HAS_DIMENSION — {"quantity": "口径", "unit": "cm", "raw": "口径6.1、末端径3.4、通长8、辖长6.15厘米", "approximate": false, "value": 6.1} | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 逐项对照原页：M1：201-1 车軎的口径为6.1cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-106` | M1：201-1 车軎 — HAS_DIMENSION — {"quantity": "末端径", "unit": "cm", "raw": "口径6.1、末端径3.4、通长8、辖长6.15厘米", "approximate": false, "value": 3.4} | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 逐项对照原页：M1：201-1 车軎的末端径为3.4cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-107` | M1：201-1 车軎 — HAS_DIMENSION — {"quantity": "通长", "unit": "cm", "raw": "口径6.1、末端径3.4、通长8、辖长6.15厘米", "approximate": false, "value": 8} | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 逐项对照原页：M1：201-1 车軎的通长为8cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-108` | M1：201-1 车軎 — HAS_MASS_RECORD — "原文记重470克；是否包含所配辖未另行注明" | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_MASS_RECORD所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-109` | M1：201-1 车軎 — HAS_SHAPE — "末端圆形，顶中央圆形穿孔" | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-110` | M1：201-1 车軎 — HAS_SHAPE — "近两端各有一道圆凸箍" | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-111` | M1：201-1 车軎 — HAS_SHAPE — "近顶圆箍上侈出鸟首饰物，长变形喙" | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-112` | M1：201-1 车軎 — HAS_SHAPE — "另一圆箍至沿之间有对称的两个长方形穿孔" | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-113` | M1：201-1 车軎 — HAS_SHAPE — "宽直沿，沿内侧呈斜坡形" | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-114` | M1：201-1 车軎 — HAS_PROCESSING — "通体错金银；器身经不同程度锉磨加工" | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_PROCESSING所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-115` | M1：201-1 车軎 — HAS_PATTERN_DETAIL — "箍上均有三道凹弦纹；鸟首下颈至喙端有明显范线痕" | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_PATTERN_DETAIL所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-116` | M1：201-1 车軎 — HAS_DECORATION_MOTIF — 带纹 | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 原页对该对象或部位记有“带纹”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-117` | M1：201-1 车軎 — HAS_DECORATION_MOTIF — 勾连云纹 | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 原页对该对象或部位记有“勾连云纹”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-118` | M1：201-1 车軎 — HAS_ASSOCIATED_COMPONENT — M1：201-1车軎所配辖 | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 原页对应图示或正文明确支持“M1：201-1 车軎”与“M1：201-1车軎所配辖”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:pdf-119` | M1：201-1车軎所配辖 — INSTANCE_OF — 辖 | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 原页标本名称、图注或正文用词支持“M1：201-1车軎所配辖”归类为“辖”；不据编号相近合并不同对象。 |
| `fact:pdf-120` | M1：201-1车軎所配辖 — HAS_DIMENSION — {"quantity": "长", "unit": "cm", "raw": "口径6.1、末端径3.4、通长8、辖长6.15厘米", "approximate": false, "value": 6.15} | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 逐项对照原页：M1：201-1车軎所配辖的长为6.15cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-121` | M1：201-1车軎所配辖 — HAS_SHAPE — "兽面辖首，辖身长方条形；末端长方形横穿，顶有近方形浅痕" | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-122` | M1：201-1车軎所配辖 — HAS_PROCESSING — "器身有锉磨加工痕" | source:001 PDF第5页 / evidence:pdf-p05-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_PROCESSING所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-123` | CH1：5轮标本 — HAS_PART — CH1：5轮牙 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页对应图示或正文明确支持“CH1：5轮标本”与“CH1：5轮牙”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:pdf-124` | CH1：5轮牙 — INSTANCE_OF — 牙 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：5轮牙”归类为“牙”；不据编号相近合并不同对象。 |
| `fact:pdf-125` | CH1：5轮标本 — HAS_PART — CH1：5轮辐（尺寸记录对象） | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页对应图示或正文明确支持“CH1：5轮标本”与“CH1：5轮辐（尺寸记录对象）”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:pdf-126` | CH1：5轮辐（尺寸记录对象） — INSTANCE_OF — 辐 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：5轮辐（尺寸记录对象）”归类为“辐”；不据编号相近合并不同对象。 |
| `fact:pdf-127` | CH1：5轮标本 — HAS_PART — CH1：5轮毂 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页对应图示或正文明确支持“CH1：5轮标本”与“CH1：5轮毂”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:pdf-128` | CH1：5轮毂 — INSTANCE_OF — 毂 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：5轮毂”归类为“毂”；不据编号相近合并不同对象。 |
| `fact:pdf-129` | CH1：5轮牙 — HAS_SHAPE — "截面略呈梯形" | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-130` | CH1：5轮牙 — HAS_SHAPE — "着地面和两侧略鼓" | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-131` | CH1：5轮牙 — HAS_DIMENSION — {"quantity": "牙高", "unit": "cm", "raw": "牙高6.7、宽4.6厘米", "approximate": false, "value": 6.7} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5轮牙的牙高为6.7cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-132` | CH1：5轮牙 — HAS_DIMENSION — {"quantity": "牙宽", "unit": "cm", "raw": "牙高6.7、宽4.6厘米", "approximate": false, "value": 4.6} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5轮牙的牙宽为4.6cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-133` | CH1：5轮辐（尺寸记录对象） — HAS_DIMENSION — {"quantity": "通长", "unit": "cm", "raw": "辐通长50厘米", "approximate": false, "value": 50} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5轮辐（尺寸记录对象）的通长为50cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-134` | CH1：5轮辐（尺寸记录对象） — HAS_PART — CH1：5轮辐内段（股） | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页对应图示或正文明确支持“CH1：5轮辐（尺寸记录对象）”与“CH1：5轮辐内段（股）”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:pdf-135` | CH1：5轮辐内段（股） — INSTANCE_OF — 股 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：5轮辐内段（股）”归类为“股”；不据编号相近合并不同对象。 |
| `fact:pdf-136` | CH1：5轮辐（尺寸记录对象） — HAS_PART — CH1：5轮辐外段（骹） | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页对应图示或正文明确支持“CH1：5轮辐（尺寸记录对象）”与“CH1：5轮辐外段（骹）”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:pdf-137` | CH1：5轮辐外段（骹） — INSTANCE_OF — 骹 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：5轮辐外段（骹）”归类为“骹”；不据编号相近合并不同对象。 |
| `fact:pdf-138` | CH1：5轮辐内段（股） — HAS_SHAPE — "横截面扁棱形" | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-139` | CH1：5轮辐外段（骹） — HAS_SHAPE — "横截面圆柱形" | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-140` | CH1：5轮辐内段（股） — HAS_DIMENSION — {"quantity": "宽", "unit": "cm", "raw": "内段为股，与毂榫卯结合，横截面扁棱形，宽4.4、厚1.4厘米", "approximate": false, "value": 4.4} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5轮辐内段（股）的宽为4.4cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-141` | CH1：5轮辐内段（股） — HAS_DIMENSION — {"quantity": "厚", "unit": "cm", "raw": "内段为股，与毂榫卯结合，横截面扁棱形，宽4.4、厚1.4厘米", "approximate": false, "value": 1.4} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5轮辐内段（股）的厚为1.4cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-142` | CH1：5轮辐外段（骹） — HAS_DIMENSION — {"quantity": "直径", "unit": "cm", "raw": "外段为骹，与轮牙榫卯结合，横截面圆柱形，直径2.9厘米", "approximate": false, "value": 2.9} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5轮辐外段（骹）的直径为2.9cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-143` | CH1：5轮辐（尺寸记录对象） — HAS_SHAPE — "骹与股过渡较平滑，无明显界线；骹长于股" | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-144` | CH1：5轮辐内段（股） — TENON_JOINT_WITH — CH1：5轮毂 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页对应图示或正文明确支持“CH1：5轮辐内段（股）”与“CH1：5轮毂”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:pdf-145` | CH1：5轮辐外段（骹） — TENON_JOINT_WITH — CH1：5轮牙 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页对应图示或正文明确支持“CH1：5轮辐外段（骹）”与“CH1：5轮牙”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:pdf-146` | CH1：5轮毂 — HAS_SHAPE — "圆锥状，近贤端较粗，呈圆鼓腹，中空" | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-147` | CH1：5轮毂 — HAS_DIMENSION — {"quantity": "通长", "unit": "cm", "raw": "毂通长70、贤端径13.5、壶中径17、轵端径6厘米", "approximate": false, "value": 70} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5轮毂的通长为70cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-148` | CH1：5轮毂 — HAS_DIMENSION — {"quantity": "贤端径", "unit": "cm", "raw": "毂通长70、贤端径13.5、壶中径17、轵端径6厘米", "approximate": false, "value": 13.5} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5轮毂的贤端径为13.5cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-149` | CH1：5轮毂 — HAS_DIMENSION — {"quantity": "壶中径", "unit": "cm", "raw": "毂通长70、贤端径13.5、壶中径17、轵端径6厘米", "approximate": false, "value": 17} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5轮毂的壶中径为17cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-150` | CH1：5轮毂 — HAS_DIMENSION — {"quantity": "轵端径", "unit": "cm", "raw": "毂通长70、贤端径13.5、壶中径17、轵端径6厘米", "approximate": false, "value": 6} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5轮毂的轵端径为6cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-151` | CH1：5轮毂 — HAS_PART — CH1：5毂轵部窄篆 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页对应图示或正文明确支持“CH1：5轮毂”与“CH1：5毂轵部窄篆”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:pdf-152` | CH1：5毂轵部窄篆 — INSTANCE_OF — 篆 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：5毂轵部窄篆”归类为“篆”；不据编号相近合并不同对象。 |
| `fact:pdf-153` | CH1：5毂轵部窄篆 — HAS_RECORDED_QUANTITY — "13道" | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_RECORDED_QUANTITY所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-154` | CH1：5毂轵部窄篆 — HAS_SHAPE — "环棱状窄篆" | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-155` | CH1：5毂轵部窄篆 — HAS_DIMENSION — {"quantity": "间隔", "unit": "cm", "raw": "篆间隔1.6、宽0.8、高0.4~0.6厘米", "approximate": false, "value": 1.6} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5毂轵部窄篆的间隔为1.6cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-156` | CH1：5毂轵部窄篆 — HAS_DIMENSION — {"quantity": "宽", "unit": "cm", "raw": "篆间隔1.6、宽0.8、高0.4~0.6厘米", "approximate": false, "value": 0.8} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5毂轵部窄篆的宽为0.8cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-157` | CH1：5毂轵部窄篆 — HAS_DIMENSION — {"quantity": "高", "unit": "cm", "raw": "篆间隔1.6、宽0.8、高0.4~0.6厘米", "approximate": false, "min": 0.4, "max": 0.6} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5毂轵部窄篆的高为0.4~0.6cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-158` | CH1：5轮标本 — HAS_PART — CH1：5轮附加圆木条 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页对应图示或正文明确支持“CH1：5轮标本”与“CH1：5轮附加圆木条”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:pdf-159` | CH1：5轮附加圆木条 — INSTANCE_OF — 车轮附加圆木条 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：5轮附加圆木条”归类为“车轮附加圆木条”；不据编号相近合并不同对象。 |
| `fact:pdf-160` | CH1：5轮附加圆木条 — HAS_MATERIAL — 木材 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页对该对象或部位记有“木材”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-161` | CH1：5轮附加圆木条 — HAS_RECORDED_QUANTITY — "2根" | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_RECORDED_QUANTITY所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-162` | CH1：5轮附加圆木条 — HAS_POSITION — "辐条外侧沿毂两侧平行附加，两端贴附轮牙中部" | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_POSITION所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-163` | CH1：5轮附加圆木条 — HAS_DIMENSION — {"quantity": "长", "unit": "cm", "raw": "木条长118、径3厘米", "approximate": false, "value": 118} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5轮附加圆木条的长为118cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-164` | CH1：5轮附加圆木条 — HAS_DIMENSION — {"quantity": "直径", "unit": "cm", "raw": "木条长118、径3厘米", "approximate": false, "value": 3} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5轮附加圆木条的直径为3cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-165` | CH1：5轮标本 — HAS_PART — CH1：5轮捆扎皮条 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页对应图示或正文明确支持“CH1：5轮标本”与“CH1：5轮捆扎皮条”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:pdf-166` | CH1：5轮捆扎皮条 — INSTANCE_OF — 捆扎皮条 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页标本名称、图注或正文用词支持“CH1：5轮捆扎皮条”归类为“捆扎皮条”；不据编号相近合并不同对象。 |
| `fact:pdf-167` | CH1：5轮捆扎皮条 — HAS_MATERIAL — 皮质 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页对该对象或部位记有“皮质”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-168` | CH1：5轮捆扎皮条 — HAS_SURFACE_FINISH — 红漆 | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 原页对该对象或部位记有“红漆”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-169` | CH1：5轮捆扎皮条 — HAS_POSITION — "木条与辐条交汇处捆扎四道；皮条底漆上饰红漆" | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页中该主体的记载，HAS_POSITION所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-170` | CH1：5轮捆扎皮条 — HAS_DIMENSION — {"quantity": "宽", "unit": "cm", "raw": "皮条宽1.5厘米", "approximate": false, "value": 1.5} | source:001 PDF第6页 / evidence:pdf-p06-t01 | 来源支持 | 逐项对照原页：CH1：5轮捆扎皮条的宽为1.5cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-171` | M1：257-1马衔 — INSTANCE_OF — 衔 | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 原页标本名称、图注或正文用词支持“M1：257-1马衔”归类为“衔”；不据编号相近合并不同对象。 |
| `fact:pdf-172` | M1：257-2a马镳 — INSTANCE_OF — 镳 | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 原页标本名称、图注或正文用词支持“M1：257-2a马镳”归类为“镳”；不据编号相近合并不同对象。 |
| `fact:pdf-173` | M1：257 马具组 — HAS_FIND_POSITION — "南室第二层东段西部偏北处" | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_FIND_POSITION所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-174` | M1：257-1马衔 — HAS_MATERIAL — 铜 | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 原页对该对象或部位记有“铜”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-175` | M1：257-1马衔 — HAS_DIMENSION — {"quantity": "通长", "unit": "cm", "raw": "通长22.5厘米，重220克", "approximate": false, "value": 22.5} | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 逐项对照原页：M1：257-1马衔的通长为22.5cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-176` | M1：257-1马衔 — HAS_MASS_RECORD — "220克" | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_MASS_RECORD所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-177` | M1：257-2a马镳 — HAS_DIMENSION — {"quantity": "长", "unit": "cm", "raw": "镳长37厘米", "approximate": false, "value": 37} | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 逐项对照原页：M1：257-2a马镳的长为37cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-178` | M1：257-1马衔 — HAS_SHAPE — "两节铜棒套成，每节两端各有一环" | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-179` | M1：257-1马衔 — HAS_SHAPE — "外端大环椭圆形，里端相套小环圆形" | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-180` | M1：257-1马衔 — HAS_SHAPE — "棒中部做成绳索状" | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-181` | M1：257-1马衔 — HAS_SHAPE — "两铜棒大环外侧范线上均有枣核形浇痕，其中一痕明显凸出" | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-182` | M1：257-1马衔 — HAS_DIMENSION — {"quantity": "枣核形浇痕长", "unit": "cm", "raw": "痕长1.4、宽0.3厘米", "approximate": false, "value": 1.4} | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 逐项对照原页：M1：257-1马衔的枣核形浇痕长为1.4cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-183` | M1：257-1马衔 — HAS_DIMENSION — {"quantity": "枣核形浇痕宽", "unit": "cm", "raw": "痕长1.4、宽0.3厘米", "approximate": false, "value": 0.3} | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 逐项对照原页：M1：257-1马衔的枣核形浇痕宽为0.3cm；近似/范围和原始表达一致，保留标本或局部所有者。 |
| `fact:pdf-184` | M1：257-1马衔 — HAS_PROCESSING — "仅对范线和芯线稍作锉磨加工" | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_PROCESSING所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-185` | M1：257-1马衔 — HAS_SHAPE — "一棒环内侧有一周明显芯线，棒两侧范线与两环外侧一圈范线相接" | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-186` | M1：257-1马衔 — HAS_SHAPE — "另一棒大环内侧有一周明显芯线；小环顶端平，有与内径等距且平行的两道芯线" | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-187` | M1：257-1马衔 — HAS_SHAPE — "另一棒两道芯线与小环内侧两端芯线相接；两侧范线分别与大环外侧范线及小环芯线中间相接" | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 逐项对照原页中该主体的记载，HAS_SHAPE所表达内容相符；只支持当前主体和来源语境。 |
| `fact:pdf-188` | M1：257 残存漆骨帽马镳 — INSTANCE_OF — 镳 | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 原页标本名称、图注或正文用词支持“M1：257 残存漆骨帽马镳”归类为“镳”；不据编号相近合并不同对象。 |
| `fact:pdf-189` | M1：257 残存漆骨帽马镳 — HAS_PART — M1：257残存马镳的骨帽 | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 原页对应图示或正文明确支持“M1：257 残存漆骨帽马镳”与“M1：257残存马镳的骨帽”的所述关系；组成不自动等于可拆性或装配先后，标本范围不外推。 |
| `fact:pdf-190` | M1：257残存马镳的骨帽 — HAS_MATERIAL — 骨质 | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 原页对该对象或部位记有“骨质”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-191` | M1：257残存马镳的骨帽 — HAS_SURFACE_FINISH — 黑漆 | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 原页对该对象或部位记有“黑漆”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-192` | M1：257残存马镳的骨帽 — HAS_DECORATION_MOTIF — 勾连云纹 | source:001 PDF第7页 / evidence:pdf-p07-t02 | 来源支持 | 原页对该对象或部位记有“勾连云纹”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-193` | M2：432-3铜节约 — INSTANCE_OF — 节约 | source:001 PDF第7页 / evidence:pdf-figure-15 | 来源支持 | 原页标本名称、图注或正文用词支持“M2：432-3铜节约”归类为“节约”；不据编号相近合并不同对象。 |
| `fact:pdf-194` | M2：432-3铜节约 — HAS_MATERIAL — 铜 | source:001 PDF第7页 / evidence:pdf-figure-15 | 来源支持 | 原页对该对象或部位记有“铜”，与事实范围相符；保留原文材质和残存状态，不推广到整类或六号车。 |
| `fact:pdf-195` | M2：432马勒推测复原图记录 — REFERS_TO_TYPE — 辔 | source:001 PDF第8页 / evidence:pdf-figure-16 | 来源支持 | 逐项核对该图题、正文主题或明确标注，来源记录涉及“辔”；保留来源记录语境。 |
| `fact:pdf-196` | M2：432马勒推测复原图记录 — HAS_DIAGRAM_LABELS — "正、反；比例尺0、16厘米（比例尺不作器物尺寸）" | source:001 PDF第8页 / evidence:pdf-figure-16 | 来源支持 | 逐项核对图中所列文字、子编号及比例尺；编辑标点/标题按记录说明处理，比例尺不转作器物尺寸。 |
| `fact:pdf-197` | 第8页四马缰绳示意记录 — REFERS_TO_TYPE — 缰 | source:001 PDF第8页 / evidence:pdf-figure-17 | 来源支持 | 逐项核对该图题、正文主题或明确标注，来源记录涉及“缰”；保留来源记录语境。 |
| `fact:pdf-198` | 第8页四马缰绳示意记录 — DEPICTS — 轙环 | source:001 PDF第8页 / evidence:pdf-figure-17 | 来源支持 | 原页复原图/示意图可见或标注“轙环”；仅支持图中呈现，不认定具体战车出土实物组成。 |
| `fact:pdf-199` | 第8页四马缰绳示意记录 — DEPICTS — 游环 | source:001 PDF第8页 / evidence:pdf-figure-17 | 来源支持 | 原页复原图/示意图可见或标注“游环”；仅支持图中呈现，不认定具体战车出土实物组成。 |
| `fact:pdf-200` | 第8页四马缰绳示意记录 — DEPICTS — 服马 | source:001 PDF第8页 / evidence:pdf-figure-17 | 来源支持 | 原页复原图/示意图可见或标注“服马”；仅支持图中呈现，不认定具体战车出土实物组成。 |
| `fact:pdf-201` | 第8页四马缰绳示意记录 — DEPICTS — 骖马 | source:001 PDF第8页 / evidence:pdf-figure-17 | 来源支持 | 原页复原图/示意图可见或标注“骖马”；仅支持图中呈现，不认定具体战车出土实物组成。 |
| `fact:pdf-202` | 第8页四马缰绳示意记录 — HAS_DIAGRAM_LABELS — "轙环、游环、左骖、左服、右服、右骖、御者左手、御者右手" | source:001 PDF第8页 / evidence:pdf-figure-17 | 来源支持 | 逐项核对图中所列文字、子编号及比例尺；编辑标点/标题按记录说明处理，比例尺不转作器物尺寸。 |
| `fact:pdf-203` | 缰 — DESCRIPTION — "第8页示意图用青、红色线路分别向御者左、右手汇集，绿色线路在内侧两马之间交叉；仅作图示观察。" | source:001 PDF第8页 / evidence:pdf-figure-17 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:pdf-204` | 图三一七6号车复原图记录 — DEPICTS — 九连墩一号车马坑6号车 | source:001 PDF第9页 / evidence:pdf-figure-18 | 来源支持 | 原页复原图/示意图可见或标注“九连墩一号车马坑6号车”；仅支持图中呈现，不认定具体战车出土实物组成。 |
| `fact:pdf-205` | 图三一七6号车复原图记录 — DEPICTS — 舆 | source:001 PDF第9页 / evidence:pdf-figure-18 | 来源支持 | 原页复原图/示意图可见或标注“舆”；仅支持图中呈现，不认定具体战车出土实物组成。 |
| `fact:pdf-206` | 图三一七6号车复原图记录 — DEPICTS — 围栏 | source:001 PDF第9页 / evidence:pdf-figure-18 | 来源支持 | 原页复原图/示意图可见或标注“围栏”；仅支持图中呈现，不认定具体战车出土实物组成。 |
| `fact:pdf-207` | 图三一七6号车复原图记录 — DEPICTS — 辀 | source:001 PDF第9页 / evidence:pdf-figure-18 | 来源支持 | 原页复原图/示意图可见或标注“辀”；仅支持图中呈现，不认定具体战车出土实物组成。 |
| `fact:pdf-208` | 图三一七6号车复原图记录 — DEPICTS — 衡 | source:001 PDF第9页 / evidence:pdf-figure-18 | 来源支持 | 原页复原图/示意图可见或标注“衡”；仅支持图中呈现，不认定具体战车出土实物组成。 |
| `fact:pdf-209` | 图三一七6号车复原图记录 — DEPICTS — 轭 | source:001 PDF第9页 / evidence:pdf-figure-18 | 来源支持 | 原页复原图/示意图可见或标注“轭”；仅支持图中呈现，不认定具体战车出土实物组成。 |
| `fact:pdf-210` | 图三一七6号车复原图记录 — DEPICTS — 车轮 | source:001 PDF第9页 / evidence:pdf-figure-18 | 来源支持 | 原页复原图/示意图可见或标注“车轮”；仅支持图中呈现，不认定具体战车出土实物组成。 |
| `fact:pdf-211` | 图三一七6号车复原图记录 — DEPICTS — 车轴 | source:001 PDF第9页 / evidence:pdf-figure-18 | 来源支持 | 原页复原图/示意图可见或标注“车轴”；仅支持图中呈现，不认定具体战车出土实物组成。 |
| `fact:pdf-212` | 图三一七6号车复原图记录 — HAS_DIAGRAM_LABELS — "围栏局部；比例尺0、10厘米与0、80厘米（不反算实物尺寸）" | source:001 PDF第9页 / evidence:pdf-figure-18 | 来源支持 | 逐项核对图中所列文字、子编号及比例尺；编辑标点/标题按记录说明处理，比例尺不转作器物尺寸。 |
| `fact:pdf-213` | 舆 — DESCRIPTION — "原第9页“舆的总体结构”配图三一七，并标注“围栏局部”；其后车茵、车蔽衣、伞、盖仅有标题。" | source:001 PDF第9页 / evidence:pdf-figure-18 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:pdf-214` | 7号车平剖面图记录 — REFERS_TO_TYPE — 靷 | source:001 PDF第2页 / evidence:pdf-figure-02 | 来源支持 | 逐项核对该图题、正文主题或明确标注，来源记录涉及“靷”；保留来源记录语境。 |
| `fact:pdf-215` | 7号车平剖面图记录 — HAS_DIAGRAM_LABELS — "北；A、A′、B、B′剖面定位符；比例尺0、80厘米；红字“红色部分为‘靷’”。" | source:001 PDF第2页 / evidence:pdf-figure-02 | 来源支持 | 逐项核对图中所列文字、子编号及比例尺；编辑标点/标题按记录说明处理，比例尺不转作器物尺寸。 |
| `fact:pdf-216` | 7号车平剖面图记录 — DESCRIPTION — "图三一八 一号车马坑——7号车平、剖面图。" | source:001 PDF第2页 / evidence:pdf-figure-02 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:pdf-217` | 8号车平剖面图记录 — REFERS_TO_TYPE — 靷 | source:001 PDF第2页 / evidence:pdf-figure-03 | 证据不足 | 同页7号车图红字明确标注靷，8号车仅画类似红线，无独立靷标签；相似性不足以当作明文记载。 |
| `fact:pdf-218` | 8号车平剖面图记录 — HAS_DIAGRAM_LABELS — "北；A、A′、B、B′剖面定位符；原图子编号1、2、3、4、5；比例尺0、80厘米。" | source:001 PDF第2页 / evidence:pdf-figure-03 | 来源支持 | 逐项核对图中所列文字、子编号及比例尺；编辑标点/标题按记录说明处理，比例尺不转作器物尺寸。 |
| `fact:pdf-219` | 8号车平剖面图记录 — DESCRIPTION — "图三一九 一号车马坑——8号车平、剖面图。" | source:001 PDF第2页 / evidence:pdf-figure-03 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:pdf-220` | 轮牙辐毂拼装示意记录 — REFERS_TO_TYPE — 车轮 | source:001 PDF第4页 / evidence:pdf-figure-07 | 来源支持 | 逐项核对该图题、正文主题或明确标注，来源记录涉及“车轮”；保留来源记录语境。 |
| `fact:pdf-221` | 轮牙辐毂拼装示意记录 — HAS_DIAGRAM_LABELS — "1.轮牙拼合；2.安装辐与牙；3.安装后车轮；4.辐条结构；5.车轮剖视；6.后视车轮；7.车毂结构。" | source:001 PDF第4页 / evidence:pdf-figure-07 | 来源支持 | 逐项核对图中所列文字、子编号及比例尺；编辑标点/标题按记录说明处理，比例尺不转作器物尺寸。 |
| `fact:pdf-222` | 轮牙辐毂拼装示意记录 — DESCRIPTION — "图二八三 一号车马坑——轮牙、辐、毂拼装方式示意图。" | source:001 PDF第4页 / evidence:pdf-figure-07 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:pdf-223` | 轮轴部位图示记录 — REFERS_TO_TYPE — 车轮 | source:001 PDF第5页 / evidence:pdf-figure-09 | 来源支持 | 逐项核对该图题、正文主题或明确标注，来源记录涉及“车轮”；保留来源记录语境。 |
| `fact:pdf-224` | 轮轴部位图示记录 — HAS_DIAGRAM_LABELS — "上图：牙、辐、軎、轴、伏兔、轮、毂。左下图：股、骹、辐。右下图：贤、壶中、轵、毂、篆。" | source:001 PDF第5页 / evidence:pdf-figure-09 | 来源支持 | 逐项核对图中所列文字、子编号及比例尺；编辑标点/标题按记录说明处理，比例尺不转作器物尺寸。 |
| `fact:pdf-225` | 轮轴部位图示记录 — DESCRIPTION — "原图未附独立图题；本标题为编辑标题。" | source:001 PDF第5页 / evidence:pdf-figure-09 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:pdf-226` | 中凹轮比较图记录 — REFERS_TO_TYPE — 车轮 | source:001 PDF第6页 / evidence:pdf-figure-11 | 来源支持 | 逐项核对该图题、正文主题或明确标注，来源记录涉及“车轮”；保留来源记录语境。 |
| `fact:pdf-227` | 中凹轮比较图记录 — HAS_DIAGRAM_LABELS — "正视图、股端、骹端、辐条、侧视图、夹辅；子编号1、2。" | source:001 PDF第6页 / evidence:pdf-figure-11 | 来源支持 | 逐项核对图中所列文字、子编号及比例尺；编辑标点/标题按记录说明处理，比例尺不转作器物尺寸。 |
| `fact:pdf-228` | 中凹轮比较图记录 — DESCRIPTION — "图一 中凹轮结构示意图。1.根据长沙203号汉墓2号车车轮绘制；2.根据辉县琉璃阁131号战国车马坑第16号车车轮绘制。" | source:001 PDF第6页 / evidence:pdf-figure-11 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:pdf-229` | 夹辅车轮比较图记录 — REFERS_TO_TYPE — 车轮 | source:001 PDF第6页 / evidence:pdf-figure-12 | 来源支持 | 逐项核对该图题、正文主题或明确标注，来源记录涉及“车轮”；保留来源记录语境。 |
| `fact:pdf-230` | 夹辅车轮比较图记录 — HAS_DIAGRAM_LABELS — "轴、轮牙、辐条、毂、夹辅、夹辅截面。" | source:001 PDF第6页 / evidence:pdf-figure-12 | 来源支持 | 逐项核对图中所列文字、子编号及比例尺；编辑标点/标题按记录说明处理，比例尺不转作器物尺寸。 |
| `fact:pdf-231` | 夹辅车轮比较图记录 — DESCRIPTION — "图七 有夹辅车轮结构及其稳定性能示意图。" | source:001 PDF第6页 / evidence:pdf-figure-12 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
| `fact:pdf-232` | 车轮受力变形图记录 — REFERS_TO_TYPE — 车轮 | source:001 PDF第6页 / evidence:pdf-figure-13 | 来源支持 | 逐项核对该图题、正文主题或明确标注，来源记录涉及“车轮”；保留来源记录语境。 |
| `fact:pdf-233` | 车轮受力变形图记录 — HAS_DIAGRAM_LABELS — "轮毂、载重力、轴末端、138cm、188cm、F；子编号1、2、3。" | source:001 PDF第6页 / evidence:pdf-figure-13 | 来源支持 | 逐项核对图中所列文字、子编号及比例尺；编辑标点/标题按记录说明处理，比例尺不转作器物尺寸。 |
| `fact:pdf-234` | 车轮受力变形图记录 — DESCRIPTION — "图四 车轮受力变形示意图与车轮状态（左边剖面图，右边全图）。1.轮与轴受力示意图；2.直辐轮变形示意图；3.中凹轮受力示意图。" | source:001 PDF第6页 / evidence:pdf-figure-13 | 来源支持 | 已逐条对照相应正文、图题或图像。该描述保留作者/汇编/标题/图示语境；它不是额外实测或六号车实物结论。 |
