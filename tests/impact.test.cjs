const assert = require('node:assert/strict');
const {calculate} = require('../assets/impact.js');
const base = {production: 3000, consumption: 3500, ownFraction: .4, buyRate: .31,
  excessRate: .08, returnRate: .08, costsBefore: 0, costsAfter: 0};
assert.equal(calculate(base).difference, 414);
// Production above consumption cannot all be offset at the purchase tariff.
const surplus = calculate({...base, production: 10000, consumption: 2000});
assert.equal(surplus.offset, 0);
assert.equal(surplus.excess, 8000);
assert.equal(surplus.difference, 0);
assert.equal(calculate({...base, costsBefore: 100, costsAfter: 150}).difference, 464);
assert.equal(calculate({...base, production: 0}).difference, 0);
assert.equal(calculate({...base, returnRate: -.02}).returnValue, -36);
assert.throws(() => calculate({...base, production: NaN}));
assert.throws(() => calculate({...base, ownFraction: 1.1}));
console.log('7 impactberekeningen geslaagd');
