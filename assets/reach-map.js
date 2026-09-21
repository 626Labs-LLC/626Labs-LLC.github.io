/*!
 * Store reach map — where a Microsoft Store app has actually been installed.
 *
 * Drop this on any page that links a theme's product-tokens.css:
 *
 *   <div class="reach-map" data-app="9NMJCS390KWB" data-label="RoRoRo"></div>
 *   <script src="/assets/reach-map.js" defer></script>
 *
 * NO TILE PROVIDER. Country-level symbols need geographic context, not zoomable
 * imagery, so the base map is inline SVG projected from public-domain Natural
 * Earth geometry (data/world-robinson.json, built by scripts/build-world-map.py).
 * Nothing to key, nothing to watermark, nothing to expire.
 *
 * Every colour is a theme token from archetypes.REQUIRED_TOKENS, so the map
 * re-themes itself on the monthly rotation instead of freezing in one palette.
 *
 * Renders nothing at all when the app has no market data yet — the geography
 * pull in track-store-analytics.mjs is soft-failed, so `null` genuinely means
 * "not fetched", and a half-empty world map is worse than no map.
 */
(() => {
  "use strict";

  const WORLD_URL = "/data/world-robinson.json";
  const STATS_URL = "/data/store-analytics.json";
  const R_MAX = 26;
  const R_MIN = 2.6;

  const CSS = `
.reach-map{--rm-dot:var(--cyan);margin:var(--s-8,32px) 0}
.reach-map[hidden]{display:none}
.reach-map__frame{position:relative;border:1px solid var(--border-1);
  border-radius:var(--r-md,10px);background:var(--bg-1);padding:8px;overflow:hidden}
.reach-map__frame svg{display:block;width:100%;height:auto}
.reach-map__land{fill:var(--bg-2);stroke:var(--border-1);stroke-width:.6;
  vector-effect:non-scaling-stroke}
.reach-map__ring{fill:none;stroke:var(--bg-1);stroke-width:2;pointer-events:none}
.reach-map__dot{fill:var(--rm-dot);fill-opacity:.42;stroke:var(--rm-dot);
  stroke-width:1.1;cursor:pointer;transition:fill-opacity var(--dur-fast,.12s)}
.reach-map__dot:hover,.reach-map__dot:focus{fill-opacity:.9;outline:none}
.reach-map__dot:focus-visible{stroke:var(--magenta);stroke-width:2}
.reach-map__tip{position:absolute;left:0;top:0;pointer-events:none;opacity:0;
  transform:translate(-50%,-150%);background:var(--bg-0);border:1px solid var(--cyan);
  border-radius:var(--r-sm,6px);padding:5px 9px;font-family:var(--font-mono);
  font-size:12px;color:var(--fg-1);white-space:nowrap;z-index:3;
  transition:opacity var(--dur-fast,.12s)}
.reach-map__tip b{color:var(--cyan)}
.reach-map__meta{display:flex;flex-wrap:wrap;align-items:flex-end;gap:18px;
  margin-top:14px;font-family:var(--font-mono);font-size:11px;color:var(--fg-3)}
.reach-map__key{display:flex;align-items:flex-end;gap:14px}
.reach-map__key i{display:flex;flex-direction:column;align-items:center;gap:5px;
  font-style:normal}
.reach-map__note{margin-top:10px;font-family:var(--font-mono);font-size:11px;
  color:var(--fg-muted)}
.reach-map details{margin-top:14px}
.reach-map summary{cursor:pointer;font-family:var(--font-mono);font-size:12px;
  color:var(--fg-3)}
.reach-map table{width:100%;border-collapse:collapse;margin-top:10px;font-size:13px}
.reach-map th,.reach-map td{text-align:left;padding:5px 9px;
  border-bottom:1px solid var(--border-1)}
.reach-map th{font-family:var(--font-mono);font-size:11px;text-transform:uppercase;
  letter-spacing:.1em;color:var(--fg-3);font-weight:500}
.reach-map td.n{text-align:right;font-family:var(--font-mono);color:var(--cyan)}
/* The dots grow in from nothing on first view. Purely decorative, so it is fully
   disabled under reduced-motion rather than merely shortened. */
@media (prefers-reduced-motion:no-preference){
  .reach-map__dot,.reach-map__ring{transform-box:fill-box;transform-origin:center;
    transform:scale(0);transition:transform .6s var(--ease-out,cubic-bezier(.2,.8,.2,1)),
    fill-opacity var(--dur-fast,.12s)}
  .reach-map.is-live .reach-map__dot,.reach-map.is-live .reach-map__ring{transform:scale(1)}
}`;

  const NS = "http://www.w3.org/2000/svg";
  const el = (n, attrs) => {
    const e = document.createElementNS(NS, n);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  };
  const fmt = (n) => n.toLocaleString("en-US");

  function injectCSS() {
    if (document.getElementById("reach-map-css")) return;
    const s = document.createElement("style");
    s.id = "reach-map-css";
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  // Area-proportional. Radius scales with sqrt(value) so a 770-install country
  // reads ~28x a 1-install country rather than 770x. R_MIN keeps the long tail
  // of single-install countries visible instead of sub-pixel.
  const radius = (n, max) => Math.max(R_MIN, Math.sqrt(n / max) * R_MAX);

  function legendSteps(max) {
    const steps = [1, 10, 100, 1000, 10000].filter((v) => v < max);
    return [...steps.slice(-3), max];
  }

  function render(node, world, markets, label) {
    const entries = Object.entries(markets)
      .filter(([iso, n]) => n > 0 && world.points[iso])
      .map(([iso, n]) => ({ iso, n, ...world.points[iso] }));
    if (!entries.length) return false;

    const max = Math.max(...entries.map((d) => d.n));
    const total = entries.reduce((s, d) => s + d.n, 0);
    // Unplaceable markets are reported rather than silently dropped.
    const missing = Object.entries(markets)
      .filter(([iso, n]) => n > 0 && !world.points[iso]);
    const vb = world.viewBox.join(" ");

    const frame = document.createElement("div");
    frame.className = "reach-map__frame";
    const svg = el("svg", {
      viewBox: vb, role: "img",
      "aria-label": `World map: ${label} installs across ${entries.length} countries`,
    });
    const gLand = el("g", {});
    for (const d of world.land) gLand.appendChild(el("path", { class: "reach-map__land", d }));
    svg.appendChild(gLand);

    const gDots = el("g", {});
    // Biggest first so the long tail paints on top and stays clickable.
    for (const d of entries.sort((a, b) => b.n - a.n)) {
      const r = radius(d.n, max).toFixed(2);
      gDots.appendChild(el("circle", { class: "reach-map__ring", cx: d.x, cy: d.y, r }));
      const c = el("circle", {
        class: "reach-map__dot", cx: d.x, cy: d.y, r,
        tabindex: "0", role: "listitem",
        "aria-label": `${d.name}: ${fmt(d.n)} installs`,
      });
      const show = (cx, cy) => {
        tip.innerHTML = `${d.name} &middot; <b>${fmt(d.n)}</b>`;
        tip.style.left = cx + "px";
        tip.style.top = cy + "px";
        tip.style.opacity = "1";
      };
      c.addEventListener("mousemove", (e) => {
        const b = frame.getBoundingClientRect();
        show(e.clientX - b.left, e.clientY - b.top);
      });
      c.addEventListener("focus", () => {
        const b = frame.getBoundingClientRect();
        const r2 = c.getBoundingClientRect();
        show(r2.left - b.left + r2.width / 2, r2.top - b.top);
      });
      const hide = () => { tip.style.opacity = "0"; };
      c.addEventListener("mouseleave", hide);
      c.addEventListener("blur", hide);
      gDots.appendChild(c);
    }
    svg.appendChild(gDots);
    frame.appendChild(svg);

    const tip = document.createElement("div");
    tip.className = "reach-map__tip";
    frame.appendChild(tip);
    node.appendChild(frame);

    const meta = document.createElement("div");
    meta.className = "reach-map__meta";
    meta.innerHTML =
      `<span>${fmt(total)} installs &middot; ${entries.length} countries</span>` +
      `<span class="reach-map__key">Installs ` +
      legendSteps(max).map((v) => {
        const r = radius(v, max);
        const s = (r + 2) * 2;
        return `<i><svg width="${s}" height="${s}" aria-hidden="true">` +
          `<circle cx="${s / 2}" cy="${s / 2}" r="${r.toFixed(2)}" ` +
          `fill="var(--cyan)" fill-opacity=".42" stroke="var(--cyan)" ` +
          `stroke-width="1.1"/></svg>${fmt(v)}</i>`;
      }).join("") + `</span>`;
    node.appendChild(meta);

    const rows = entries.map((d) =>
      `<tr><td>${d.name}</td><td>${d.iso}</td><td class="n">${fmt(d.n)}</td></tr>`).join("");
    const det = document.createElement("details");
    det.innerHTML =
      `<summary>Table view (${entries.length} countries)</summary>` +
      `<table><thead><tr><th>Country</th><th>ISO</th>` +
      `<th style="text-align:right">Installs</th></tr></thead><tbody>${rows}</tbody></table>`;
    node.appendChild(det);

    const note = document.createElement("p");
    note.className = "reach-map__note";
    note.textContent =
      "Robinson projection. Base geometry: Natural Earth (public domain)." +
      (missing.length ? ` ${missing.length} market(s) had no map coordinate.` : "");
    node.appendChild(note);

    // Grow the dots in when the map first scrolls into view.
    if ("IntersectionObserver" in window) {
      new IntersectionObserver((es, o) => {
        for (const e of es) {
          if (e.isIntersecting) { node.classList.add("is-live"); o.disconnect(); }
        }
      }, { threshold: 0.15 }).observe(node);
    } else {
      node.classList.add("is-live");
    }
    return true;
  }

  async function init() {
    const nodes = [...document.querySelectorAll(".reach-map[data-app]")];
    if (!nodes.length) return;
    injectCSS();
    let world, stats;
    try {
      [world, stats] = await Promise.all([
        fetch(WORLD_URL).then((r) => r.json()),
        fetch(STATS_URL).then((r) => r.json()),
      ]);
    } catch (e) {
      for (const n of nodes) n.hidden = true;
      return;
    }
    for (const node of nodes) {
      const app = (stats.apps || {})[node.dataset.app];
      const markets = app && app.acquisitionsByMarket;
      const label = node.dataset.label || (app && app.name) || "this app";
      if (!markets || !Object.keys(markets).length || !render(node, world, markets, label)) {
        node.hidden = true;
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
