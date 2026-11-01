/* Live hero numbers: refreshes every <span data-live="..."> that render-hub
   emits for a {{live:KEY}} token, from the daily data files, fetched once at
   runtime. The span ships with a static fallback from site.json's hero.live,
   so a failed fetch, a missing app or stale data leaves that number standing.

   Runtime on purpose, like the repo meter: the Store bot writes
   data/store-analytics.json every morning, and a render-time number would
   dirty render-hub --check every day.

   store-dau: the app's Microsoft Store daily active users, averaged over the
   last 7 reported days (one day is noisy: RoRoRo read 44 on 2026-10-11 between
   ~160s), floored to the ten and shown as "280+". A floor, never a round-up,
   so the claim is always one the data clears. */
(function () {
  "use strict";
  var STALE_DAYS = 14;
  var sources = {
    "store-dau": function (data, app) {
      var rec = data && data.apps && data.apps[app];
      var days = rec && rec.usageDaily;
      if (!days) return null;
      var keys = Object.keys(days).sort().slice(-7);
      if (keys.length < 7) return null;
      var last = Date.parse(keys[keys.length - 1] + "T00:00:00Z");
      if (!(Date.now() - last < STALE_DAYS * 86400000)) return null;
      var sum = 0;
      for (var i = 0; i < keys.length; i++) sum += (days[keys[i]] || {}).dailyActiveUsers || 0;
      var floor = Math.floor(sum / keys.length / 10) * 10;
      return floor >= 10 ? floor.toLocaleString("en-US") + "+" : null;
    },
  };
  var files = { "store-dau": "/data/store-analytics.json" };

  function run() {
    var spans = document.querySelectorAll("span[data-live]");
    var wanted = {};
    for (var i = 0; i < spans.length; i++) {
      var src = spans[i].getAttribute("data-live");
      if (sources[src]) (wanted[src] = wanted[src] || []).push(spans[i]);
    }
    Object.keys(wanted).forEach(function (src) {
      fetch(files[src], { cache: "no-cache" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) {
          wanted[src].forEach(function (el) {
            var v = sources[src](data, el.getAttribute("data-app"));
            if (v) el.textContent = v;
          });
        })
        .catch(function () { /* the fallback stays */ });
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run);
  else run();
})();
