const physicalKinds = new Set([
  "ComponentType", "Component", "Chariot", "ReferenceSpecimen", "ComponentRegion", "StructuralRegionType",
  "Material", "PreservationFeature", "SurfaceFinish", "DecorationMotif", "HarnessRole",
]);
const knowledgeRelations = new Set([
  "HAS_PART", "HAS_REGION", "TENON_JOINT_WITH", "HAS_ASSOCIATED_COMPONENT", "INSTANCE_OF",
  "HAS_MATERIAL", "HAS_PRESERVED_FEATURE", "HAS_SURFACE_FINISH", "HAS_DECORATION_MOTIF",
]);

const mapRegions = {
  wheel: { label: "车轮", color: "#347b65", x: -335, y: -195 },
  axle: { label: "车轴与轴端", color: "#48748c", x: 37, y: -232 },
  traction: { label: "车舆与牵引", color: "#a3713d", x: 381, y: -100 },
  harness: { label: "系驾马具", color: "#87678e", x: 261, y: 238 },
  shared: { label: "材质与外观", color: "#718140", x: -82, y: 282 },
  reference: { label: "其他记录", color: "#6b7b79", x: -365, y: 173 },
};

export const ontologyRegions = {
  objects: { label: "器物与部件", color: "#347b65", x: -330, y: 0 },
  appearance: { label: "外观与系驾", color: "#718140", x: -96, y: 0 },
  reference: { label: "资料与语境", color: "#48748c", x: 135, y: 0 },
  metadata: { label: "教学与模型", color: "#87678e", x: 368, y: 0 },
};
const ontologyPrefix = "@ontology/";
const ontologyId = kind => ontologyPrefix + kind;

export function ontologyKind(id) {
  return id.startsWith(ontologyPrefix) ? id.slice(ontologyPrefix.length) : "";
}
const ontologyGroups = {
  ComponentType: "objects", Chariot: "objects", Component: "objects", ReferenceSpecimen: "objects",
  ComponentRegion: "objects", StructuralRegionType: "objects",
  Material: "appearance", PreservationFeature: "appearance", SurfaceFinish: "appearance",
  DecorationMotif: "appearance", HarnessRole: "appearance",
  Connection: "metadata", Pose: "metadata", ModelVersion: "metadata", AssemblyStep: "metadata", Subsystem: "metadata",
};

export function projectOntology(ontology, labels) {
  const entities = Object.entries(ontology.entity_kinds).map(([id, definition]) => ({
    id, label: labels[id] || id, kind: "OntologyKind", definition,
  }));
  const knownKinds = new Set(entities.map(node => node.id));
  const regions = Object.fromEntries(entities.map(node => [node.id, ontologyGroups[node.id] || "reference"]));
  const rules = Object.entries(ontology.predicates).map(([id, rule]) => ({ id, ...rule }));
  const facts = rules.flatMap(rule => (rule.endpoint_pairs || [])
    .filter(([subject, target]) => knownKinds.has(subject) && knownKinds.has(target))
    .map(([subject_id, object_id]) => ({ subject_id, object_id, predicate: rule.id })));
  return { entities, facts, regions, rules };
}

export function filterKnowledge(entities, facts) {
  const nodes = entities.filter(entity => physicalKinds.has(entity.kind) &&
    !/[（(]教学(?:区域|功能集合)[）)]/.test(entity.label) &&
    !entity.note?.includes("与楚车知识无关"));
  const allowed = new Set(nodes.map(entity => entity.id));
  return { entities: nodes, facts: facts.filter(fact => allowed.has(fact.subject_id) &&
    (!fact.object_id || (allowed.has(fact.object_id) && knowledgeRelations.has(fact.predicate)))) };
}

export function networkLinks(facts, allowed, focus, includeLoops = false) {
  const result = new Map();
  for (const fact of facts) {
    const { subject_id: from, object_id: to } = fact;
    if (!to || (!includeLoops && from === to) || !allowed.has(from) || !allowed.has(to)) continue;
    if (focus && from !== focus && to !== focus) continue;
    const [left, right] = [from, to].sort();
    const key = left + "|" + right;
    const existing = result.get(key);
    const draft = Boolean(fact.publication_managed && fact.review_status !== "confirmed");
    if (existing) existing.draft &&= draft;
    else result.set(key, { from: left, to: right, draft });
  }
  return [...result.values()];
}

export function layoutNetwork(entities, links, regions, focus, palette = mapRegions) {
  const byId = new Map();
  const members = new Map();
  const degree = new Map();
  for (const link of links) {
    degree.set(link.from, (degree.get(link.from) || 0) + 1);
    if (link.to !== link.from) degree.set(link.to, (degree.get(link.to) || 0) + 1);
  }
  for (const entity of [...entities].sort((a, b) => a.id.localeCompare(b.id))) {
    const group = palette[regions[entity.id]] ? regions[entity.id] : "reference";
    const node = { ...entity, group, degree: degree.get(entity.id) || 0, x: 0, y: 0 };
    byId.set(node.id, node);
    if (!members.has(group)) members.set(group, []);
    members.get(group).push(node);
  }
  if (focus && byId.has(focus)) {
    const neighbors = [...byId.values()].filter(node => node.id !== focus)
      .sort((a, b) => a.group.localeCompare(b.group) || a.label.localeCompare(b.label, "zh-CN"));
    const radius = Math.max(158, neighbors.length * 14);
    for (const [index, node] of neighbors.entries()) {
      const angle = index * Math.PI * 2 / neighbors.length - Math.PI / 2;
      node.x = Math.cos(angle) * radius;
      node.y = Math.sin(angle) * radius * .84;
    }
    return byId;
  }

  const nodes = [...byId.values()];
  const springs = links.filter(link => link.from !== link.to).map(link => [byId.get(link.from), byId.get(link.to)]);
  const indexOf = new Map(nodes.map((node, index) => [node.id, index]));
  for (const [group, items] of members) {
    const { x, y } = palette[group];
    items.sort((a, b) => b.degree - a.degree || a.id.localeCompare(b.id));
    for (const [index, node] of items.entries()) {
      const angle = index * 2.399963;
      const radius = Math.sqrt(index) * 27;
      node.x = x + Math.cos(angle) * radius;
      node.y = y + Math.sin(angle) * radius;
    }
  }

  // Short springs draw related terms together while the regional anchors keep
  // unrelated subgraphs apart. The loop settles once per data or focus change.
  for (let step = 0; step < 116; step++) {
    const dx = new Float64Array(nodes.length);
    const dy = new Float64Array(nodes.length);
    const damping = .86 - step * .004;
    for (const [index, node] of nodes.entries()) {
      const anchor = palette[node.group];
      const weight = node.degree ? .015 : .025;
      dx[index] = (anchor.x - node.x) * weight;
      dy[index] = (anchor.y - node.y) * weight;
      for (let j = 0; j < index; j++) {
        const neighbor = nodes[j];
        const x = node.x - neighbor.x;
        const y = node.y - neighbor.y;
        const distanceSquared = Math.max(1, x * x + y * y);
        if (distanceSquared > 11000) continue;
        const force = Math.min(1.8, 670 / distanceSquared);
        dx[index] += force * x;
        dy[index] += force * y;
        dx[j] -= force * x;
        dy[j] -= force * y;
      }
    }
    for (const [from, to] of springs) {
      const x = to.x - from.x;
      const y = to.y - from.y;
      const distance = Math.max(1, Math.hypot(x, y));
      const same = from.group === to.group;
      const length = same ? 65 : 180;
      const force = (distance - length) / distance * (same ? .19 : .025);
      const a = indexOf.get(from.id);
      const b = indexOf.get(to.id);
      dx[a] += x * force;
      dy[a] += y * force;
      dx[b] -= x * force;
      dy[b] -= y * force;
    }
    for (const [index, node] of nodes.entries()) {
      node.x += Math.max(-11, Math.min(11, dx[index])) * damping;
      node.y += Math.max(-11, Math.min(11, dy[index])) * damping;
    }
  }
  return byId;
}

const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
const labelPriority = { Chariot: 3, ComponentType: 2, ReferenceSpecimen: 1 };

export function layeredLayout(knowledgePoints, ontologyPoints) {
  const lower = [...knowledgePoints.values()];
  if (!ontologyPoints) {
    return new Map(lower.map(node => [node.id, { ...node, color: mapRegions[node.group].color }]));
  }
  const upper = [...ontologyPoints.values()];
  const lowerTop = lower.length ? Math.min(...lower.map(node => node.y)) : 0;
  const upperBottom = upper.length ? Math.max(...upper.map(node => node.y)) : 0;
  return new Map([
    ...upper.map(node => [ontologyId(node.id), { ...node, id: ontologyId(node.id),
      x: node.x * 1.65, y: (node.y - upperBottom) * .64 - 58, color: ontologyRegions[node.group].color }]),
    ...lower.map(node => [node.id, { ...node, y: node.y - lowerTop + 76, color: mapRegions[node.group].color }]),
  ]);
}

export class NetworkMap {
  constructor(container, choose, reportZoom) {
    this.container = container;
    this.choose = choose;
    this.reportZoom = reportZoom;
    this.points = new Map();
    this.buttons = new Map();
    this.links = [];
    this.near = new Set();
    this.active = new Set();
    this.canvas = document.createElement("canvas");
    this.canvas.setAttribute("aria-hidden", "true");
    this.layer = document.createElement("div");
    this.layer.className = "network-layer";
    this.divider = document.createElement("div");
    this.divider.className = "network-divider";
    this.divider.hidden = true;
    this.divider.setAttribute("aria-hidden", "true");
    this.empty = document.createElement("p");
    this.empty.className = "network-empty muted";
    this.empty.textContent = "当前筛选下没有实体。";
    container.replaceChildren(this.canvas, this.divider, this.layer, this.empty);
    this.frame = 0;
    this.scale = 1;
    this.position = { x: 0, y: 0 };
    this.size = { width: 0, height: 0 };
    this.wheel = event => {
      event.preventDefault();
      const rect = container.getBoundingClientRect();
      const delta = event.deltaY * (event.deltaMode === 1 ? 14 : 1);
      this.zoomBy(Math.exp(-delta * .0014), event.clientX - rect.left, event.clientY - rect.top);
    };
    container.addEventListener("wheel", this.wheel, { passive: false });
    container.addEventListener("pointerdown", event => {
      if (event.button !== 0 || event.target.closest(".network-node")) return;
      this.drag = { id: event.pointerId, x: event.clientX, y: event.clientY };
      container.setPointerCapture(event.pointerId);
      container.classList.add("panning");
    });
    container.addEventListener("pointermove", event => {
      if (this.drag?.id !== event.pointerId) return;
      this.position.x += event.clientX - this.drag.x;
      this.position.y += event.clientY - this.drag.y;
      this.drag.x = event.clientX;
      this.drag.y = event.clientY;
      this.schedule();
    });
    for (const name of ["pointerup", "pointercancel", "lostpointercapture"]) {
      container.addEventListener(name, event => {
        if (this.drag?.id !== event.pointerId) return;
        this.drag = null;
        container.classList.remove("panning");
      });
    }
    container.addEventListener("keydown", event => {
      if (event.target !== container) return;
      const moves = { ArrowLeft: [45, 0], ArrowRight: [-45, 0], ArrowUp: [0, 45], ArrowDown: [0, -45] };
      if (moves[event.key]) {
        this.position.x += moves[event.key][0];
        this.position.y += moves[event.key][1];
        this.schedule();
      } else if (event.key === "+" || event.key === "=") this.zoomBy(1.2);
      else if (event.key === "-") this.zoomBy(1 / 1.2);
      else if (event.key === "0" || event.key === "Home") this.fit();
      else return;
      event.preventDefault();
    });
    new ResizeObserver(() => this.resize()).observe(container);
  }

  setGraph(entities, facts, regions, selected, neighborhood, schema, selectedKind) {
    const ids = new Set(entities.map(entity => entity.id));
    const focus = neighborhood && ids.has(selected) ? selected : "";
    const links = networkLinks(facts, ids, focus);
    const visible = focus ? new Set([focus, ...links.flatMap(link => [link.from, link.to])]) : ids;
    const nodes = entities.filter(entity => visible.has(entity.id));
    const schemaEntities = schema?.entities || [];
    const schemaLinks = schema ? networkLinks(schema.facts, new Set(schemaEntities.map(node => node.id)), "", true) : [];
    const key = JSON.stringify([focus, nodes.map(node => [node.id, regions[node.id]]), links.map(link => [link.from, link.to]),
      schema ? schemaEntities.map(node => node.id) : null, schemaLinks.map(link => [link.from, link.to])]);
    const nodeKind = nodes.find(node => node.id === selected)?.kind;
    this.showOntology = Boolean(schema);
    this.active = new Set([selected]);
    if (schema && (selectedKind || nodeKind)) this.active.add(ontologyId(selectedKind || nodeKind));
    this.links = [
      ...schemaLinks.map(link => ({ ...link, from: ontologyId(link.from), to: ontologyId(link.to) })),
      ...links,
    ];
    this.near = new Set(this.links.filter(link => this.active.has(link.from) || this.active.has(link.to))
      .flatMap(link => [link.from, link.to]));
    if (key !== this.key) {
      this.key = key;
      this.points = layeredLayout(layoutNetwork(nodes, links, regions, focus),
        schema ? layoutNetwork(schemaEntities, schemaLinks, schema.regions, "", ontologyRegions) : null);
      this.fit();
    }
    this.bridge = nodeKind && (!selectedKind || selectedKind === nodeKind) && this.points.has(ontologyId(nodeKind))
      ? { from: selected, to: ontologyId(nodeKind) } : null;
    this.syncButtons([...schemaEntities.map(node => ({ ...node, id: ontologyId(node.id) })), ...nodes]);
    this.empty.hidden = this.points.size > 0;
    this.resize();
    this.schedule();
  }

  syncButtons(nodes) {
    const present = new Set(nodes.map(node => node.id));
    for (const [id, button] of this.buttons) {
      if (present.has(id)) continue;
      button.remove();
      this.buttons.delete(id);
    }
    for (const node of nodes) {
      let button = this.buttons.get(node.id);
      if (!button) {
        button = document.createElement("button");
        button.type = "button";
        button.className = "network-node";
        button.dataset.id = node.id;
        button.append(document.createElement("span"));
        button.addEventListener("click", () => this.choose(node.id));
        this.buttons.set(node.id, button);
        this.layer.append(button);
      }
      const point = this.points.get(node.id);
      button.style.setProperty("--node-color", point.color);
      button.classList.toggle("draft", node.publication_status === "draft");
      button.classList.toggle("active", this.active.has(node.id));
      button.classList.toggle("near", this.near.has(node.id));
      button.setAttribute("aria-label", node.label);
      button.setAttribute("aria-pressed", String(this.active.has(node.id)));
      button.title = node.label;
      button.firstChild.textContent = node.label;
    }
  }

  resize() {
    const width = this.container.clientWidth, height = this.container.clientHeight;
    if (!width || !height || (width === this.size.width && height === this.size.height)) return;
    if (this.size.width) {
      this.position.x += (width - this.size.width) / 2;
      this.position.y += (height - this.size.height) / 2;
    }
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = Math.round(width * dpr);
    this.canvas.height = Math.round(height * dpr);
    const initial = !this.size.width;
    this.size = { width, height, dpr };
    if (initial) this.fit();
    this.schedule();
  }

  fit() {
    if (!this.size.width) return;
    const { width, height } = this.size;
    const nodes = [...this.points.values()];
    const xs = nodes.length ? nodes.map(node => node.x) : [0];
    const ys = nodes.length ? nodes.map(node => node.y) : [0];
    const left = Math.min(...xs), right = Math.max(...xs);
    const top = Math.min(...ys), bottom = Math.max(...ys);
    this.scale = clamp(Math.min((width - 126) / (right - left || 1), (height - 98) / (bottom - top || 1)), .15, 1.5);
    this.position = { x: width / 2 - (left + right) / 2 * this.scale,
      y: height / 2 - (top + bottom) / 2 * this.scale };
    this.reportZoom(this.scale);
    this.schedule();
  }

  zoomBy(factor, x = this.size.width / 2, y = this.size.height / 2) {
    const before = this.scale;
    this.scale = clamp(before * factor, .15, 3.5);
    this.position.x = x - (x - this.position.x) * this.scale / before;
    this.position.y = y - (y - this.position.y) * this.scale / before;
    this.reportZoom(this.scale);
    this.schedule();
  }

  centerOn(id) {
    const point = this.points.get(id);
    if (!point) return;
    this.position = { x: this.size.width / 2 - point.x * this.scale, y: this.size.height / 2 - point.y * this.scale };
    this.schedule();
  }

  schedule() {
    if (this.frame) return;
    this.frame = requestAnimationFrame(() => { this.frame = 0; this.paint(); });
  }

  paint() {
    const { width, height, dpr } = this.size;
    if (!width) return;
    const pen = this.canvas.getContext("2d");
    pen.setTransform(dpr, 0, 0, dpr, 0, 0);
    pen.clearRect(0, 0, width, height);
    this.divider.hidden = !this.showOntology || this.position.y < 0 || this.position.y > height;
    this.divider.style.top = this.position.y + "px";
    const screen = new Map([...this.points].map(([id, point]) => [id, {
      x: point.x * this.scale + this.position.x, y: point.y * this.scale + this.position.y,
    }]));
    for (const active of [false, true]) {
      for (const edge of this.links) {
        if ((this.active.has(edge.from) || this.active.has(edge.to)) !== active) continue;
        const a = screen.get(edge.from), b = screen.get(edge.to);
        pen.strokeStyle = active ? "#387963" : this.near.size ? "#e3eae4" : "#c9d7cc";
        pen.lineWidth = active ? 1.65 : .9;
        pen.setLineDash(edge.draft ? [4, 3] : []);
        pen.beginPath();
        pen.moveTo(a.x, a.y);
        if (edge.from === edge.to) {
          pen.bezierCurveTo(a.x - 24, a.y - 30, a.x + 24, a.y - 30, a.x, a.y);
        } else pen.lineTo(b.x, b.y);
        pen.stroke();
      }
    }
    if (this.bridge) {
      const a = screen.get(this.bridge.from), b = screen.get(this.bridge.to);
      const bend = (a.y + b.y) / 2;
      pen.strokeStyle = "#4c7792";
      pen.lineWidth = 1.35;
      pen.setLineDash([4, 4]);
      pen.beginPath();
      pen.moveTo(a.x, a.y);
      pen.bezierCurveTo(a.x, bend, b.x, bend, b.x, b.y);
      pen.stroke();
    }
    const boxes = [];
    const ordered = [...this.points.values()].sort((a, b) =>
      Number(this.active.has(b.id)) - Number(this.active.has(a.id)) ||
      Number(this.near.has(b.id)) - Number(this.near.has(a.id)) ||
      (labelPriority[b.kind] || 0) - (labelPriority[a.kind] || 0) || b.degree - a.degree);
    pen.font = "12px 'Segoe UI', 'Microsoft YaHei', sans-serif";
    for (const point of ordered) {
      const { x, y } = screen.get(point.id);
      const button = this.buttons.get(point.id);
      const outside = x < -15 || y < -15 || x > width + 15 || y > height + 15;
      button.hidden = outside;
      if (outside) continue;
      const prominent = point.kind === "ComponentType" || point.kind === "Chariot";
      const size = clamp((9 + Math.sqrt(point.degree) * 1.8 + (prominent ? 3 : 0)) * Math.sqrt(this.scale), 8, 23);
      button.style.left = x + "px";
      button.style.top = y + "px";
      button.style.width = button.style.height = (this.active.has(point.id) ? size + 5 : size) + "px";
      const labelWidth = Math.min(144, pen.measureText(button.title).width + 12);
      const left = x - labelWidth / 2, right = x + labelWidth / 2;
      const options = [{ left, right, top: y + size / 2, bottom: y + size / 2 + 19 }];
      if (point.kind === "OntologyKind") {
        options.push({ left, right, top: y - size / 2 - 19, bottom: y - size / 2, above: true });
      }
      const box = options.find(candidate => candidate.left > 3 && candidate.right < width - 3
        && candidate.top > 2 && candidate.bottom < height - 2 && !boxes.some(other =>
          candidate.left < other.right && candidate.right > other.left &&
          candidate.top < other.bottom && candidate.bottom > other.top));
      button.classList.toggle("label-visible", Boolean(box));
      button.classList.toggle("label-above", Boolean(box?.above));
      if (box) boxes.push(box);
    }
  }
}

export function paintMapLegend(container, palette = mapRegions) {
  for (const { label, color } of Object.values(palette)) {
    const spot = document.createElement("span");
    spot.textContent = label;
    spot.style.setProperty("--legend-color", color);
    container.append(spot);
  }
}
