/* Comercio IA: the purchase demo on the home page as accessible tabs.
   Without JavaScript the five steps stay visible one under the other. */
(function () {
  "use strict";
  var root = document.querySelector("[data-demo]");
  if (!root) return;
  var list = root.querySelector("[data-demo-tabs]");
  var tabs = Array.prototype.slice.call(list.querySelectorAll("button"));
  var panels = tabs.map(function (t) { return document.getElementById(t.getAttribute("aria-controls")); });
  if (!tabs.length || panels.indexOf(null) !== -1) return;

  document.documentElement.classList.add("js");
  list.setAttribute("role", "tablist");
  list.hidden = false;
  var wide = window.matchMedia("(min-width: 1081px)");
  function orient() { list.setAttribute("aria-orientation", wide.matches ? "vertical" : "horizontal"); }
  orient();
  if (wide.addEventListener) wide.addEventListener("change", orient);

  tabs.forEach(function (t, i) {
    t.setAttribute("role", "tab");
    panels[i].setAttribute("role", "tabpanel");
    panels[i].setAttribute("aria-labelledby", t.id);
  });

  function select(i, focus) {
    tabs.forEach(function (t, j) {
      var on = i === j;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
      panels[j].hidden = !on;
    });
    if (focus) {
      tabs[i].focus();
      if (tabs[i].scrollIntoView && !wide.matches) tabs[i].scrollIntoView({ block: "nearest", inline: "nearest" });
    }
  }

  tabs.forEach(function (t, i) {
    t.addEventListener("click", function () { select(i, false); });
    t.addEventListener("keydown", function (e) {
      var n = tabs.length, to = null;
      if (e.key === "ArrowRight" || e.key === "ArrowDown") to = (i + 1) % n;
      else if (e.key === "ArrowLeft" || e.key === "ArrowUp") to = (i - 1 + n) % n;
      else if (e.key === "Home") to = 0;
      else if (e.key === "End") to = n - 1;
      if (to !== null) { e.preventDefault(); select(to, true); }
    });
  });

  // A link to one step (#paso-3, #step-3) opens it.
  function fromHash() {
    var id = decodeURIComponent(location.hash.slice(1));
    for (var i = 0; i < panels.length; i++) if (panels[i].id === id) { select(i, false); return true; }
    return false;
  }
  if (!fromHash()) select(0, false);
  window.addEventListener("hashchange", fromHash);
})();
