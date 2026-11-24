const nodeWidth = 152;
const nodeHeight = 37;
const horizontalStep = 174;
const verticalStep = 62;

export function showGraph(container, entities, facts, selected, neighborhood, scale, onSelect) {
  const edges = facts.filter(fact => fact.object_id && fact.subject_id !== fact.object_id);
  const incident = edges.filter(fact => fact.subject_id === selected || fact.object_id === selected);
  const connected = new Set(incident.flatMap(fact => [fact.subject_id, fact.object_id]));
  if (selected) connected.add(selected);
  const visible = neighborhood && selected ? entities.filter(entity => connected.has(entity.id)) : entities;
  const sorted = [...visible].sort((a, b) => a.kind.localeCompare(b.kind) || a.label.localeCompare(b.label, "zh-CN"));
  const columns = Math.max(2, Math.floor((container.clientWidth - 28) / (horizontalStep * scale)));
  const rows = Math.ceil(sorted.length / columns);
  const width = columns * horizontalStep + 16;
  const height = Math.max(rows * verticalStep + 28, container.clientHeight / scale);
  const points = new Map();
  const surface = document.createElement("div");
  surface.className = "graph-surface";
  surface.style.width = width + "px";
  surface.style.height = height + "px";
  surface.style.zoom = scale;
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  canvas.setAttribute("aria-hidden", "true");
  surface.append(canvas);
  for (const [index, entity] of sorted.entries()) {
    const x = 18 + (index % columns) * horizontalStep;
    const y = 20 + Math.floor(index / columns) * verticalStep;
    points.set(entity.id, [x + nodeWidth / 2, y + nodeHeight / 2]);
    const node = document.createElement("button");
    node.type = "button";
    node.className = "graph-node";
    node.classList.toggle("selected", entity.id === selected);
    node.classList.toggle("neighbor", connected.has(entity.id));
    node.classList.toggle("draft", entity.publication_status === "draft");
    node.dataset.id = entity.id;
    node.style.left = x + "px";
    node.style.top = y + "px";
    node.textContent = entity.label;
    node.title = entity.label + " · " + entity.id;
    node.setAttribute("aria-pressed", String(entity.id === selected));
    node.addEventListener("click", () => onSelect(entity.id));
    surface.append(node);
  }
  const pen = canvas.getContext("2d");
  for (const edge of [...edges.filter(fact => !incident.includes(fact)), ...incident]) {
    const start = points.get(edge.subject_id);
    const end = points.get(edge.object_id);
    if (!start || !end) continue;
    const highlighted = selected === edge.subject_id || selected === edge.object_id;
    pen.strokeStyle = highlighted ? "#247460" : "#d5dfd9";
    pen.lineWidth = highlighted ? 1.8 : 0.7;
    pen.setLineDash(edge.publication_managed && edge.review_status !== "confirmed" ? [4, 3] : []);
    const [sx, sy] = start, [ex, ey] = end;
    const rise = Math.min(44, Math.abs(ex - sx) / 12 + 12);
    pen.beginPath();
    pen.moveTo(sx, sy);
    pen.bezierCurveTo((sx + ex) / 2, sy - rise, (sx + ex) / 2, ey - rise, ex, ey);
    pen.stroke();
  }
  const previousTop = container.scrollTop, previousLeft = container.scrollLeft;
  container.replaceChildren(surface);
  container.scrollTop = previousTop;
  container.scrollLeft = previousLeft;
}
