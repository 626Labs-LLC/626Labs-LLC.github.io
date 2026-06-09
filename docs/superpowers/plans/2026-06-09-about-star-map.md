# About Star Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A plugin-constellation star map panel inside the About section of 626labs.dev — stars derive from live plugins in site.json, draw-on reveal, ambient twinkle, hover labels.

**Architecture:** `render_about()` in scripts/render-hub.py emits the panel markup + a byte-stable JSON blob inside the `about` zone; static CSS and a vanilla-JS canvas module live in index.html's static shell (outside `SITE_JSON:` zones). Layout is deterministic: hand-designed spine curve, arc-length slots, FNV-1a hash jitter, seeded-PRNG dust. Versions join at runtime via a fetch of data/plugin-versions.json (never baked — keeps `--check` byte-stable against daily version bumps).

**Tech Stack:** Python 3 (renderer), vanilla JS + Canvas 2D (no libraries, no build step), GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-06-09-about-star-map-design.md` (amended 2026-06-09: runtime version join, flagship derived from product field, starMap presence = feature toggle).

**Conventions (per vibe-cartographer checklist):** every task carries Depends on / Acceptance / Effort; the final task is Documentation & Security Verification.

**Process note:** Repo rule requires `gitnexus_impact` on `render_about` before editing. The GitNexus MCP server is not connected in all sessions; the equivalent evidence is recorded here: `render_about` has exactly one caller — `main()` at scripts/render-hub.py:1639 — and no other references (`grep -n "render_about" scripts/*.py`). Blast radius: the `about` zone of index.html only. Risk: LOW. If the GitNexus MCP is available in your session, run `gitnexus_impact({target: "render_about", direction: "upstream"})` and confirm it agrees before Task 1. The PostToolUse hook re-runs `npx gitnexus analyze` after commits.

---

## File structure

| File | Change | Responsibility |
|---|---|---|
| `content/site.json` | Add `about.starMap` config block | Editorial source of truth; presence toggles the feature |
| `scripts/render-hub.py` | Extend `render_about()` (line 994) + its call site (line 1639) | Emit panel markup + JSON blob inside the about zone |
| `index.html` | Add `.starmap*` CSS before `</style>` (line ~1523); add `<script id="starmap-js">` after the footer's main script block (after line ~2500s `</script>`) | Static shell: presentation + behavior, untouched by the renderer |
| `docs/superpowers/specs/2026-06-09-about-star-map-design.md` | Already committed | The contract |

No new files. No workflow changes. No new dependencies.

**Testing reality:** this repo has no JS unit-test framework (no-build static site by design). The test harness here is: `python scripts/render-hub.py --check` (byte-stable render), `python scripts/site-doctor.py --check` (content health), targeted `python -c` assertions against the rendered output, and scripted browser verification. Tasks use those — do not introduce a test framework for this feature.

---

### Task 1: Renderer — starMap config, panel markup, data blob

**Files:**
- Modify: `content/site.json` (about block, after `"stack"` array ends ~line 790)
- Modify: `scripts/render-hub.py:994-1048` (`render_about`) and `scripts/render-hub.py:1639` (call site)

**Depends on:** nothing.
**Acceptance:** rendered index.html contains the `.starmap` figure and a parseable `#starmap-data` blob whose plugin ids exactly match the live-plugin selection; `--check` passes twice; doctor passes; `starMap` absent → no panel emitted.
**Effort:** ~30 min.

- [ ] **Step 1: Add the starMap config to site.json**

In `content/site.json`, inside the `"about"` object, add a `starMap` key directly after the `"stack"` array (before `"paragraphs"`):

```json
    "stack": [
      "TypeScript",
      "Swift",
      "Python",
      "Claude Code",
      "React 19",
      "Fort Worth, TX"
    ],
    "starMap": {
      "products": ["Celestia 3", "RORORO", "We See You at the Movies"]
    },
```

- [ ] **Step 2: Write the blob builder + panel emitter in render-hub.py**

In `scripts/render-hub.py`, directly above `def render_about(` (line 994), add:

```python
def _starmap_blob(about: dict, products: list) -> str:
    """Byte-stable JSON for the star map. Plugin order = site.json order
    (load-bearing: it assigns spine slots). No timestamps, no randomness.
    Versions are deliberately NOT baked — the JS fetches
    data/plugin-versions.json at runtime so the daily version bump can't
    drift this file against --check."""
    cfg = about.get("starMap") or {}
    live = [
        p for p in products
        if site_facts.is_claude_plugin(p) and p.get("status") == "live"
    ]
    plugins = [
        {
            "id": p.get("id", ""),
            "name": p.get("title", p.get("id", "")),
            "flagship": bool(p.get("flagship")),
        }
        for p in live
    ]
    if plugins and not any(pl["flagship"] for pl in plugins):
        plugins[0]["flagship"] = True
    blob = {
        "plugins": plugins,
        "products": [{"name": n} for n in (cfg.get("products") or [])],
    }
    # sort_keys for byte-stability; lists keep their (load-bearing) order.
    # Escape "</" so the JSON can never close its own <script> element.
    return json.dumps(blob, separators=(",", ":"), sort_keys=True).replace("</", "<\\/")


def _render_starmap(about: dict, products: list) -> str:
    """The constellation panel. Emitted only when about.starMap exists —
    presence of the config block is the feature toggle."""
    if about.get("starMap") is None:
        return ""
    return f"""
  <div class="wrap">
    <figure class="starmap" id="plugin-constellation">
      <canvas class="starmap-sky" aria-hidden="true"></canvas>
      <div class="starmap-tooltip" hidden></div>
      <figcaption class="starmap-caption">
        <span class="starmap-label">The plugin constellation</span>
        <span class="starmap-legend">
          <span class="lg lg-plugin">live plugin</span>
          <span class="lg lg-flagship">flagship</span>
          <span class="lg lg-product">products</span>
        </span>
      </figcaption>
    </figure>
    <script type="application/json" id="starmap-data">{_starmap_blob(about, products)}</script>
  </div>
"""
```

- [ ] **Step 3: Wire the panel into render_about**

Change the signature at line 995 and the return at lines 1028-1048:

```python
def render_about(about: dict, products: list | None = None) -> str:
```

(keep the existing docstring and body above the return), then replace the return statement with:

```python
    return f"""\
<section class="section manifesto" id="about">
  <div class="wrap manifesto-inner">
    <div>
      <div class="eyebrow"><span>{eyebrow}</span><span class="line"></span></div>
      <h2>{headline}{accent_html}</h2>
      <div class="stack">
{stack_html}
      </div>
    </div>
    <div class="manifesto-body">
{para_html}
    </div>
  </div>
{_render_starmap(about, products or [])}
  <div class="wrap">
    <div class="principles">
{principles_html}
    </div>
  </div>
</section>"""
```

- [ ] **Step 4: Update the call site**

At `scripts/render-hub.py:1639`, change:

```python
        out = substitute_zone(out, "about", render_about(content["about"]))
```

to:

```python
        out = substitute_zone(
            out, "about",
            render_about(content["about"], content.get("products") or []),
        )
```

Note: `content` here has already been through `site_facts.resolve_tokens`, which only substitutes `{{fact:...}}` strings — product dicts keep their `id`/`status`/`claudeCode`/`flagship` fields untouched.

- [ ] **Step 5: Render and verify the blob**

```bash
python scripts/render-hub.py
python -c "
import json, re, sys
html = open('index.html', encoding='utf-8').read()
m = re.search(r'<script type=\"application/json\" id=\"starmap-data\">(.*?)</script>', html, re.S)
assert m, 'blob missing'
blob = json.loads(m.group(1))  # '<\/' is a valid JSON escape — parses as-is
site = json.load(open('content/site.json', encoding='utf-8'))
live = [p['id'] for p in site['products'] if p.get('claudeCode') and p.get('status') == 'live']
assert [p['id'] for p in blob['plugins']] == live, (blob['plugins'], live)
assert any(p['flagship'] for p in blob['plugins'])
assert blob['products'] == [{'name': n} for n in site['about']['starMap']['products']]
print('blob OK:', len(blob['plugins']), 'plugins,', len(blob['products']), 'products')
"
```

Expected: `blob OK: <N> plugins, 3 products` where N matches the live plugin count.

- [ ] **Step 6: Verify idempotency and content health**

```bash
python scripts/render-hub.py --check
python scripts/site-doctor.py --check
```

Expected: both exit 0 ("up to date" / doctor passes).

- [ ] **Step 7: Verify the toggle (rollback path)**

Temporarily remove the `starMap` block from site.json, run `python scripts/render-hub.py`, confirm `grep -c "plugin-constellation" index.html` returns 0; restore the block, re-render, confirm it returns 1 (the figure id — it becomes 2 after Task 3 adds the JS lookup). Leave the tree in the enabled state.

- [ ] **Step 8: Commit**

```bash
git add content/site.json scripts/render-hub.py index.html
git commit -m "feat(about): emit star map panel + data blob from render_about"
```

---

### Task 2: CSS — the panel's clothes

**Files:**
- Modify: `index.html` — insert before `</style>` at line ~1523, directly after the `.principle` rules (keeps About-section styles together)

**Depends on:** Task 1 (markup exists to style).
**Acceptance:** panel renders as a bordered, rounded navy field, 340px sky (240px under 760px width), mono-uppercase caption with three legend dots; no layout shift elsewhere; `--check` still passes.
**Effort:** ~15 min.

- [ ] **Step 1: Insert the styles**

```css
    /* ── About star map ─────────────────────────── */
    .starmap {
      margin-top: var(--s-10);
      position: relative;
      border: 1px solid rgba(23, 212, 250, 0.18);
      border-radius: var(--r-lg);
      overflow: hidden;
      background: radial-gradient(ellipse at 60% 40%, #14283f 0%, #0f1f31 70%);
    }
    .starmap-sky { display: block; width: 100%; height: 340px; }
    @media (max-width: 760px) { .starmap-sky { height: 240px; } }
    .starmap-caption {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: var(--s-4);
      padding: 10px 14px;
      border-top: 1px solid var(--border-1);
      font-family: var(--font-mono);
      font-size: 10.5px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--fg-2);
    }
    .starmap-legend { display: flex; gap: var(--s-4); }
    .starmap-legend .lg { display: inline-flex; align-items: center; gap: 6px; }
    .starmap-legend .lg::before {
      content: "";
      width: 7px; height: 7px; border-radius: 50%;
    }
    .starmap-legend .lg-plugin::before   { background: #17d4fa; box-shadow: 0 0 6px rgba(23, 212, 250, 0.8); }
    .starmap-legend .lg-flagship::before { background: #f22f89; box-shadow: 0 0 6px rgba(242, 47, 137, 0.8); }
    .starmap-legend .lg-product::before  { background: #e8f6ff; box-shadow: 0 0 6px rgba(232, 246, 255, 0.7); }
    @media (max-width: 600px) {
      .starmap-caption { flex-direction: column; align-items: flex-start; gap: 6px; }
    }
    .starmap-tooltip {
      position: absolute;
      z-index: 2;
      pointer-events: none;
      font-family: var(--font-mono);
      font-size: 10.5px;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--fg-1);
      background: rgba(10, 22, 38, 0.92);
      border: 1px solid rgba(23, 212, 250, 0.35);
      border-radius: 6px;
      padding: 5px 9px;
      white-space: nowrap;
    }
```

- [ ] **Step 2: Verify visually + idempotency**

```bash
python scripts/render-hub.py --check
python -m http.server 8030
```

Open `http://localhost:8030/#about`: bordered navy panel with caption + legend dots between the About paragraphs and the principles grid. Empty sky is correct at this stage (JS lands in Task 3). Stop the server.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat(about): star map panel styles"
```

---

### Task 3: JS — the sky itself (layout, reveal, ambient, tooltip)

**Files:**
- Modify: `index.html` — insert a new `<script>` block immediately after the existing main `</script>` (the one that opens at line ~2502 and contains LAB_POOL), before `</body>`

**Depends on:** Tasks 1-2 (blob + panel + styles in place).
**Acceptance:** reveal fires once at ~35% visibility and settles to ambient; identical star positions across reloads; RAF stops when the panel leaves the viewport; reduced-motion gets a static settled sky; hover/tap shows `ID · vX.Y.Z` tooltips (name-only if the version fetch fails); zero console errors; graceful no-op when the blob is absent.
**Effort:** ~60-90 min.

- [ ] **Step 1: Insert the complete star map script**

The script is self-contained, reads brand constants locally, and never throws on missing prerequisites:

```html
<script>
  // ============================================================
  //  STARMAP — the plugin constellation in #about
  //  Data: #starmap-data blob (emitted by render-hub.py).
  //  Versions: runtime fetch of data/plugin-versions.json —
  //  never baked into the render (see spec: byte-stable --check).
  //  Deterministic by construction: FNV-1a jitter + seeded dust.
  // ============================================================
  (function () {
    "use strict";
    var panel = document.getElementById("plugin-constellation");
    var dataEl = document.getElementById("starmap-data");
    if (!panel || !dataEl) return;
    var canvas = panel.querySelector(".starmap-sky");
    var tooltip = panel.querySelector(".starmap-tooltip");
    if (!canvas || !canvas.getContext) return;
    var data;
    try { data = JSON.parse(dataEl.textContent); } catch (e) { return; }
    var plugins = data.plugins || [];
    var prodNames = (data.products || []).map(function (p) { return p.name; });
    if (!plugins.length) return;

    var CYAN = "#17d4fa", MAG = "#f22f89", DUST = "#cfe9f5", PROD = "#e8f6ff";
    var ctx = canvas.getContext("2d");
    var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // ── deterministic helpers ─────────────────────
    function fnv1a(str) {
      var h = 0x811c9dc5;
      for (var i = 0; i < str.length; i++) {
        h ^= str.charCodeAt(i);
        h = Math.imul(h, 0x01000193) >>> 0;
      }
      return h >>> 0;
    }
    function mulberry32(a) {
      return function () {
        a |= 0; a = (a + 0x6D2B79F5) | 0;
        var t = Math.imul(a ^ (a >>> 15), 1 | a);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
      };
    }
    function jitter(id) {
      var h = fnv1a(id);
      return [
        ((h & 0xffff) / 0xffff - 0.5) * 0.06,
        (((h >>> 16) & 0xffff) / 0xffff - 0.5) * 0.06
      ];
    }

    // ── the curated spine ─────────────────────────
    // Hand-designed wave (normalized coords). Slots sample it
    // arc-length-evenly, so any plugin count lays out sanely.
    var SPINE = [[.07,.60],[.20,.36],[.36,.64],[.52,.32],[.68,.58],[.84,.38],[.94,.55]];
    var PROD_ANCHORS = [[.07,.15],[.92,.12],[.12,.87],[.93,.83],[.50,.08]];

    function spineAt(t) {
      var segs = [], total = 0, i, dx, dy, len;
      for (i = 0; i < SPINE.length - 1; i++) {
        dx = SPINE[i+1][0] - SPINE[i][0];
        dy = SPINE[i+1][1] - SPINE[i][1];
        len = Math.sqrt(dx*dx + dy*dy);
        segs.push(len); total += len;
      }
      var target = t * total, acc = 0;
      for (i = 0; i < segs.length; i++) {
        if (acc + segs[i] >= target) {
          var k = segs[i] ? (target - acc) / segs[i] : 0;
          return [
            SPINE[i][0] + (SPINE[i+1][0] - SPINE[i][0]) * k,
            SPINE[i][1] + (SPINE[i+1][1] - SPINE[i][1]) * k
          ];
        }
        acc += segs[i];
      }
      return SPINE[SPINE.length - 1].slice();
    }

    // ── layout (recomputed on resize) ─────────────
    var W = 0, H = 0, stars = [], prods = [], dust = [], edges = [];
    function layout() {
      var dpr = Math.min(2, window.devicePixelRatio || 1);
      W = canvas.clientWidth; H = canvas.clientHeight;
      canvas.width = W * dpr; canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var padX = 26, padY = 30;
      function px(n) { return padX + n[0] * (W - 2 * padX); }
      function py(n) { return padY + n[1] * (H - 2 * padY); }

      stars = plugins.map(function (p, i) {
        var slot = spineAt((i + 0.5) / plugins.length);
        var j = jitter(p.id);
        return {
          kind: "plugin", id: p.id, name: p.name, flagship: !!p.flagship,
          x: px([slot[0] + j[0], 0]), y: py([0, slot[1] + j[1]]),
          r: p.flagship ? 3.6 : 2.7, i: i
        };
      });

      // edges: chain along the spine + up to two deterministic cross-links
      edges = [];
      var n = plugins.length, i;
      for (i = 0; i < n - 1; i++) edges.push([i, i + 1]);
      if (n >= 5) {
        var c0 = fnv1a(plugins[0].id) % (n - 2);
        edges.push([c0, c0 + 2]);
      }
      if (n >= 8) {
        var c1 = fnv1a(plugins[n - 1].id) % (n - 2);
        if (c1 !== (edges[edges.length - 1][0])) edges.push([c1, c1 + 2]);
      }

      prods = prodNames.slice(0, PROD_ANCHORS.length).map(function (name, i) {
        var j = jitter(name);
        var a = PROD_ANCHORS[i];
        return {
          kind: "product", id: name, name: name,
          x: px([a[0] + j[0], 0]), y: py([0, a[1] + j[1]]), r: 2.3, i: i
        };
      });

      var rng = mulberry32(20260609);
      dust = [];
      for (i = 0; i < 50; i++) {
        dust.push({
          x: rng() * W, y: rng() * H,
          r: rng() < 0.12 ? 1.5 : 0.9,
          a: 0.12 + rng() * 0.35,
          ph: rng() * 6.28, sp: 0.5 + rng()
        });
      }
    }

    // ── drawing ───────────────────────────────────
    function bgFill() {
      var g = ctx.createRadialGradient(W * .6, H * .4, 0, W * .6, H * .4, W * .7);
      g.addColorStop(0, "#14283f"); g.addColorStop(1, "#0f1f31");
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    }
    function dot(x, y, r, color, alpha, blur) {
      ctx.save();
      ctx.globalAlpha = Math.max(0, Math.min(1, alpha));
      ctx.shadowBlur = blur; ctx.shadowColor = color;
      ctx.fillStyle = color;
      ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fill();
      ctx.restore();
    }
    var clamp = function (v) { return Math.max(0, Math.min(1, v)); };
    var easeOut = function (k) { return 1 - Math.pow(1 - k, 3); };
    function easeOutBack(k) {
      var c = 1.70158;
      return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2);
    }

    // Reveal timeline (spec): dust 0-700, stars from 400 (160 stagger,
    // 380 each, overshoot), lines from 1900 (200 stagger, 450 each).
    var revealStart = null;   // set on first 35%-visibility intersection
    var revealT = function (now) {
      return reduced ? Infinity : (revealStart === null ? 0 : now - revealStart);
    };

    function draw(now) {
      var t = revealT(now);
      var tt = now / 1000;
      bgFill();
      var ox = reduced ? 0 : 6 * Math.sin(tt * .05);
      var oy = reduced ? 0 : 3 * Math.cos(tt * .04);

      var dustK = easeOut(clamp(t / 700));
      dust.forEach(function (s) {
        var twk = reduced ? 1 : (0.7 + 0.3 * Math.sin(tt * s.sp + s.ph));
        dot(s.x + ox * .5, s.y + oy * .5, s.r, DUST, s.a * twk * dustK, 0);
      });

      prods.forEach(function (p) {
        var k = easeOut(clamp((t - 200 - p.i * 120) / 500));
        var twk = reduced ? .85 : (0.7 + 0.25 * Math.sin(tt * .7 + p.i * 2));
        dot(p.x + ox, p.y + oy, p.r, PROD, twk * k, 8 * k);
      });

      ctx.save();
      ctx.strokeStyle = CYAN; ctx.lineWidth = 1;
      var pulse = reduced ? 0.32 : (0.28 + 0.08 * Math.sin(tt * .8));
      edges.forEach(function (e, j) {
        var k = easeOut(clamp((t - 1900 - j * 200) / 450));
        if (k <= 0) return;
        var a = stars[e[0]], b = stars[e[1]];
        var x1 = a.x + (b.x - a.x) * k, y1 = a.y + (b.y - a.y) * k;
        ctx.globalAlpha = pulse * k;
        ctx.beginPath();
        ctx.moveTo(a.x + ox, a.y + oy);
        ctx.lineTo(x1 + ox, y1 + oy);
        ctx.stroke();
      });
      ctx.restore();

      stars.forEach(function (s) {
        var k = clamp((t - 400 - s.i * 160) / 380);
        if (k <= 0) return;
        var sc = k >= 1 ? 1 : easeOutBack(k);
        var twk = reduced ? .9 : (0.75 + 0.25 * Math.sin(tt * 1.3 + s.i * 1.7));
        dot(s.x + ox, s.y + oy, s.r * sc, s.flagship ? MAG : CYAN, twk * k, 10 * k);
      });
    }

    // ── lifecycle: draw only while visible ────────
    var rafId = null;
    function loop(now) { draw(now); rafId = requestAnimationFrame(loop); }
    function start() { if (rafId === null && !reduced) rafId = requestAnimationFrame(loop); }
    function stop() { if (rafId !== null) { cancelAnimationFrame(rafId); rafId = null; } }

    layout();
    if (reduced) draw(performance.now());

    var io = new IntersectionObserver(function (entries) {
      var vis = entries[0].isIntersecting;
      if (vis) {
        if (reduced) { draw(performance.now()); return; }
        if (revealStart === null) revealStart = performance.now();
        start();
      } else {
        stop();
      }
    }, { threshold: 0.35 });
    io.observe(panel);

    window.addEventListener("resize", function () {
      layout();
      if (reduced || rafId === null) draw(performance.now());
    });

    // ── versions: runtime join, progressive ───────
    var versions = {};
    fetch("data/plugin-versions.json")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (v) { if (v) versions = v; })
      .catch(function () { /* tooltips degrade to name-only */ });

    // ── tooltip: nearest star within 14px ─────────
    function hit(mx, my) {
      var best = null, bestD = 14;
      stars.concat(prods).forEach(function (s) {
        var d = Math.hypot(mx - s.x, my - s.y);
        if (d < bestD) { bestD = d; best = s; }
      });
      return best;
    }
    function showTip(s) {
      var v = s.kind === "plugin" ? versions[s.id] : null;
      tooltip.textContent = s.id.toUpperCase() + (v ? " · " + v : "");
      tooltip.hidden = false;
      var tx = Math.min(s.x + 12, W - 10 - tooltip.offsetWidth);
      var ty = Math.max(8, s.y - 10 - tooltip.offsetHeight);
      tooltip.style.left = tx + "px";
      tooltip.style.top = ty + "px";
    }
    function onPoint(e) {
      var rect = canvas.getBoundingClientRect();
      var s = hit(e.clientX - rect.left, e.clientY - rect.top);
      if (s) showTip(s); else tooltip.hidden = true;
    }
    canvas.addEventListener("pointermove", onPoint);
    canvas.addEventListener("pointerdown", onPoint);
    canvas.addEventListener("pointerleave", function () { tooltip.hidden = true; });
  })();
</script>
```

- [ ] **Step 2: Re-verify the render contract**

```bash
python scripts/render-hub.py --check
```

Expected: exit 0 — the new script lives outside every `SITE_JSON:` zone, so the renderer must not see drift. If this fails, the script was inserted inside a zone; move it.

- [ ] **Step 3: Browser verification — reveal + ambient**

```bash
python -m http.server 8030
```

Open `http://localhost:8030/`, scroll to About. Verify: reveal fires once when the panel is ~1/3 visible (dust fades, stars pop with overshoot, lines draw), then settles to twinkle + drift. Reload → identical star positions (determinism). Console: zero errors.

- [ ] **Step 4: Browser verification — lifecycle + reduced motion + tooltip**

- DevTools Performance monitor: scroll away from About → CPU drops to idle (RAF stopped); scroll back → ambient resumes without replaying the reveal.
- DevTools Rendering tab → emulate `prefers-reduced-motion: reduce` → hard reload: settled sky immediately, no animation, no RAF loop.
- Hover the flagship star → `VIBE-CARTOGRAPHER · v1.9.1` (version from the runtime fetch). Hover a product → name-only. DevTools offline (or block the versions fetch) → tooltips degrade to name-only, no console error.
- Touch emulation: tap a star → tooltip; tap empty sky → dismissed.

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "feat(about): star map canvas — spine layout, reveal, ambient, tooltips"
```

---

### Task 4: Verification sweep (the spec's full checklist)

**Files:** none modified (temporary local edits only, reverted).

**Depends on:** Tasks 1-3.
**Acceptance:** every item in the spec's Verification plan passes, including the growth test.
**Effort:** ~30 min.

- [ ] **Step 1: Pipeline checks**

```bash
python scripts/render-hub.py && python scripts/render-hub.py --check
python scripts/site-doctor.py --check
```

Expected: both clean, twice in a row (idempotent).

- [ ] **Step 2: Growth test — the constellation must grow itself**

Temporarily add a fake live plugin to `content/site.json` products:

```json
    {
      "id": "vibe-fake",
      "title": "Vibe Fake",
      "tagline": "Test star.",
      "description": "Growth-test placeholder.",
      "tags": [],
      "status": "live",
      "claudeCode": true,
      "screenshots": []
    },
```

Run `python scripts/render-hub.py`, serve, and confirm: one more star on the spine, chain edge extended, layout sane, tooltip reads `VIBE-FAKE` (no version — and that's the degradation path working). Then **revert site.json, re-render, and confirm `git status` shows only the intended Task 1-3 changes**.

- [ ] **Step 3: Responsive + no-JS**

- Widths 360 / 768 / 1440 (DevTools): panel height honors the 760px breakpoint, caption legible (legend stacks under 600px), no horizontal overflow.
- Disable JavaScript (DevTools → Settings → Debugger) → reload: framed navy field + caption render, empty sky, no errors. Re-enable.

- [ ] **Step 4: Accessibility spot-check**

- Canvas has `aria-hidden="true"` in the rendered output: `grep -c 'starmap-sky" aria-hidden="true"' index.html` → 1.
- The paragraph above the panel still names every live plugin (the `{{fact:live_plugin_names}}` text) — the decorative-canvas justification from the spec.

---

### Task 5: Documentation & Security Verification (final — Cart convention)

**Files:**
- Modify: `CLAUDE.md` (What's where table, `index.html` row)

**Depends on:** Tasks 1-4.
**Acceptance:** docs reflect the new surface; no secrets in the diff; branch pushed and PR opened against main.
**Effort:** ~20 min.

- [ ] **Step 1: Document the surface in CLAUDE.md**

In the What's where table, extend the `index.html` row description:

```markdown
| `index.html` | The live site. Hand-written shell with `SITE_JSON:<zone>:start/end` markers that get filled by render-hub.py. The About star map's CSS + JS live in the static shell; its markup + data blob are emitted by `render_about()` (config: `about.starMap` in site.json — remove the block to disable the panel). Versions in star tooltips come from a runtime fetch of `data/plugin-versions.json`, never from the render. |
```

- [ ] **Step 2: Security pass**

- `git diff main...HEAD` — confirm: no tokens, no keys, no new external requests beyond the same-origin `data/plugin-versions.json` fetch, no `innerHTML` with non-literal input (tooltip uses `textContent`), blob escapes `</`.
- No new dependencies, no new workflow permissions. Nothing to audit beyond the diff.

- [ ] **Step 3: Final render + commit + push + PR**

```bash
python scripts/render-hub.py --check && python scripts/site-doctor.py --check
git add CLAUDE.md
git commit -m "docs: star map surface in repo guide"
git push -u origin feat/about-star-map
gh pr create --base main --title "feat(about): plugin constellation star map" --body "..."
```

PR body should name: the spec + plan paths, the four locked design decisions, the runtime-version-join rationale, and the verification sweep results. End the body with the standard generation footer.

- [ ] **Step 4: Post-merge note**

After merge, `rebuild-hub.yml` re-renders on the site.json change and Pages redeploys — verify the panel on the live site, then log completion to the 626 dashboard (decision t2n361qiKRFvMuY1A8RW already records the architecture; add a completion note via `manage_decisions` only if something diverged from this plan).
