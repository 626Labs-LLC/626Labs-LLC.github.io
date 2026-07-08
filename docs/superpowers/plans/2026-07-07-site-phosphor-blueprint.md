# 626labs.dev Phosphor Blueprint Conversion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the live homepage (`index.html`) to the Phosphor Blueprint treatment — absolute-black drafting grid, scanlines, near-black glass, bloom, persistence hovers — via an append-only override layer, then prove nothing else on the site moved.

**Architecture:** One `<style>`-terminal "treatment layer" block overrides the semantic tokens (`--bg-*`, `--border-*`) and adds the PB kit; one scanline `<div>` after `<body>`; one `theme-color` meta swap. Base CSS above the layer stays untouched, `SITE_JSON` zones stay untouched. Judgment pass tunes the signature moments on screenshots; a dedicated second sweep hunts strays; gates + PR close it.

**Tech Stack:** Hand-written HTML/CSS (no build), Python for the render/doctor gates, local HTTP server + Playwright for visual verification.

**Spec:** `docs/superpowers/specs/2026-07-07-site-phosphor-blueprint-design.md`

## Global Constraints

- Zero edits inside any `SITE_JSON:*` zone. Gate: `python scripts/render-hub.py --check` exit 0.
- Zero content/copy/structure changes. This is a re-skin.
- Color discipline: new color literals only as `rgb(0,0,0)`/pure-black rgba, rgba of existing token triples (cyan 23,212,250 / magenta 242,47,137), or existing tokens. The one hex exception: `<meta name="theme-color" content="#000000">` (HTML attribute, pure black).
- No new animation (`prefers-reduced-motion` stays satisfied). No emoji.
- Scanline alpha ships at `.42`; legibility escape hatch: drop toward `.3` if long body copy shimmers.
- Article care: Field Note / Thinking / Stories cards re-skin surface-only — type layout pixel-faithful.
- Branch: `feat/site-phosphor-blueprint` (already cut from origin/main). Conventional commits, one per task.
- Local viewing: `python -m http.server <port>` from the REPO ROOT (fonts import is root-absolute; `file://` falls back to system fonts). Bust browser cache when re-checking CSS (`fetch(url, {cache:'reload'})`) — http.server sends no Cache-Control and Chrome's heuristic cache serves stale for hours.

---

### Task 1: Treatment layer + scanline overlay + theme-color

**Files:**
- Modify: `index.html:10` (theme-color), `index.html` (`</style>` — insert layer immediately before it), `index.html:1580` (`<body>` — insert overlay div after it)

**Interfaces:**
- Produces: the `.pb-*` classes and re-pointed semantic tokens every later task tunes. The treatment layer is the ONLY place PB styling lives — later tuning edits THIS block, never base CSS.

- [ ] **Step 1: theme-color**

`index.html:10`: `<meta name="theme-color" content="#0f1f31" />` → `<meta name="theme-color" content="#000000" />`

- [ ] **Step 2: Insert the treatment layer**

Immediately before the closing `</style>` of the main style block, insert:

```css
    /* ============================================================
       Phosphor Blueprint — treatment layer (adopted 2026-07-07)
       Append-only override; base system above stays intact.
       Spec: docs/superpowers/specs/2026-07-07-site-phosphor-blueprint-design.md
       ============================================================ */
    :root {
      --pb-field: rgb(0,0,0);
      --pb-grid-fine: rgba(23,212,250,.05);
      --pb-grid-coarse: rgba(23,212,250,.11);
      --pb-scanline: rgba(0,0,0,.42);
      --pb-panel: rgba(0,0,0,.72);
      --pb-panel-border: rgba(23,212,250,.25);
      --pb-bloom-cyan: 0 0 14px rgba(23,212,250,.5);
      --pb-bloom-magenta: 0 0 8px rgba(242,47,137,.6);
      --pb-trail: 0 0 6px rgba(23,212,250,.9), 0 0 28px rgba(23,212,250,.5), 12px 0 24px rgba(23,212,250,.25);

      /* navy retires on this surface */
      --bg-0: var(--pb-field);
      --bg-1: rgba(0,0,0,.6);
      --bg-2: rgba(0,0,0,.72);
      --border-1: rgba(23,212,250,.14);
      --border-2: rgba(23,212,250,.25);
    }
    body {
      background:
        linear-gradient(90deg, var(--pb-grid-fine) 1px, transparent 1px),
        linear-gradient(0deg,  var(--pb-grid-fine) 1px, transparent 1px),
        linear-gradient(90deg, var(--pb-grid-coarse) 1px, transparent 1px),
        linear-gradient(0deg,  var(--pb-grid-coarse) 1px, transparent 1px),
        var(--pb-field);
      background-size: 24px 24px, 24px 24px, 120px 120px, 120px 120px;
    }
    .pb-scanlines {
      position: fixed; inset: 0; pointer-events: none; z-index: 60; /* above nav (50), below skip-link (200) */
      background: repeating-linear-gradient(0deg, var(--pb-scanline) 0 1px, transparent 1px 3px);
    }
    nav.nav { background: rgba(0,0,0,.72); }
    header.hero h1 { text-shadow: var(--pb-bloom-cyan); }
    .hero-bg .grid { display: none; } /* body's drafting grid owns the field — two grids moiré */
    .btn-primary:hover { box-shadow: var(--pb-trail); }
    @media (max-width: 720px) {
      body { /* coarse grid only on small screens — fine grid reads as noise */
        background:
          linear-gradient(90deg, var(--pb-grid-coarse) 1px, transparent 1px),
          linear-gradient(0deg,  var(--pb-grid-coarse) 1px, transparent 1px),
          var(--pb-field);
        background-size: 120px 120px, 120px 120px;
      }
    }
```

- [ ] **Step 3: Scanline overlay div**

After `<body>` (line 1580), insert: `<div class="pb-scanlines" aria-hidden="true"></div>`

- [ ] **Step 4: Render gate**

Run: `python scripts/render-hub.py --check`
Expected: exit 0 (treatment layer + div are outside all zones).

- [ ] **Step 5: First look**

Serve repo root, screenshot `/` at 1440px full-page. Expected: black field with two-scale grid, scanlines everywhere, glass nav, hero H1 blooming, no navy body anywhere above the fold. This is the calibration artifact for Task 2 — imperfections in section styling are EXPECTED here.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat(site): Phosphor Blueprint treatment layer — black drafting field, scanlines, glass nav"
```

---

### Task 2: Curated judgment pass (screenshots drive; edits stay inside the treatment layer)

**Files:**
- Modify: `index.html` (treatment layer block only)

**Interfaces:**
- Consumes: Task 1's layer. All tuning appends/edits rules INSIDE the layer block.

Named dials to judge on full-page screenshots at 1440px (each is a decision to make, with its default):

- [ ] **Hero glows** (`.hero-bg .glow-a/.glow-b`): default keep at reduced strength (`opacity: .6` in layer); kill if they read aurora-not-phosphor on black.
- [ ] **Stat/number moments**: `.hero-meta b`, `.principle .num`, `.preview-bullet .num` — bloom the ones that read as "stat values", skip any that turn noisy at small sizes.
- [ ] **Terminal titlebars**: lab-run cards (`section.lab .lab-card`) are the only candidates. Add the `626 // session`-pattern chrome ONLY if it fits without crowding the card head; product cards NEVER get it.
- [ ] **Scrims/protection gradients**: grep the file for `rgba(15,31,49` and `rgba(15, 31, 49` inside the style block — every scrim that fades to navy gets a layer override fading to black instead. List each one in the commit body.
- [ ] **Border-strong hovers**: keep white (`--border-strong` untouched) unless cyan reads better on the glass cards — pick once, apply consistently.
- [ ] **Article-care check (constraint)**: Thinking/Stories/Field Note cards — surface re-skin only; overlay before/after screenshots and confirm type layout is pixel-faithful (same wrap points, same spacing).
- [ ] **Legibility**: read the longest copy section (product descriptions) in the 1440 screenshot; if it shimmers, drop `--pb-scanline` to `.3` and note it.
- [ ] **Gate + commit**

```bash
python scripts/render-hub.py --check
git add index.html
git commit -m "feat(site): PB judgment pass — <one line per dial decided>"
```

---

### Task 3: Second sweep (Este's constraint — fresh-eyes stray hunt)

**Files:** none modified unless strays found (fixes go in the treatment layer; commit separately if any).

- [ ] **Stray grep:** `grep -n "#0f1f31\|#192e44\|#223a54\|15, 31, 49\|15,31,49" index.html` — every hit is either (a) inside a `SITE_JSON` zone (renderer-owned, leave, note it), (b) a deliberate keep (justify in writing), or (c) a bug (fix in layer). Zero unexplained hits.
- [ ] **Full-scroll screenshots** at 1440 / 768 / 390: every section top to bottom. Hunting: navy islands, opaque-black panels that lost the grid ghost, scanline artifacts over screenshots/images, grid seams at section boundaries, unstyled hover states.
- [ ] **Interactive states:** nav links, all three button variants (hover + focus-visible), product card hover, story card hover, skip-link focus (Tab from address bar), contact links.
- [ ] **No-leak verification (one page per bucket):** `/vibe-cartographer/`, `/press.html`, `/editorial/`, one story page — `git status` proves untracked/unmodified; render each locally and screenshot; article formatting inspected deliberately (headings, pull-quotes, line measure intact on the light layer).
- [ ] **Gates:** `python scripts/render-hub.py --check` exit 0; `python scripts/site-doctor.py --report` (read it), then `--check` exit 0.
- [ ] **Commit** (only if strays were fixed): `fix(site): PB second sweep — <strays fixed>`

---

### Task 4: Ship — PR + follow-up tasks

- [ ] **Push branch:** `git push -u origin feat/site-phosphor-blueprint`
- [ ] **PR:** title `feat(site): 626labs.dev goes Phosphor Blueprint (index pass)`. Body: before/after screenshots at 1440/768/390, the coverage matrix from the spec, dials decided in Task 2, sweep results, gates output. End with the standard PR footer.
- [ ] **Dashboard follow-up tasks** (so passes don't evaporate): Pass 2 — plugin-page template conversion; Pass 3 — standalone dark pages (press/privacy/rororo/workflow/thesis/404); Pass 4 — OG/social/brand assets to PB.
- [ ] **Decision log:** conversion shipped to PR, awaiting merge.
- [ ] **Report to Este:** PR link + screenshots + what changes on merge (Pages redeploy).
