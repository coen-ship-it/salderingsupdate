(function (root) {
  "use strict";
  function refresh(doc, now) {
    var next = Infinity;
    doc.querySelectorAll("[data-offer-until]").forEach(function (section) {
      var expiry = Date.parse(section.getAttribute("data-offer-until"));
      section.hidden = !Number.isFinite(expiry) || now >= expiry;
      if (!section.hidden) next = Math.min(next, expiry);
    });
    return next;
  }
  function install(win, doc) {
    function update() {
      var now = Date.now();
      var next = refresh(doc, now);
      if (Number.isFinite(next)) win.setTimeout(update, Math.min(next - now, 2147483647));
    }
    update();
    if (win.location && win.location.hash) {
      var target = doc.getElementById(win.location.hash.slice(1));
      if (target && target.hasAttribute("data-offer-until") && !target.hidden) target.scrollIntoView();
    }
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = {refresh: refresh, install: install};
  } else {
    install(root, root.document);
  }
}(typeof window !== "undefined" ? window : globalThis));
