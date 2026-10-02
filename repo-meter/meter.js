/* The repo meter: fills every <div class="repo-meter" data-repo="owner/repo">
   on the page from /data/repo-activity.json, fetched once at runtime.
   Spec: docs/superpowers/specs/2026-10-01-repo-meter-design.md.

   Runtime on purpose: the renderers emit the empty element and nothing from
   the data file, so the daily bot write never dirties render-hub --check or
   render-plugin-pages --check (the same reason version chips fetch
   plugin-versions.json in the browser).

   26 columns (weeks, oldest left), 7 rows (Sunday to Saturday). Levels are
   per repo, by quartile of that repo's non-zero days, so a quiet repo still
   shows its own rhythm. No colors here: meter.css reads the theme's tokens.

   window.repoMeter.scan() fills any meter added after load (rororo-plugins
   builds its cards from a fetched catalog); already-filled meters are
   skipped, so calling it twice is harmless. */
(function () {
  "use strict";
  var WEEKS = 26, DAY = 86400000;
  var MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  var dataPromise = null;
  function ymd(d) { return d.toISOString().slice(0, 10); }
  function pretty(k) { var p = k.split("-"); return MON[+p[1] - 1] + " " + (+p[2]) + ", " + p[0]; }
  function levels(days) {
    var vals = Object.keys(days).map(function (k) { return days[k]; }).filter(function (n) { return n > 0; }).sort(function (a, b) { return a - b; });
    if (!vals.length) return function () { return 0; };
    var q = function (f) { return vals[Math.min(vals.length - 1, Math.floor(vals.length * f))]; };
    var q1 = q(0.25), q2 = q(0.5), q3 = q(0.75);
    return function (n) { return n <= 0 ? 0 : n <= q1 ? 1 : n <= q2 ? 2 : n <= q3 ? 3 : 4; };
  }
  function render(el, rec) {
    var now = new Date();
    var end = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
    // The last column ends on today; the first column starts on a Sunday.
    var start = new Date(end.getTime() - (WEEKS * 7 - 1) * DAY);
    start = new Date(start.getTime() - start.getUTCDay() * DAY);
    var days = rec ? rec.days || {} : {}, lv = levels(days);
    var html = "", total = 0, cells = 0;
    for (var d = new Date(start.getTime()); cells < WEEKS * 7; d = new Date(d.getTime() + DAY), cells++) {
      var k = ymd(d), n = days[k] || 0, off = d > end;
      if (!off) total += n;
      html += '<i class="rm-d l' + lv(n) + (off ? " off" : "") + '" title="' + pretty(k) + ": " + n + " commit" + (n === 1 ? "" : "s") + '"></i>';
    }
    var sum = "<b>" + total.toLocaleString() + "</b> commit" + (total === 1 ? "" : "s") + " in " + WEEKS + " weeks" + (rec.lastCommit ? ", last " + pretty(rec.lastCommit) : "");
    el.innerHTML = '<div class="rm-grid" style="--rm-weeks:' + WEEKS + '" aria-hidden="true">' + html + '</div><p class="rm-sum">' + sum + "</p>";
    var label = el.getAttribute("data-label") || el.getAttribute("aria-label") || "Commit activity";
    el.setAttribute("data-label", label);
    el.setAttribute("aria-label", label + ": " + sum.replace(/<[^>]+>/g, ""));
    el.setAttribute("data-filled", "1");
  }
  function load() {
    if (!dataPromise) {
      dataPromise = fetch("/data/repo-activity.json", { cache: "no-cache" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .catch(function () { return null; });
    }
    return dataPromise;
  }
  function scan() {
    var els = document.querySelectorAll(".repo-meter[data-repo]:not([data-filled])");
    if (!els.length) return;
    load().then(function (data) {
      if (!data) return; /* the meters stay empty and take no height */
      els.forEach(function (el) {
        if (el.hasAttribute("data-filled")) return;
        var repo = el.getAttribute("data-repo");
        var rec = data.repos && data.repos[repo];
        if (!rec) {
          /* A repo the bot could not read (private, moved, gone) stays an
             empty element and takes no height. "No public activity" would
             read as dead, and the flagship's repo is private by design. */
          el.setAttribute("data-filled", "skip");
          return;
        }
        render(el, rec, false);
      });
    });
  }
  window.repoMeter = { scan: scan };
  scan();
})();
