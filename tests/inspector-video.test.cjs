const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'frontend/inspector/app.js'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(root, 'data/candidates/knowledge.v0.10.json'), 'utf8'));
const content = {};
const scope = {
  state: { data, review: true, selectedFact: null },
  origins: { documented: '资料记载', inferred: '推断解释', hypothesis: '复原假设' },
  knowledgeBases: { modern_reconstruction_observation: '现代复原实验记录', modern_reconstruction_inference: '现代复原推测' },
  $: () => content,
  escapeHtml: text => String(text ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('"', '&quot;'),
  relatedFacts: id => data.facts.filter(f => f.subject_id === id || f.object_id === id),
  renderMedia: () => '',
};
vm.runInNewContext(source.slice(source.indexOf('function formatEvidenceTime('), source.indexOf('async function loadData(')), scope);
vm.runInNewContext(source.slice(source.indexOf('function renderEvidence('), source.indexOf('function renderMappings(')), scope);
vm.runInNewContext(source.slice(source.indexOf('function atlasLayout('), source.indexOf('function graphLayout(')), scope);

test('the updated atlas includes all video cases without overlapping existing nodes', () => {
  const atlas = scope.atlasLayout(data.entities, data.facts);
  assert.equal(atlas.positions.size, 126);
  const nodes = [...atlas.positions];
  for (const entity of data.entities.filter(e => e.id.startsWith('record:video1-'))) {
    assert.ok(atlas.positions.has(entity.id), entity.id);
  }
  for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
    assert.ok(Math.abs(nodes[i][1][0] - nodes[j][1][0]) >= 174 || Math.abs(nodes[i][1][1] - nodes[j][1][1]) >= 84, `${nodes[i][0]} overlaps ${nodes[j][0]}`);
  }
  assert.equal(data.facts.filter(f => f.object_id).length, 229);
});

test('video and PDF evidence use distinct human-readable locators', () => {
  assert.equal(scope.evidenceLocation({ start_seconds: 1564, end_seconds: 1612 }), '视频 26:04—26:52');
  assert.equal(scope.evidenceLocation({ pdf_page: 6 }), 'PDF 第 6 页');
  const url = scope.evidenceSourceUrl({ id: 'source:video1', format: 'mp4' }, { start_seconds: 1564, end_seconds: 1612 });
  assert.equal(url, '/api/sources/source%3Avideo1#t=1564,1612');
});

test('video evidence renders reconstruction labels and scope without fabricated PDF pages', () => {
  data.sources.find(s => s.id === 'source:video1').available = true;
  scope.renderEvidence({ id: 'record:video1-tenon-explanation' });
  assert.match(content.innerHTML, /现代复原推测/);
  assert.match(content.innerHTML, /视频 25:28—26:46/);
  assert.match(content.innerHTML, /不是六号车确定属性/);
  assert.match(content.innerHTML, /打开原视频/);
  assert.doesNotMatch(content.innerHTML, /PDF 第 undefined/);
  assert.equal(scope.factOrigin({ origin: 'hypothesis', knowledge_basis: 'modern_reconstruction_inference' }), '复原假设 · 现代复原推测');
});
