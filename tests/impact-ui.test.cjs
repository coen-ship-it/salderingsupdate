const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const impact = require('../assets/impact.js');
const html = fs.readFileSync(path.join(__dirname, '../articles/2026-04-09-impact-saldering-berekenen-hoeveel-verlies-ik.html'), 'utf8');
const script = html.match(/<script>\s*(function bereken\(\)[\s\S]*?)<\/script>/)[1];
const values = {opwek: 3000, jaarverbruik: 3500, verbruik: 40, tarief: .31,
  vergoedingNu: .08, vergoedingNa: .08, kostenNu: 0, kostenNa: 0};
const fields = {};
let valid = true;
for (const [id, value] of Object.entries(values)) {
  fields[id] = {value: String(value), reportValidity: () => valid};
}
for (const id of ['rOpwek', 'rEigen', 'rTerug', 'rAfname', 'rSaldering', 'rVergoeding', 'rVerschil', 'resultBedrag', 'resultAdvies']) {
  fields[id] = {textContent: ''};
}
let shown = 0;
fields.resultBox = {classList: {add: value => { assert.equal(value, 'show'); shown++; }}, scrollIntoView() {}};
const uses = [];
const context = {document: {getElementById: id => fields[id]}, SalderingsImpact: impact,
  window: {SalderingsAffiliateTracking: {trackCalculator: name => uses.push(name)}}, Intl};
vm.createContext(context);
vm.runInContext(script, context);
context.bereken();
assert.ok(fields.resultBedrag.textContent.includes('414'));
assert.equal(shown, 1);
assert.deepEqual(uses, ['impact-detail']);
valid = false;
context.bereken();
assert.equal(shown, 1);
assert.equal(uses.length, 1);
valid = true;
delete context.window.SalderingsAffiliateTracking;
assert.doesNotThrow(() => context.bereken());
assert.equal(shown, 2);
assert.equal((html.match(/clickref=impact-saldering-berekenen-hoeveel-verlies-ik__na-berekening-/g) || []).length, 2);
assert.ok(!html.includes('awinmid=123332'));
assert.ok(!html.includes('awinmid=125964'));
console.log('Calculator result, validation, measurement and two focused follow-up links passed.');
