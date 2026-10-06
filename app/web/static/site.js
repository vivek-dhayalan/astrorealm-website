/* AstroRealm website — place search, map pin, rich text, print. No form data leaves except to our own server. */
(function () {
  "use strict";

  // ---------------------------------------------------------------- small helpers
  function debounce(fn, ms) {
    var t;
    return function () {
      var args = arguments, self = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(self, args); }, ms);
    };
  }
  function store(key, val) {
    try { if (val === undefined) return localStorage.getItem(key); localStorage.setItem(key, val); }
    catch (e) { return null; }
  }
  var tNear = document.body.getAttribute("data-t-near") || "Near";
  var tPinned = document.body.getAttribute("data-t-pinned") || "Pinned location";
  function placeLabel(p) {
    return [p.name, p.admin1, p.countryName].filter(Boolean).join(", ");
  }

  // ---------------------------------------------------------------- actions
  document.addEventListener("click", function (ev) {
    var el = ev.target.closest("[data-action]");
    if (!el) return;
    var a = el.getAttribute("data-action");
    if (a === "print") window.print();
    else if (a === "back") history.back();
    else if (a === "theme") setTheme(el.getAttribute("data-theme"), el.closest("details"));
    else if (a === "consent-ok") { store("consent-ok", "1"); document.getElementById("consent").hidden = true; }
    else if (a === "map") toggleMap(el.closest(".place-field"));
    else if (a === "tip") {
      var t = el.closest(".tip"), open = !t.classList.contains("open");
      document.querySelectorAll(".tip.open").forEach(function (x) {
        x.classList.remove("open"); x.querySelector(".tip-btn").setAttribute("aria-expanded", "false");
      });
      if (open) { t.classList.add("open"); el.setAttribute("aria-expanded", "true"); }
    }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      document.querySelectorAll(".tip.open").forEach(function (x) { x.classList.remove("open"); });
      document.querySelectorAll(".hmenu[open]").forEach(function (d) { d.open = false; });
    }
  });
  // language menu: remember the choice, so later visits open in this language
  document.addEventListener("click", function (e) {
    var a = e.target.closest(".lang-menu a[hreflang]");
    if (a) store("lang", a.getAttribute("hreflang"));
  });
  // language menu: close when clicking anywhere else
  document.addEventListener("click", function (e) {
    document.querySelectorAll(".hmenu[open]").forEach(function (d) { if (!d.contains(e.target)) d.open = false; });
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".tip")) document.querySelectorAll(".tip.open").forEach(function (x) { x.classList.remove("open"); });
  });
  // ---------------------------------------------------------------- theme (auto / light / dark), remembered locally
  function markTheme(t) {
    document.querySelectorAll('[data-action="theme"]').forEach(function (b) {
      b.setAttribute("aria-checked", b.getAttribute("data-theme") === t ? "true" : "false");
    });
  }
  function setTheme(t, menu) {
    if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t);
    else { t = "auto"; document.documentElement.removeAttribute("data-theme"); }
    try { if (t === "auto") localStorage.removeItem("theme"); else localStorage.setItem("theme", t); } catch (e) {}
    markTheme(t);
    if (menu) menu.open = false;
  }
  markTheme(document.documentElement.getAttribute("data-theme") || "auto");

  // ---------------------------------------------------------------- result sheets: fit the A5 page to small screens
  function fitSheets() {
    var box = document.querySelector(".sheets");
    if (!box) return;
    var sheetPx = 148 / 25.4 * 96;  // A5 width
    var fit = Math.min(1, (box.clientWidth - 2) / sheetPx);
    document.documentElement.style.setProperty("--fit", fit.toFixed(3));
  }
  fitSheets();
  window.addEventListener("resize", fitSheets);

  var consent = document.getElementById("consent");
  if (consent && store("consent-ok") !== "1") consent.hidden = false;

  // ---------------------------------------------------------------- place search
  function setCoords(field, lat, lon) {
    var p = field.getAttribute("data-prefix");
    var latEl = field.querySelector('input[name="' + p + 'lat"]');
    var lonEl = field.querySelector('input[name="' + p + 'lon"]');
    latEl.value = lat === "" ? "" : Number(lat).toFixed(5);
    lonEl.value = lon === "" ? "" : Number(lon).toFixed(5);
    field.querySelector(".coords").textContent = latEl.value ? latEl.value + ", " + lonEl.value : "";
  }

  function initPlace(field) {
    var input = field.querySelector('input[type="text"]');
    var list = field.querySelector(".suggest");
    var items = [], active = -1;

    function close() { list.hidden = true; input.setAttribute("aria-expanded", "false"); active = -1; }
    function choose(i) {
      var p = items[i];
      if (!p) return;
      input.value = placeLabel(p);
      setCoords(field, p.lat, p.lon);
      if (field._marker) { field._marker.setLngLat([p.lon, p.lat]); field._map.jumpTo({ center: [p.lon, p.lat], zoom: 10 }); }
      close();
    }
    function render() {
      list.innerHTML = "";
      items.forEach(function (p, i) {
        var li = document.createElement("li");
        li.setAttribute("role", "option");
        li.id = input.id + "-opt-" + i;
        li.setAttribute("aria-selected", i === active ? "true" : "false");
        var main = document.createElement("div"); main.textContent = p.name;
        var sub = document.createElement("div"); sub.className = "sub";
        sub.textContent = [p.admin1, p.countryName].filter(Boolean).join(", ");
        li.appendChild(main); li.appendChild(sub);
        li.addEventListener("mousedown", function (e) { e.preventDefault(); choose(i); });
        list.appendChild(li);
      });
      list.hidden = items.length === 0;
      input.setAttribute("aria-expanded", items.length ? "true" : "false");
      if (active >= 0) input.setAttribute("aria-activedescendant", input.id + "-opt-" + active);
    }
    var search = debounce(function () {
      var q = input.value.trim();
      if (q.length < 2) { items = []; render(); return; }
      fetch("/v1/places?limit=8&q=" + encodeURIComponent(q), { headers: { Accept: "application/json" } })
        .then(function (r) { return r.ok ? r.json() : { candidates: [] }; })
        .then(function (d) { items = d.candidates || []; active = -1; render(); })
        .catch(function () { items = []; render(); });
    }, 250);

    input.addEventListener("input", function () { setCoords(field, "", ""); search(); });
    input.addEventListener("keydown", function (e) {
      if (list.hidden) return;
      if (e.key === "ArrowDown") { active = Math.min(items.length - 1, active + 1); render(); e.preventDefault(); }
      else if (e.key === "ArrowUp") { active = Math.max(0, active - 1); render(); e.preventDefault(); }
      else if (e.key === "Enter" && active >= 0) { choose(active); e.preventDefault(); }
      else if (e.key === "Escape") close();
    });
    input.addEventListener("blur", function () { setTimeout(close, 150); });
  }

  // ---------------------------------------------------------------- map pin (MapLibre + OpenFreeMap)
  function toggleMap(field) {
    var box = field.querySelector(".map");
    box.hidden = !box.hidden;
    if (box.hidden) return;
    if (field._map) { field._map.resize(); return; }
    if (!window.maplibregl) return;
    var p = field.getAttribute("data-prefix");
    var lat = parseFloat(field.querySelector('input[name="' + p + 'lat"]').value);
    var lon = parseFloat(field.querySelector('input[name="' + p + 'lon"]').value);
    var has = !isNaN(lat) && !isNaN(lon);
    var start = has ? [lon, lat] : [78.9, 20.6];   // MapLibre uses [longitude, latitude]
    var map = new maplibregl.Map({
      container: box, style: document.body.getAttribute("data-map-style"),
      center: start, zoom: has ? 10 : 4, attributionControl: { compact: true }
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    var marker = new maplibregl.Marker({ draggable: true, color: "#b44d12" }).setLngLat(start).addTo(map);
    field._map = map; field._marker = marker;
    function pick(ll) {
      marker.setLngLat(ll);
      setCoords(field, ll.lat, ll.lng);
      var input = field.querySelector('input[type="text"]');
      fetch("/v1/places/nearest?lat=" + ll.lat.toFixed(5) + "&lon=" + ll.lng.toFixed(5))
        .then(function (r) { return r.ok ? r.json() : {}; })
        .then(function (d) { input.value = d.nearest ? tNear + " " + placeLabel(d.nearest) : tPinned; })
        .catch(function () { input.value = tPinned; });
    }
    map.on("click", function (e) { pick(e.lngLat); });
    marker.on("dragend", function () { pick(marker.getLngLat()); });
  }

  // ---------------------------------------------------------------- rich text
  function initRte(rte) {
    var area = rte.querySelector(".rte-area");
    var target = rte.querySelector("textarea");
    rte.querySelectorAll("[data-cmd]").forEach(function (b) {
      b.addEventListener("mousedown", function (e) { e.preventDefault(); });
      b.addEventListener("click", function () { area.focus(); document.execCommand(b.getAttribute("data-cmd")); });
    });
    var form = rte.closest("form");
    if (form) form.addEventListener("submit", function () { target.value = area.innerHTML; });
  }

  document.querySelectorAll(".place-field").forEach(initPlace);
  document.querySelectorAll(".rte").forEach(initRte);
})();
