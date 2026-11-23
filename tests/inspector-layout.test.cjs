const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'frontend/inspector/app.js'), 'utf8');
const scope = {};
vm.runInNewContext(source.slice(source.indexOf('function atlasLayout('), source.indexOf('function graphLayout(')), scope);
vm.runInNewContext(source.slice(source.indexOf('function graphLabelLines('), source.indexOf('function svgElement(')), scope);
const load = (name) => JSON.parse(fs.readFileSync(path.join(root, 'data/candidates', name), 'utf8'));
const current = load('teacher-pdf.v0.7.json');
const initial = JSON.stringify(current);
const atlas = scope.atlasLayout(current.entities, current.facts);

test('the atlas places every entity once in a region without overlapping node boxes', () => {
  assert.equal(atlas.positions.size, current.entities.length);
  const assigned = atlas.groups.flatMap(group => [...group.ids]);
  assert.equal(assigned.length, current.entities.length);
  assert.equal(new Set(assigned).size, current.entities.length);
  const nodes = [...atlas.positions];
  for (const [id, [x, y]] of nodes) {
    const group = atlas.groups.find(group => group.ids.includes(id));
    assert.ok(x - 77 > group.x && x + 77 < group.x + group.width, id);
    assert.ok(y - 32 > group.y + 125 && y + 32 < group.y + group.height, id);
  }
  for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
    assert.ok(Math.abs(nodes[i][1][0] - nodes[j][1][0]) >= 174 || Math.abs(nodes[i][1][1] - nodes[j][1][1]) >= 84, `${nodes[i][0]} overlaps ${nodes[j][0]}`);
  }
});

test('dimensions remain owner properties and never become atlas nodes or routes', () => {
  assert.equal(current.entities.filter(entity => entity.kind === 'Measurement').length, 0);
  const dimensions = current.facts.filter(fact => fact.predicate === 'HAS_DIMENSION');
  assert.equal(dimensions.length, 54);
  for (const fact of dimensions) assert.ok(atlas.positions.has(fact.subject_id));
  assert.equal(atlas.regionByEntity.get('specimen:ch13-yoke'), 'traction');
  assert.equal(atlas.regionByEntity.get('specimen:002'), 'axle');
  assert.equal(atlas.regionByEntity.get('component:m1302-front'), atlas.regionByEntity.get('specimen:004'));
});

test('the map draws every real entity relation and invents none', () => {
  const edges = current.facts.filter(fact => fact.object_id);
  const routes = scope.atlasRoutes(current.entities, edges, atlas.positions);
  assert.deepEqual([...routes.keys()].sort(), edges.map(edge => edge.id).sort());
  for (const [id, route] of routes) {
    assert.match(route.d, /^M .* C /, id);
    assert.doesNotMatch(route.d, /NaN|Infinity|undefined/, id);
    assert.ok(route.label.every(Number.isFinite), id);
  }
  assert.equal(JSON.stringify(current), initial);
});

test('selection and input order cannot reshuffle the atlas', () => {
  const again = scope.atlasLayout([...current.entities].reverse(), [...current.facts].reverse());
  assert.equal(JSON.stringify([...again.positions]), JSON.stringify([...atlas.positions]));
});

test('earlier dataset versions and confirmed catalogues retain all their nodes', () => {
  for (const version of [1, 2, 3, 4]) {
    const data = load(`wheel-axle.v0.${version}.json`);
    assert.equal(scope.atlasLayout(data.entities, data.facts).positions.size, data.entities.length);
  }
  const fifth = load('teacher-pdf.v0.5.json');
  assert.equal(scope.atlasLayout(fifth.entities, fifth.facts).positions.size, fifth.entities.length);
  const sixth = load('teacher-pdf.v0.6.json');
  assert.equal(scope.atlasLayout(sixth.entities, sixth.facts).positions.size, sixth.entities.length);
  const confirmed = structuredClone(current.entities);
  for (const entity of confirmed) delete entity.measurement;
  assert.equal(scope.atlasLayout(confirmed, []).positions.size, confirmed.length);
});

test('long measurement labels keep a bounded caption and an intact numeric unit', () => {
  const lines = scope.graphLabelLines('相对舆中轴经线向前距离2cm');
  assert.equal(lines.length, 2);
  assert.equal(lines[1], '2cm');
  assert.ok([...lines[0]].length <= 6);
  assert.deepEqual([...scope.graphLabelLines('贤端径13.5cm')], ['贤端径', '13.5cm']);
});
