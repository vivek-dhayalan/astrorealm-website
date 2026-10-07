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
  // ---------------------------------------------------------------- "Save as PDF" file name
  // Browsers name the PDF after document.title. Result pages keep a generic title (no names in history or tab
  // sync); the meaningful one is swapped in only while the print dialog is open.
  var printSheets = document.querySelector(".sheets[data-print-title]");
  if (printSheets) {
    var savedTitle = document.title;
    window.addEventListener("beforeprint", function () {
      savedTitle = document.title;
      document.title = printSheets.getAttribute("data-print-title") || savedTitle;
    });
    window.addEventListener("afterprint", function () { document.title = savedTitle; });
  }
  // ---------------------------------------------------------------- "select up to N" checkbox groups
  document.querySelectorAll(".checks[data-max]").forEach(function (group) {
    var max = parseInt(group.getAttribute("data-max"), 10) || 2;
    function sync() {
      var boxes = group.querySelectorAll('input[type="checkbox"]');
      var n = group.querySelectorAll('input[type="checkbox"]:checked').length;
      boxes.forEach(function (b) {
        b.disabled = !b.checked && n >= max;
        b.closest("label").classList.toggle("is-disabled", b.disabled);
      });
    }
    group.addEventListener("change", sync);
    sync();
  });
  // ---------------------------------------------------------------- keep a half-filled form across a language switch
  // Switching language loads the same form in another language. Its fields are handed over in sessionStorage —
  // this tab only, read once on the next page and deleted straight away, dropped after 10 minutes. Never sent anywhere.
  var DRAFT = "formDraft", SKIP = { ui: 1, "cf-turnstile-response": 1 };
  function formOnPage() { return document.querySelector("form.form[action]"); }
  function cleanHtml(html) {
    var ok = { B: 1, STRONG: 1, I: 1, EM: 1, U: 1, P: 1, BR: 1, UL: 1, OL: 1, LI: 1, DIV: 1, SPAN: 1 };
    var doc = new DOMParser().parseFromString("<div>" + html + "</div>", "text/html");
    (function walk(node) {
      Array.prototype.slice.call(node.children).forEach(function (el) {
        if (!ok[el.tagName]) { el.replaceWith(document.createTextNode(el.textContent)); return; }
        Array.prototype.slice.call(el.attributes).forEach(function (at) { el.removeAttribute(at.name); });
        walk(el);
      });
    })(doc.body.firstChild);
    return doc.body.firstChild.innerHTML;
  }
  document.addEventListener("click", function (e) {
    var a = e.target.closest(".lang-menu a[hreflang]"), form = formOnPage();
    if (!a || !form) return;
    var fields = [];
    Array.prototype.forEach.call(form.elements, function (el) {
      if (!el.name || SKIP[el.name] || el.type === "submit" || el.type === "button") return;
      if (el.type === "checkbox" || el.type === "radio") fields.push([el.name, el.value, el.checked]);
      else fields.push([el.name, el.value]);
    });
    var area = form.querySelector(".rte-area");
    try {
      var ui = form.querySelector('input[name="ui"]');
      sessionStorage.setItem(DRAFT, JSON.stringify({ action: form.getAttribute("action"), at: Date.now(),
        fields: fields, rte: area ? area.innerHTML : "", from: ui ? ui.value : "" }));
    } catch (err) {}
  });
  (function restoreDraft() {
    var raw = null, form = formOnPage();
    try { raw = sessionStorage.getItem(DRAFT); sessionStorage.removeItem(DRAFT); } catch (err) { return; }
    if (!raw || !form) return;
    var d;
    try { d = JSON.parse(raw); } catch (err) { return; }
    if (!d || d.action !== form.getAttribute("action") || Date.now() - d.at > 10 * 60 * 1000) return;
    // output languages left at the old page's default follow the new page's language instead
    var picked = d.fields.filter(function (f) { return f[0] === "lang" && f[2]; }).map(function (f) { return f[1]; });
    var keepLangs = !(picked.length === 1 && picked[0] === d.from);
    d.fields.forEach(function (f) {
      Array.prototype.forEach.call(form.elements, function (el) {
        if (el.name !== f[0] || SKIP[el.name] || (el.name === "lang" && !keepLangs)) return;
        if (el.type === "checkbox" || el.type === "radio") { if (el.value === f[1]) el.checked = !!f[2]; }
        else el.value = f[1];
      });
    });
    var area = form.querySelector(".rte-area");
    if (area && d.rte) {
      area.innerHTML = cleanHtml(d.rte);
      var ta = form.querySelector('textarea[name="description"]');
      if (ta) ta.value = area.innerHTML;
    }
    form.querySelectorAll(".checks[data-max]").forEach(function (g) { g.dispatchEvent(new Event("change")); });
  })();
  // ---------------------------------------------------------------- take birth details to another form page
  // Links marked data-carry-to (horoscope ⇄ dasha) hand the details over the same way as a language switch:
  // sessionStorage, this tab only, deleted once filled in. Never in the URL.
  var CARRY = ["name", "sex", "dob", "tob", "place", "lat", "lon", "ayanamsa"];
  document.addEventListener("click", function (e) {
    var a = e.target.closest("a[data-carry-to]");
    if (!a) return;
    var fields = [], given = a.getAttribute("data-carry"), form = formOnPage();
    if (given) {
      try { var v = JSON.parse(given); CARRY.forEach(function (k) { if (v[k]) fields.push([k, String(v[k])]); }); } catch (err) {}
    } else if (form) {
      // from a form, the ayanamsa may just be that page's default (Lahiri on horoscope, KP on dasha): leave it
      CARRY.forEach(function (k) { var el = form.elements[k]; if (k !== "ayanamsa" && el && el.value) fields.push([k, el.value]); });
    }
    if (!fields.length) return;
    try {
      sessionStorage.setItem(DRAFT, JSON.stringify({ action: a.getAttribute("data-carry-to"), at: Date.now(),
        fields: fields, rte: "", from: "" }));
    } catch (err) {}
  });

  // ---------------------------------------------------------------- dasha explorer: mahadasha → … → prana
  // All levels stay on the page as a hierarchy: picking a period in one table opens the next table below it.
  (function () {
    var box = document.getElementById("dasha-x"), src = document.getElementById("dasha-data");
    if (!box || !src) return;
    var D;
    try { D = JSON.parse(src.textContent); } catch (err) { return; }
    var LBL = D.labels, ORDER = D.order, Y = D.years, TOTAL = 120, LAST = 4;
    var sel = [];  // the period picked at each level: [lord, startMs, endMs]
    function seq(first) { var i = ORDER.indexOf(first); return ORDER.slice(i).concat(ORDER.slice(0, i)); }
    function subs(p) {
      var out = [], start = p[1], total = p[2] - p[1];
      seq(p[0]).forEach(function (lord) { var end = start + total * Y[lord] / TOTAL; out.push([lord, start, end]); start = end; });
      out[out.length - 1][2] = p[2];
      return out;
    }
    function pad(n) { return (n < 10 ? "0" : "") + n; }
    function fmt(ms) {
      var d = new Date(ms + D.offsetMin * 60000);
      return pad(d.getUTCDate()) + "-" + pad(d.getUTCMonth() + 1) + "-" + d.getUTCFullYear() + " " +
        pad(d.getUTCHours()) + ":" + pad(d.getUTCMinutes()) + ":" + pad(d.getUTCSeconds());
    }
    function dur(ms) {
      var days = ms / 86400000, u = LBL.units;
      if (days >= 365) return u.y.replace("{n}", (days / 365.25).toFixed(2));
      if (days >= 1) return u.d.replace("{n}", days.toFixed(1));
      return u.h.replace("{n}", (days * 24).toFixed(1));
    }
    function el(tag, cls, text) { var x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; }
    function pname(p) { return LBL.planet[p[0]] || p[0]; }
    function same(a, b) { return a && b && a[0] === b[0] && a[1] === b[1]; }
    var levelsBox = box.querySelector(".dx-levels"), today = box.querySelector(".dx-today");
    function table(level, rows) {
      var now = Date.now(), t = el("table", "grid dx-table"), th = el("thead"), tr = el("tr");
      LBL.cols.forEach(function (c, i) { tr.appendChild(el("th", i === 3 ? "num" : "", c)); });
      th.appendChild(tr); t.appendChild(th);
      var tb = el("tbody");
      rows.forEach(function (p) {
        if (p[2] <= D.birth) return;  // wholly before birth
        var shown = Math.max(p[1], D.birth), running = p[1] <= now && now < p[2];
        var cls = [running ? "now" : (p[2] <= now ? "past" : ""), same(sel[level], p) ? "sel" : ""].join(" ").trim();
        var r = el("tr", cls), c0 = el("td");
        if (level < LAST) {
          var b = el("button", "dx-open", pname(p)); b.type = "button";
          b.setAttribute("aria-expanded", same(sel[level], p) ? "true" : "false");
          b.addEventListener("click", function () { pick(level, p); });
          c0.appendChild(b);
        } else c0.textContent = pname(p);
        if (running) { var dot = el("span", "dx-dot"); dot.title = LBL.running; dot.setAttribute("aria-label", LBL.running); c0.appendChild(dot); }
        r.appendChild(c0);
        r.appendChild(el("td", "", fmt(shown)));
        r.appendChild(el("td", "", fmt(p[2])));
        r.appendChild(el("td", "num", dur(p[2] - shown)));
        tb.appendChild(r);
      });
      t.appendChild(tb);
      return t;
    }
    function render() {
      levelsBox.textContent = "";
      var rows = D.mds;
      for (var level = 0; level <= LAST; level++) {
        var sec = el("section", "dx-level dx-l" + level), h = el("h2", "dx-head");
        h.appendChild(el("span", "", LBL.levels[level]));
        if (level) h.appendChild(el("span", "dx-path", sel.slice(0, level).map(pname).join(" › ")));
        sec.appendChild(h);
        var wrap = el("div", "dx-wrap"); wrap.appendChild(table(level, rows)); sec.appendChild(wrap);
        levelsBox.appendChild(sec);
        if (!sel[level] || level === LAST) break;
        rows = subs(sel[level]);
      }
      today.hidden = false;
    }
    function pick(level, p) {
      sel = sel.slice(0, level);
      sel[level] = p;
      render();
      var next = levelsBox.querySelector(".dx-l" + (level + 1));
      if (next && next.scrollIntoView) next.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
    function toToday() {
      var now = Date.now(), rows = D.mds;
      sel = [];
      for (var lvl = 0; lvl < LAST; lvl++) {
        var cur = rows.filter(function (x) { return x[1] <= now && now < x[2]; })[0];
        if (!cur) break;
        sel.push(cur); rows = subs(cur);
      }
      render();
    }
    today.addEventListener("click", toToday);
    toToday();  // open the running chain on arrival: all five levels, today marked
  })();
})();
