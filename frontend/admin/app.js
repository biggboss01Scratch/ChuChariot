import { showGraph } from "./graph.js";
import { filterKnowledge, NetworkMap, ontologyKind, paintMapLegend, projectOntology } from "./network.js";

const $ = selector => document.querySelector(selector);
const admin = "/api/v1/internal/admin";
const changes = "/api/v1/internal/change-sets";
const loginAccount = "chuchariot-operator";
const statusLabels = { new: "建议新增", duplicate: "重复", conflict: "可能冲突", possible_duplicate: "相近记录", needs_review: "待确认", unrelated: "无关" };
const tableLabels = { entities: "实体", facts: "事实", evidence: "证据", sources: "来源", model_mappings: "模型映射" };
const kindLabels = { ComponentType: "部件类别", Component: "具体部件", Chariot: "战车", ReferenceSpecimen: "对照标本",
  ReferenceRecord: "资料记录", ComponentRegion: "描述区域", StructuralRegionType: "区域类别", Material: "材质",
  PreservationFeature: "保存特征", SurfaceFinish: "表面髹饰", DecorationMotif: "纹饰", HarnessRole: "系驾角色",
  Connection: "连接记录", ModelVersion: "模型版本", Pose: "位姿", AssemblyStep: "装配步骤", Subsystem: "教学分组",
  EvidenceBasisClass: "依据类别", TermSense: "语境词义", Source: "来源" };
const importPredicates = new Set(["DESCRIPTION", "HAS_DIMENSION", "HAS_PART", "HAS_REGION", "HAS_MATERIAL", "TENON_JOINT_WITH", "HAS_PRESERVED_FEATURE", "HAS_SURFACE_FINISH", "HAS_ASSOCIATED_COMPONENT", "HAS_DECORATION_MOTIF", "INSTANCE_OF"]);

let token = "", view, entities, evidence, sources;
let selected = "", neighborhood = false, zoom = 1, linking = "";
let currentTab = "graph", editorSave, upload, analysis, trashPage = 1;
let graphPreview;
let graphLayout = "network";
const graphScopes = { grid: "all", network: "knowledge" };
let network, schema;
let ontologySelection = "";
let showOntology = false;
const importSelection = new Map();
const publicationSelection = new Set();

function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function button(text, action, cls) {
  const node = el("button", text, cls);
  node.type = "button";
  node.addEventListener("click", action);
  return node;
}

function paragraph(text, cls = "muted") {
  return el("p", text, cls);
}

function label(text, control) {
  const node = el("label", text);
  control.setAttribute("aria-label", text);
  node.append(control);
  return node;
}

function input(value = "", options = {}) {
  const node = el("input");
  Object.assign(node, { value, ...options });
  return node;
}

function area(value = "", rows = 3) {
  const node = el("textarea");
  Object.assign(node, { value, rows });
  return node;
}

function select(options, value = "") {
  const node = el("select");
  for (const [key, text] of options) {
    const option = el("option", text);
    option.value = key;
    node.append(option);
  }
  node.value = value;
  return node;
}

function row(...children) {
  const wrapper = el("div", null, "form-row");
  wrapper.append(...children);
  return wrapper;
}

function check(text, checked, changed) {
  const node = el("label", null, "inline-check");
  const box = input("", { type: "checkbox", checked });
  box.addEventListener("change", () => changed(box.checked));
  node.append(box, document.createTextNode(text));
  return node;
}

function notice(text, error = false) {
  const box = $("#notice");
  box.textContent = text;
  box.hidden = !text;
  box.classList.toggle("error", error);
}

async function api(path, body, key) {
  const headers = { Authorization: "Bearer " + token };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (key) headers["Idempotency-Key"] = key;
  const response = await fetch(path, { headers, method: body === undefined ? "GET" : "POST",
    body: body === undefined ? undefined : JSON.stringify(body) });
  const result = await response.json();
  if (!response.ok) {
    const error = result.error;
    const details = error?.details?.map(item => item.path + " · " + item.message).join("\n");
    const message = { 401: "请输入操作员凭据。", 403: "操作员凭据无效。", 409: "图谱已变化，请刷新后重新检查。",
      422: "记录校验未通过。" }[response.status];
    throw new Error(details || (response.status === 401 || response.status === 403 ? message :
      error?.message === "Invalid request" ? message : error?.message) || message || "请求失败（" + response.status + "）");
  }
  return result;
}

async function run(job, control) {
  if (control?.disabled) return;
  if (control) control.disabled = true;
  try { await job(); } catch (error) { notice(error.message, true); }
  finally { if (control) control.disabled = false; }
}

function renderRevision() { $("#revision").textContent = view ? "知识修订 " + view.meta.graph_revision : ""; }

async function refresh() {
  view = await api(admin + "/state");
  schema = projectOntology(view.ontology, kindLabels);
  if (!view.ontology.entity_kinds[ontologySelection]) ontologySelection = "";
  entities = new Map(view.dataset.entities.map(item => [item.id, item]));
  evidence = new Map(view.dataset.evidence.map(item => [item.id, item]));
  sources = new Map(view.dataset.sources.map(item => [item.id, item]));
  if (!entities.has(selected)) selected = "";
  renderRevision();
  renderPublication();
  if (currentTab === "graph") renderGraphPage();
}

function go(tab) {
  currentTab = tab;
  if (tab !== "graph") graphPreview = undefined;
  for (const name of ["graph", "imports", "publication", "trash"]) $("#" + name + "-page").hidden = name !== tab;
  for (const entry of $("#tabs").querySelectorAll("button")) entry.setAttribute("aria-pressed", String(entry.dataset.tab === tab));
  if (tab === "graph") renderGraphPage();
  if (tab === "publication") renderPublication();
  if (tab === "trash") run(renderTrash);
}

function entryLabel(id) { return entities.get(id)?.label || id || ""; }
function predicateLabel(name) { return view.ontology.predicates[name]?.label.split("；")[0] || name; }
function factValue(fact) {
  if (fact.object_id) return entryLabel(fact.object_id);
  if (typeof fact.value !== "object" || fact.value === null) return fact.value ?? "";
  const value = fact.value;
  return (value.quantity || "") + " " + (value.approximate ? "约 " : "") +
    (value.value ?? (value.min + "–" + value.max)) + " " + (value.unit || "");
}

function highlight(id, scroll = false) {
  if (!entities.has(id) && !graphPreview?.item.new_entities.some(entity => entity.id === id)) return;
  if (linking && linking !== id) {
    const source = linking;
    linking = "";
    notice("");
    openFact(null, source, id);
    return;
  }
  if (graphScopes[graphLayout] === "knowledge" && !graphPreview &&
      !filterKnowledge([entities.get(id)], []).entities.length) graphScopes[graphLayout] = "all";
  selected = id;
  ontologySelection = "";
  renderGraphPage();
  if (scroll) {
    if (graphLayout === "network") {
      network.centerOn(id);
      return;
    }
    const node = [...$("#graph-view").querySelectorAll("button")].find(item => item.dataset.id === id);
    if (node) $("#graph-view").scrollTo({ top: node.offsetTop * zoom - 90, left: node.offsetLeft * zoom - 70 });
  }
}

function renderGraphPage() {
  if (!view) return;
  const dataset = view.dataset;
  const mapMode = graphLayout === "network";
  const scope = graphScopes[graphLayout];
  const graph = scope === "knowledge" ? filterKnowledge(dataset.entities, dataset.facts) : dataset;
  const previewNodes = graphPreview?.item.new_entities.map(entity => ({ ...entity, publication_status: "draft" })) || [];
  if (selected && !graph.entities.some(entity => entity.id === selected) &&
      !previewNodes.some(entity => entity.id === selected)) {
    selected = "";
    linking = "";
    neighborhood = false;
  }
  $("#graph-count").textContent = graph.entities.length + " 个实体 · " + graph.facts.length + " 条事实";
  $("#graph-scope").value = scope;
  $("#grid-layout").setAttribute("aria-pressed", String(!mapMode));
  $("#network-layout").setAttribute("aria-pressed", String(mapMode));
  $("#graph-view").hidden = $("#grid-legend").hidden = mapMode;
  $("#network-view").hidden = $("#network-footer").hidden = $("#fit-network").hidden = !mapMode;
  $("#toggle-ontology").hidden = !mapMode;
  $("#toggle-ontology").setAttribute("aria-pressed", String(showOntology));
  showZoom(mapMode ? network?.scale || 1 : zoom);
  $("#overview").setAttribute("aria-pressed", String(!neighborhood));
  $("#neighborhood").setAttribute("aria-pressed", String(neighborhood));
  $("#neighborhood").disabled = !selected;
  const term = $("#search").value.trim().toLocaleLowerCase();
  const items = graph.entities.filter(entry =>
    [entry.label, entry.id, ...entry.aliases].some(value => value.toLocaleLowerCase().includes(term)));
  const list = $("#entity-list");
  list.replaceChildren(...items.map(entry => {
    const node = button(entry.label, () => highlight(entry.id, true));
    node.title = entry.label + " · " + entry.id;
    node.setAttribute("aria-current", String(entry.id === selected));
    return node;
  }));
  if (!items.length) list.append(paragraph("没有找到匹配的实体。"));
  const addEdge = graphPreview?.item.object_id && graphPreview.item.status !== "duplicate";
  const previewEdges = addEdge ? [{ subject_id: graphPreview.item.subject_id, object_id: graphPreview.item.object_id,
    publication_managed: true, review_status: "pending" }] : [];
  const graphEntities = [...graph.entities, ...previewNodes];
  const graphFacts = [...graph.facts, ...previewEdges];
  if (mapMode) {
    if (!network) network = new NetworkMap($("#network-view"), chooseNetworkNode, showZoom);
    network.setGraph(graphEntities, graphFacts, view.regions || {}, selected, neighborhood,
      showOntology ? schema : null, ontologySelection);
  } else showGraph($("#graph-view"), graphEntities, graphFacts, selected, neighborhood, zoom, highlight);
  renderDetail(graph.facts);
}

function chooseNetworkNode(id) {
  const kind = ontologyKind(id);
  if (kind) chooseOntology(kind);
  else highlight(id);
}

function chooseOntology(kind) {
  showOntology = true;
  ontologySelection = kind;
  renderGraphPage();
}

function ontologyDetails(parent, kind) {
  const node = schema.entities.find(item => item.id === kind);
  parent.append(el("h2", node.label), paragraph("本体类型 · " + view.ontology.version), el("code", kind),
    paragraph(node.definition, ""));
  const rules = schema.rules.filter(rule =>
    rule.subject_kinds?.includes(kind) || rule.endpoint_pairs?.some(pair => pair.includes(kind)));
  if (entities.has(selected)) {
    parent.append(button("返回所选实体", () => { ontologySelection = ""; renderGraphPage(); }, "quiet"));
  }
  const section = el("section");
  section.append(el("h3", "允许的关系与属性 · " + rules.length));
  for (const rule of rules) {
    const detail = el("details", null, "schema-rule");
    detail.append(el("summary", predicateLabel(rule.id)), el("code", rule.id), paragraph(rule.label));
    if (rule.endpoint_pairs) {
      for (const [from, to] of rule.endpoint_pairs.filter(pair => pair.includes(kind))) {
        detail.append(paragraph((kindLabels[from] || from) + " → " + (kindLabels[to] || to), ""));
      }
    } else {
      const valueType = rule.object_kind === "dimension" ? "结构化尺寸 · " + view.ontology.units.join(" / ") : "文本";
      detail.append(paragraph("值类型 · " + valueType, ""));
    }
    if (rule.acyclic) detail.append(paragraph("约束 · 关系链必须无环"));
    section.append(detail);
  }
  parent.append(section);
}

function showZoom(scale) {
  $("#graph-mode").textContent = Math.round(scale * 100) + "%" + (graphPreview ? " · 入库预览" : "");
}

function proofView(id) {
  const proof = evidence.get(id);
  if (!proof) return paragraph("证据 " + id, "muted");
  const source = sources.get(proof.source_id);
  const section = el("div");
  section.append(paragraph((source?.title || proof.source_id) + " · " + proof.locator), el("blockquote", proof.quote));
  if (source?.source_type === "uploaded_text") {
    const open = button("查看上传原文", () => run(async () => {
      const response = await fetch("/api/v1/internal/sources/" + encodeURIComponent(source.id) + "/content",
        { headers: { Authorization: "Bearer " + token } });
      if (!response.ok) throw new Error("当前无法读取上传原文。");
      const text = await response.text();
      const textArea = area(text, 12);
      textArea.readOnly = true;
      openEditor(source.title, "关闭", [textArea], async () => {});
    }, open), "quiet");
    section.append(open);
  }
  return section;
}

function renderDetail(visibleFacts) {
  const parent = $("#detail");
  const item = entities.get(selected);
  parent.replaceChildren();
  if (graphLayout === "network" && ontologySelection) {
    ontologyDetails(parent, ontologySelection);
    return;
  }
  if (graphPreview) {
    const preview = el("section");
    const { item: previewItem, candidate } = graphPreview;
    preview.append(el("h2", "导入建议预览"), paragraph(statusLabels[previewItem.status] + " · " + candidate.subject.label),
      paragraph(candidate.object?.label || factValue({ value: candidate.value })), el("blockquote", candidate.quote),
      button("返回导入审核", () => go("imports")));
    parent.append(preview);
    if (!item) return;
  }
  if (!item) {
    parent.append(el("h2", "实体详情"), paragraph("选择图上的节点或左侧实体，查看属性、关系和证据。"));
    return;
  }
  parent.append(el("h2", item.label), paragraph((kindLabels[item.kind] || item.kind) +
    (item.publication_status === "draft" ? " · 待发布" : "")), el("code", item.id));
  if (graphLayout === "network") parent.append(button("查看本体类型", () => chooseOntology(item.kind), "quiet"));
  if (item.scope_id) parent.append(paragraph("所属对象 · " + entryLabel(item.scope_id)));
  if (item.note) parent.append(paragraph(item.note));
  const edit = el("div", null, "actions");
  edit.append(button("编辑实体", () => openEntity(item)),
    button("新增事实", () => openFact(null, item.id)),
    button(linking ? "取消连线" : "图上连线", () => {
      linking = linking ? "" : item.id;
      notice(linking ? "请在图谱或列表点击目标实体。" : "");
      renderDetail(visibleFacts);
    }),
    button("删除", () => confirmChange("删除实体", "删除「" + item.label + "」？如有引用，后端会列出需要处理的记录。",
      [{ table: "entities", id: item.id, action: "delete" }]), "danger"));
  if (item.publication_status === "draft") edit.append(button("发布实体", () => publish([["entities", item.id]])));
  parent.append(edit);
  const facts = visibleFacts.filter(fact => fact.subject_id === item.id || fact.object_id === item.id);
  const section = el("section");
  section.append(el("h3", "属性与关系 · " + facts.length));
  for (const fact of facts) {
    const card = el("article", null, "fact-detail");
    const related = fact.subject_id === item.id ? fact.object_id : fact.subject_id;
    card.append(paragraph(predicateLabel(fact.predicate), "muted"));
    if (related) card.append(button(entryLabel(related), () => highlight(related, true), "quiet"));
    else card.append(paragraph(factValue(fact), ""));
    card.append(paragraph(fact.review_status === "confirmed" ? "已审核" :
      fact.publication_managed ? "待发布" : "候选资料"));
    if (fact.evidence_ids.length) {
      const proof = el("details");
      proof.append(el("summary", "查看 " + fact.evidence_ids.length + " 条证据"), ...fact.evidence_ids.map(proofView));
      card.append(proof);
    }
    const buttons = el("div", null, "actions");
    buttons.append(button("编辑", () => openFact(fact, fact.subject_id)),
      button("删除", () => confirmChange("删除事实", "删除这条事实？", [{ table: "facts", id: fact.id, action: "delete" }]), "danger"));
    if (fact.review_status !== "confirmed") buttons.append(button("发布", () => publish([["facts", fact.id]])));
    card.append(buttons);
    section.append(card);
  }
  parent.append(section);
}

function openEditor(title, saveText, fields, save) {
  $("#editor-title").textContent = title;
  $("#save-editor").textContent = saveText;
  $("#editor-fields").replaceChildren(...fields);
  $("#editor-error").textContent = "";
  editorSave = save;
  $("#editor").showModal();
}

async function commitOperations(operations, reason) {
  const meta = view.meta;
  const command = await api(changes, { base_graph_revision: meta.graph_revision, ontology_version: meta.ontology_version,
    schema_version: meta.schema_version, reason, operations }, crypto.randomUUID());
  const validation = await api(changes + "/" + command.id + "/validate", {});
  if (!validation.valid) throw new Error(validation.errors.map(error => error.message).join("\n"));
  await api(changes + "/" + command.id + "/commit", { expected_graph_revision: meta.graph_revision });
  await refresh();
}

function confirmChange(title, description, operations, after) {
  const reason = input(title, { required: true, maxLength: 200 });
  openEditor(title, "确认" + title.slice(0, 2), [paragraph(description), label("操作说明", reason)], async () => {
    await commitOperations(operations, reason.value);
    if (after) await after();
    notice(title + "已完成。");
  });
}

function openEntity(record) {
  const kind = select(Object.keys(view.ontology.entity_kinds).filter(value => value !== "ModelVersion")
    .map(value => [value, kindLabels[value] || value]), record?.kind || "ComponentType");
  const name = input(record?.label, { required: true, maxLength: 180 });
  const aliases = input(record?.aliases?.join("、") || "");
  const scope = select(entityOptions(record?.id), record?.scope_id || "");
  const note = area(record?.note || "", 2);
  openEditor(record ? "编辑实体" : "新增实体", "存入知识库",
    [row(label("名称", name), label("实体类型", kind)), label("别名（用顿号或逗号分隔）", aliases),
      label("所属对象", scope), label("备注", note)], async () => {
      const id = record?.id || "entity:manual-" + crypto.randomUUID();
      const value = { ...record, id, label: name.value.trim(), kind: kind.value,
        aliases: aliases.value.split(/[、，,]+/).map(part => part.trim()).filter(Boolean), note: note.value };
      if (scope.value) value.scope_id = scope.value;
      else delete value.scope_id;
      await commitOperations([{ table: "entities", id, action: record ? "update" : "create", record: value }], "编辑图谱实体");
      highlight(id, true);
      notice("实体已入库，等待发布。");
    });
}

function entityOptions(exclude) {
  return [["", "请选择"], ...[...entities.values()].filter(item => item.id !== exclude)
    .sort((a, b) => a.label.localeCompare(b.label, "zh-CN")).map(item => [item.id, item.label + " · " + item.id])];
}

function factFields(initialPredicate, initialValue, initialTarget, initialOrigin, initialRationale, allowPredicate, importMode = false) {
  const definitions = view.ontology.predicates;
  const predicate = select(Object.keys(definitions).filter(key => (!importMode || importPredicates.has(key)))
    .map(key => [key, predicateLabel(key) + " · " + key]), initialPredicate || "DESCRIPTION");
  const object = select(entityOptions(), initialTarget);
  const text = area(typeof initialValue === "string" ? initialValue : "");
  const quantity = input(initialValue?.quantity || "");
  const unit = select(view.ontology.units.map(key => [key, key]), initialValue?.unit || "cm");
  const numbers = input(initialValue == null || typeof initialValue !== "object" ? "" :
    initialValue.value ?? initialValue.min + "–" + initialValue.max);
  const approximate = input("", { type: "checkbox", checked: Boolean(initialValue?.approximate) });
  const raw = input(initialValue?.raw || "");
  const origin = select([["documented", "资料记载"], ["inferred", "推断"], ["hypothesis", "假设"]], initialOrigin || "documented");
  const rationale = area(initialRationale || "", 2);
  const objectRow = label("目标实体", object);
  const valueRow = label("文字内容", text);
  const dimensions = el("div");
  dimensions.append(row(label("测量项目", quantity), label("数值或范围", numbers), label("单位", unit)),
    label("原文表达", raw), label("约数", approximate));
  function adjust() {
    for (const option of predicate.options) option.disabled = !allowPredicate(definitions[option.value]);
    if (predicate.selectedOptions[0]?.disabled) predicate.value = [...predicate.options].find(o => !o.disabled)?.value || "";
    const definition = definitions[predicate.value];
    objectRow.hidden = definition?.object_kind !== "entity";
    valueRow.hidden = definition?.object_kind !== "text";
    dimensions.hidden = definition?.object_kind !== "dimension";
  }
  predicate.addEventListener("change", adjust);
  adjust();
  function value() {
    const key = predicate.value;
    if (!key) throw new Error("请选择本体允许的关系或属性。");
    const result = { predicate: key, origin: origin.value };
    if (rationale.value.trim()) result.rationale = rationale.value.trim();
    const definition = definitions[key];
    if (definition.object_kind === "entity") {
      if (!importMode && !object.value) throw new Error("请选择关系的目标实体。");
      if (object.value) result.object_id = object.value;
    } else if (definition.object_kind === "dimension") {
      const parts = numbers.value.trim().split(/\s*(?:–|—|~|～|至|-)\s*/);
      const values = parts.map(Number);
      if (!quantity.value.trim() || !raw.value.trim() || ![1, 2].includes(parts.length) ||
          values.some(number => !Number.isFinite(number) || number <= 0)) throw new Error("填写测量项目、数值、单位和原文。");
      result.value = { quantity: quantity.value.trim(), unit: unit.value, raw: raw.value.trim(),
        approximate: approximate.checked, ...(values.length === 1 ? { value: values[0] } : { min: values[0], max: values[1] }) };
    } else {
      if (!text.value.trim()) throw new Error("请填写事实内容。");
      result.value = text.value.trim();
    }
    return result;
  }
  return { fields: [label("关系或属性", predicate), objectRow, valueRow, dimensions,
    row(label("依据性质", origin), label("推断理由或备注", rationale))], value, adjust,
    predicate, objectRow };
}

async function manualEvidence(title, rawText) {
  const text = rawText.replace(/\r\n?/g, "\n").trim();
  if (!text) return { operations: [] };
  const filename = (title.trim() || "手工录入原文").replace(/[/:\\\r\n]/g, "_").replace(/\.(?:md|txt)$/i, "") + ".txt";
  const bytes = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text)));
  const hash = Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join("");
  const sourceId = "source:upload-" + hash;
  const previous = [...evidence.values()].find(item => item.source_id === sourceId && item.quote === text);
  const operations = [];
  if (!sources.has(sourceId)) operations.push({ table: "sources", id: sourceId, action: "create",
    record: { id: sourceId, title: filename, resource_id: "resource:upload-" + hash, filename, format: "txt",
      source_type: "uploaded_text", text_content: text, content_sha256: hash } });
  if (previous) return { id: previous.id, operations };
  const id = "evidence:manual-" + crypto.randomUUID();
  const end = text.split("\n").length;
  operations.push({ table: "evidence", id, action: "create", record: { id, source_id: sourceId,
    start_line: 1, end_line: end, locator: end === 1 ? "第 1 行" : "第 1–" + end + " 行", quote: text,
    transcription: "embedded_text", check_status: "pending", scope_note: "管理员录入的文本摘录。" } });
  return { id, operations };
}

function openFact(record, subjectId, targetId) {
  const subject = select(entityOptions(), subjectId);
  const form = factFields(record?.predicate || (targetId ? "HAS_PART" : "DESCRIPTION"), record?.value,
    record?.object_id || targetId, record?.origin, record?.rationale, definition => {
      const kind = entities.get(subject.value)?.kind;
      return definition.object_kind === "entity" ? definition.endpoint_pairs.some(pair => pair[0] === kind)
        : definition.subject_kinds.includes(kind);
    });
  subject.addEventListener("change", form.adjust);
  const refs = new Set(record?.evidence_ids || []);
  const picker = el("details");
  const list = el("div", null, "evidence-picker");
  for (const item of evidence.values()) {
    const title = (sources.get(item.source_id)?.title || item.source_id) + " · " + item.locator + " · " + item.quote.slice(0, 48);
    list.append(check(title, refs.has(item.id), enabled => enabled ? refs.add(item.id) : refs.delete(item.id)));
  }
  picker.append(el("summary", "链接已有证据"), list);
  const sourceTitle = input("", { maxLength: 180 });
  const sourceText = area("", 3);
  const newProof = el("details");
  newProof.append(el("summary", "粘贴新证据"), label("出处名称", sourceTitle), label("引用原文", sourceText));
  openEditor(record ? "编辑事实" : "新增事实", "存入知识库",
    [label("主体实体", subject), ...form.fields, picker, newProof], async () => {
      const id = record?.id || "fact:manual-" + crypto.randomUUID();
      const update = form.value();
      const proof = await manualEvidence(sourceTitle.value, sourceText.value);
      const item = { ...record, ...update, id, subject_id: subject.value,
        evidence_ids: [...new Set([...refs, ...(proof.id ? [proof.id] : [])])], review_status: "pending",
        extraction: record?.extraction || { method: "manual_admin", run_id: "run:manual-admin" } };
      if (!update.object_id) delete item.object_id;
      if (update.value === undefined) delete item.value;
      if (!update.rationale) delete item.rationale;
      delete item.review;
      await commitOperations([...proof.operations, { table: "facts", id, action: record ? "update" : "create", record: item }], "编辑图谱事实");
      highlight(subject.value, true);
      notice("事实已入库，等待发布。");
    });
}

function makeCard(labeled, heading, text) {
  const card = el("article", null, "card");
  const header = el("div", null, "card-heading");
  if (labeled) header.append(labeled);
  header.append(el("h3", heading));
  card.append(header);
  if (text) card.append(paragraph(text));
  return card;
}

function publish(records) {
  const gathered = new Map();
  function add(table, id) {
    if (!id || gathered.has(id)) return;
    if (table === "entities" && entities.get(id)?.publication_status !== "draft") return;
    gathered.set(id, { table, id, action: "review", review_status: "confirmed", note: "管理员确认发布" });
    if (table === "entities") add("entities", entities.get(id)?.scope_id);
    else {
      const fact = view.dataset.facts.find(item => item.id === id);
      add("entities", fact?.subject_id);
      add("entities", fact?.object_id);
    }
  }
  for (const pair of records) add(...pair);
  if (!gathered.size) return notice("请选择要发布的记录。", true);
  const operations = [...gathered.values()];
  const names = operations.map(op => op.table === "entities" ? entryLabel(op.id) :
    entryLabel(view.dataset.facts.find(fact => fact.id === op.id)?.subject_id) + " · " + op.id);
  confirmChange("发布知识", "将发布 " + operations.length + " 条记录，含所选事实的待发布实体：" + names.join("、"),
    operations, () => { publicationSelection.clear(); renderPublication(); });
}

function renderPublication() {
  if (!view) return;
  const draftEntities = view.dataset.entities.filter(entity => entity.publication_status === "draft");
  const draftFacts = view.dataset.facts.filter(fact => fact.publication_managed && fact.review_status !== "confirmed");
  const records = [...draftEntities.map(item => ["entities", item]), ...draftFacts.map(item => ["facts", item])];
  const active = new Set(records.map(([, item]) => item.id));
  for (const id of publicationSelection) if (!active.has(id)) publicationSelection.delete(id);
  $("#pending-count").textContent = records.length || "";
  $("#publication-list").replaceChildren(...records.map(([table, item]) => {
    const title = table === "entities" ? item.label : entryLabel(item.subject_id) + " · " + factValue(item);
    const card = makeCard(el("span", tableLabels[table], "badge warn"), title, item.id);
    card.append(check("选中发布", publicationSelection.has(item.id), enabled =>
      enabled ? publicationSelection.add(item.id) : publicationSelection.delete(item.id)));
    card.append(button("查看图谱", () => { go("graph"); highlight(table === "entities" ? item.id : item.subject_id, true); }, "quiet"));
    return card;
  }));
  if (!records.length) $("#publication-list").append(paragraph("暂无通过管理端入库、等待发布的记录。"));
  $("#publish-selected").onclick = () => publish(records.filter(([, item]) => publicationSelection.has(item.id)).map(([table, item]) => [table, item.id]));
}

async function renderTrash() {
  const result = await api("/api/v1/internal/deleted?page=" + trashPage + "&page_size=25");
  $("#trash-prev").disabled = trashPage <= 1;
  $("#trash-next").disabled = trashPage * 25 >= result.total;
  $("#trash-list").replaceChildren(...result.items.map(item => {
    const card = makeCard(el("span", tableLabels[item.table], "badge"), item.record.label || item.record.title || item.record.id,
      item.deleted_revision + " · " + item.deleted_reason);
    card.append(button("恢复", () => confirmChange("恢复记录", "恢复「" + item.record.id + "」？",
      [{ table: item.table, id: item.record.id, action: "restore" }], renderTrash)));
    return card;
  }));
  if (!result.items.length) $("#trash-list").append(paragraph("回收站暂无记录。"));
}

function importBody() { return { ...upload, candidates: analysis.candidates }; }

async function recheck() {
  const checked = await api(admin + "/imports/check", importBody());
  Object.assign(analysis, checked);
  importSelection.clear();
  renderImport();
}

function renderImport() {
  if (!analysis) return;
  $("#review").hidden = false;
  $("#import-summary").textContent = upload.filename + " · " + analysis.items.length + " 条建议 · " +
    analysis.unrelated.length + " 段无关内容 · " + analysis.graph_revision;
  const filter = $("#import-filter").value;
  const parent = $("#import-candidates");
  const unrelated = $("#unrelated-list");
  parent.replaceChildren();
  unrelated.replaceChildren();
  if (analysis.warnings.length) parent.append(paragraph(analysis.warnings.join(" "), "error"));
  for (const item of analysis.items) {
    if (filter && filter !== item.status) continue;
    const candidate = analysis.candidates[item.index];
    const value = candidate.object?.label || factValue({ value: candidate.value });
    const card = makeCard(el("span", statusLabels[item.status], "badge " + item.status),
      candidate.subject.label + " · " + (value || predicateLabel(candidate.predicate)), item.message);
    const columns = el("div", null, "review-grid");
    const original = el("div");
    original.append(el("h3", item.evidence?.locator || "上传原文"), el("blockquote", candidate.quote));
    columns.append(original);
    const match = el("div");
    match.append(el("h3", "现有图谱"));
    if (!item.matches.length) match.append(paragraph("暂无可直接比对的记录。"));
    for (const fact of item.matches.slice(0, 4)) {
      const details = el("details");
      details.append(el("summary", entryLabel(fact.subject_id) + " · " + factValue(fact)),
        ...fact.evidence_ids.map(proofView),
        button("在图上查看", () => { go("graph"); highlight(fact.subject_id, true); }));
      match.append(details);
    }
    columns.append(match);
    card.append(columns);
    const actions = el("div", null, "actions");
    actions.append(button("编辑并重新检查", () => editProposal(item.index)));
    if (item.subject_id) actions.append(button("在图上预览", () => {
      graphPreview = { item, candidate };
      graphScopes[graphLayout] = "all";
      ontologySelection = "";
      neighborhood = true;
      selected = item.subject_id;
      go("graph");
    }));
    if (item.status === "duplicate" && item.evidence && item.matches[0] && !item.matches[0].evidence_ids.includes(item.evidence.id)) {
      actions.append(check("给原事实补充证据", importSelection.has(item.index), enabled =>
        selectImport(item.index, enabled, "evidence")));
    }
    if (["new", "conflict", "possible_duplicate"].includes(item.status)) {
      actions.append(check(item.status === "new" ? "选中入库" : "已核对，作为独立记载入库",
        importSelection.has(item.index), enabled => selectImport(item.index, enabled, "add", item.status !== "new")));
    }
    card.append(actions);
    parent.append(card);
  }
  if (!filter || filter === "unrelated") {
    for (const item of analysis.unrelated) {
      const card = makeCard(el("span", "无关", "badge duplicate"), "第 " + item.start_line + " 行", item.reason);
      card.append(el("blockquote", item.quote));
      unrelated.append(card);
    }
  }
  if (!parent.childElementCount && !unrelated.childElementCount) parent.append(paragraph("该筛选下没有条目。"));
  $("#import-commit").disabled = !importSelection.size;
  $("#import-commit").textContent = importSelection.size ? "选中项入库（" + importSelection.size + "）" : "选中项入库";
}

function selectImport(index, enabled, action, acknowledgeConflict = false) {
  if (enabled) importSelection.set(index, { index, action, acknowledge_conflict: acknowledgeConflict });
  else importSelection.delete(index);
  $("#import-commit").disabled = !importSelection.size;
  $("#import-commit").textContent = importSelection.size ? "选中项入库（" + importSelection.size + "）" : "选中项入库";
}

function editProposal(index) {
  const proposal = analysis.candidates[index];
  const subject = select(entityOptions(), proposal.subject.id || "");
  const name = input(proposal.subject.label, { required: true });
  const kinds = [["", "待确认"], ...Object.keys(view.ontology.entity_kinds).map(key => [key, kindLabels[key] || key])];
  const kind = select(kinds, proposal.subject.kind || "");
  const scope = select(entityOptions(), proposal.subject.scope_id || "");
  subject.addEventListener("change", () => { const entity = entities.get(subject.value); if (entity) {
    name.value = entity.label; kind.value = entity.kind; scope.value = entity.scope_id || "";
  } });
  const targetLabel = input(proposal.object?.label || "");
  const targetKind = select(kinds, proposal.object?.kind || "");
  const targetScope = select(entityOptions(), proposal.object?.scope_id || "");
  const form = factFields(proposal.predicate, proposal.value, proposal.object?.id, proposal.origin,
    proposal.rationale, () => true, true);
  form.objectRow.append(row(label("新目标名称", targetLabel), label("新目标类型", targetKind), label("新目标归属", targetScope)));
  const quote = area(proposal.quote, 5);
  const start = input(proposal.start_line ?? "", { type: "number", min: 1 });
  const scopeConfirmed = input("", { type: "checkbox", checked: Boolean(proposal.scope_confirmed) });
  openEditor("编辑导入建议", "保存并重新检查", [label("绑定已有主体", subject),
    row(label("主体名称", name), label("主体类型", kind), label("主体归属", scope)),
    ...form.fields, label("支持原文（须与上传文本一致）", quote),
    row(label("引用起始行（可选）", start), label("已核对主体归属", scopeConfirmed))], async () => {
      const record = form.value();
      const subjectRef = { label: name.value.trim(), ...(subject.value ? { id: subject.value } : {}),
        ...(kind.value ? { kind: kind.value } : {}), ...(scope.value ? { scope_id: scope.value } : {}) };
      if (view.ontology.predicates[record.predicate].object_kind === "entity") {
        const target = entities.get(record.object_id);
        record.object = target ? { id: target.id, label: target.label } : { label: targetLabel.value.trim(),
          ...(targetKind.value ? { kind: targetKind.value } : {}), ...(targetScope.value ? { scope_id: targetScope.value } : {}) };
        delete record.object_id;
      }
      const previous = analysis.candidates[index];
      analysis.candidates[index] = { ...record, subject: subjectRef, quote: quote.value,
        ...(start.value ? { start_line: Number(start.value) } : {}), scope_confirmed: scopeConfirmed.checked };
      try { await recheck(); } catch (error) { analysis.candidates[index] = previous; throw error; }
      notice("已按修改后的内容重新检查。");
    });
}

const credentialField = $("#token");
const passwordStore = window.PasswordCredential && navigator.credentials;
async function rememberCredential(password) {
  try {
    await passwordStore.store(new PasswordCredential({ id: loginAccount, name: "楚车知识管理", password }));
  } catch {
    // The browser may decline saving; the authenticated session still works.
  }
}

if (passwordStore) {
  $("#remember-option").hidden = false;
  passwordStore.get({ password: true, mediation: "silent" }).then(credential => {
    if (credential?.id === loginAccount && !credentialField.value && !$("#login").hidden) {
      credentialField.value = credential.password;
    }
  }).catch(() => {});
}

$("#login-form").addEventListener("submit", event => {
  event.preventDefault();
  run(async () => {
    token = credentialField.value.trim();
    try { await refresh(); } catch (error) { token = ""; throw error; }
    const remember = $("#remember-token").checked;
    if (remember && passwordStore) void rememberCredential(token);
    credentialField.value = "";
    $("#login").hidden = true;
    $("#workspace").hidden = false;
    $("#logout").hidden = false;
    notice("");
    go("graph");
  }, event.submitter);
});

$("#logout").addEventListener("click", () => location.reload());
$("#tabs").addEventListener("click", event => { const tab = event.target.closest("button")?.dataset.tab; if (tab) go(tab); });
$("#search").addEventListener("input", renderGraphPage);
$("#add-entity").addEventListener("click", () => openEntity());
$("#refresh").addEventListener("click", event => run(refresh, event.currentTarget));
$("#grid-layout").addEventListener("click", () => { graphLayout = "grid"; renderGraphPage(); });
$("#network-layout").addEventListener("click", () => { graphLayout = "network"; renderGraphPage(); });
$("#toggle-ontology").addEventListener("click", () => {
  showOntology = !showOntology;
  if (!showOntology) ontologySelection = "";
  renderGraphPage();
});
$("#graph-scope").addEventListener("change", event => {
  graphScopes[graphLayout] = event.target.value;
  graphPreview = undefined;
  renderGraphPage();
});
paintMapLegend($("#network-legend"));
$("#overview").addEventListener("click", () => { neighborhood = false; renderGraphPage(); });
$("#neighborhood").addEventListener("click", () => { neighborhood = true; renderGraphPage(); });
$("#zoom-out").addEventListener("click", () => {
  if (graphLayout === "network") network.zoomBy(1 / 1.2);
  else { zoom = Math.max(.65, zoom - .15); renderGraphPage(); }
});
$("#zoom-in").addEventListener("click", () => {
  if (graphLayout === "network") network.zoomBy(1.2);
  else { zoom = Math.min(1.6, zoom + .15); renderGraphPage(); }
});
$("#fit-network").addEventListener("click", () => network.fit());
$("#trash-prev").addEventListener("click", () => { --trashPage; run(renderTrash); });
$("#trash-next").addEventListener("click", () => { ++trashPage; run(renderTrash); });
$("#close-editor").addEventListener("click", () => $("#editor").close());
$("#editor-form").addEventListener("submit", async event => {
  event.preventDefault();
  const save = $("#save-editor");
  if (save.disabled) return;
  save.disabled = true;
  $("#editor-error").textContent = "";
  try { await editorSave(); $("#editor").close(); }
  catch (error) { $("#editor-error").textContent = error.message; }
  finally { save.disabled = false; }
});

const importFilter = $("#import-filter");
for (const [value, caption] of [["", "全部"], ...Object.entries(statusLabels)]) {
  const choice = el("option", caption);
  choice.value = value;
  importFilter.append(choice);
}
importFilter.addEventListener("change", renderImport);
$("#upload-form").addEventListener("submit", event => {
  event.preventDefault();
  run(async () => {
    const file = $("#upload-file").files[0];
    if (!file) return;
    $("#upload-status").textContent = "正在把材料和当前图谱交给 AI 分析…";
    try {
      if (!/\.(md|txt)$/i.test(file.name) || file.size > 320003) throw new Error("请选择少于 8 万字符的 Markdown 或 TXT。");
      let text;
      try { text = new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer()); }
      catch { throw new Error("请选择 UTF-8 编码的文本文件。"); }
      if (text.length > 80000 || !text.trim()) throw new Error("请选择非空、少于 8 万字符的 Markdown 或 TXT。");
      const nextUpload = { filename: file.name, text };
      const nextAnalysis = await api(admin + "/imports/analyze", nextUpload);
      upload = nextUpload;
      analysis = nextAnalysis;
      importSelection.clear();
      importFilter.value = "";
      renderImport();
      notice("");
    } finally { $("#upload-status").textContent = ""; }
  }, event.submitter);
});
$("#recheck").addEventListener("click", event => run(async () => { await recheck(); notice("已查最新图谱。"); }, event.currentTarget));
$("#import-commit").addEventListener("click", () => {
  const count = importSelection.size;
  openEditor("确认入库", "存入知识库", [paragraph("将保存 " + count + " 条已选建议，随后可在待发布页继续核对。")], async () => {
    await api(admin + "/imports/commit", { ...importBody(), base_graph_revision: analysis.graph_revision,
      selections: [...importSelection.values()] }, crypto.randomUUID());
    await refresh();
    await recheck();
    notice("选中建议已入库，等待发布。");
  });
});
