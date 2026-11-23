# 队友接入说明 · 知识图谱v0.9

当前候选 `teacher-pdf.v0.9.json` 配 `ontology.v0.6.json`、`fusion-media.v0.9.json`，契约仍为0.2.0。共120实体、395条待审核事实、218条实体关系、54项尺寸、62段证据和7组未改的候选映射。

在仓库根目录使用Python 3.11+，直接读取已提交文件：

```powershell
python -m chuchariot --dataset data/candidates/teacher-pdf.v0.9.json --ontology data/ontology/ontology.v0.6.json validate
python -m chuchariot --dataset data/candidates/teacher-pdf.v0.9.json --ontology data/ontology/ontology.v0.6.json preview --port 8769 --media-manifest data/sources/fusion-media.v0.9.json
```

打开 `http://127.0.0.1:8769/?view=map`。127.0.0.1指运行程序的本机；原件和图片未准备时仍可查看知识，资源入口显示不可用。媒体和PDF配置方法见[融合说明](fusion.md)。不指定数据和本体的CLI仍读取旧样例。

## 路径查询

```powershell
python -m chuchariot --dataset data/candidates/teacher-pdf.v0.9.json --ontology data/ontology/ontology.v0.6.json connection-path type:001 type:body --include-pending
```

```python
from chuchariot.knowledge import KnowledgeStore

store = KnowledgeStore.load(
    "data/candidates/teacher-pdf.v0.9.json",
    "data/ontology/ontology.v0.6.json",
)
path = store.connection_path("type:001", "type:body", include_pending=True)
for hop in path["hops"]:
    print(hop["from"]["label"], hop["to"]["label"],
          hop["evidence_basis"]["label"], hop["fact"]["origin"])
```

对应“车轮→毂→车轴→伏兔→舆”。每跳返回fact、from/to实体、connection、evidence_basis、metadata_facts、evidence；证据含来源与页码。默认仅查确认内容，本批found为false；候选模式需明确标记。查询是有向、最多1—16跳的最短教学导航，不证明连续物理连接或装配顺序。

HTTP：`GET /api/connection-path?from=type:001&to=type:body&review=1`。全量快照仍为 `GET /api/preview?review=1`。详细错误和字段见[接口说明](api.md)。

## 三维对接重点

- 分别用 `type:futu`（伏兔）、`type:body-floor`（舆底）、`regiontype:floor-support`（教学支承区）组织讲解；实际高亮须另行核验模型节点，当前三者没有新增映射。
- 马勒 `type:horse-bridle`、衔 `type:bit`、镳 `type:cheekpiece`、辔 `type:bridle`、缰 `type:reins`、靷 `type:trace` 保持独立。绳带集合 `type:rope-family`只是教学功能集合。
- 四个 `Subsystem`是教师栏目；六个地图分区仍是浏览布局。`IN_SUBSYSTEM`、`TEACHING_GROUPS_TYPE`和`SCHEMATIC_NEXT`不能改称已确认实物组成。
- 54项尺寸仍是带来源的属性；不要生成尺寸节点，也不要把对照标本尺寸归给六号车。基础字段及属性读取见[数据规范](data-model.md)。
- v0.8、v0.9完整保留旧基线；导入时只选一个版本，不能叠加重复。v0.8应配本体0.5，v0.9配0.6。旧构建脚本只生成其对应历史版本。

本轮差异、原件核对范围和待核问题见[同步检查](teammate-sync-v0.9.md)。原PDF、GLB、图片缓存不在Git中；仍需从组内渠道准备。
