/* Comercio IA: reading settings, cookie consent and analytics.
   Analytics loads only after the visitor accepts it. Nothing here sends data before that. */
(function () {
  "use strict";

  // Google Analytics 4 measurement ID. Empty = analytics off and no cookie notice.
  var GA_ID = "G-CCFR41KLL9";

  // One origin: consent and settings are stored per origin, and the canonical host is the apex.
  if (location.hostname === "www.comercioia.cl") {
    location.replace("https://comercioia.cl" + location.pathname + location.search + location.hash);
    return;
  }

  var html = document.documentElement;
  var es = (html.lang || "es").toLowerCase().indexOf("es") === 0;
  var T = es ? {
    title: "Ajustes de lectura", size: "Tamaño del texto", readable: "Fuente más legible", spacing: "Más espacio entre líneas",
    links: "Subrayar enlaces", contrast: "Alto contraste", still: "Detener animaciones", on: "Activado", off: "Desactivado",
    reset: "Restablecer", close: "Cerrar", statement: "Declaración de accesibilidad", statementHref: "/accesibilidad/",
    consent: "Usamos Google Analytics para saber qué páginas se leen y mejorar el sitio. Solo se activa si lo aceptas; puedes cambiar tu decisión cuando quieras.",
    accept: "Aceptar analítica", reject: "Rechazar", more: "Política de privacidad", moreHref: "/privacidad/"
  } : {
    title: "Reading settings", size: "Text size", readable: "More legible font", spacing: "More line spacing",
    links: "Underline links", contrast: "High contrast", still: "Stop animations", on: "On", off: "Off",
    reset: "Reset", close: "Close", statement: "Accessibility statement", statementHref: "/en/accessibility/",
    consent: "We use Google Analytics to learn which pages are read and improve the site. It only runs if you accept; you can change your choice at any time.",
    accept: "Accept analytics", reject: "Reject", more: "Privacy policy", moreHref: "/en/privacy/"
  };

  function load(key) { try { return JSON.parse(localStorage.getItem(key) || "null"); } catch (e) { return null; } }
  function store(key, v) { try { localStorage.setItem(key, JSON.stringify(v)); } catch (e) { /* storage blocked: settings last for this page only */ } }
  function el(tag, attrs, text) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    if (text != null) n.textContent = text;
    return n;
  }

  /* ---------------- Reading settings ---------------- */
  var KEY_A11Y = "cia-a11y";
  var prefs = load(KEY_A11Y) || { size: 0, readable: false, spacing: false, links: false, contrast: false, still: false };

  function applyPrefs() {
    html.classList.remove("a11y-size-1", "a11y-size-2");
    if (prefs.size > 0) html.classList.add("a11y-size-" + prefs.size);
    ["readable", "spacing", "links", "contrast", "still"].forEach(function (k) { html.classList.toggle("a11y-" + k, !!prefs[k]); });
  }
  applyPrefs();

  function buildPanel(button) {
    var panel = el("div", { id: "a11y-panel", "class": "a11y-panel", role: "dialog", "aria-modal": "false", "aria-labelledby": "a11y-title", hidden: "" });
    panel.appendChild(el("h2", { id: "a11y-title" }, T.title));

    var sizeRow = el("div", { "class": "row" });
    sizeRow.appendChild(el("span", { id: "a11y-size-l" }, T.size));
    var seg = el("div", { "class": "seg", role: "group", "aria-labelledby": "a11y-size-l" });
    ["A", "A+", "A++"].forEach(function (lbl, i) {
      var b = el("button", { type: "button", "aria-pressed": String(prefs.size === i) }, lbl);
      b.addEventListener("click", function () { prefs.size = i; save(); seg.querySelectorAll("button").forEach(function (x, j) { x.setAttribute("aria-pressed", String(j === i)); }); });
      seg.appendChild(b);
    });
    sizeRow.appendChild(seg);
    panel.appendChild(sizeRow);

    [["readable", T.readable], ["spacing", T.spacing], ["links", T.links], ["contrast", T.contrast], ["still", T.still]].forEach(function (pair) {
      var k = pair[0];
      var row = el("div", { "class": "row" });
      var id = "a11y-" + k + "-l";
      row.appendChild(el("span", { id: id }, pair[1]));
      var sw = el("button", { type: "button", "class": "switch", "aria-pressed": String(!!prefs[k]), "aria-labelledby": id }, prefs[k] ? T.on : T.off);
      sw.addEventListener("click", function () {
        prefs[k] = !prefs[k]; save();
        sw.setAttribute("aria-pressed", String(prefs[k])); sw.textContent = prefs[k] ? T.on : T.off;
      });
      row.appendChild(sw);
      panel.appendChild(row);
    });

    var foot = el("div", { "class": "foot" });
    var reset = el("button", { type: "button", "class": "linkish" }, T.reset);
    reset.addEventListener("click", function () {
      prefs = { size: 0, readable: false, spacing: false, links: false, contrast: false, still: false }; save();
      panelEl.remove(); panelEl = buildPanel(button); panelEl.hidden = false; panelEl.querySelector("button").focus();
    });
    var stmt = el("a", { href: T.statementHref }, T.statement);
    var close = el("button", { type: "button", "class": "linkish" }, T.close);
    close.addEventListener("click", function () { toggle(false); button.focus(); });
    foot.appendChild(reset); foot.appendChild(stmt); foot.appendChild(close);
    panel.appendChild(foot);
    document.body.appendChild(panel);
    return panel;
  }

  function save() {
    store(KEY_A11Y, prefs);
    applyPrefs();
  }

  var a11yBtn = document.getElementById("a11y-btn");
  var panelEl = null;
  function toggle(open) {
    if (!panelEl) panelEl = buildPanel(a11yBtn);
    panelEl.hidden = !open;
    a11yBtn.setAttribute("aria-expanded", String(open));
    if (open) { var first = panelEl.querySelector("button"); if (first) first.focus(); }
  }
  if (a11yBtn) {
    a11yBtn.hidden = false;
    a11yBtn.setAttribute("aria-controls", "a11y-panel");
    a11yBtn.addEventListener("click", function () { toggle(a11yBtn.getAttribute("aria-expanded") !== "true"); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && panelEl && !panelEl.hidden) { toggle(false); a11yBtn.focus(); } });
  }

  /* ---------------- Cookie consent + Google Analytics ---------------- */
  var KEY_CONSENT = "cia-consent";
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }

  function startAnalytics() {
    if (!GA_ID || window.__ciaGa) return;
    window.__ciaGa = true;
    gtag("consent", "default", { ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied", analytics_storage: "granted" });
    gtag("js", new Date());
    gtag("config", GA_ID, { anonymize_ip: true, allow_google_signals: false, allow_ad_personalization_signals: false });
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(GA_ID);
    document.head.appendChild(s);
  }

  function stopAnalytics() {
    // Remove GA cookies set on this domain after a withdrawal.
    document.cookie.split(";").forEach(function (c) {
      var name = c.split("=")[0].trim();
      if (name === "_ga" || name.indexOf("_ga_") === 0) {
        ["comercioia.cl", ".comercioia.cl", location.hostname, ""].forEach(function (d) {
          document.cookie = name + "=; Max-Age=0; path=/" + (d ? "; domain=" + d : "");
        });
      }
    });
  }

  var returnFocus = null;
  function decide(granted) {
    store(KEY_CONSENT, { analytics: granted, at: new Date().toISOString() });
    hideBanner();
    // Don't drop focus on <body>: go back where the visitor came from, or to the content.
    var target = returnFocus || document.getElementById("main");
    if (target) {
      if (!returnFocus) target.setAttribute("tabindex", "-1");
      target.focus({ preventScroll: true });
    }
    returnFocus = null;
    if (granted) startAnalytics(); else { stopAnalytics(); if (window.__ciaGa) location.reload(); }
  }

  var banner = null;
  function showBanner() {
    if (!GA_ID) return;
    if (banner) { banner.hidden = false; liftFab(); return; }
    banner = el("div", { "class": "consent", role: "region", "aria-label": es ? "Aviso de cookies" : "Cookie notice" });
    banner.appendChild(el("p", null, T.consent));
    var row = el("div", { "class": "actions-row" });
    var acc = el("button", { type: "button", "class": "btn" }, T.accept);
    var rej = el("button", { type: "button", "class": "btn-alt" }, T.reject);
    acc.addEventListener("click", function () { decide(true); });
    rej.addEventListener("click", function () { decide(false); });
    var more = el("a", { href: T.moreHref }, T.more);
    row.appendChild(acc); row.appendChild(rej); row.appendChild(more);
    banner.appendChild(row);
    // First in the document, so keyboard users reach it before the page.
    document.body.insertBefore(banner, document.body.firstChild);
    liftFab();
    window.addEventListener("resize", liftFab);
  }
  function hideBanner() { if (banner) banner.hidden = true; liftFab(); }
  // Keep the floating accessibility button (and its panel) above the cookie notice.
  function liftFab() {
    var h = banner && !banner.hidden ? banner.offsetHeight + 12 : 0;
    html.style.setProperty("--consent-h", h + "px");
  }

  var consent = load(KEY_CONSENT);
  if (consent && consent.analytics === true) startAnalytics();
  else if (!consent) showBanner();

  document.querySelectorAll("[data-cookie-settings]").forEach(function (b) {
    if (!GA_ID) return;
    b.hidden = false;
    b.addEventListener("click", function () { returnFocus = b; showBanner(); if (banner) banner.querySelector("button").focus(); });
  });

  /* ---------------- Events ---------------- */
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a || !window.__ciaGa) return;
    var href = a.getAttribute("href");
    if (href.indexOf("/ucp/") === 0) gtag("event", "schema_open", { schema_path: href });
    else if (href.indexOf("github.com/Pintor-Project/comercioia") !== -1) gtag("event", "github_click", { link_url: href });
    else if (href.indexOf("mailto:") === 0) gtag("event", "contact_click", { method: "email" });
    else if (href.indexOf("synaptiktech.com") !== -1) gtag("event", "reference_implementation_click", { link_url: href });
  });
})();
