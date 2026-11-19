# 楚国战车专题交互导览系统

面向博物馆专题介绍场景，以可追溯的知识图谱组织楚国战车资料，规划结合三维模型和专题讲解提供交互导览。AI 问答是规划中的加分项。

**当前交付是 P1 知识层候选与临时检查工具。** 页面在本机只读运行，用于组内开发测试和证据复核。正式展陈页面、实时三维浏览与生产后端属于后续阶段。

第一次接手请从[项目文档索引](docs/index.md)开始。那里汇总当前状态、数据批次、验证结果、资料位置和交接任务。

## 从仓库复现

在包含本 README 的目录运行，要求 Python 3.11+。知识查询、校验、临时页面及测试均可在纯 Python 标准库环境运行。

```powershell
python -m chuchariot --dataset data/candidates/wheel-axle.v0.3.json validate --model-report data/scenes/model-inspection.json
python -m chuchariot --dataset data/candidates/wheel-axle.v0.3.json relations type:001 --include-pending
python -X utf8 -m unittest discover -s tests -v
```

本批预期为 **17 个实体、28 条待审核事实、22 段证据、7 组候选模型映射**，共 34 项测试。不指定 `--dataset` 的 CLI 继续读取初版样例。

## 启动临时检查页

```powershell
python -m chuchariot --dataset data/candidates/wheel-axle.v0.3.json preview --port 8767 --media-manifest data/sources/fusion-media.v0.1.json
```

浏览器访问 `http://127.0.0.1:8767/`，在运行命令的终端按 `Ctrl+C` 停止。该地址属于运行服务的电脑。候选检查模式可查文字、关系、证据位置和媒体索引。切换到已确认视图时，当前正式确认数为零。

如需打开原 PDF 或查看从原件生成的图片，请按[来源与资源登记](docs/sources.md)准备本地资料，再执行[融合检查复现命令](docs/fusion.md#本地复现)。从 GitHub 获取的版本包含索引和生成脚本，原件与缓存由组内渠道另行准备。

## 开发交接

小组按[软件计划设计书](docs/software-plan.md)串行接力。接手后记录收到的提交号，按[交接记录](docs/handover.md)复现当前批次，完成后同步更新[数据规范](docs/data-model.md)、[覆盖与待核问题](docs/coverage.md)和[进度记录](docs/progress.md)。
