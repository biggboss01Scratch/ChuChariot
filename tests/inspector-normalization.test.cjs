const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'frontend/inspector/app.js'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(root, 'data/candidates/knowledge.v0.11.json'), 'utf8'));
const content = {};
const scope = {
  state: { data, review: true, selectedFact: null },
  $: () => content,
  escapeHtml: text => String(text ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('"', '&quot;'),
  relatedFacts: id => data.facts.filter(f => f.subject_id === id || f.object_id === id),
  getEntity: id => data.entities.find(e => e.id === id),
  entityLink: id => `<button>${data.entities.find(e => e.id === id)?.label || id}</button>`,
  badge: () => '<span>待复核</span>',
  renderMedia: () => '',
};
vm.runInNewContext(source.slice(source.indexOf('const kinds ='), source.indexOf('const escapeHtml =')), scope);
vm.runInNewContext(source.slice(source.indexOf('function formatEvidenceTime('), source.indexOf('async function loadData(')), scope);
vm.runInNewContext(source.slice(source.indexOf('function atlasLayout('), source.indexOf('function graphLayout(')), scope);
vm.runInNewContext(source.slice(source.indexOf('const propertyPredicates ='), source.indexOf('function renderMedia(')), scope);
vm.runInNewContext(source.slice(source.indexOf('function renderEvidence('), source.indexOf('function renderMappings(')), scope);

test('all normalized regions and contextual terms stay visible without overlapping map nodes', () => {
  const atlas = scope.atlasLayout(data.entities, data.facts);
  assert.equal(atlas.positions.size, 128);
  const nodes = [...atlas.positions];
  for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
    assert.ok(Math.abs(nodes[i][1][0] - nodes[j][1][0]) >= 174 || Math.abs(nodes[i][1][1] - nodes[j][1][1]) >= 84, `${nodes[i][0]} overlaps ${nodes[j][0]}`);
  }
  assert.equal(atlas.regionByEntity.get('component:ch15-spoke-inner'), atlas.regionByEntity.get('specimen:001'));
});

test('spoke region details retain shape, measurements and a clear region explanation', () => {
  const entity = scope.getEntity('component:ch15-spoke-inner');
  scope.renderKnowledge(entity);
  assert.match(content.innerHTML, /描述区域/);
  assert.match(content.innerHTML, /4\.4 cm/);
  assert.match(content.innerHTML, /1\.4 cm/);
  assert.match(content.innerHTML, /横截面扁棱形/);
  assert.match(content.innerHTML, /不表示可拆卸零件/);
  assert.match(content.innerHTML, /榫卯相接/);
});

test('teacher terminology details show the contextual sense and canonical bridle', () => {
  scope.renderKnowledge(scope.getEntity('type:bridle'));
  assert.match(content.innerHTML, /语境词义/);
  assert.match(content.innerHTML, /来源原词/);
  assert.match(content.innerHTML, /本语境指称/);
  assert.match(content.innerHTML, /马勒（勒）/);
  assert.match(content.innerHTML, /不是一件额外的马具/);
});

test('dictionary evidence opens the official entry and never invents a PDF page', () => {
  scope.renderEvidence(scope.getEntity('term:pei-reins'));
  assert.match(content.innerHTML, /词典条目/);
  assert.match(content.innerHTML, /名词义项1/);
  assert.match(content.innerHTML, /打开官方词典条目/);
  assert.match(content.innerHTML, /https:\/\/dict\.revised\.moe\.edu\.tw/);
  assert.doesNotMatch(content.innerHTML, /PDF 第 undefined/);
});
