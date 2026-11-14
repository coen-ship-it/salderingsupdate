const assert = require('node:assert/strict');
const {refresh, install} = require('../assets/battery-offers.js');
const expiry = '2026-11-21T00:00:00+01:00';
function section(value) { return {hidden:true, getAttribute:()=>value}; }
const valid = section(expiry), invalid = section('not-a-date');
const doc = {querySelectorAll:()=>[valid, invalid]};
assert.equal(refresh(doc, Date.parse('2026-11-20T22:59:59Z')), Date.parse(expiry));
assert.equal(valid.hidden, false);
assert.equal(invalid.hidden, true);
assert.equal(refresh(doc, Date.parse('2026-11-20T23:00:00Z')), Infinity);
assert.equal(valid.hidden, true, 'Hide at the Dutch expiry boundary, not one day later');
const oldNow = Date.now;
let timer;
try {
  Date.now = ()=>Date.parse('2026-11-20T22:59:59Z');
  install({setTimeout:(fn,delay)=>{timer={fn,delay};}}, doc);
  assert.equal(timer.delay,1000);
  Date.now = ()=>Date.parse(expiry);
  timer.fn();
  assert.equal(valid.hidden,true,'An already-open page must also expire');
  let scrolled = 0;
  valid.hasAttribute = ()=>true;
  valid.scrollIntoView = ()=>{scrolled++;};
  doc.getElementById = ()=>valid;
  const win = {location:{hash:'#tijdelijke-batterijprijzen'},setTimeout:()=>{}};
  Date.now = ()=>Date.parse('2026-11-14T12:00:00Z');
  install(win,doc);
  assert.equal(scrolled,1,'Direct fragment URLs must scroll after revealing the offers');
  Date.now = ()=>Date.parse(expiry);
  install(win,doc);
  assert.equal(scrolled,1,'Never scroll to an expired hidden section');
} finally { Date.now = oldNow; }
console.log('Battery offer expiry checks passed');
