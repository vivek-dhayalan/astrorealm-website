/* AstroRealm — baby-names page: name numerology and first-sound check, worked out in the browser as you type.
   Names typed here never leave the page. The arithmetic mirrors app/core/numerology.py and app/core/naming.py
   (tests/test_naming.py runs both on the same names). */
(function (root) {
  "use strict";

  // ---------------------------------------------------------------- pure functions (shared with the tests)
  function reduce(n, keepMaster, masters) {
    while (n > 9 && !(keepMaster && masters.indexOf(n) >= 0)) {
      n = String(n).split("").reduce(function (a, c) { return a + Number(c); }, 0);
    }
    return n;
  }
  function letters(name) {
    return (name || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toUpperCase().replace(/[^A-Z]/g, "").split("")
      .filter(Boolean);
  }
  function chaldean(name, T) {
    var vals = letters(name).map(function (c) { return [c, T.chaldean[c]]; });
    var total = vals.reduce(function (a, v) { return a + v[1]; }, 0);
    return { letters: vals, total: total, number: reduce(total, false, T.masters) };
  }
  function pythagorean(name, T) {
    var vals = letters(name).map(function (c) { return [c, T.pythagorean[c]]; });
    var total = vals.reduce(function (a, v) { return a + v[1]; }, 0);
    var number = reduce(total, true, T.masters);
    return { letters: vals, total: total, number: number, digit: reduce(number, false, T.masters) };
  }
  function pyramid(values, T) {
    var rows = [values.slice()];
    while (rows[rows.length - 1].length > 1) {
      var r = rows[rows.length - 1], next = [];
      for (var i = 0; i + 1 < r.length; i++) next.push(reduce(r[i] + r[i + 1], false, T.masters));
      rows.push(next);
    }
    return { rows: rows, apex: values.length ? rows[rows.length - 1][0] : null };
  }

  var VOWELS = "aeiou";
  var FORMS = { a: ["aa", "a"], i: ["ee", "ii", "i", "y"], u: ["oo", "uu", "u"], e: ["ai", "ay", "e"], o: ["au", "ow", "o"] };
  function base(c) {
    c = c.replace(/w/g, "v").replace(/f/g, "ph");
    if (c === "sh" || c === "ch") return c;
    if (c.length > 1 && c.charAt(c.length - 1) === "h") c = c.slice(0, -1);
    return c;
  }
  function split(s) {
    s = s.toLowerCase();
    var i = 0;
    while (i < s.length && VOWELS.indexOf(s.charAt(i)) < 0) i++;
    return [s.slice(0, i), s.slice(i)];
  }
  function latinMatch(name, syllable) {
    var sy = split(syllable), cons = sy[0], vowel = sy[1];
    var n = (name || "").normalize("NFKD").toLowerCase().replace(/[^a-z]/g, "");
    var nn = split(n), ncons = nn[0], rest = nn[1], want = base(cons);
    var heads = [base(ncons)];
    if (ncons.length > 1 && "rylv".indexOf(ncons.charAt(ncons.length - 1)) >= 0) heads.push(base(ncons.slice(0, -1)));
    if (heads.indexOf(want) < 0 || !rest) return false;
    var forms = FORMS[vowel ? vowel.charAt(0) : "a"];
    for (var k = 0; k < forms.length; k++) {
      var f = forms[k];
      if (rest.indexOf(f) === 0) {
        var nxt = rest.charAt(f.length);
        if (f === "a" && "iuy".indexOf(nxt) >= 0 && nxt) return false;
        if (f === "e" && nxt === "e") return false;
        if (f === "o" && nxt === "o") return false;
        return true;
      }
    }
    return false;
  }
  function scriptOf(text) {
    for (var i = 0; i < text.length; i++) {
      var o = text.charCodeAt(i);
      if (o >= 0x0900 && o <= 0x097F) return "dev";
      if (o >= 0x0B80 && o <= 0x0BFF) return "ta";
      if (o >= 0x0C00 && o < 0x0C80) return "te";
      if (o >= 0x0C80 && o < 0x0D00) return "kn";
      if (o >= 0x0D00 && o < 0x0D80) return "ml";
      if (/[A-Za-z]/.test(text.charAt(i))) return "latin";
    }
    return "latin";
  }
  function firstSound(name, syllables, pada) {
    name = (name || "").trim();
    var sc = scriptOf(name), table = syllables[sc] || syllables.latin;
    var order = [pada].concat([1, 2, 3, 4].filter(function (p) { return p !== pada; }));
    for (var i = 0; i < order.length; i++) {
      var p = order[i], list = table[p - 1];
      for (var j = 0; j < list.length; j++) {
        var s = list[j], ok = sc === "latin" ? latinMatch(name, s) : name.indexOf(s) === 0;
        if (ok) return { result: p === pada ? "PADA" : "STAR", pada: p, syllable: s, script: sc };
      }
    }
    return { result: "NONE", pada: null, syllable: null, script: sc };
  }

  var NM = { reduce: reduce, letters: letters, chaldean: chaldean, pythagorean: pythagorean, pyramid: pyramid,
             latinMatch: latinMatch, firstSound: firstSound };
  if (typeof module !== "undefined" && module.exports) { module.exports = NM; return; }
  root.AstroNaming = NM;

  // ---------------------------------------------------------------- the page
  var src = document.getElementById("naming-data"), box = document.getElementById("nm-names");
  if (!src || !box) return;
  var boot;
  try { boot = JSON.parse(src.textContent); } catch (err) { return; }
  var L = boot.labels, D = boot.data, addBtn = document.getElementById("nm-add");
  var form = document.querySelector("form[data-live]"), starBox = document.getElementById("nm-star");
  var resultsBox = document.getElementById("nm-results"), tryBox = document.getElementById("nm-try");

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = text;
    return e;
  }
  function fmt(s, kw) { return s.replace(/\{(\w+)\}/g, function (m, k) { return kw[k] !== undefined ? kw[k] : m; }); }
  function verdict(n) {
    var v = D.verdicts[String(n)];
    return el("span", "verdict v-" + v, L["v_" + v]);
  }
  function letterRow(vals) {
    var row = el("div", "nm-letters");
    vals.forEach(function (v) {
      var s = el("span", "nm-l");
      s.appendChild(el("b", "", v[0])); s.appendChild(el("i", "", String(v[1])));
      row.appendChild(s);
    });
    return row;
  }
  function method(title) {
    var m = el("section", "nm-m");
    m.appendChild(el("h3", "", title));
    return m;
  }
  function result(label, total, number, extra) {
    var p = el("p", "nm-res");
    p.appendChild(document.createTextNode(label + " " + total + " → "));
    p.appendChild(el("b", "nm-num", String(number)));
    if (extra) p.appendChild(el("span", "nm-tag", extra));
    return p;
  }

  function render(row) {
    var input = row.querySelector("input"), out = row.querySelector(".nm-out"), name = input.value;
    out.textContent = "";
    if (!name.trim() || !D) return;
    var fs = firstSound(name, D.syllables, D.pada);
    var fsLine = el("p", "nm-fs");
    fsLine.appendChild(el("span", "nm-fs-label", L.first_sound + ": "));
    fsLine.appendChild(el("span", "badge fs-" + fs.result,
      fmt(L["fs_" + fs.result], { s: fs.syllable || "", p: fs.pada || "" })));
    out.appendChild(fsLine);
    var ch = chaldean(name, D), py = pythagorean(name, D);
    if (!ch.letters.length) { out.appendChild(el("p", "hint", L.need_latin)); return; }
    var grid = el("div", "nm-methods");

    var m1 = method(L.m_chaldean);
    m1.appendChild(letterRow(ch.letters));
    var r1 = result(L.total, ch.total, ch.number); r1.appendChild(verdict(ch.number)); m1.appendChild(r1);
    grid.appendChild(m1);

    var m2 = method(L.m_pyth);
    m2.appendChild(letterRow(py.letters));
    var master = D.masters.indexOf(py.number) >= 0 ? L.master : "";
    var r2 = result(L.total, py.total, py.number, master); r2.appendChild(verdict(py.digit)); m2.appendChild(r2);
    grid.appendChild(m2);

    var m3 = method(L.m_pyramid);
    var pyr = pyramid(ch.letters.map(function (v) { return v[1]; }), D), tri = el("div", "nm-pyr");
    pyr.rows.forEach(function (r, i) {
      var line = el("div", i === pyr.rows.length - 1 ? "nm-apex" : "");
      r.forEach(function (n) { line.appendChild(el("span", "", String(n))); });
      tri.appendChild(line);
    });
    m3.appendChild(tri);
    var r3 = el("p", "nm-res");
    r3.appendChild(document.createTextNode(L.apex + " "));
    r3.appendChild(el("b", "nm-num", String(pyr.apex)));
    r3.appendChild(verdict(pyr.apex));
    m3.appendChild(r3);
    grid.appendChild(m3);
    out.appendChild(grid);
  }
  function renderAll() { box.querySelectorAll(".nm-row").forEach(render); }

  function relabel() {
    var rows = box.querySelectorAll(".nm-row");
    rows.forEach(function (r, i) {
      var lab = r.querySelector("label"), inp = r.querySelector("input");
      lab.textContent = fmt(L.name_label, { n: i + 1 });
      inp.id = "nm-name-" + (i + 1); lab.htmlFor = inp.id;
      r.querySelector(".nm-remove").hidden = rows.length === 1;
    });
    if (addBtn) addBtn.hidden = rows.length >= 5;
  }
  function addRow(focus) {
    var row = el("div", "nm-row"), head = el("div", "nm-in");
    var lab = el("label", "label"), inp = el("input");
    inp.type = "text"; inp.maxLength = 60; inp.autocomplete = "off"; inp.spellcheck = false;
    inp.placeholder = L.name_ph; inp.setAttribute("autocapitalize", "words");
    var rm = el("button", "nm-remove linkish", L.remove); rm.type = "button";
    head.appendChild(lab); head.appendChild(inp); head.appendChild(rm);
    var out = el("div", "nm-out"); out.setAttribute("aria-live", "polite");
    row.appendChild(head); row.appendChild(out);
    box.appendChild(row);
    inp.addEventListener("input", function () { render(row); });
    rm.addEventListener("click", function () { row.remove(); relabel(); });
    relabel();
    if (focus) inp.focus();
  }
  box.textContent = "";
  addRow(false);
  if (addBtn) { addBtn.hidden = false; addBtn.addEventListener("click", function () { addRow(true); }); }

  // ---------------------------------------------------------------- fill the page in as soon as the details are complete
  // Only the birth details go to our server (as when the form is submitted); names typed below stay on this page.
  if (!form || !window.fetch) return;
  var url = form.getAttribute("data-live"), last = "", seq = 0, timer = null, submit = form.querySelector(".nm-submit");
  if (submit) submit.closest(".submit-row").classList.add("nm-live");   // the button stays as a fallback
  function complete() {
    var e = form.elements;
    return e.dob.value && e.tob.value && ((e.lat && e.lat.value) || (e.place && e.place.value.trim().length > 1));
  }
  function show(j) {
    starBox.innerHTML = j.star;
    resultsBox.innerHTML = j.cards; resultsBox.hidden = false;
    tryBox.hidden = false;
    D = j.data; renderAll();
  }
  function fail(msg) {
    starBox.querySelectorAll(".nm-error").forEach(function (n) { n.remove(); });
    if (msg) { var p = el("p", "nm-error banner", msg); p.setAttribute("role", "alert"); starBox.appendChild(p); }
  }
  function refresh(force) {
    if (!complete()) return;
    var fd = new FormData(form);
    fd.delete("cf-turnstile-response");
    var body = new URLSearchParams(fd).toString();
    if (body === last && !force) return;
    last = body;
    var mine = ++seq;
    starBox.classList.add("nm-busy");
    fetch(url, { method: "POST", body: body, headers: { "Content-Type": "application/x-www-form-urlencoded",
                                                         Accept: "application/json" } })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (mine !== seq) return;   // a newer request has gone out
        starBox.classList.remove("nm-busy");
        if (j.ok) show(j);
        else fail(j.message || (j.errors && Object.keys(j.errors).map(function (k) { return j.errors[k]; })[0]));
      })
      .catch(function () { if (mine === seq) { starBox.classList.remove("nm-busy"); last = ""; } });
  }
  function soon(e) {
    // typing in the place box waits for a pick from the list (or leaving the box); everything else updates at once
    var placeTyping = e && e.type === "input" && e.target && e.target.name === "place";
    if (placeTyping) return;
    clearTimeout(timer);
    timer = setTimeout(refresh, 250);
  }
  form.addEventListener("change", soon);
  form.addEventListener("input", soon);
  form.addEventListener("submit", function (e) { if (complete()) { e.preventDefault(); refresh(true); } });
  // details handed over from another page (or kept from a language switch) are filled in after this script runs
  setTimeout(soon, 0);
  window.addEventListener("load", function () { soon(); });
})(this);
