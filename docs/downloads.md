# 本地资料下载索引

保存日期：2026-11-19。共 **7项可读资料：3份PDF、4篇机构网页正文**；其中2份PDF为本次新增，1份为此前已保存的出版社公开样章。

点击下方本地文件即可查看。文件位于 `assets/references/local/`，机器记录见 [download-manifest.json](../data/sources/download-manifest.json)，包含原站URL、文件大小、SHA256、获取范围和检查结果。

这些资料能支持项目到什么程度，见[任务相关性核查](source-relevance.md)：逐项记录正文位置、对应需求和使用限制。

## PDF

| 资料 | 本地文件 | 范围与检查 |
|---|---|---|
| 张万辉《先秦辐式双轮马车轮辋制作技艺研究》，2022 | [打开PDF](../assets/references/local/zhang-2022-wheel-rim.pdf) | 完整论文7页，印刷163—169页；全部页可解析，首末页已渲染核对 |
| 邵朋飞《探微〈考工记〉中的工匠精神——以“轮”的制造为例》，2022 | [打开PDF](../assets/references/local/shao-2022-wheel-craft.pdf) | 完整论文9页，印刷247—255页；全部页可解析，首末页已渲染核对 |
| 刘永华《中国古代车舆马具》，2013 | [打开样章PDF](../assets/references/local/liu-2013-chariot-excerpt.pdf) | 出版社公开样章9页，**不是整书**；复用已有有效文件 |

邵朋飞论文的期刊网页题名为《探微〈考工记〉中“轮”的制造——以“轮”的制造为例》，与下载PDF正文不同。此处采用PDF第1页及页脚引用格式中的“工匠精神”题名，原网站题名保留在装配目录中。

原站入口：[张万辉论文PDF](https://pubs.cstam.org.cn/data/article/gcyj/preview/pdf/22062003.pdf)、[邵朋飞论文PDF](https://pubs.cstam.org.cn/data/article/gcyj/preview/pdf/22060201.pdf)、[清华大学出版社样章](https://www.tup.com.cn/upload/books/yz/043859-03.pdf)。

## 机构网页正文

以下为可离线阅读的正文文字副本，标明原站与保存日期。原始HTML另保存在同目录的 `originals/`；**图片、视频、附件和原站样式未离线打包**，查看图表请使用副本中的原站链接。网页副本没有冒充原始论文PDF。

| 资料 | 本地阅读副本 |
|---|---|
| 北京大学：甘肃张家川马家塬遗址，含“五、车舆复原” | [打开正文](../assets/references/local/web/pku-majiayuan.html) |
| 中国国家博物馆：既远却近的背影——孙机先生与系驾法研究 | [打开正文](../assets/references/local/web/national-museum-harness.html) |
| 湖北省博物馆：“九连墩的故事”展览说明 | [打开正文](../assets/references/local/web/hubei-jiuliandun-exhibition.html) |
| 故宫博物院：双兔车軎 | [打开正文](../assets/references/local/web/palace-museum-axle-cap.html) |

## 尚未取得的正文

| 资料 | 本次状态 |
|---|---|
| 陕西传统木轮大车制作技艺调查 | 原ScienceEngine PDF地址返回404；期刊平台连接重置，旧站证书过期，尚无有效本地PDF |
| 西周时期车马埋葬中的礼制意涵 | 院方地址返回浏览器验证HTML，未取得PDF |
| 略论《考工记》车的制造规范 | 期刊页面仅书目/摘要，全文指向CNKI，需机构访问 |
| 九连墩楚墓 | 未发现公开全文；保留书目，待图书馆借阅 |
| 中国古代设计思想研究、考工司南 | 所见原站仅简介、序言或目录，未取得全书 |
| 孙机原论文、九连墩2003年简报、考工记译注、殷车复原论文 | 仍为待追查原文线索，未将引用它们的材料当作原文 |

超时截断文件和HTML错误响应只留在被忽略的 `tmp/`，未放入正式阅读目录。未进行登录、付费、购买或绕过站点验证。

## 使用和接力开发

- 下载成功只表示文件取得并通过完整性检查，**不等于全部内容已精读、已审核或已入图谱**。现有候选数据未变。
- 精读时按来源、页码、时代、标本归属建立候选，继续区分通用工艺与九连墩六号车事实。
- 本地下载缓存已被Git忽略；目录与下载记录可随项目交接。其他电脑需按记录的原站入口重新获取，不依赖本机绝对路径，也不默认再发布全文。
