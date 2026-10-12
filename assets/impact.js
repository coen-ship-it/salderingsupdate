(function (root) {
  "use strict";
  function calculate(input) {
    var keys = ["production", "consumption", "ownFraction", "buyRate", "excessRate", "returnRate", "costsBefore", "costsAfter"];
    keys.forEach(function (key) {
      if (!Number.isFinite(input[key])) throw new Error("Vul alle bedragen en verbruiksgegevens in.");
    });
    if (input.production < 0 || input.consumption < 0 || input.ownFraction < 0 || input.ownFraction > 1 || input.buyRate < 0 || input.costsBefore < 0 || input.costsAfter < 0) {
      throw new Error("Controleer de invoer: verbruik en kosten moeten positief zijn.");
    }
    var own = Math.min(input.production * input.ownFraction, input.consumption);
    var returned = Math.max(input.production - own, 0);
    var imported = Math.max(input.consumption - own, 0);
    var offset = Math.min(returned, imported);
    var excess = Math.max(returned - imported, 0);
    var before = (imported - offset) * input.buyRate - excess * input.excessRate + input.costsBefore;
    var after = imported * input.buyRate - returned * input.returnRate + input.costsAfter;
    return {own: own, returned: returned, imported: imported, offset: offset, excess: excess,
      before: before, after: after, difference: after - before,
      offsetValue: offset * input.buyRate, returnValue: returned * input.returnRate};
  }
  if (typeof module !== "undefined" && module.exports) module.exports = {calculate: calculate};
  else root.SalderingsImpact = {calculate: calculate};
}(typeof window !== "undefined" ? window : globalThis));
