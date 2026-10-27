(function (root) {
  "use strict";

  function isProduction(win) {
    return !!win.location && ["salderingsupdate.nl", "www.salderingsupdate.nl"].includes(win.location.hostname);
  }

  function trackCalculator(win, name) {
    if (!isProduction(win) || !["home", "impact-detail"].includes(name) || typeof win.gtag !== "function") return false;
    var measured = win.__salderingsCalculators || {};
    if (measured[name]) return false;
    try {
      win.gtag("event", "calculator_used", {calculator_name: name});
      measured[name] = true;
      win.__salderingsCalculators = measured;
      return true;
    } catch (_) {
      return false;
    }
  }

  function describe(href, partners) {
    var url;
    try { url = new URL(href); } catch (_) { return null; }
    if (url.protocol !== "https:") return null;
    var partner = partners.find(function (p) {
      var campaignKey = p.network === "awin" ? "awinmid" : "si";
      var publisherKey = p.network === "awin" ? "awinaffid" : "wi";
      return url.hostname === p.host && url.pathname === p.path &&
        url.searchParams.get(campaignKey) === p.campaign &&
        url.searchParams.get(publisherKey) === p.publisher;
    });
    if (!partner) return null;
    var ref = url.searchParams.get(partner.network === "awin" ? "clickref" : "ws") || "";
    // Only our public page/placement identifiers, never arbitrary query values.
    if (!/^[a-zA-Z0-9._-]{1,100}$/.test(ref)) ref = "unlabelled";
    return {
      affiliate_partner: partner.name,
      affiliate_network: partner.network,
      affiliate_campaign: partner.campaign,
      affiliate_placement: ref.includes("__") ? ref.split("__").slice(1).join("__") : "body",
      link_domain: partner.domain,
      link_id: ref,
      link_classes: "affiliate " + partner.network,
      outbound: true
    };
  }

  function install(win, doc, partners) {
    if (!isProduction(win)) return;
    if (win.__salderingsAffiliateTracking) return;
    win.__salderingsAffiliateTracking = true;
    function record(event) {
      if (!event.isTrusted || event.defaultPrevented) return;
      if (event.type === "click" && event.button !== 0) return;
      if (event.type === "auxclick" && event.button !== 1) return;
      var anchor = event.target && event.target.closest && event.target.closest("a[href]");
      if (!anchor) return;
      var data = describe(anchor.href, partners);
      if (!data || typeof win.gtag !== "function") return;
      // Leave navigation untouched; a blocked tag must not block an affiliate link.
      try { win.gtag("event", "affiliate_click", data); } catch (_) { /* Analytics is optional. */ }
    }
    doc.addEventListener("click", record);
    doc.addEventListener("auxclick", record);
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = {describe: describe, install: install, trackCalculator: trackCalculator};
  } else {
    root.SalderingsAffiliateTracking = {trackCalculator: function (name) { return trackCalculator(root, name); }};
    install(root, root.document, root.SalderingsAffiliatePartners || []);
  }
}(typeof window !== "undefined" ? window : globalThis));
