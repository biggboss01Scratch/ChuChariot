const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { test } = require("node:test");

const source = fs.readFileSync(path.join(__dirname, "../frontend/admin/network.js"), "utf8");
const modulePromise = import("data:text/javascript;base64," + Buffer.from(source).toString("base64"));

test("knowledge filter excludes teaching metadata and keeps ordinary attributes and physical links", async () => {
  const { filterKnowledge } = await modulePromise;
  const nodes = [
    { id: "type:wheel", kind: "ComponentType", label: "车轮" },
    { id: "type:hub", kind: "ComponentType", label: "毂" },
    { id: "basis:teaching", kind: "EvidenceBasisClass", label: "教学方案" },
    { id: "region:support", kind: "StructuralRegionType", label: "支承位置（教学区域）" },
  ];
  const facts = [
    { id: "fact:part", subject_id: "type:wheel", predicate: "HAS_PART", object_id: "type:hub" },
    { id: "fact:guide", subject_id: "type:wheel", predicate: "SCHEMATIC_NEXT", object_id: "type:hub" },
    { id: "fact:detail", subject_id: "type:hub", predicate: "DESCRIPTION", value: "中空" },
    { id: "fact:scope", subject_id: "type:wheel", predicate: "HAS_EVIDENCE_BASIS", object_id: "basis:teaching" },
  ];
  const result = filterKnowledge(nodes, facts);
  assert.deepEqual(result.entities.map(n => n.id), ["type:wheel", "type:hub"]);
  assert.deepEqual(result.facts.map(f => f.id), ["fact:part", "fact:detail"]);
  assert.equal(facts.length, 4);
});

test("the network uses real unique edges and lays direct neighbors around their center", async () => {
  const { networkLinks, layoutNetwork } = await modulePromise;
  const nodes = ["a", "b", "c"].map(id => ({ id, label: id }));
  const facts = [["a", "b"], ["b", "a"], ["a", "c"], ["b", "c"], ["c", "z"]]
    .map(([subject_id, object_id]) => ({ subject_id, object_id }));
  const ids = new Set(nodes.map(node => node.id));
  const all = networkLinks(facts, ids, "");
  const focus = networkLinks(facts, ids, "a");
  assert.deepEqual(all.map(({ from, to }) => [from, to]), [["a", "b"], ["a", "c"], ["b", "c"]]);
  assert.equal(focus.length, 2);
  const points = layoutNetwork(nodes, focus, {}, "a");
  assert.equal(points.get("a").x, 0);
  assert.equal(points.get("a").y, 0);
  assert.ok(points.get("b").y < 0 && points.get("c").y > 0);
  assert.deepEqual(layoutNetwork(nodes, all, {}, ""), layoutNetwork([...nodes].reverse(), all, {}, ""));
});

test("the ontology network projects declared type pairs and keeps attributes in rule details", async () => {
  const { projectOntology, networkLinks, layoutNetwork, ontologyRegions } = await modulePromise;
  const ontology = JSON.parse(fs.readFileSync(path.join(__dirname, "../data/ontology/ontology.v0.7.json"), "utf8"));
  const schema = projectOntology(ontology, { ComponentType: "部件类别" });
  assert.equal(schema.entities.length, Object.keys(ontology.entity_kinds).length);
  assert.equal(schema.facts.length, Object.values(ontology.predicates).flatMap(rule => rule.endpoint_pairs || []).length);
  assert.ok(schema.facts.some(f => f.predicate === "HAS_PART" && f.subject_id === "Chariot" && f.object_id === "Component"));
  assert.ok(schema.rules.some(rule => rule.id === "HAS_DIMENSION" && rule.subject_kinds.includes("ReferenceSpecimen")));
  assert.ok(schema.facts.every(f => f.predicate !== "HAS_DIMENSION"));
  const ids = new Set(schema.entities.map(e => e.id));
  const links = networkLinks(schema.facts, ids, "", true);
  assert.ok(links.some(edge => edge.from === "ComponentType" && edge.to === edge.from));
  assert.equal(layoutNetwork(schema.entities, links, schema.regions, "", ontologyRegions).size, ids.size);
});

test("ontology and record nodes share coordinates on opposite sides of the divider", async () => {
  const { layeredLayout, ontologyKind } = await modulePromise;
  const facts = new Map([["type:001", { id: "type:001", group: "wheel", x: 8, y: -194 }]]);
  const kinds = new Map([["ComponentType", { id: "ComponentType", group: "objects", x: 9, y: 250 }]]);
  const points = [...layeredLayout(facts, kinds).values()];
  assert.equal(ontologyKind(points[0].id), "ComponentType");
  assert.equal(ontologyKind(points[1].id), "");
  assert.ok(points[0].y < 0 && points[1].y > 0);
  assert.ok(points[0].x >= 9);
  assert.equal(points[1].x, 8);
});
