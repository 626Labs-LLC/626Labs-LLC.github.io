/* On the bench: fills <div class="bench" data-bench> on the home page from
   /data/bench.json, the public repos with the most commits in the last two
   weeks. The file is written daily by scripts/refresh-repo-activity.mjs.

   Runtime on purpose, like the repo meter beside it: render-hub emits the
   empty element and nothing from the data file, so the bot's write never
   dirties --check. Before the fetch lands, and if it fails or no repo
   clears the floor, the element stays empty and takes no height.

   Every string from the file is set as text, never as markup: titles and
   blurbs are GitHub repo descriptions. A link is followed only when it is
   root-relative or https. No colors here: bench.css reads the theme's
   tokens. */
(function () {
  "use strict";
  var MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  function pretty(k) { var p = String(k || "").split("-"); return p.length === 3 ? MON[+p[1] - 1] + " " + (+p[2]) : ""; }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function safeHref(h) {
    h = String(h || "");
    if (/^https:\/\//.test(h)) return h;
    if (h.charAt(0) === "/" && h.charAt(1) !== "/") return h;
    return "";
  }
  function fill(root, data) {
    var items = (data && data.items) || [];
    if (!items.length) return;
    var top = items[0].commits || 1;
    var head = el("div", "bench-head");
    head.appendChild(el("span", "bench-eyebrow", root.getAttribute("data-eyebrow") || "On the bench"));
    var note = root.getAttribute("data-note");
    if (note) head.appendChild(el("span", "bench-note", note));
    var stamp = pretty(String(data.generatedAt || "").slice(0, 10));
    if (stamp) head.appendChild(el("span", "bench-stamp", "Updated " + stamp));
    var list = el("ol", "bench-list");
    items.forEach(function (it, i) {
      var href = safeHref(it.href);
      var card = el(href ? "a" : "div", "bench-item");
      if (href) {
        card.setAttribute("href", href);
        if (href.charAt(0) !== "/") { card.setAttribute("target", "_blank"); card.setAttribute("rel", "noopener"); }
      }
      var line = el("div", "bench-line");
      line.appendChild(el("span", "bench-rank", String(i + 1)));
      line.appendChild(el("span", "bench-title", it.title || it.repo));
      card.appendChild(line);
      if (it.blurb) card.appendChild(el("p", "bench-blurb", it.blurb));
      var bar = el("span", "bench-bar");
      bar.style.setProperty("--bench-share", Math.max(4, Math.round((it.commits / top) * 100)) + "%");
      bar.setAttribute("aria-hidden", "true");
      card.appendChild(bar);
      var n = it.commits;
      var stat = el("p", "bench-stat");
      stat.appendChild(el("b", null, n.toLocaleString()));
      stat.appendChild(document.createTextNode(" commit" + (n === 1 ? "" : "s") + " in " + (data.windowDays || 14) + " days"));
      card.appendChild(stat);
      if (it.featured === false) card.appendChild(el("span", "bench-new", "Not on the site yet"));
      var li = el("li");
      li.appendChild(card);
      list.appendChild(li);
    });
    root.appendChild(head);
    root.appendChild(list);
    root.setAttribute("data-filled", "1");
  }
  var root = document.querySelector(".bench[data-bench]");
  if (!root) return;
  fetch("/data/bench.json", { cache: "no-cache" })
    .then(function (r) { return r.ok ? r.json() : null; })
    .catch(function () { return null; })
    .then(function (data) { if (data) fill(root, data); });
})();
