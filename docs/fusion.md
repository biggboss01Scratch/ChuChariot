# 文字、资料图和模型节点联合检查

2026-11-23第九批：选择 `data/sources/fusion-media.v0.9.json`、候选v0.9、本体0.6。沿用全部25项媒体和7组候选模型映射；新增25个知识实体没有新增几何绑定，不能认为伏兔、舆底、支承区和各马具绳索已经能分别三维高亮。详见[同步检查](teammate-sync-v0.9.md)。以下旧记录保留。

2026-11-23补充：第五批应选 `data/sources/fusion-media.v0.5.json`，包含18张原件图块和7组旧模型静态图，匹配 `teacher-pdf.v0.5.json` 与本体0.3。旧媒体清单继续用于旧批次。新增裁剪通过既有 `scripts.extract_source_clips` 脚本生成；见[第五批复现](extraction-2026-11-23.md)。

2026-11-19 · 第三批候选数据与本地临时检查页。该工具供组内验收数据和关联，使用本机服务及静态节点图。正式三维展陈另行开发。[项目文档索引](index.md)

在检查页选「车轮」「毂」或「軎」。详情中有对应事实、PDF 局部截图、GLB 节点静态图。截图能回到原页，模型图能定位到节点索引。当前共有 17 个实体、28 条候选、22 段证据、8 个资料图块和 7 个节点图。所有新事实待正式审核。

## 如何关联

三类记录通过既有的实体 ID 相连。文字断言保留在候选 JSON，`fact.evidence_ids` 指向证据。资料图块引用证据 ID、实体 ID、PDF 页、渲染像素尺寸和裁剪矩形。模型仍通过 `model_mappings` 管理，静态图引用映射 ID、节点索引和 GLB 内容哈希。

`data/sources/fusion-media.v0.1.json` 是本批关联清单。读取时校验证据页、实体、模型版本和节点。页面基于事实与映射的审核状态筛选媒体。例如，同一个车軎图块可展示在 M1：201-1 和车軎类别下，只有各自的可见事实支持该关联时才出现。对照器物没有六号车实例的模型绑定。

本地缓存位于 `assets/references/local/fusion/`。组员可用对应原件重建图像。随候选包分发的是定位数据和生成脚本，原件和本地缓存按照现有 Git 规则管理。

## 模型核对

用原始 GLB 的网格、节点层级和初始变换渲染整车及 7 组候选节点。局部图以淡色显示周边模型，绿色显示选中的节点后代。这种强调方式会将选中件显示在前景，主要用于辨认数据绑定。

| 检查内容 | 结果 |
|---|---|
| 轴、双轮、毂、辐、牙、軎、辖 | 逐组检查了网格视图，现有节点映射的部件类别与图形相符。历史归属及材质仍保留候选状态。 |
| 轴端件与资料图 | 教学模型使用简化几何，缺少 M1：201-1 对照图可见的云纹或兽面细节。该差异只能说明模型与该对照图的表现不同，六号车对应部件的装饰仍待查证。 |
| 轮牙分段 | 左右轮牙的组各有三个网格。六号车原始证据尚不足，分段保持为模型设定。 |
| “部件拼装”片段 | 毂、辐、牙等节点存在变化的 `scale` 轨道，画面包含部件缩放效果。展陈应将其解释为动画处理。 |
| “行进与轮轴运动”片段 | 根节点 `708` 的起止平移不同。直接重复播放原始轨道会发生位置跳变。 |

本轮复核范围为静态几何、节点绑定及上述动画轨道。现有视图用静态渲染，后续实时 3D 可用同一映射选择节点。完整几何复原需继续对照六号车的原始发掘记录。

## 本地复现

检查页运行使用 Python 标准库。生成图片另需 Python Pillow、NumPy 和 Poppler `pdftoppm`。在仓库根目录运行以下 PowerShell 命令，其中两个原件位于仓库父目录。

```powershell
$pdf = (Get-ChildItem .. -File -Filter 'obP5c*.pdf')[0]
$model = (Get-ChildItem .. -File -Filter '*动画模型.glb')[0]
$data = 'data/candidates/wheel-axle.v0.3.json'
$manifest = 'data/sources/fusion-media.v0.1.json'
$images = 'assets/references/local/fusion'
python scripts/extract_source_clips.py --pdf $pdf.FullName --manifest $manifest --output $images
python scripts/render_model_views.py --model $model.FullName --manifest $manifest --dataset $data --output $images
python -m chuchariot --dataset $data validate --model-report data/scenes/model-inspection.json
python -m chuchariot --dataset $data preview --port 8767 --resource-dir .. --resource-dir assets/references/local --media-manifest $manifest --media-dir $images
```

启动命令成功后，在同一台电脑的浏览器打开 `http://127.0.0.1:8767/`。在终端按 `Ctrl+C` 停止。第三批具备独立数据集 ID，在导入时用独立输出路径 `data/local/wheel-axle.v0.3.json`。

第三批新增 5 条扩展页拾遗与 4 条媒体索引候选。独立子 Agent 对应原页预审了这 9 条，引文和图像观察修正已记录。[拾遗和复核摘要](../data/run-summaries/2026-11-19-fusion-gleaning.json)
