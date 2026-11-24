const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const source = fs.readFileSync(path.resolve(__dirname, '../frontend/inspector/app.js'), 'utf8');
const scope = {};
vm.runInNewContext(source.slice(source.indexOf('function filteredGraphFacts('), source.indexOf('function renderRelationFilters(')), scope);
const data = {
  facts: [
    { id: 'structure', object_id: 'rim' },
    { id: 'appearance', object_id: 'wood' },
    { id: 'internal', object_id: 'subsystem' },
    { id: 'dimension', predicate: 'HAS_DIMENSION', value: { value: 132, unit: 'cm' } },
    { id: 'description', predicate: 'DESCRIPTION', value: '来源限定的解释' },
  ],
  presentation: { groups: [
    { id: 'structure', fact_ids: ['structure'] },
    { id: 'appearance', fact_ids: ['appearance'] },
    { id: 'classification', fact_ids: ['internal'] },
  ] },
};

test('relationship toggles change drawn links while retaining properties and descriptions', () => {
  const before = JSON.stringify(data);
  const filtered = scope.filteredGraphFacts(data, new Set(['structure']));
  assert.deepEqual(Array.from(filtered, f => f.id), ['structure', 'dimension', 'description']);
  assert.equal(JSON.stringify(data), before);
  assert.equal(scope.filteredGraphFacts(data, null), data.facts);
});

test('unchecking every group leaves attributes available and draws no invented relations', () => {
  const filtered = scope.filteredGraphFacts(data, new Set());
  assert.equal(filtered.filter(f => f.object_id).length, 0);
  assert.equal(filtered.length, 2);
});

test('an internal group cannot be selected from a public-only group catalogue', () => {
  const publicData = structuredClone(data);
  publicData.presentation.groups = publicData.presentation.groups.filter(g => g.id !== 'classification');
  const filtered = scope.filteredGraphFacts(publicData, new Set(['structure', 'classification']));
  assert.deepEqual(Array.from(filtered, f => f.id), ['structure', 'dimension', 'description']);
});
