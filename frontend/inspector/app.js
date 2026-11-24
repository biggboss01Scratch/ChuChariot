"use strict";

const $ = (selector) => document.querySelector(selector);
const GRAPH_WIDTH = 1180;
const pageOptions = new URLSearchParams(window.location.search);
const state = { data: null, selected: pageOptions.get("entity") || "type:001", review: true, tab: "detail", query: "", kind: "", neighbors: pageOptions.get("neighbors") === "1", expanded: pageOptions.get("view") === "map", highlight: false, selectedFact: null, zoom: 1, center: { x: GRAPH_WIDTH / 2, y: 410 }, requestVersion: 0, positions: new Map(), graphHeight: 820, graphWidth: GRAPH_WIDTH, graphGroups: [], layoutKey: null, regionByEntity: new Map(), routes: new Map() };
Object.assign(state, { audience: pageOptions.get("audience") === "internal" ? "internal" : "public", relationGroups: null, hideIsolated: pageOptions.get("audience") !== "internal" });
const kinds = { ComponentType: "部件类别", Chariot: "研究对象", Component: "具体部件", ReferenceSpecimen: "对照标本", Measurement: "尺寸记录", Material: "材质", PreservationFeature: "保存特征", SurfaceFinish: "表面髹饰", DecorationMotif: "纹饰图案", ModelVersion: "模型版本", Connection: "连接记录", Pose: "位姿记录", AssemblyStep: "演示步骤" };
const relationNames = { HAS_PART: "包含部件", INSTANCE_OF: "属于类别", HAS_MEASUREMENT: "具有尺寸", HAS_DIMENSION: "尺寸或距离", HAS_MATERIAL: "材质为", HAS_PRESERVED_FEATURE: "残存特征", HAS_SURFACE_FINISH: "表面髹饰", HAS_DECORATION_MOTIF: "纹饰为", SUBCLASS_OF: "属于父类", DESCRIPTION: "资料描述", PARTICIPATES_IN_CONNECTION: "参与连接", HAS_POSE: "具有位姿", INVOLVES_COMPONENT: "涉及部件", DEPENDS_ON: "依赖步骤" };
const shortRelations = { HAS_PART: "组成", INSTANCE_OF: "归类", HAS_MEASUREMENT: "尺寸", HAS_MATERIAL: "材质", HAS_PRESERVED_FEATURE: "保存特征", HAS_SURFACE_FINISH: "髹饰", HAS_DECORATION_MOTIF: "纹饰", SUBCLASS_OF: "类别", DESCRIPTION: "描述" };
const origins = { documented: "资料记载", inferred: "推断解释", hypothesis: "复原假设" };
const knowledgeBases = { modern_reconstruction_observation: "现代复原实验记录", modern_reconstruction_inference: "现代复原推测" };
const statusNames = { pending: "待审核", confirmed: "已确认", disputed: "有争议" };
const symbols = { ComponentType: "件", ReferenceSpecimen: "标", Measurement: "尺", Material: "材", PreservationFeature: "存", SurfaceFinish: "饰", DecorationMotif: "纹", ModelVersion: "模", Chariot: "车" };
Object.assign(kinds, { ReferenceRecord: "来源记录", HarnessRole: "系驾角色", ComponentRegion: "描述区域" });
Object.assign(symbols, { ReferenceRecord: "录", HarnessRole: "驾", ComponentRegion: "区" });
Object.assign(relationNames, { HAS_REGION: "包含描述区域" });
Object.assign(shortRelations, { HAS_REGION: "区域" });
Object.assign(kinds, { Subsystem: "教师栏目/教学分组", StructuralRegionType: "部位或特征类别", EvidenceBasisClass: "路径依据类别", TermSense: "语境词义" });
Object.assign(symbols, { Subsystem: "组", StructuralRegionType: "区", EvidenceBasisClass: "据", Connection: "链", TermSense: "词" });
Object.assign(relationNames, { USES_TERM: "来源原称", TERM_DENOTES: "本语境指称", TERM_RELATED_TO: "词义涉及" });
Object.assign(shortRelations, { USES_TERM: "原称", TERM_DENOTES: "语境指称", TERM_RELATED_TO: "词义涉及" });
Object.assign(relationNames, { IN_SUBSYSTEM: "归入教学分组", SCHEMATIC_NEXT: "教学路径下一节点", CONNECTION_FROM: "路径起点", CONNECTION_TO: "路径终点", HAS_EVIDENCE_BASIS: "路径依据类别", SCHEMATIC_HAS_REGION: "教学结构区域", REGION_NEAR_COMPONENT: "教学区域邻近", TEACHING_GROUPS_TYPE: "教学功能分组", SCHEMATIC_ASSEMBLY_WITH: "示意装配关联" });
Object.assign(shortRelations, { IN_SUBSYSTEM: "教学分组", SCHEMATIC_NEXT: "教学路径", CONNECTION_FROM: "起点", CONNECTION_TO: "终点", HAS_EVIDENCE_BASIS: "依据类别", SCHEMATIC_HAS_REGION: "示意区域", REGION_NEAR_COMPONENT: "示意邻近", TEACHING_GROUPS_TYPE: "功能分组", SCHEMATIC_ASSEMBLY_WITH: "示意装配" });
Object.assign(relationNames, { REFERS_TO_TYPE: "记录涉及类别", DEPICTS: "图示呈现", TENON_JOINT_WITH: "榫卯相接", HAS_ASSOCIATED_COMPONENT: "所配部件", HAS_SHAPE: "形态与结构", HAS_PROCESSING: "加工记载", HAS_POSITION: "位置记载", HAS_FIND_POSITION: "出土位置", HAS_RECORDED_QUANTITY: "原文数量", HAS_MASS_RECORD: "原文重量", HAS_ORIGINAL_IDENTIFIERS: "原文标识范围", HAS_DIAGRAM_LABELS: "图内标注", HAS_PATTERN_DETAIL: "纹饰部位与细节" });
Object.assign(shortRelations, { REFERS_TO_TYPE: "类别", DEPICTS: "图示", TENON_JOINT_WITH: "榫卯", HAS_ASSOCIATED_COMPONENT: "所配" });
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const getEntity = (id) => state.data.entities.find((e) => e.id === id);
const relatedFacts = (id) => state.data.facts.filter((f) => f.subject_id === id || f.object_id === id);
const badge = (status) => `<span class="badge ${escapeHtml(status)}">${escapeHtml(statusNames[status] || status)}</span>`;
const entityLink = (id) => `<button class="entity-link" data-entity="${escapeHtml(id)}">${escapeHtml(getEntity(id)?.label || id)}</button>`;

function formatEvidenceTime(seconds) {
  const total = Math.floor(seconds);
  return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}

function evidenceLocation(evidence) {
  if (Number.isFinite(evidence.start_seconds)) return `视频 ${formatEvidenceTime(evidence.start_seconds)}—${formatEvidenceTime(evidence.end_seconds)}`;
  if (Number.isInteger(evidence.start_line)) return `文本 · ${evidence.locator}`;
  return Number.isInteger(evidence.pdf_page) ? `PDF 第 ${evidence.pdf_page} 页` : `词典条目 · ${evidence.locator}`;
}

function factOrigin(fact) {
  return [origins[fact.origin] || fact.origin, knowledgeBases[fact.knowledge_basis]].filter(Boolean).join(" · ");
}

function factRelationName(fact, short = false) {
  if (state.audience === "public" && fact.predicate === "REFERS_TO_TYPE") return "复原案例涉及";
  return (short ? shortRelations[fact.predicate] : null) || relationNames[fact.predicate] || fact.predicate;
}

function evidenceSourceUrl(source, evidence) {
  if (source.format === "md") return source.url;
  const anchor = source.format === "mp4" ? `t=${evidence.start_seconds},${evidence.end_seconds}` : `page=${evidence.pdf_page}`;
  if (source.content_url) return `${source.content_url}#${anchor}`;
  return `/api/sources/${encodeURIComponent(source.id)}#${anchor}`;
}

let operatorToken = "";
async function databaseHeaders() {
  if (!window.CHUCHARIOT_DATABASE_API || state.audience !== "internal") return {};
  if (!operatorToken) {
    const dialog = $("#operator-login"), input = $("#operator-token");
    operatorToken = await new Promise((resolve) => {
      dialog.addEventListener("close", () => {
        resolve(dialog.returnValue === "login" ? input.value.trim() : "");
        input.value = "";
      }, { once: true });
      dialog.showModal();
    });
  }
  if (!operatorToken) throw new Error("内部访问需要操作员凭据");
  return { Authorization: `Bearer ${operatorToken}` };
}

async function loadData() {
  const requestVersion = ++state.requestVersion;
  $("#reload-button").disabled = true;
  $("#workspace").setAttribute("aria-busy", "true");
  if (window.CHUCHARIOT_DATABASE_API) $("#workspace").inert = true;
  $("#error-box").hidden = true;
  try {
    const database = window.CHUCHARIOT_DATABASE_API;
    const url = database ? `/api/v1/${state.audience === "internal" ? "internal/" : ""}inspector?confirmed=${!state.review}`
      : `/api/preview?review=${state.review ? "1" : "0"}&audience=${state.audience}`;
    const response = await fetch(url, { cache: "no-store", headers: await databaseHeaders() });
    const data = await response.json();
    if (requestVersion !== state.requestVersion) return;
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) operatorToken = "";
      throw new Error(data.error?.message || data.error || "数据读取失败");
    }
    if (state.audience === "public" && data.presentation?.audience !== "public") throw new Error("当前服务尚未支持公众筛选，请重启新版知识检查服务");
    state.data = data;
    if (database) {
      state.review = data.meta.review_mode;
      $("#operator-logout").hidden = state.audience !== "internal";
    }
    if (!getEntity(state.selected)) state.selected = data.entities[0]?.id || null;
    if (state.audience === "public" && state.tab === "mappings") state.tab = "detail";
    if (!data.entities.some((entity) => entity.kind === state.kind)) state.kind = "";
    renderOverview();
    renderRelationFilters();
    renderList();
    renderGraph();
    renderDetail();
    $("#load-status").textContent = `${database ? `Neo4j · ${data.meta.graph_revision}` : "已读取本地数据"} · ${new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}`;
  } catch (error) {
    if (requestVersion !== state.requestVersion) return;
    $("#error-box").textContent = `无法读取知识数据：${error.message}。请确认本地预览服务正在运行，并检查终端中的校验结果。`;
    $("#error-box").hidden = false;
    $("#load-status").textContent = "读取失败";
  } finally {
    if (requestVersion === state.requestVersion) {
      $("#reload-button").disabled = false;
      $("#workspace").setAttribute("aria-busy", "false");
      if (window.CHUCHARIOT_DATABASE_API) $("#workspace").inert = !state.data;
    }
  }
}

function renderOverview() {
  const { stats, meta, entities } = state.data;
  for (const name of ["entities", "confirmed", "pending", "evidence"]) $(`#stat-${name}`).textContent = stats[name];
  $("#dataset-id").textContent = meta.dataset_id;
  $("#dataset-version").textContent = `数据格式 ${meta.schema_version} · ${meta.validation === "passed" ? "结构校验通过" : "待检查"}`;
  $("#pending-note").textContent = stats.dimension_properties
    ? `含${stats.dimension_properties}项尺寸属性 · 尚待组员复核` : "已整理，尚待组员复核";
  $("#dimension-legend").hidden = !entities.some((entity) => entity.kind === "Measurement");
  $("#review-mode").classList.toggle("active", state.review);
  $("#confirmed-mode").classList.toggle("active", !state.review);
  $("#review-mode").setAttribute("aria-pressed", String(state.review));
  $("#confirmed-mode").setAttribute("aria-pressed", String(!state.review));
  $("#mode-description").textContent = state.review
    ? `当前显示候选内容。${stats.pending} 条事实尚待组员复核，不能作为已证实结论。`
    : `仅展示已确认事实；当前 ${stats.confirmed} 条。实体目录保留，未确认尺寸隐藏。`;
  const kindsPresent = [...new Set(entities.map((e) => e.kind))];
  $("#kind-filter").innerHTML = '<option value="">全部类型</option>' + kindsPresent.map((kind) => `<option value="${escapeHtml(kind)}">${escapeHtml(kinds[kind] || kind)}</option>`).join("");
  $("#kind-filter").value = state.kind;
  for (const audience of ["public", "internal"]) {
    $(`#${audience}-view`).classList.toggle("active", state.audience === audience);
    $(`#${audience}-view`).setAttribute("aria-pressed", String(state.audience === audience));
  }
  $("#audience-description").textContent = state.audience === "public"
    ? "公众图谱预览：隐藏管理、分类、栏目和路径元数据；来源、推测与审核状态仍保留。"
    : "内部完整核对：可查看所有实体、分类、来源词义、教学栏目和路径依据。";
  $("#tab-mappings").hidden = state.audience === "public";
}

function filteredGraphFacts(data, selectedGroups) {
  if (!data.presentation || selectedGroups === null) return data.facts;
  const allowed = new Set(data.presentation.groups.filter((group) => selectedGroups.has(group.id)).flatMap((group) => group.fact_ids));
  return data.facts.filter((fact) => !fact.object_id || allowed.has(fact.id));
}

function renderRelationFilters() {
  const groups = (state.data.presentation?.groups || []).filter((group) => group.fact_ids.length);
  if (state.relationGroups === null) state.relationGroups = new Set(groups.map((group) => group.id));
  $("#relation-filters").innerHTML = groups.length ? groups.map((group) => `<label><input type="checkbox" data-relation-group="${escapeHtml(group.id)}" ${state.relationGroups.has(group.id) ? "checked" : ""}>${escapeHtml(group.label)} <small>${group.fact_ids.length}</small></label>`).join("") : '<span>当前审核范围暂无关系</span>';
  $("#hide-isolated").checked = state.hideIsolated;
}

function setAudience(audience) {
  if (window.CHUCHARIOT_DATABASE_API && audience !== state.audience) {
    state.data = null;
    for (const selector of ["#entity-list", "#graph", "#minimap", "#detail-content"]) $(selector).replaceChildren();
    $("#detail-name").textContent = "正在加载…";
    $("#detail-id").textContent = "";
    $("#workspace").inert = true;
  }
  state.audience = audience;
  state.relationGroups = null;
  state.hideIsolated = audience === "public";
  state.selectedFact = null;
  state.layoutKey = null;
  const url = new URL(window.location.href);
  url.searchParams.set("audience", audience);
  window.history.replaceState(null, "", url);
  loadData();
}

function matchedEntities() {
  const query = state.query.trim().toLocaleLowerCase();
  const order = { ComponentType: 0, Chariot: 1, Component: 2, ReferenceSpecimen: 3, Measurement: 4, ModelVersion: 5 };
  return state.data.entities.filter((e) => (!state.kind || e.kind === state.kind) &&
    (!query || [e.id, e.label, ...e.aliases].some((s) => s.toLocaleLowerCase().includes(query))))
    .sort((a, b) => (order[a.kind] ?? 9) - (order[b.kind] ?? 9) || a.id.localeCompare(b.id));
}

function renderList() {
  const entities = matchedEntities();
  $("#entity-count").textContent = `${entities.length} / ${state.data.entities.length}`;
  $("#entity-list").innerHTML = entities.length ? entities.map((e) => `<button class="entity-item ${e.id === state.selected ? "active" : ""}" data-entity="${escapeHtml(e.id)}" data-kind="${escapeHtml(e.kind)}" aria-pressed="${e.id === state.selected}"><span class="entity-symbol" aria-hidden="true">${escapeHtml(symbols[e.kind] || "件")}</span><span class="entity-caption"><strong>${escapeHtml(e.label)}</strong><small>${escapeHtml(kinds[e.kind] || e.kind)} · ${escapeHtml(e.id)}</small></span></button>`).join("") : '<p class="no-results">没有匹配的实体，试试名称、别名或 ID。</p>';
}

function selectEntity(id) {
  if (!getEntity(id)) return;
  state.selected = id;
  state.highlight = true;
  state.selectedFact = null;
  state.tab = "detail";
  renderList();
  renderGraph();
  renderDetail();
  $("#detail-content").scrollTop = 0;
  if (state.expanded) document.body.classList.add("map-detail-open");
  else if (window.matchMedia("(max-width: 1180px)").matches) $(".detail-panel").scrollIntoView({ block: "start" });
}

// Display regions organize the map; they never add semantic edges to the data.
function atlasLayout(entities, facts, regionHints = {}) {
  const themes = [
    { key: "wheel", label: "轮系", subtitle: "轮 · 牙 · 辐 · 毂", color: "#408979", terms: ["车轮", "毂", "辐", "牙", "股", "骹", "篆", "车轮附加圆木条", "捆扎皮条"] },
    { key: "traction", label: "牵引与车体", subtitle: "轭 · 靷 · 衡 · 辀及其标本", color: "#ac8142", terms: ["轭", "靷", "衡", "轙", "骨衡帽", "辀", "辀首", "舆", "伏兔", "围栏", "舆底", "舆底支承位置（教学区域）"] },
    { key: "axle", label: "轴与軎辖", subtitle: "车轴 · 车軎 · 辖及来源记录", color: "#587faa", terms: ["车轴", "軎", "辖"] },
    { key: "harness", label: "马具与系驾", subtitle: "衔 · 镳 · 缰辔 · 系驾角色", color: "#9a709e", terms: ["衔", "镳", "辔", "节约", "缰", "轙环", "游环", "马勒（勒）", "绳索与带具（教学功能集合）"] },
    { key: "shared", label: "材质与髹饰", subtitle: "共享材料 · 保存状态 · 纹饰", color: "#75884f", terms: [] },
    { key: "reference", label: "图示与资料目录", subtitle: "复原与比较图 · 模型 · 待补充类别", color: "#85838b", terms: [] },
  ];
  const byId = new Map(entities.map((entity) => [entity.id, entity]));
  const categories = new Map(), assignment = new Map();
  for (const fact of facts) if (["INSTANCE_OF", "REFERS_TO_TYPE"].includes(fact.predicate)) categories.set(fact.subject_id, fact.object_id);
  function region(id, visiting = new Set()) {
    if (assignment.has(id)) return assignment.get(id);
    const entity = byId.get(id);
    if (!entity || visiting.has(id)) return "reference";
    visiting.add(id);
    let key;
    if (themes.some((theme) => theme.key === regionHints[id])) key = regionHints[id];
    else if (["Material", "PreservationFeature", "SurfaceFinish", "DecorationMotif"].includes(entity.kind)) key = "shared";
    else if (entity.kind === "HarnessRole") key = "harness";
    else if (entity.scope_id) key = region(entity.scope_id, visiting);
    else if (["Chariot", "ModelVersion"].includes(entity.kind) || /图|复原/.test(entity.label)) key = "reference";
    else if (categories.has(id)) key = region(categories.get(id), visiting);
    else key = themes.find((theme) => theme.terms.includes(entity.label))?.key || "reference";
    assignment.set(id, key);
    return key;
  }
  entities.forEach((entity) => region(entity.id));
  const positions = new Map(), groups = [];
  const rank = { ComponentType: 0, StructuralRegionType: 0, ReferenceSpecimen: 1, Component: 2, ComponentRegion: 2, ReferenceRecord: 3, TermSense: 3, Measurement: 4 };
  const tileWidth = 1210, gap = 180;
  let rowY = 60;
  for (let row = 0; row < 2; row++) {
    const rowGroups = [];
    for (let column = 0; column < 3; column++) {
      const theme = themes[row * 3 + column];
      const members = entities.filter((entity) => assignment.get(entity.id) === theme.key)
        .sort((a, b) => (rank[a.kind] ?? 5) - (rank[b.kind] ?? 5) || a.id.localeCompare(b.id));
      if (!members.length) continue;
      const slots = members.map((_, index) => [130 + index % 6 * 190, 190 + Math.floor(index / 6) * 120]);
      const indices = new Map(members.map((entity, index) => [entity.id, index]));
      const edges = facts.filter((fact) => indices.has(fact.subject_id) && indices.has(fact.object_id))
        .map((fact) => ({ a: indices.get(fact.subject_id), b: indices.get(fact.object_id),
          weight: ["HAS_MEASUREMENT", "HAS_PART", "HAS_ASSOCIATED_COMPONENT"].includes(fact.predicate) ? 3 : 1 }));
      const order = members.map((_, index) => index);
      // Minimize weighted link length on a fixed lattice, preserving empty space
      // between every pair of node boxes and deterministic positions on selection.
      const incident = members.map((_, index) => edges.filter((edge) => edge.a === index || edge.b === index));
      function energy(edge) {
        const a = slots[order[edge.a]], b = slots[order[edge.b]];
        return edge.weight * ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2);
      }
      const edgePairs = [];
      for (let i = 0; i < edges.length; i++) for (let j = i + 1; j < edges.length; j++) {
        const a = edges[i], b = edges[j];
        if (a.a !== b.a && a.a !== b.b && a.b !== b.a && a.b !== b.b) edgePairs.push([a, b]);
      }
      function crossing(pair) {
        const a = slots[order[pair[0].a]], b = slots[order[pair[0].b]], c = slots[order[pair[1].a]], d = slots[order[pair[1].b]];
        const turn = (p, q, r) => (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]);
        return turn(a, b, c) * turn(a, b, d) < 0 && turn(c, d, a) * turn(c, d, b) < 0 ? 200000 : 0;
      }
      for (let pass = 0; pass < 12; pass++) {
        let improved = false;
        for (let a = 0; a < members.length; a++) for (let b = a + 1; b < members.length; b++) {
          const affected = [...new Set([...incident[a], ...incident[b]])];
          const changed = new Set(affected), pairs = edgePairs.filter((pair) => changed.has(pair[0]) || changed.has(pair[1]));
          const cost = () => affected.reduce((sum, edge) => sum + energy(edge), 0) + pairs.reduce((sum, pair) => sum + crossing(pair), 0);
          const before = cost();
          [order[a], order[b]] = [order[b], order[a]];
          const after = cost();
          if (after + 1 < before) improved = true;
          else [order[a], order[b]] = [order[b], order[a]];
        }
        if (!improved) break;
      }
      const x = 60 + column * (tileWidth + gap), height = Math.ceil(members.length / 6) * 120 + 180;
      members.forEach((entity, index) => positions.set(entity.id, [x + slots[order[index]][0], rowY + slots[order[index]][1]]));
      rowGroups.push({ ...theme, x, y: rowY, width: tileWidth, height, ids: members.map((entity) => entity.id) });
    }
    groups.push(...rowGroups);
    rowY += Math.max(0, ...rowGroups.map((group) => group.height)) + gap;
  }
  return { positions, groups, regionByEntity: assignment, width: 60 + 3 * (tileWidth + gap) - gap + 60, height: rowY - gap + 60 };
}

function atlasRoutes(entities, facts, positions) {
  const routes = new Map();
  const boxes = entities.map((entity) => ({ id: entity.id, point: positions.get(entity.id) }));
  for (const fact of facts) {
    const a = positions.get(fact.subject_id), b = positions.get(fact.object_id);
    if (!a || !b) continue;
    const dx = b[0] - a[0], dy = b[1] - a[1], length = Math.hypot(dx, dy) || 1;
    let best;
    for (const bend of [0, 55, -55, 120, -120, 220, -220, 380, -380]) {
      const c1 = [a[0] + dx / 3 - dy / length * bend, a[1] + dy / 3 + dx / length * bend];
      const c2 = [a[0] + dx * 2 / 3 - dy / length * bend, a[1] + dy * 2 / 3 + dx / length * bend];
      let hits = 0;
      for (let i = 1; i < 24; i++) {
        const t = i / 24, u = 1 - t;
        const x = u ** 3 * a[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * b[0];
        const y = u ** 3 * a[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * b[1];
        for (const box of boxes) if (box.id !== fact.subject_id && box.id !== fact.object_id && Math.abs(x - box.point[0]) < 86 && Math.abs(y - box.point[1]) < 42) hits++;
      }
      const score = hits * 10000 + Math.abs(bend);
      if (!best || score < best.score) best = { c1, c2, score };
      if (!score) break;
    }
    const fromTangent = [best.c1[0] - a[0], best.c1[1] - a[1]], toTangent = [best.c2[0] - b[0], best.c2[1] - b[1]];
    const start = Math.min(80 / (Math.abs(fromTangent[0]) || 1), 35 / (Math.abs(fromTangent[1]) || 1));
    const end = Math.min(84 / (Math.abs(toTangent[0]) || 1), 39 / (Math.abs(toTangent[1]) || 1));
    routes.set(fact.id, { d: `M ${a[0] + fromTangent[0] * start} ${a[1] + fromTangent[1] * start} C ${best.c1.join(" ")} ${best.c2.join(" ")} ${b[0] + toTangent[0] * end} ${b[1] + toTangent[1] * end}`,
      label: [0, 1].map((axis) => .125 * a[axis] + .375 * best.c1[axis] + .375 * best.c2[axis] + .125 * b[axis]) });
  }
  return routes;
}

function graphLayout(entities, facts, focusId = null) {
  if (focusId && entities.some((entity) => entity.id === focusId)) {
    const neighbors = entities.filter((entity) => entity.id !== focusId);
    const rows = Math.ceil(neighbors.length / 2);
    const height = Math.max(440, rows * 110 + 140);
    const positions = new Map([[focusId, [400, height / 2]]]);
    for (let side = 0; side < 2; side++) {
      const column = neighbors.filter((_, index) => index % 2 === side);
      column.forEach((entity, index) => positions.set(entity.id,
        [side ? 680 : 120, height / 2 + (index - (column.length - 1) / 2) * 110]));
    }
    return { positions, width: 800, height,
      groups: [{ x: 20, y: 20, width: 760, height: height - 40,
        ids: entities.map((entity) => entity.id), label: "当前实体直接关联" }] };
  }
  const adjacency = new Map(entities.map((entity) => [entity.id, new Set()]));
  for (const fact of facts) {
    if (!fact.object_id || fact.subject_id === fact.object_id || !adjacency.has(fact.subject_id) || !adjacency.has(fact.object_id)) continue;
    adjacency.get(fact.subject_id).add(fact.object_id);
    adjacency.get(fact.object_id).add(fact.subject_id);
  }
  const components = [], seen = new Set();
  for (const id of [...adjacency.keys()].sort()) {
    if (seen.has(id)) continue;
    const ids = [], queue = [id];
    seen.add(id);
    for (let i = 0; i < queue.length; i++) {
      const current = queue[i];
      ids.push(current);
      for (const next of [...adjacency.get(current)].sort()) if (!seen.has(next)) { seen.add(next); queue.push(next); }
    }
    components.push(ids);
  }

  function layoutComponent(ids) {
    const points = new Map();
    // Peeling leaves identifies a simple cycle. Shared attributes then form a
    // ring instead of drawing two crossing paths through their specimens.
    const degree = new Map(ids.map((id) => [id, adjacency.get(id).size]));
    const leaves = ids.filter((id) => degree.get(id) < 2), removed = new Set(leaves);
    for (let i = 0; i < leaves.length; i++) for (const next of adjacency.get(leaves[i])) {
      degree.set(next, degree.get(next) - 1);
      if (degree.get(next) === 1 && !removed.has(next)) { removed.add(next); leaves.push(next); }
    }
    const core = new Set(ids.filter((id) => !removed.has(id)));
    const simpleCycle = core.size > 2 && [...core].every((id) => [...adjacency.get(id)].filter((next) => core.has(next)).length === 2);

    function branch(root, blocked) {
      const children = new Map(), visited = new Set(blocked);
      visited.add(root);
      const queue = [root];
      for (let i = 0; i < queue.length; i++) {
        const id = queue[i], nextIds = [...adjacency.get(id)].filter((next) => !visited.has(next)).sort();
        children.set(id, nextIds);
        for (const next of nextIds) { visited.add(next); queue.push(next); }
      }
      const local = new Map();
      let leaf = 0;
      function place(id, depth) {
        const next = children.get(id);
        let y;
        if (!next.length) y = 90 * leaf++;
        else { for (const child of next) place(child, depth + 1); y = next.reduce((sum, child) => sum + local.get(child)[1], 0) / next.length; }
        local.set(id, [depth * 220, y]);
      }
      place(root, 0);
      const rootY = local.get(root)[1];
      return new Map([...local].map(([id, [x, y]]) => [id, [x, y - rootY]]));
    }

    if (simpleCycle) {
      const first = [...core].sort((a, b) => adjacency.get(b).size - adjacency.get(a).size || a.localeCompare(b))[0];
      const cycle = [first];
      let previous = null, current = first;
      do {
        const next = [...adjacency.get(current)].filter((id) => core.has(id) && id !== previous).sort().find((id) => id !== first || cycle.length === core.size);
        if (!next || next === first) break;
        cycle.push(next); previous = current; current = next;
      } while (cycle.length < core.size);
      const radius = Math.max(135, core.size * 32);
      for (let i = 0; i < cycle.length; i++) {
        const angle = Math.PI + i * 2 * Math.PI / cycle.length;
        const anchor = [radius * Math.cos(angle), radius * Math.sin(angle)];
        for (const [id, [x, y]] of branch(cycle[i], core)) {
          points.set(id, [anchor[0] + x * Math.cos(angle) - y * Math.sin(angle), anchor[1] + x * Math.sin(angle) + y * Math.cos(angle)]);
        }
      }
    } else {
      // Use a tree centre so long chains do not consume the whole canvas.
      function eccentricity(root) {
        const distances = new Map([[root, 0]]), queue = [root];
        for (let i = 0; i < queue.length; i++) for (const next of adjacency.get(queue[i])) if (!distances.has(next)) {
          distances.set(next, distances.get(queue[i]) + 1); queue.push(next);
        }
        return Math.max(...distances.values());
      }
      const centres = ids.map((id) => ({ id, distance: eccentricity(id) }));
      centres.sort((a, b) => a.distance - b.distance || adjacency.get(b.id).size - adjacency.get(a.id).size || a.id.localeCompare(b.id));
      for (const [id, point] of branch(centres[0].id, new Set())) points.set(id, point);
    }
    const xs = [...points.values()].map(([x]) => x), ys = [...points.values()].map(([, y]) => y);
    const left = Math.min(...xs) - 96, top = Math.min(...ys) - 78;
    const width = Math.max(...xs) - left + 96, height = Math.max(...ys) - top + 62;
    const types = entities.filter((entity) => ids.includes(entity.id) && entity.kind === "ComponentType")
      .sort((a, b) => adjacency.get(b.id).size - adjacency.get(a.id).size || a.id.localeCompare(b.id));
    const label = types.length ? types.slice(0, 2).map((entity) => entity.label).join(" · ")
      : entities.find((entity) => entity.id === ids[0]).label;
    return { ids, label, width, height, positions: new Map([...points].map(([id, [x, y]]) => [id, [x - left, y - top]])) };
  }

  const blocks = components.filter((ids) => ids.length > 1).sort((a, b) => b.length - a.length || a[0].localeCompare(b[0])).map(layoutComponent);
  const positions = new Map(), groups = [];
  let x = 20, y = 20, rowHeight = 0, maxWidth = GRAPH_WIDTH;
  for (const block of blocks) {
    if (x > 20 && x + block.width > GRAPH_WIDTH - 20) { x = 20; y += rowHeight + 24; rowHeight = 0; }
    for (const [id, [px, py]] of block.positions) positions.set(id, [x + px, y + py]);
    groups.push({ x, y, width: block.width, height: block.height, ids: block.ids, label: block.label });
    rowHeight = Math.max(rowHeight, block.height);
    maxWidth = Math.max(maxWidth, x + block.width + 20);
    x += block.width + 24;
  }
  y += rowHeight + 24;
  const isolated = components.filter((ids) => ids.length === 1).flat();
  if (isolated.length) {
    const columns = Math.max(1, Math.floor((GRAPH_WIDTH - 40) / 220));
    for (let i = 0; i < isolated.length; i++) positions.set(isolated[i], [130 + i % columns * 220, y + 78 + Math.floor(i / columns) * 100]);
    const height = Math.ceil(isolated.length / columns) * 100 + 40;
    groups.push({ x: 20, y, width: GRAPH_WIDTH - 40, height, ids: isolated, label: "独立目录记录" });
    y += height;
  }
  return { positions, groups, height: Math.max(820, y + 120), width: maxWidth };
}

function graphCaption(entity) {
  if (entity.kind === "Measurement") {
    if (!entity.measurement) return entity.label.replace(/^CH1：\d/, "");
    const m = entity.measurement;
    return `${m.quantity.replace("右轮", "")}${m.value ?? `${m.min}–${m.max}`}${m.unit}`;
  }
  if (entity.id === "object:001") return "九连墩六号车";
  if (entity.kind === "ModelVersion") return "教学模型";
  if (entity.kind === "ReferenceSpecimen") return entity.label.replace("轮标本", "轮").replace("轴标本", "轴").replace(" 车", " ");
  if (entity.kind === "Component") return entity.label.replace(" 残存漆骨帽", " ");
  if (entity.kind === "PreservationFeature") return entity.label.replace(/^残存/, "");
  return entity.label;
}

function graphLabelLines(text) {
  const lines = [];
  let line = "", length = 0;
  for (const char of text) {
    const width = /[\x00-\x7f]/.test(char) ? .55 : 1;
    if (length + width > 6 && line) { lines.push(line); line = ""; length = 0; }
    line += char; length += width;
  }
  if (line) lines.push(line);
  const dimension = text.match(/^(.+?)(\d[\d.–-]*(?:cm|mm|m))$/);
  if (lines.length > 1 && dimension) {
    const prefixWidth = [...dimension[1]].reduce((sum, char) => sum + (/[\x00-\x7f]/.test(char) ? .55 : 1), 0);
    return [prefixWidth > 6 ? lines[0].slice(0, -1) + "…" : dimension[1], dimension[2]];
  }
  return lines.length > 2 ? [lines[0], lines[1].slice(0, -1) + "…"] : lines;
}

function svgElement(tag, attributes = {}, text) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, String(value));
  if (text !== undefined) element.textContent = text;
  return element;
}

function resetGraphView() {
  state.zoom = 1;
  state.center = { x: state.graphWidth / 2, y: state.graphHeight / 2 };
}

function graphViewportSize(zoom = state.zoom, svg = $("#graph")) {
  const aspect = Math.max(1, svg.clientWidth) / Math.max(1, svg.clientHeight);
  const width = Math.max(state.graphWidth, state.graphHeight * aspect) / zoom;
  return { width, height: width / aspect };
}

function setGraphViewport(svg) {
  const { width, height } = graphViewportSize(state.zoom, svg);
  svg.setAttribute("viewBox", `${state.center.x - width / 2} ${state.center.y - height / 2} ${width} ${height}`);
  return { width, height };
}

function renderGraph() {
  if (!state.data) return;
  const svg = $("#graph");
  const { entities } = state.data;
  const facts = filteredGraphFacts(state.data, state.relationGroups);
  const connections = facts.filter((f) => f.object_id && (!state.neighbors || f.subject_id === state.selected || f.object_id === state.selected));
  const adjacent = new Set([state.selected]);
  for (const f of connections.filter((fact) => fact.subject_id === state.selected || fact.object_id === state.selected)) {
    adjacent.add(f.subject_id);
    if (f.object_id) adjacent.add(f.object_id);
  }
  const connected = new Set(connections.flatMap((fact) => [fact.subject_id, fact.object_id]));
  const visibleEntities = entities.filter((entity) => (!state.neighbors || adjacent.has(entity.id)) &&
    (!state.hideIsolated || connected.has(entity.id) || entity.id === state.selected));
  const layoutKey = JSON.stringify([state.data.meta.dataset_id, state.neighbors, visibleEntities.map((entity) => entity.id), connections.map((fact) => fact.id)]);
  if (layoutKey !== state.layoutKey) {
    const layout = state.neighbors ? graphLayout(visibleEntities, connections, state.selected) : atlasLayout(visibleEntities, connections, state.data.presentation?.regions);
    state.positions = layout.positions;
    state.graphGroups = layout.groups;
    state.graphWidth = layout.width;
    state.graphHeight = layout.height;
    state.regionByEntity = layout.regionByEntity || new Map();
    state.routes = state.neighbors ? new Map() : atlasRoutes(visibleEntities, connections, layout.positions);
    state.layoutKey = layoutKey;
    resetGraphView();
    renderMapNavigation();
  }
  syncGraphMode();
  const matches = new Set(matchedEntities().map((e) => e.id));
  const { width, height } = setGraphViewport(svg);
  const scale = Math.max(Math.min(svg.clientWidth / width, svg.clientHeight / height), 0.02);
  const labelSize = state.neighbors ? Math.min(24, Math.max(18, 12 / scale)) : 20;
  const highlighted = (fact) => (state.highlight || state.neighbors) && (fact.subject_id === state.selected || fact.object_id === state.selected);
  svg.replaceChildren();
  const defs = svgElement("defs");
  const marker = svgElement("marker", { id: "arrow-head", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" });
  marker.append(svgElement("path", { d: "M 1 1 L 9 5 L 1 9", fill: "none", stroke: "context-stroke", "stroke-width": 1.3 }));
  defs.append(marker); svg.append(defs);
  const groupLayer = svgElement("g"), edgeLayer = svgElement("g"), labelLayer = svgElement("g"), nodeLayer = svgElement("g");
  for (const group of state.graphGroups) {
    const headingSize = state.neighbors ? labelSize - 2 : Math.min(72, Math.max(28, 17 / scale));
    groupLayer.append(svgElement("rect", { x: group.x, y: group.y, width: group.width, height: group.height, rx: 24, class: "graph-cluster", ...(group.color ? { style: `fill:${group.color}0a;stroke:${group.color}45` } : {}) }));
    groupLayer.append(svgElement("text", { x: group.x + 28, y: group.y + (state.neighbors ? 29 : 76), class: "cluster-label", "font-size": headingSize, ...(group.color ? { style: `fill:${group.color}` } : {}) }, `${group.label} · ${group.ids.length}`));
    if (group.subtitle) groupLayer.append(svgElement("text", { x: group.x + 28, y: group.y + 119, class: "cluster-subtitle", "font-size": Math.min(42, Math.max(18, 11 / scale)) }, group.subtitle));
  }
  for (const fact of [...connections].sort((a, b) => Number(highlighted(a)) - Number(highlighted(b)))) {
    const from = state.positions.get(fact.subject_id), to = state.positions.get(fact.object_id);
    if (!from || !to) continue;
    const [dx, dy] = [to[0] - from[0], to[1] - from[1]];
    const start = Math.min(83 / (Math.abs(dx) || 1), 37 / (Math.abs(dy) || 1));
    const end = Math.min(88 / (Math.abs(dx) || 1), 42 / (Math.abs(dy) || 1));
    const related = highlighted(fact);
    const cross = !state.neighbors && state.regionByEntity.get(fact.subject_id) !== state.regionByEntity.get(fact.object_id);
    const route = state.routes.get(fact.id);
    const edge = svgElement(route ? "path" : "line", {
      ...(route ? { d: route.d } : { x1: from[0] + dx * start, y1: from[1] + dy * start, x2: to[0] - dx * end, y2: to[1] - dy * end }),
      class: `graph-edge origin-${fact.origin} ${related ? "related" : state.highlight ? "dimmed" : ""} ${cross ? "cross-region" : ""}`,
      "data-fact": fact.id, "marker-end": "url(#arrow-head)",
    });
    edge.append(svgElement("title", {}, `${getEntity(fact.subject_id).label} → ${factRelationName(fact)} → ${getEntity(fact.object_id).label} · ${factOrigin(fact)} · ${statusNames[fact.review_status]}`));
    edgeLayer.append(edge);
    if (related && scale >= .35) {
      const at = route?.label || [(from[0] + to[0]) / 2, (from[1] + to[1]) / 2];
      labelLayer.append(svgElement("text", { x: at[0], y: at[1] - 10, class: "edge-label", "font-size": labelSize - 3 }, factRelationName(fact, true)));
    }
  }
  for (const entity of visibleEntities) {
    const [x, y] = state.positions.get(entity.id);
    const active = entity.id === state.selected && (state.highlight || state.neighbors);
    const related = adjacent.has(entity.id) && (state.highlight || state.neighbors);
    const group = svgElement("g", { transform: `translate(${x} ${y})`, class: `node ${active ? "active" : related ? "related" : ""} ${!matches.has(entity.id) ? "search-muted" : ""}`,
      "data-entity": entity.id, "data-kind": entity.kind, "data-region": state.regionByEntity.get(entity.id) || "local", tabindex: 0, role: "button", "aria-label": `查看${entity.label}` });
    group.append(svgElement("title", {}, `${entity.label} · ${kinds[entity.kind] || entity.kind}`));
    group.append(svgElement("rect", { x: -77, y: -32, width: 154, height: 64, rx: 12 }));
    const lines = graphLabelLines(graphCaption(entity));
    const label = svgElement("text", { class: "node-label", "font-size": labelSize });
    lines.forEach((line, index) => label.append(svgElement("tspan", { x: 0, y: 7 + (index - (lines.length - 1) / 2) * (labelSize + 2) }, line)));
    group.append(label);
    nodeLayer.append(group);
  }
  svg.append(groupLayer, edgeLayer, labelLayer, nodeLayer);
  const shownIds = new Set(visibleEntities.map((entity) => entity.id));
  const dimensionCount = facts.filter((fact) => fact.predicate === "HAS_DIMENSION" && shownIds.has(fact.subject_id) && (!state.neighbors || fact.subject_id === state.selected)).length;
  $("#graph-summary").textContent = `${visibleEntities.length}${state.neighbors ? ` / ${entities.length}` : ""} 个实体 · ${connections.length} 条${state.review ? "候选" : "已确认"}关系${dimensionCount ? ` · ${dimensionCount}项尺寸属性` : ""}${state.neighbors ? " · 当前实体直接关联" : ` · ${state.graphGroups.length}个浏览分区`}`;
  $("#zoom-value").textContent = `${Math.round(state.zoom * 100)}%`;
  $("#relation-summary").textContent = `当前显示 ${connections.length} 条连线；筛选只改变绘图`;
  $("#graph-empty").hidden = connections.length > 0;
  $("#graph-empty strong").textContent = state.review ? "当前筛选没有关系" : "当前没有已确认的关系";
  $("#graph-empty p").textContent = state.review ? "可勾选关系类型或选择其他实体；属性与来源仍可查看。" : "可切换候选检查预览待复核知识，审核状态不会因此改变。";
  renderMinimap();
}

function syncGraphMode() {
  document.body.classList.toggle("map-expanded", state.expanded);
  $(".graph-panel").classList.toggle("atlas", !state.neighbors);
  $("#graph-title").textContent = state.neighbors ? "局部关联" : "楚车知识大地图";
  $("#map-mode").classList.toggle("active", !state.neighbors);
  $("#local-mode").classList.toggle("active", state.neighbors);
  $("#map-mode").setAttribute("aria-pressed", String(!state.neighbors));
  $("#local-mode").setAttribute("aria-pressed", String(state.neighbors));
  $("#map-expand").textContent = state.expanded ? "退出大屏" : "展开地图";
  $("#map-expand").setAttribute("aria-pressed", String(state.expanded));
  $("#map-regions").hidden = state.neighbors;
  $("#map-overview").hidden = state.neighbors;
  $("#map-searchbar").hidden = !state.expanded;
  $("#zoom-reset").textContent = state.neighbors ? "适应画布" : "全图总览";
  $("#map-clear").hidden = state.neighbors;
}

function renderMapNavigation() {
  $("#map-regions").innerHTML = '<button data-map-region="all">全图总览</button>' + state.graphGroups.filter((group) => group.key)
    .map((group) => `<button data-map-region="${group.key}" style="--region-color:${group.color}">${escapeHtml(group.label)}<span>${group.ids.length}</span></button>`).join("");
}

function renderMinimap() {
  const svg = $("#minimap");
  if (state.neighbors) return;
  svg.setAttribute("viewBox", `0 0 ${state.graphWidth} ${state.graphHeight}`);
  svg.replaceChildren();
  for (const group of state.graphGroups) svg.append(svgElement("rect", { x: group.x, y: group.y, width: group.width, height: group.height, rx: 30, fill: group.color + "25", stroke: group.color, "stroke-width": 12 }));
  for (const point of state.positions.values()) svg.append(svgElement("circle", { cx: point[0], cy: point[1], r: 14, fill: "#5f8173" }));
  const { width, height } = graphViewportSize();
  svg.append(svgElement("rect", { x: state.center.x - width / 2, y: state.center.y - height / 2, width, height, fill: "#20776110", stroke: "#207761", "stroke-width": 22, class: "map-viewport" }));
}

function focusMapBounds(bounds) {
  state.center = { x: bounds.x + bounds.width / 2, y: bounds.y + bounds.height / 2 };
  const base = graphViewportSize(1);
  state.zoom = Math.max(.5, Math.min(16, .87 * Math.min(base.width / bounds.width, base.height / bounds.height)));
  renderGraph();
}

function focusCurrentEntity() {
  const point = state.positions.get(state.selected);
  if (point) focusMapBounds({ x: point[0] - 440, y: point[1] - 310, width: 880, height: 620 });
}

function setGraphMode(neighbors) {
  state.neighbors = neighbors;
  state.layoutKey = null;
  renderGraph();
}

function locateMapSearch() {
  const query = $("#map-search").value.trim().toLocaleLowerCase();
  if (!query) return;
  const matches = state.data.entities.filter((entity) => [entity.id, entity.label, ...entity.aliases].some((value) => value.toLocaleLowerCase().includes(query)))
    .sort((a, b) => Number(b.label.toLocaleLowerCase() === query) - Number(a.label.toLocaleLowerCase() === query)
      || Number(a.kind === "Measurement") - Number(b.kind === "Measurement") || a.label.length - b.label.length || a.id.localeCompare(b.id));
  if (!matches.length) { $("#map-search-status").textContent = "没有匹配实体"; return; }
  const index = state.mapSearchIndex || 0, entity = matches[index % matches.length];
  state.mapSearchIndex = index + 1;
  $("#map-locate").textContent = matches.length > 1 ? "下一个" : "定位实体";
  selectEntity(entity.id);
  focusCurrentEntity();
  $("#map-search-status").textContent = `${index % matches.length + 1} / ${matches.length}：${entity.label}`;
}

function renderDetail() {
  const entity = getEntity(state.selected);
  if (!entity) { $("#detail-content").textContent = "当前数据集中没有实体。"; return; }
  $("#detail-kind").textContent = kinds[entity.kind] || entity.kind;
  $("#detail-name").textContent = entity.label;
  $("#detail-id").textContent = entity.id;
  const summary = entity.fact_review_summary;
  $("#detail-status").innerHTML = (summary.pending ? `<span class="badge pending">${summary.pending} 条待审核事实</span>` : "") +
    (summary.confirmed ? `<span class="badge confirmed">${summary.confirmed} 条已确认事实</span>` : "") +
    (summary.disputed ? `<span class="badge disputed">${summary.disputed} 条有争议事实</span>` : "") +
    (!summary.pending && !summary.confirmed && !summary.disputed ? '<span class="badge">仅目录记录</span>' : "");
  for (const button of document.querySelectorAll("[data-tab]")) {
    const active = button.dataset.tab === state.tab;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  }
  $("#detail-content").setAttribute("aria-labelledby", `tab-${state.tab}`);
  if (state.tab === "detail") renderKnowledge(entity);
  else if (state.tab === "evidence") renderEvidence(entity);
  else renderMappings(entity);
}

const propertyPredicates = new Set(["HAS_MEASUREMENT", "HAS_DIMENSION", "HAS_MATERIAL", "HAS_PRESERVED_FEATURE", "HAS_SURFACE_FINISH", "HAS_DECORATION_MOTIF"]);
const fieldNames = { id: "实体编号", kind: "实体类型", label: "名称", aliases: "别名", scope_id: "归属对象或语境记录", lexeme: "来源原词", source_id: "词义来源", note: "备注", resource_id: "资源编号", content_sha256: "文件 SHA-256", measurement: "尺寸记录", quantity: "测量项目", value: "记录值", unit: "单位", raw: "原始表达", approximate: "是否近似", min: "下限", max: "上限" };
const propertyNames = { HAS_MATERIAL: "材质", HAS_PRESERVED_FEATURE: "保存特征", HAS_SURFACE_FINISH: "表面髹饰", HAS_DECORATION_MOTIF: "纹饰" };

function renderEntityFields(entity) {
  function rows(record, prefix = "") {
    return Object.entries(record).map(([key, value]) => {
      if (key === "fact_review_summary" || key === "measurement_visibility") return "";
      const label = prefix + (fieldNames[key] || key);
      if (value && typeof value === "object" && !Array.isArray(value)) return rows(value, `${label} / `);
      let display;
      if (key === "scope_id") display = entityLink(value);
      else if (key === "source_id") display = escapeHtml(state.data.sources.find((source) => source.id === value)?.title || value);
      else if (key === "kind") display = escapeHtml(kinds[value] || value);
      else if (Array.isArray(value)) display = value.length ? value.map((item) => escapeHtml(typeof item === "object" ? JSON.stringify(item) : item)).join("、") : "无";
      else display = escapeHtml(value === true ? "是" : value === false ? "否" : value ?? "未填写");
      return `<div><dt>${escapeHtml(label)}</dt><dd>${display}</dd></div>`;
    }).join("");
  }
  return `<section class="entity-fields" aria-label="实体字段"><h3 class="section-label">实体字段</h3><dl class="key-values">${rows(entity)}</dl></section>`;
}

function isPropertyFact(fact, entityId) {
  return fact.subject_id === entityId && fact.predicate !== "DESCRIPTION" &&
    (propertyPredicates.has(fact.predicate) || !fact.object_id);
}

function measurementValue(measurement) {
  const value = measurement.value ?? `${measurement.min}–${measurement.max}`;
  return `${measurement.approximate ? "约 " : ""}${value} ${measurement.unit}`;
}

function renderProperties(entity, facts) {
  const properties = facts.filter((fact) => isPropertyFact(fact, entity.id));
  let content = `<section class="entity-properties" aria-label="属性与取值"><h3 class="section-label">属性与取值 · ${properties.length} 项</h3>`;
  if (!properties.length) {
    content += `<p class="property-empty">${state.review ? "当前尚未录入直接属性。" : "当前没有已确认的直接属性，待审核内容已隐藏。"}</p>`;
  } else {
    content += '<dl class="property-list">' + properties.map((fact) => {
      const target = fact.object_id ? getEntity(fact.object_id) : null;
      const measurement = fact.predicate === "HAS_DIMENSION" ? fact.value : fact.predicate === "HAS_MEASUREMENT" ? target?.measurement : null;
      const label = measurement?.quantity || propertyNames[fact.predicate] || relationNames[fact.predicate] || fact.predicate;
      const value = measurement ? escapeHtml(measurementValue(measurement))
        : fact.object_id ? entityLink(fact.object_id) : escapeHtml(fact.value);
      const references = [...new Set(fact.evidence_ids.map((id) => {
        const evidence = state.data.evidence.find((item) => item.id === id);
        return evidence ? evidenceLocation(evidence) : null;
      }).filter(Boolean))];
      return `<div class="property-row" data-property-fact="${escapeHtml(fact.id)}"><dt>${escapeHtml(label)}</dt><dd><div class="property-value">${value}</div><div class="property-meta">${badge(fact.review_status)}<span>${escapeHtml(factOrigin(fact))}</span></div>${measurement ? `<p class="property-raw">原始表达：${escapeHtml(measurement.raw)}</p>` : ""}<div class="property-proof"><span>${references.length ? escapeHtml(references.join("、")) : "暂无证据片段"}</span><button class="text-button" data-proof="${escapeHtml(fact.id)}">查看依据</button></div></dd></div>`;
    }).join("") + '</dl>';
  }
  if (entity.kind === "ComponentType") content += '<p class="property-scope">这里只显示该类别直接记录的属性。具体标本的尺寸、材质请从下方关联记录进入标本查看。</p>';
  if (entity.kind === "ComponentRegion") content += '<p class="property-scope">这是资料描述的局部区域，用于限定属性作用部位，不表示可拆卸零件。</p>';
  if (entity.kind === "StructuralRegionType") content += '<p class="property-scope">这是构件部位或形态特征的类别，不表示独立分件。具体尺寸请查看对照标本中的区域；部位也可单独高亮，三维对应仍需核对。</p>';
  if (entity.kind === "TermSense") content += '<p class="property-scope">这是特定来源或义项中的用词，不是一件额外的马具。请沿“本语境指称”查看规范概念；“词义涉及”不表示同义或整体部分关系。</p>';
  if (["Subsystem", "EvidenceBasisClass", "Connection"].includes(entity.kind)) content += '<p class="property-scope">这是教学分组或路径依据记录。各跳可来自不同标本或图示，不能当作同车实物连接、受力链或安装顺序；新增三维高亮仍需模型映射。</p>';
  return content + '</section>';
}

function renderFactCards(facts) {
  return facts.map((fact) => `<article class="fact-card"><div class="fact-meta"><code>${escapeHtml(fact.id)}</code>${badge(fact.review_status)}</div><p class="fact-statement">${entityLink(fact.subject_id)}<span class="relation-word">${escapeHtml(factRelationName(fact))}</span>${fact.object_id ? entityLink(fact.object_id) : escapeHtml(fact.value)}</p><div class="fact-origin">${escapeHtml(factOrigin(fact))} · ${fact.evidence_ids.length} 段证据</div>${fact.rationale ? `<p class="property-scope">推断或假设理由：${escapeHtml(fact.rationale)}</p>` : ""}<button class="text-button" data-proof="${escapeHtml(fact.id)}">查看事实依据</button></article>`).join("");
}

function renderKnowledge(entity) {
  const facts = relatedFacts(entity.id);
  let content = renderProperties(entity, facts);
  content += renderEntityFields(entity);
  if (entity.measurement) {
    const m = entity.measurement;
    content += `<div class="measurement-card"><p>${escapeHtml(m.quantity)}</p><strong>${escapeHtml(m.value ?? `${m.min}–${m.max}`)}</strong><span class="unit">${escapeHtml(m.unit)}</span><small>${m.approximate ? "原文近似值" : "保留资料记载值"} · ${state.review ? "候选尺寸，待复核" : "已按项目规则审核"}</small><small>原始表达：${escapeHtml(m.raw)}</small></div>`;
  } else if (entity.measurement_visibility) {
    content += '<div class="empty-state"><strong>未确认尺寸已隐藏</strong>切换“候选检查”可以查看候选数值及其来源。</div>';
  }
  content += renderMedia(entity);
  const descriptions = facts.filter((fact) => fact.subject_id === entity.id && fact.predicate === "DESCRIPTION");
  const relations = facts.filter((fact) => !isPropertyFact(fact, entity.id) && !descriptions.includes(fact));
  content += `<h3 class="section-label">文字描述 · ${descriptions.length} 条</h3>`;
  content += descriptions.length ? renderFactCards(descriptions) : '<p class="property-empty">当前视图暂无文字描述。</p>';
  content += `<h3 class="section-label">结构与关联 · ${relations.length} 条</h3>`;
  content += relations.length ? renderFactCards(relations) : '<p class="property-empty">当前视图暂无关联关系。</p>';
  content += `<details><summary>查看当前实体记录</summary><pre>${escapeHtml(JSON.stringify(entity, null, 2))}</pre></details>`;
  $("#detail-content").innerHTML = content;
}

function renderMedia(entity, { kind, evidenceId } = {}) {
  const items = (state.data.media || []).filter((item) => item.entity_ids.includes(entity.id) &&
    (!kind || item.kind === kind) && (!evidenceId || item.evidence_id === evidenceId));
  if (!items.length) return "";

  const cards = items.map((item) => {
    const url = `/api/media/${encodeURIComponent(item.id)}?review=${state.review ? "1" : "0"}`;
    const evidence = state.data.evidence.find((record) => record.id === item.evidence_id);
    const source = state.data.sources.find((record) => record.id === evidence?.source_id);
    const lookup = source?.available
      ? `<a class="pdf-link" href="/api/sources/${encodeURIComponent(source.id)}#page=${evidence.pdf_page}" target="_blank" rel="noopener">PDF 第 ${evidence.pdf_page} 页</a>`
      : item.kind === "model_view" ? `<small>节点 ${item.node_indices.join("、")}</small>` : "";
    return `<figure class="media-card">
      ${item.available ? `<a href="${url}" target="_blank" rel="noopener"><img loading="lazy" src="${url}" alt="${escapeHtml(item.label)}"></a>` : '<p class="media-missing">本地文件待生成</p>'}
      <figcaption><strong>${escapeHtml(item.label)}</strong><small>${escapeHtml(item.context)}</small>${lookup}</figcaption>
    </figure>`;
  });
  return `<section class="media-section" aria-label="部件图像"><h3 class="section-label">部件图像</h3><div class="media-grid">${cards.join("")}</div></section>`;
}

function renderEvidence(entity) {
  const facts = relatedFacts(entity.id);
  const ids = new Set(facts.flatMap((f) => f.evidence_ids));
  const evidence = state.data.evidence.filter((e) => ids.has(e.id));
  if (!evidence.length) {
    $("#detail-content").innerHTML = `<div class="empty-state"><strong>当前视图没有可用证据</strong>${state.review ? "尚未为该对象整理关联事实或来源，不能自行补写依据。" : "待审核事实的证据仅在候选检查模式中显示。"}</div>`;
    return;
  }
  const selectedEvidence = new Set(state.data.facts.find((f) => f.id === state.selectedFact)?.evidence_ids || []);
  $("#detail-content").innerHTML = '<p class="note">证据保留资料定位和适用范围。</p>' + evidence.map((e) => {
    const source = state.data.sources.find((s) => s.id === e.source_id);
    const factIds = facts.filter((f) => f.evidence_ids.includes(e.id)).map((f) => f.id);
    const video = source?.format === "mp4";
    const dictionary = source?.format === "md" && source?.source_type === "dictionary_excerpt";
    const uploadedText = source?.source_type === "uploaded_text";
    const labels = [...new Set(facts.filter((f) => f.evidence_ids.includes(e.id)).map((f) => knowledgeBases[f.knowledge_basis]).filter(Boolean))];
    const checked = e.check_status === "source_checked" ? (video ? "已抽帧核对画面或字幕；尚待组员复核" : dictionary ? "已核对官方词典条目摘录；尚待组员复核" : "Codex已对照原页；尚待组员复核") : "来源对应待核对";
    const link = uploadedText ? '<p>整份上传材料可在管理端查看。</p>' :
      source?.available || dictionary ? `<a class="pdf-link" href="${escapeHtml(evidenceSourceUrl(source, e))}" target="_blank" rel="noopener">${dictionary ? "打开官方词典条目" : `打开原${video ? "视频" : " PDF"}`} · ${escapeHtml(evidenceLocation(e))}</a>` : '<p>原资料未配置。启动时可通过 --resource-dir 指定资料目录。</p>';
    return `<article class="evidence-card ${selectedEvidence.has(e.id) ? "focused" : ""}"><div class="source-page"><strong>${escapeHtml(evidenceLocation(e))}</strong><code>${escapeHtml(e.id)}</code></div>${labels.length ? `<p>${labels.map(escapeHtml).join(" · ")}</p>` : ""}<blockquote>${escapeHtml(e.quote)}</blockquote><p>${escapeHtml(e.locator)}</p><p class="scope-note">${escapeHtml(e.scope_note)}</p><p>对应事实：${factIds.map(escapeHtml).join("、")}</p><p>来源：${escapeHtml(source?.title || e.source_id)}</p><p>${checked}</p>${link}${video || dictionary ? "" : renderMedia(entity, { kind: "source_clip", evidenceId: e.id })}</article>`;
  }).join("");
}

function renderMappings(entity) {
  const mappings = state.data.mappings.filter((m) => m.entity_id === entity.id);
  let html = mappings.length ? '<p class="note">以下是模型节点映射线索，尚未通过几何语义核验。此页不播放三维模型。</p>' : '<div class="empty-state"><strong>当前视图没有模型映射</strong>对象可能尚未映射；待审核映射只在候选检查模式中显示。</div>';
  html += renderMedia(entity, { kind: "model_view" });
  html += mappings.map((m) => `<article class="mapping-card"><div class="fact-meta"><code>${escapeHtml(m.id)}</code>${badge(m.review_status)}</div><h3>${escapeHtml(getEntity(m.model_version_id)?.label || m.model_version_id)}</h3><div>${m.node_indices.map((n) => `<code class="node-index">node ${n}</code>`).join("")}</div><p>${escapeHtml(m.note)}</p><p>绑定版本：${escapeHtml(m.model_version_id)}</p></article>`).join("");
  const report = state.data.model_report;
  if (report?.node_count) html += `<div class="model-summary"><h3 class="section-label">已有模型结构初查</h3><p>${report.node_count} 个节点 · ${report.mesh_count} 个 mesh · ${report.animations.length} 段动画</p><p>${report.animations.map((a) => escapeHtml(a.name)).join("、")}</p><p>这里只展示结构元数据，几何正确性、单位和动画播放效果仍待检查。</p></div>`;
  $("#detail-content").innerHTML = html;
}

document.addEventListener("click", (event) => {
  const region = event.target.closest("[data-map-region]");
  if (region && state.data) {
    if (region.dataset.mapRegion === "all") { resetGraphView(); renderGraph(); }
    else { const bounds = state.graphGroups.find((group) => group.key === region.dataset.mapRegion); if (bounds) focusMapBounds(bounds); }
    return;
  }
  const entity = event.target.closest("[data-entity]");
  if (entity && state.data) { selectEntity(entity.dataset.entity); return; }
  const tab = event.target.closest("[data-tab]");
  if (tab && state.data) { state.tab = tab.dataset.tab; renderDetail(); return; }
  const proof = event.target.closest("[data-proof]");
  if (proof) { state.selectedFact = proof.dataset.proof; state.tab = "evidence"; renderDetail(); }
});
$("#operator-logout")?.addEventListener("click", () => {
  operatorToken = "";
  $("#operator-logout").hidden = true;
  setAudience("public");
});
document.addEventListener("click", async (event) => {
  const link = event.target.closest('a[href^="/api/v1/internal/sources/"]');
  if (!link || !window.CHUCHARIOT_DATABASE_API) return;
  event.preventDefault();
  try {
    const response = await fetch(link.href, { headers: await databaseHeaders(), cache: "no-store" });
    if (!response.ok) throw new Error("原资料读取失败或凭据已失效");
    const url = URL.createObjectURL(await response.blob());
    const open = document.createElement("a");
    open.href = url + new URL(link.href).hash;
    open.target = "_blank";
    open.rel = "noopener";
    open.click();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  } catch (error) {
    $("#error-box").textContent = error.message;
    $("#error-box").hidden = false;
  }
});
$("#graph").addEventListener("keydown", (event) => {
  if ((event.key === "Enter" || event.key === " ") && event.target.dataset.entity) {
    event.preventDefault(); selectEntity(event.target.dataset.entity);
  }
});
$("#search").addEventListener("input", (event) => { state.query = event.target.value; if (state.data) { renderList(); renderGraph(); } });
$("#kind-filter").addEventListener("change", (event) => { state.kind = event.target.value; renderList(); renderGraph(); });
$("#map-mode").addEventListener("click", () => setGraphMode(false));
$("#local-mode").addEventListener("click", () => setGraphMode(true));
$("#map-expand").addEventListener("click", () => { state.expanded = !state.expanded; document.body.classList.remove("map-detail-open"); renderGraph(); });
$("#map-close-detail").addEventListener("click", () => document.body.classList.remove("map-detail-open"));
$("#map-details").addEventListener("click", () => document.body.classList.toggle("map-detail-open"));
$("#map-focus").addEventListener("click", focusCurrentEntity);
$("#map-clear").addEventListener("click", () => { state.highlight = false; renderGraph(); });
$("#map-locate").addEventListener("click", locateMapSearch);
$("#map-search").addEventListener("input", () => { state.mapSearchIndex = 0; $("#map-search-status").textContent = ""; $("#map-locate").textContent = "定位实体"; });
$("#map-search").addEventListener("keydown", (event) => { if (event.key === "Enter" && state.data) locateMapSearch(); });
$("#reload-button").addEventListener("click", loadData);
$("#public-view").addEventListener("click", () => setAudience("public"));
$("#internal-view").addEventListener("click", () => setAudience("internal"));
$("#relation-filters").addEventListener("change", (event) => {
  const group = event.target.dataset.relationGroup;
  if (!group || !state.data) return;
  if (event.target.checked) state.relationGroups.add(group); else state.relationGroups.delete(group);
  state.layoutKey = null;
  renderGraph();
});
$("#hide-isolated").addEventListener("change", (event) => { state.hideIsolated = event.target.checked; renderGraph(); });
$("#back-to-graph").addEventListener("click", () => $(".graph-panel").scrollIntoView({ block: "start" }));
$("#review-mode").addEventListener("click", () => { state.review = true; loadData(); });
$("#confirmed-mode").addEventListener("click", () => { state.review = false; loadData(); });
function zoomBy(factor) { state.zoom = Math.max(.5, Math.min(state.neighbors ? 4 : 16, state.zoom * factor)); renderGraph(); }
$("#zoom-in").addEventListener("click", () => zoomBy(1.2));
$("#zoom-out").addEventListener("click", () => zoomBy(1 / 1.2));
$("#zoom-reset").addEventListener("click", () => { resetGraphView(); renderGraph(); });
function graphPointAt(event, svg, width, height, center) {
  const rect = svg.getBoundingClientRect(), scale = Math.min(rect.width / width, rect.height / height);
  return { x: center.x + (event.clientX - rect.left - rect.width / 2) / scale,
    y: center.y + (event.clientY - rect.top - rect.height / 2) / scale };
}
$("#graph").addEventListener("wheel", (event) => {
  event.preventDefault();
  const svg = $("#graph"), previous = state.zoom;
  const previousSize = graphViewportSize(previous, svg);
  const anchor = graphPointAt(event, svg, previousSize.width, previousSize.height, state.center);
  state.zoom = Math.max(.5, Math.min(state.neighbors ? 4 : 16, previous * (event.deltaY < 0 ? 1.16 : 1 / 1.16)));
  const ratio = previous / state.zoom;
  state.center = { x: anchor.x + (state.center.x - anchor.x) * ratio, y: anchor.y + (state.center.y - anchor.y) * ratio };
  renderGraph();
}, { passive: false });
$("#minimap").addEventListener("click", (event) => {
  const point = graphPointAt(event, $("#minimap"), state.graphWidth, state.graphHeight, { x: state.graphWidth / 2, y: state.graphHeight / 2 });
  state.center = { x: Math.max(0, Math.min(state.graphWidth, point.x)), y: Math.max(0, Math.min(state.graphHeight, point.y)) };
  state.zoom = Math.max(2.5, state.zoom);
  renderGraph();
});
let drag = null;
$("#graph").addEventListener("pointerdown", (event) => {
  if (event.target.closest("[data-entity]")) return;
  drag = { x: event.clientX, y: event.clientY, center: { ...state.center }, pointerId: event.pointerId };
  $("#graph").setPointerCapture(event.pointerId);
});
$("#graph").addEventListener("pointermove", (event) => {
  if (!drag) return;
  const svg = $("#graph");
  const scale = graphViewportSize().width / svg.clientWidth;
  state.center = { x: drag.center.x - (event.clientX - drag.x) * scale, y: drag.center.y - (event.clientY - drag.y) * scale };
  // Only change the viewport during a drag, retaining pointer capture.
  setGraphViewport(svg);
  renderMinimap();
});
for (const name of ["pointerup", "pointercancel"]) $("#graph").addEventListener(name, () => { drag = null; });
let resizeTimer;
window.addEventListener("resize", () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(renderGraph, 120); });
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || !state.expanded) return;
  if (document.body.classList.contains("map-detail-open")) document.body.classList.remove("map-detail-open");
  else { state.expanded = false; renderGraph(); }
});
syncGraphMode();
loadData();
