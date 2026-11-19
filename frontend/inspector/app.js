"use strict";

const $ = (selector) => document.querySelector(selector);
const state = { data: null, selected: "type:001", review: true, tab: "detail", query: "", kind: "", neighbors: false, selectedFact: null, zoom: 1, center: { x: 490, y: 410 }, requestVersion: 0 };
const kinds = { ComponentType: "部件类别", Chariot: "研究对象", Component: "具体部件", ReferenceSpecimen: "对照标本", Measurement: "尺寸记录", ModelVersion: "模型版本", Connection: "连接记录", Pose: "位姿记录", AssemblyStep: "演示步骤" };
const relationNames = { HAS_PART: "包含部件", INSTANCE_OF: "属于类别", HAS_MEASUREMENT: "具有尺寸", SUBCLASS_OF: "属于父类", DESCRIPTION: "资料描述", PARTICIPATES_IN_CONNECTION: "参与连接", HAS_POSE: "具有位姿", INVOLVES_COMPONENT: "涉及部件", DEPENDS_ON: "依赖步骤" };
const shortRelations = { HAS_PART: "组成", INSTANCE_OF: "归类", HAS_MEASUREMENT: "尺寸", SUBCLASS_OF: "类别", DESCRIPTION: "描述" };
const origins = { documented: "资料记载", inferred: "结构推导", hypothesis: "复原假设" };
const statusNames = { pending: "待审核", confirmed: "已确认", disputed: "有争议" };
const symbols = { ComponentType: "件", ReferenceSpecimen: "标", Measurement: "尺", ModelVersion: "模", Chariot: "车" };
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const getEntity = (id) => state.data.entities.find((e) => e.id === id);
const relatedFacts = (id) => state.data.facts.filter((f) => f.subject_id === id || f.object_id === id);
const badge = (status) => `<span class="badge ${escapeHtml(status)}">${escapeHtml(statusNames[status] || status)}</span>`;
const entityLink = (id) => `<button class="entity-link" data-entity="${escapeHtml(id)}">${escapeHtml(getEntity(id)?.label || id)}</button>`;

async function loadData() {
  const requestVersion = ++state.requestVersion;
  $("#reload-button").disabled = true;
  $("#workspace").setAttribute("aria-busy", "true");
  $("#error-box").hidden = true;
  try {
    const response = await fetch(`/api/preview?review=${state.review ? "1" : "0"}`, { cache: "no-store" });
    const data = await response.json();
    if (requestVersion !== state.requestVersion) return;
    if (!response.ok) throw new Error(data.error || "数据读取失败");
    state.data = data;
    if (!getEntity(state.selected)) state.selected = data.entities[0]?.id || null;
    renderOverview();
    renderList();
    renderGraph();
    renderDetail();
    $("#load-status").textContent = `已读取本地数据 · ${new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}`;
  } catch (error) {
    if (requestVersion !== state.requestVersion) return;
    $("#error-box").textContent = `无法读取知识数据：${error.message}。请确认本地预览服务正在运行，并检查终端中的校验结果。`;
    $("#error-box").hidden = false;
    $("#load-status").textContent = "读取失败";
  } finally {
    if (requestVersion === state.requestVersion) {
      $("#reload-button").disabled = false;
      $("#workspace").setAttribute("aria-busy", "false");
    }
  }
}

function renderOverview() {
  const { stats, meta, entities } = state.data;
  for (const name of ["entities", "confirmed", "pending", "evidence"]) $(`#stat-${name}`).textContent = stats[name];
  $("#dataset-id").textContent = meta.dataset_id;
  $("#dataset-version").textContent = `数据格式 ${meta.schema_version} · ${meta.validation === "passed" ? "结构校验通过" : "待检查"}`;
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
  state.selectedFact = null;
  renderList();
  renderGraph();
  renderDetail();
}

function graphPositions(entities) {
  const initial = {
    "type:001": [330, 215], "type:002": [385, 590], "type:003": [105, 90],
    "type:004": [85, 235], "type:005": [125, 385], "type:006": [125, 745],
    "type:007": [355, 745], "specimen:001": [500, 365], "specimen:002": [620, 590],
    "measurement:001": [770, 240], "measurement:002": [770, 430], "measurement:003": [850, 590],
    "object:001": [585, 745], "model:001": [820, 745],
  };
  const positions = new Map(entities.filter((entity) => initial[entity.id])
    .map((entity) => [entity.id, initial[entity.id]]));
  let slot = 0;
  for (const entity of entities) {
    if (positions.has(entity.id)) continue;
    let point;
    do {
      point = [110 + (slot % 5) * 180, 90 + Math.floor(slot / 5) * 140];
      slot += 1;
    } while ([...positions.values()].some(([x, y]) => Math.abs(x - point[0]) < 150 && Math.abs(y - point[1]) < 105));
    positions.set(entity.id, point);
  }
  return positions;
}

function graphCaption(entity) {
  if (entity.kind === "Measurement") {
    if (!entity.measurement) return entity.label.replace(/^CH1：\d/, "");
    const m = entity.measurement;
    return `${m.quantity.replace("右轮", "")}${m.value ?? `${m.min}–${m.max}`}${m.unit}`;
  }
  if (entity.id === "object:001") return "九连墩六号车";
  if (entity.kind === "ModelVersion") return "教学 GLB 模型";
  return entity.label;
}

function svgElement(tag, attributes = {}, text) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, String(value));
  if (text !== undefined) element.textContent = text;
  return element;
}

function renderGraph() {
  if (!state.data) return;
  const svg = $("#graph");
  const { entities, facts } = state.data;
  const connections = facts.filter((f) => f.object_id);
  const adjacent = new Set([state.selected]);
  for (const f of relatedFacts(state.selected)) {
    adjacent.add(f.subject_id);
    if (f.object_id) adjacent.add(f.object_id);
  }
  const matches = new Set(matchedEntities().map((e) => e.id));
  const width = 980 / state.zoom, height = 820 / state.zoom;
  svg.setAttribute("viewBox", `${state.center.x - width / 2} ${state.center.y - height / 2} ${width} ${height}`);
  const scale = Math.max(Math.min(svg.clientWidth / width, svg.clientHeight / height), 0.2);
  const labelSize = Math.min(70, Math.max(17, 14 / scale));
  svg.replaceChildren();
  const defs = svgElement("defs");
  const marker = svgElement("marker", { id: "arrow-head", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" });
  marker.append(svgElement("path", { d: "M 1 1 L 9 5 L 1 9", fill: "none", stroke: "#92af9b", "stroke-width": 1.3 }));
  defs.append(marker); svg.append(defs);
  const positions = graphPositions(entities);
  const edgeLayer = svgElement("g"), labelLayer = svgElement("g"), nodeLayer = svgElement("g");
  for (const fact of connections) {
    if (state.neighbors && (!adjacent.has(fact.subject_id) || !adjacent.has(fact.object_id))) continue;
    const from = positions.get(fact.subject_id), to = positions.get(fact.object_id);
    if (!from || !to) continue;
    const [dx, dy] = [to[0] - from[0], to[1] - from[1]];
    const length = Math.hypot(dx, dy) || 1;
    const related = fact.subject_id === state.selected || fact.object_id === state.selected;
    edgeLayer.append(svgElement("line", {
      x1: from[0] + dx / length * 34, y1: from[1] + dy / length * 34,
      x2: to[0] - dx / length * 39, y2: to[1] - dy / length * 39,
      class: `graph-edge ${related ? "related" : "dimmed"}`, "marker-end": "url(#arrow-head)",
    }));
    if (scale >= .5) labelLayer.append(svgElement("text", { x: (from[0] + to[0]) / 2, y: (from[1] + to[1]) / 2 - 10,
      class: "edge-label", "font-size": labelSize - 1 }, shortRelations[fact.predicate] || relationNames[fact.predicate] || fact.predicate));
  }
  for (const entity of entities) {
    if (state.neighbors && !adjacent.has(entity.id)) continue;
    const [x, y] = positions.get(entity.id);
    const active = entity.id === state.selected;
    const dimmed = !matches.has(entity.id) || (!adjacent.has(entity.id) && !active);
    const group = svgElement("g", { transform: `translate(${x} ${y})`, class: `node ${active ? "active" : adjacent.has(entity.id) ? "related" : ""} ${dimmed ? "dimmed" : ""}`,
      "data-entity": entity.id, "data-kind": entity.kind, tabindex: 0, role: "button", "aria-label": `查看${entity.label}` });
    group.append(svgElement("title", {}, `${entity.label} · ${kinds[entity.kind] || entity.kind}`));
    group.append(svgElement("circle", { r: active ? 34 : 29 }));
    group.append(svgElement("text", { y: 8, class: "node-symbol" }, entity.kind === "ComponentType" ? entity.label.slice(-1) : symbols[entity.kind] || "件"));
    const caption = svg.clientWidth < 500 && entity.kind === "ModelVersion" ? "GLB 模型" : graphCaption(entity);
    group.append(svgElement("text", { y: 66, class: "node-label", "font-size": labelSize }, caption));
    nodeLayer.append(group);
  }
  svg.append(edgeLayer, labelLayer, nodeLayer);
  $("#graph-summary").textContent = `${entities.length} 个实体 · ${connections.length} 条${state.review ? "候选" : "已确认"}关系`;
  $("#zoom-value").textContent = `${Math.round(state.zoom * 100)}%`;
  $("#graph-empty").hidden = state.review || connections.length > 0;
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
    (!summary.pending && !summary.confirmed ? '<span class="badge">仅目录记录</span>' : "");
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

function renderKnowledge(entity) {
  let content = "";
  if (entity.note) content += `<p class="note">${escapeHtml(entity.note)}</p>`;
  const fields = [];
  if (entity.aliases.length) fields.push(`<div><dt>别名</dt><dd>${entity.aliases.map(escapeHtml).join("、")}</dd></div>`);
  if (entity.scope_id) fields.push(`<div><dt>归属对象</dt><dd>${entityLink(entity.scope_id)}</dd></div>`);
  if (fields.length) content += `<dl class="key-values">${fields.join("")}</dl>`;
  if (entity.measurement) {
    const m = entity.measurement;
    content += `<div class="measurement-card"><p>${escapeHtml(m.quantity)}</p><strong>${escapeHtml(m.value ?? `${m.min}–${m.max}`)}</strong><span class="unit">${escapeHtml(m.unit)}</span><small>${m.approximate ? "原文近似值" : "保留资料记载值"} · ${state.review ? "候选尺寸，待复核" : "已按项目规则审核"}</small><small>原始表达：${escapeHtml(m.raw)}</small></div>`;
  } else if (entity.measurement_visibility) {
    content += '<div class="empty-state"><strong>未确认尺寸已隐藏</strong>切换“候选检查”可以查看候选数值及其来源。</div>';
  }
  content += renderMedia(entity);
  const facts = relatedFacts(entity.id);
  content += `<h3 class="section-label">关联事实 · ${facts.length}</h3>`;
  content += facts.length ? facts.map((fact) => `<article class="fact-card"><div class="fact-meta"><code>${escapeHtml(fact.id)}</code>${badge(fact.review_status)}</div><p class="fact-statement">${entityLink(fact.subject_id)}<span class="relation-word">${escapeHtml(relationNames[fact.predicate] || fact.predicate)}</span>${fact.object_id ? entityLink(fact.object_id) : escapeHtml(fact.value)}</p><div class="fact-origin">${escapeHtml(origins[fact.origin] || fact.origin)} · ${fact.evidence_ids.length} 段证据</div><button class="text-button" data-proof="${escapeHtml(fact.id)}">查看事实依据</button></article>`).join("")
    : `<div class="empty-state"><strong>${state.review ? "暂未整理关联事实" : "暂无已确认事实"}</strong>${state.review ? "该对象目前仅在目录中登记，缺少关系不代表历史上不存在。" : "当前候选仍待组员复核，普通知识视图不会显示它们。"}</div>`;
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
  $("#detail-content").innerHTML = '<p class="note">证据链接到原始 PDF。相关段落和部件图见下方。</p>' + evidence.map((e) => {
    const source = state.data.sources.find((s) => s.id === e.source_id);
    const factIds = facts.filter((f) => f.evidence_ids.includes(e.id)).map((f) => f.id);
    return `<article class="evidence-card ${selectedEvidence.has(e.id) ? "focused" : ""}"><div class="source-page"><strong>PDF 第 ${e.pdf_page} 页</strong><code>${escapeHtml(e.id)}</code></div><blockquote>${escapeHtml(e.quote)}</blockquote><p>${escapeHtml(e.locator)}</p><p class="scope-note">${escapeHtml(e.scope_note)}</p><p>对应事实：${factIds.map(escapeHtml).join("、")}</p><p>来源：${escapeHtml(source?.title || e.source_id)}</p><p>${e.check_status === "source_checked" ? "已本地对照原文；尚不代表组员审核" : "原文对应待核对"}</p>${source?.available ? `<a class="pdf-link" href="/api/sources/${encodeURIComponent(source.id)}#page=${e.pdf_page}" target="_blank" rel="noopener">打开原 PDF 第 ${e.pdf_page} 页</a>` : '<p>原 PDF 未配置。启动时可通过 --resource-dir 指定资料目录。</p>'}${renderMedia(entity, { kind: "source_clip", evidenceId: e.id })}</article>`;
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
  const entity = event.target.closest("[data-entity]");
  if (entity && state.data) { selectEntity(entity.dataset.entity); return; }
  const tab = event.target.closest("[data-tab]");
  if (tab && state.data) { state.tab = tab.dataset.tab; renderDetail(); return; }
  const proof = event.target.closest("[data-proof]");
  if (proof) { state.selectedFact = proof.dataset.proof; state.tab = "evidence"; renderDetail(); }
});
$("#graph").addEventListener("keydown", (event) => {
  if ((event.key === "Enter" || event.key === " ") && event.target.dataset.entity) {
    event.preventDefault(); selectEntity(event.target.dataset.entity);
  }
});
$("#search").addEventListener("input", (event) => { state.query = event.target.value; if (state.data) { renderList(); renderGraph(); } });
$("#kind-filter").addEventListener("change", (event) => { state.kind = event.target.value; renderList(); renderGraph(); });
$("#neighbors-only").addEventListener("change", (event) => { state.neighbors = event.target.checked; renderGraph(); });
$("#reload-button").addEventListener("click", loadData);
$("#review-mode").addEventListener("click", () => { state.review = true; loadData(); });
$("#confirmed-mode").addEventListener("click", () => { state.review = false; loadData(); });
function zoomBy(factor) { state.zoom = Math.max(.6, Math.min(2.8, state.zoom * factor)); renderGraph(); }
$("#zoom-in").addEventListener("click", () => zoomBy(1.2));
$("#zoom-out").addEventListener("click", () => zoomBy(1 / 1.2));
$("#zoom-reset").addEventListener("click", () => { state.zoom = 1; state.center = { x: 490, y: 410 }; renderGraph(); });
$("#graph").addEventListener("wheel", (event) => { event.preventDefault(); zoomBy(event.deltaY < 0 ? 1.1 : 1 / 1.1); }, { passive: false });
let drag = null;
$("#graph").addEventListener("pointerdown", (event) => {
  if (event.target.closest("[data-entity]")) return;
  drag = { x: event.clientX, y: event.clientY, center: { ...state.center }, pointerId: event.pointerId };
  $("#graph").setPointerCapture(event.pointerId);
});
$("#graph").addEventListener("pointermove", (event) => {
  if (!drag) return;
  const scale = Math.max((980 / state.zoom) / $("#graph").clientWidth, (820 / state.zoom) / $("#graph").clientHeight);
  state.center = { x: drag.center.x - (event.clientX - drag.x) * scale, y: drag.center.y - (event.clientY - drag.y) * scale };
  // Only change the viewport during a drag, retaining pointer capture.
  const width = 980 / state.zoom, height = 820 / state.zoom;
  $("#graph").setAttribute("viewBox", `${state.center.x - width / 2} ${state.center.y - height / 2} ${width} ${height}`);
});
for (const name of ["pointerup", "pointercancel"]) $("#graph").addEventListener(name, () => { drag = null; });
let resizeTimer;
window.addEventListener("resize", () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(renderGraph, 120); });
loadData();
