# Brand Treatment Exploration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build six token-locked visual treatment directions as identical, directly comparable HTML specimen sheets under `Design/explorations/2026-07-07-treatments/`, plus an index page, for keep/kill/remix judging.

**Architecture:** One shared skeleton file defines the fixed specimen structure (hero, cards, buttons, chips, code, stats, texture swatch) with base-token styling and links the repo's existing `Design/colors_and_type.css`. Each direction copies the skeleton and replaces only its `<style id="treatment">` block (plus tiny markup deltas where noted). A zero-dep Python checker enforces token discipline mechanically.

**Tech Stack:** Static HTML + CSS (no build, no framework, no CDN beyond the Google Fonts `@import` already inside the token file). Python 3 for the checker.

**Spec:** `docs/superpowers/specs/2026-07-07-brand-treatment-exploration-design.md`

## Global Constraints

- **Tokens locked:** every color literal must be a value from `Design/colors_and_type.css`, or an `rgba()`/URL-encoded (`%23`) form of one. Pure white/black rgba is allowed (hairlines/scrims). Zero new hexes. The checker (Task 1) is the gate — run it in every task.
- **Type stack untouched:** Space Grotesk display, Inter body, JetBrains Mono code/meta (all arrive via the linked token file).
- **Zero dependencies:** inline `<style>` + one relative `<link rel="stylesheet" href="../../colors_and_type.css">`. SVG textures must be inline `data:` URIs.
- **Nothing ships:** no file outside `Design/explorations/2026-07-07-treatments/` may be created or modified. Never reference these files from `index.html` (site root) or `content/site.json`.
- **No emoji, no Unicode dingbats** in any sheet copy (brand rule).
- **Responsive floor:** no horizontal scroll at 1440px or 768px viewport width.
- **Commits:** conventional commits, one per task, scoped `feat(design-exploration)`. Commit only files inside the exploration directory.
- Working directory for all commands: repo root `C:\Users\estev\Projects\626labs-hub`. All paths below are repo-relative.

---

### Task 1: Scaffold — token checker + shared skeleton

**Files:**
- Create: `Design/explorations/2026-07-07-treatments/check-tokens.py`
- Create: `Design/explorations/2026-07-07-treatments/_skeleton.html`

**Interfaces:**
- Produces: `_skeleton.html` — the exact file Tasks 2–7 copy. Its `<style id="treatment">` block is the ONLY thing direction tasks replace (plus title/header text and noted markup deltas).
- Produces: `check-tokens.py` — run as `python Design/explorations/2026-07-07-treatments/check-tokens.py`; exit 0 + `OK — N files clean...` when clean, exit 1 with per-violation lines otherwise.

- [ ] **Step 1: Write the checker**

```python
#!/usr/bin/env python3
"""Token-discipline gate for the 2026-07-07 treatment exploration.

Every hex literal (raw ``#`` or URL-encoded ``%23``) and every rgb()/rgba()
triple in this directory's HTML files must trace back to a color defined in
Design/colors_and_type.css. Pure white/black are allowed for hairlines and
scrims. Exit 0 = clean, exit 1 = violations listed on stdout.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOKEN_FILE = HERE.parent.parent / "colors_and_type.css"

HEX_RE = re.compile(r"(?:#|%23)([0-9a-fA-F]{6})\b")
RGB_RE = re.compile(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})")


def hexes(text):
    return {"#" + h.lower() for h in HEX_RE.findall(text)}


token_text = TOKEN_FILE.read_text(encoding="utf-8")
allowed_hex = hexes(token_text)
allowed_rgb = {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in allowed_hex}
allowed_rgb |= {(255, 255, 255), (0, 0, 0)}

failures = []
html_files = sorted(HERE.glob("*.html"))
for f in html_files:
    text = f.read_text(encoding="utf-8")
    for h in sorted(hexes(text) - allowed_hex):
        failures.append(f"{f.name}: {h} is not a token color")
    triples = {tuple(map(int, m)) for m in RGB_RE.findall(text)}
    for t in sorted(triples - allowed_rgb):
        failures.append(f"{f.name}: rgb{t} does not derive from a token")

if failures:
    print("\n".join(failures))
    sys.exit(1)
print(f"OK — {len(html_files)} files clean against {TOKEN_FILE.name}")
```

- [ ] **Step 2: Write the skeleton**

`_skeleton.html`, complete file:

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Skeleton — 626 Labs treatment exploration</title>
<link rel="stylesheet" href="../../colors_and_type.css">
<style>
/* ---------- specimen chrome — identical across all sheets ---------- */
* { box-sizing: border-box; margin: 0; padding: 0; }
body { padding: var(--s-16) var(--s-6); }
.sheet { max-width: 1240px; margin: 0 auto; display: grid; gap: var(--s-16); }
.spec-label {
  font-family: var(--font-mono); font-size: var(--t-micro); font-weight: 600;
  text-transform: uppercase; letter-spacing: .12em; color: var(--fg-muted);
  margin-bottom: var(--s-4);
}
.thesis { color: var(--fg-3); max-width: 60ch; margin-top: var(--s-2); }

.hero { padding: var(--s-12); border-radius: var(--r-lg); background: var(--bg-1); border: 1px solid var(--border-1); }
.hero-title { font-family: var(--font-display); font-size: var(--t-h1); letter-spacing: -0.02em; line-height: var(--lh-tight); margin: var(--s-3) 0; }
.hero-sub { color: var(--fg-2); max-width: 52ch; margin-bottom: var(--s-6); }
.hero-actions { display: flex; gap: var(--s-3); flex-wrap: wrap; }

.cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--s-6); }
.card { background: var(--bg-2); border: 1px solid var(--border-1); border-radius: var(--r-md); padding: var(--s-6); box-shadow: var(--inner-stroke); }
.card-title { font-family: var(--font-display); font-size: var(--t-h4); font-weight: 600; margin: var(--s-2) 0; }
.card-body { font-size: var(--t-body-sm); color: var(--fg-2); }

.btnrow, .chiprow { display: flex; gap: var(--s-3); flex-wrap: wrap; align-items: center; }
.btn { font: 600 var(--t-body-sm)/1 var(--font-body); padding: 12px 20px; border-radius: var(--r-md); border: 1px solid transparent; text-decoration: none; display: inline-block; }
.btn-primary { background: var(--brand-cyan); color: var(--fg-on-brand); }
.btn-primary.hover { filter: brightness(1.08); box-shadow: var(--glow-cyan); }
.btn-secondary { border-color: var(--border-2); color: var(--fg-1); }
.btn-secondary.hover { background: rgba(255,255,255,.06); border-color: var(--border-strong); }
.btn-ghost { color: var(--fg-2); }
.btn-ghost.hover { background: rgba(255,255,255,.06); color: var(--fg-1); }

.chip { border-radius: var(--r-pill); padding: 5px 14px; font-size: var(--t-caption); border: 1px solid var(--border-2); color: var(--fg-2); }
.chip-active { border-color: var(--border-accent); color: var(--brand-cyan-bright); background: rgba(23,212,250,.08); }
.chip-success { border-color: rgba(43,217,154,.4); color: var(--success); background: var(--success-bg); }
.chip-warning { border-color: rgba(255,180,84,.4); color: var(--warning); background: var(--warning-bg); }
.chip-danger { border-color: rgba(255,84,114,.4); color: var(--danger); background: var(--danger-bg); }

.codeblock { background: var(--ink-900); border: 1px solid var(--border-1); border-radius: var(--r-md); padding: var(--s-5); overflow-x: auto; color: var(--fg-2); }
.code-accent { color: var(--brand-cyan-bright); }

.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--s-6); }
.stat { background: var(--bg-2); border: 1px solid var(--border-1); border-radius: var(--r-md); padding: var(--s-6); }
.stat-value { font-family: var(--font-display); font-size: var(--t-h2); font-weight: 700; }
.stat-label { font-family: var(--font-mono); font-size: var(--t-micro); text-transform: uppercase; letter-spacing: .12em; color: var(--fg-muted); margin-top: var(--s-2); }

.swatch { height: 280px; border-radius: var(--r-lg); border: 1px solid var(--border-1); background: var(--bg-1); }

@media (max-width: 800px) {
  .cards, .stats { grid-template-columns: 1fr; }
  body { padding: var(--s-8) var(--s-4); }
}
</style>
<style id="treatment">
/* ---- TREATMENT LAYER — each direction replaces this block ---- */
</style>
</head>
<body>
<main class="sheet">

  <header>
    <p class="spec-label">Treatment exploration · 2026-07-07 · Direction 0 of 6</p>
    <h1>Skeleton</h1>
    <p class="thesis">The control sheet — base tokens, no treatment. Every direction restyles exactly this page.</p>
  </header>

  <section>
    <p class="spec-label">01 · Hero</p>
    <div class="hero">
      <p class="micro">626 Labs</p>
      <h2 class="hero-title">Imagine something else.</h2>
      <p class="hero-sub">Native apps &amp; Claude Code plugins — vibe-coded, shipped, iterated in the open.</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="#">Start building</a>
        <a class="btn btn-secondary" href="#">Browse the lab</a>
      </div>
    </div>
  </section>

  <section>
    <p class="spec-label">02 · Cards</p>
    <div class="cards">
      <article class="card">
        <p class="micro">Plugin</p>
        <h3 class="card-title">Vibe Cartographer</h3>
        <p class="card-body">Idea to shipped app. Spec-driven development for solo builders.</p>
      </article>
      <article class="card">
        <p class="micro">Widget</p>
        <h3 class="card-title">Sanduhr</h3>
        <p class="card-body">Claude usage at a glance — floating, always on, out of the way.</p>
      </article>
      <article class="card">
        <p class="micro">Platform</p>
        <h3 class="card-title">Agent OS</h3>
        <p class="card-body">The Lab Dashboard. Projects, decisions, agents — one operating surface.</p>
      </article>
    </div>
  </section>

  <section>
    <p class="spec-label">03 · Buttons — rest / hover rendered side-by-side</p>
    <div class="btnrow">
      <a class="btn btn-primary" href="#">Primary</a>
      <a class="btn btn-primary hover" href="#">Primary · hover</a>
      <a class="btn btn-secondary" href="#">Secondary</a>
      <a class="btn btn-secondary hover" href="#">Secondary · hover</a>
      <a class="btn btn-ghost" href="#">Ghost</a>
      <a class="btn btn-ghost hover" href="#">Ghost · hover</a>
    </div>
  </section>

  <section>
    <p class="spec-label">04 · Chips</p>
    <div class="chiprow">
      <span class="chip">Default</span>
      <span class="chip chip-active">Active</span>
      <span class="chip chip-success">Shipped</span>
      <span class="chip chip-warning">In review</span>
      <span class="chip chip-danger">Blocked</span>
    </div>
  </section>

  <section>
    <p class="spec-label">05 · Code</p>
    <pre class="codeblock"><code>$ claude /announce sanduhr
Reading content/site.json ... done.
Drafts written: field-note, x-post, discord.
<span class="code-accent">Review before you ship.</span></code></pre>
  </section>

  <section>
    <p class="spec-label">06 · Stat tiles</p>
    <div class="stats">
      <div class="stat"><p class="stat-value">13</p><p class="stat-label">Plugins live</p></div>
      <div class="stat"><p class="stat-value">149</p><p class="stat-label">Games in manifest</p></div>
      <div class="stat"><p class="stat-value">6/26</p><p class="stat-label">626 Day</p></div>
    </div>
  </section>

  <section>
    <p class="spec-label">07 · Texture swatch — the treatment, full bleed</p>
    <div class="swatch"></div>
  </section>

</main>
</body>
</html>
```

- [ ] **Step 3: Prove the checker catches violations**

Temporarily add `<!-- #ff0000 -->` anywhere in `_skeleton.html`, then:

Run: `python Design/explorations/2026-07-07-treatments/check-tokens.py`
Expected: exit 1, output `_skeleton.html: #ff0000 is not a token color`

Remove the temporary comment.

- [ ] **Step 4: Verify clean pass**

Run: `python Design/explorations/2026-07-07-treatments/check-tokens.py`
Expected: exit 0, `OK — 1 files clean against colors_and_type.css`

- [ ] **Step 5: Visual check**

Open `Design/explorations/2026-07-07-treatments/_skeleton.html` in a browser (PowerShell: `start` the file; or Playwright screenshot at 1440px and 768px). Verify: all 7 numbered sections render, fonts are Space Grotesk / Inter / JetBrains Mono (not fallback serif), no horizontal scroll at either width.

- [ ] **Step 6: Commit**

```bash
git add Design/explorations/2026-07-07-treatments/
git commit -m "feat(design-exploration): scaffold — specimen skeleton + token-discipline checker"
```

---

### Task 2: Circuit Bloom sheet

**Files:**
- Create: `Design/explorations/2026-07-07-treatments/circuit-bloom.html`

**Interfaces:**
- Consumes: `_skeleton.html` (Task 1), `check-tokens.py` (Task 1).
- Produces: `circuit-bloom.html`, linked by the index (Task 8).

- [ ] **Step 1: Copy the skeleton**

```bash
cp Design/explorations/2026-07-07-treatments/_skeleton.html Design/explorations/2026-07-07-treatments/circuit-bloom.html
```

- [ ] **Step 2: Set identity text**

In `circuit-bloom.html` replace:
- `<title>Skeleton — 626 Labs treatment exploration</title>` → `<title>Circuit Bloom — 626 Labs treatment exploration</title>`
- `Direction 0 of 6` → `Direction 1 of 6`
- `<h1>Skeleton</h1>` → `<h1>Circuit Bloom</h1>`
- The `.thesis` line → `The 6%-opacity circuit-trace whisper promoted to a compositional element: traces routing around cards, junction nodes as accents, density gradients toward focal points.`

- [ ] **Step 3: Replace the treatment block**

Replace the contents of `<style id="treatment">` with:

```css
/* Circuit Bloom — traces promoted from whisper to composition */
body {
  background:
    radial-gradient(120% 90% at 85% -10%, rgba(23,212,250,.08), transparent 55%),
    linear-gradient(90deg, rgba(23,212,250,.05) 1px, transparent 1px),
    linear-gradient(0deg,  rgba(23,212,250,.05) 1px, transparent 1px),
    var(--bg-0);
  background-size: auto, 96px 96px, 96px 96px, auto;
}
/* junction node + trace stub entering each card */
.card { position: relative; overflow: visible; }
.card::before {
  content: ""; position: absolute; top: -5px; left: var(--s-6);
  width: 9px; height: 9px; border-radius: 50%;
  background: var(--brand-cyan);
  box-shadow: 0 0 10px rgba(23,212,250,.8);
}
.card::after {
  content: ""; position: absolute; top: calc(-1 * var(--s-6)); left: calc(var(--s-6) + 4px);
  width: 1px; height: var(--s-6); background: rgba(23,212,250,.35);
}
.cards .card:nth-child(2)::before { background: var(--brand-magenta); box-shadow: 0 0 10px rgba(242,47,137,.8); }
.cards .card:nth-child(2)::after { background: rgba(242,47,137,.35); }
/* hero: denser trace field, magenta bloom toward the CTA corner */
.hero {
  background:
    radial-gradient(60% 80% at 15% 85%, rgba(242,47,137,.10), transparent 60%),
    linear-gradient(90deg, rgba(23,212,250,.08) 1px, transparent 1px),
    linear-gradient(0deg,  rgba(23,212,250,.08) 1px, transparent 1px),
    var(--bg-1);
  background-size: auto, 48px 48px, 48px 48px, auto;
  border-color: rgba(23,212,250,.25);
}
/* swatch: full-density field — grid + node constellation */
.swatch {
  background:
    radial-gradient(circle at 12% 30%, rgba(23,212,250,.9) 2px, transparent 3px),
    radial-gradient(circle at 38% 70%, rgba(242,47,137,.9) 2px, transparent 3px),
    radial-gradient(circle at 64% 25%, rgba(23,212,250,.9) 2px, transparent 3px),
    radial-gradient(circle at 86% 60%, rgba(242,47,137,.9) 2px, transparent 3px),
    linear-gradient(90deg, rgba(23,212,250,.10) 1px, transparent 1px),
    linear-gradient(0deg,  rgba(23,212,250,.10) 1px, transparent 1px),
    var(--bg-1);
  background-size: auto, auto, auto, auto, 48px 48px, 48px 48px, auto;
}
```

Tuning is allowed (opacities, grid sizes, node positions) — the techniques (grid traces, glowing junction nodes, density gradient) are the direction and must stay.

- [ ] **Step 4: Token gate**

Run: `python Design/explorations/2026-07-07-treatments/check-tokens.py`
Expected: exit 0, `OK — 2 files clean against colors_and_type.css`

- [ ] **Step 5: Visual check**

Open in browser at 1440px and 768px. Verify: trace grid visible on body and denser in hero, glowing nodes sit on card top edges (cyan/magenta/cyan), swatch reads as a circuit constellation, no horizontal scroll.

- [ ] **Step 6: Commit**

```bash
git add Design/explorations/2026-07-07-treatments/circuit-bloom.html
git commit -m "feat(design-exploration): Circuit Bloom specimen sheet"
```

---

### Task 3: Blueprint sheet

**Files:**
- Create: `Design/explorations/2026-07-07-treatments/blueprint.html`

**Interfaces:**
- Consumes: `_skeleton.html`, `check-tokens.py` (Task 1).
- Produces: `blueprint.html`, linked by the index (Task 8).

- [ ] **Step 1: Copy the skeleton**

```bash
cp Design/explorations/2026-07-07-treatments/_skeleton.html Design/explorations/2026-07-07-treatments/blueprint.html
```

- [ ] **Step 2: Set identity text**

Replace in `blueprint.html`:
- Title → `Blueprint — 626 Labs treatment exploration`
- `Direction 0 of 6` → `Direction 2 of 6`
- `<h1>Skeleton</h1>` → `<h1>Blueprint</h1>`
- Thesis → `Schematic linework: hairline grids, dimension ticks, mono annotation labels, exploded-diagram framing. The brand as an engineering drawing.`

- [ ] **Step 3: Replace the treatment block**

```css
/* Blueprint — the brand as an engineering drawing */
body {
  background:
    linear-gradient(90deg, rgba(23,212,250,.04) 1px, transparent 1px),
    linear-gradient(0deg,  rgba(23,212,250,.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(23,212,250,.09) 1px, transparent 1px),
    linear-gradient(0deg,  rgba(23,212,250,.09) 1px, transparent 1px),
    var(--bg-0);
  background-size: 24px 24px, 24px 24px, 120px 120px, 120px 120px;
}
/* drawings have square corners */
.hero, .card, .stat, .codeblock, .swatch, .btn, .chip { border-radius: 0; }
/* annotated panels */
.hero, .card, .stat { position: relative; border-color: rgba(23,212,250,.28); background: rgba(15,31,49,.85); }
.hero::after, .card::after, .stat::after {
  position: absolute; top: -18px; right: 0;
  font: 500 10px/1 var(--font-mono); letter-spacing: .14em;
  color: var(--brand-cyan-dim);
}
.hero::after { content: "FIG. 01 — HERO"; }
.cards .card:nth-child(1)::after { content: "C-01"; }
.cards .card:nth-child(2)::after { content: "C-02"; }
.cards .card:nth-child(3)::after { content: "C-03"; }
.stats .stat:nth-child(1)::after { content: "D-01"; }
.stats .stat:nth-child(2)::after { content: "D-02"; }
.stats .stat:nth-child(3)::after { content: "D-03"; }
/* dimension line under the headline */
.hero-title { display: inline-block; border-bottom: 1px solid rgba(23,212,250,.4); padding-bottom: var(--s-2); }
/* primary CTA drawn, not filled — magenta reserved as the redline accent */
.btn-primary { background: transparent; border: 1px solid var(--brand-cyan); color: var(--brand-cyan-bright); }
.btn-primary.hover { background: rgba(23,212,250,.12); box-shadow: none; filter: none; }
.chip-active { border: 1px solid var(--brand-magenta); color: var(--brand-magenta-bright); background: rgba(242,47,137,.10); }
.swatch {
  background:
    linear-gradient(90deg, rgba(23,212,250,.06) 1px, transparent 1px),
    linear-gradient(0deg,  rgba(23,212,250,.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(23,212,250,.14) 1px, transparent 1px),
    linear-gradient(0deg,  rgba(23,212,250,.14) 1px, transparent 1px),
    var(--brand-navy-deep);
  background-size: 24px 24px, 24px 24px, 120px 120px, 120px 120px;
  border-color: rgba(23,212,250,.28);
}
```

Tuning allowed; the techniques (two-scale grid, square corners, mono annotations, drawn-not-filled CTA, magenta-as-redline) are the direction.

- [ ] **Step 4: Token gate**

Run: `python Design/explorations/2026-07-07-treatments/check-tokens.py`
Expected: exit 0, `OK — 3 files clean against colors_and_type.css`

- [ ] **Step 5: Visual check**

Verify at 1440px/768px: two-scale grid on the field, every panel square-cornered with a mono annotation floating at its top-right, primary button is outlined cyan, active chip is the lone magenta element, no horizontal scroll. Annotations must not clip against the section labels above them.

- [ ] **Step 6: Commit**

```bash
git add Design/explorations/2026-07-07-treatments/blueprint.html
git commit -m "feat(design-exploration): Blueprint specimen sheet"
```

---

### Task 4: Phosphor Terminal sheet

**Files:**
- Create: `Design/explorations/2026-07-07-treatments/phosphor-terminal.html`

**Interfaces:**
- Consumes: `_skeleton.html`, `check-tokens.py` (Task 1).
- Produces: `phosphor-terminal.html`, linked by the index (Task 8).

- [ ] **Step 1: Copy the skeleton**

```bash
cp Design/explorations/2026-07-07-treatments/_skeleton.html Design/explorations/2026-07-07-treatments/phosphor-terminal.html
```

- [ ] **Step 2: Set identity text**

Replace in `phosphor-terminal.html`:
- Title → `Phosphor Terminal — 626 Labs treatment exploration`
- `Direction 0 of 6` → `Direction 3 of 6`
- `<h1>Skeleton</h1>` → `<h1>Phosphor Terminal</h1>`
- Thesis → `CRT depth: scanlines, glow bloom, phosphor-persistence hover states, terminal chrome framing. Late-night studio monitors, made literal.`

- [ ] **Step 3: Replace the treatment block**

```css
/* Phosphor Terminal — late-night studio monitors, made literal */
body { background: var(--ink-950); }
body::after {
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 9;
  background: repeating-linear-gradient(0deg, rgba(5,12,24,.4) 0 1px, transparent 1px 3px);
}
h1, .hero-title, .stat-value { text-shadow: 0 0 14px rgba(23,212,250,.5); }
.hero, .card, .stat, .codeblock { background: var(--ink-900); border-color: rgba(23,212,250,.22); }
/* terminal titlebar on cards */
.card { padding-top: calc(var(--s-6) + 26px); position: relative; overflow: hidden; }
.card::before {
  content: "626 // session"; position: absolute; top: 0; left: 0; right: 0; height: 26px;
  font: 500 10px/26px var(--font-mono); letter-spacing: .12em; text-transform: uppercase;
  color: var(--brand-cyan-dim); padding-left: var(--s-4);
  border-bottom: 1px solid rgba(23,212,250,.22); background: rgba(23,212,250,.05);
}
/* phosphor persistence: hover leaves a trail (rendered on static hover variants) */
.btn-primary.hover {
  box-shadow: 0 0 6px rgba(23,212,250,.9), 0 0 28px rgba(23,212,250,.5), 12px 0 24px rgba(23,212,250,.25);
  filter: brightness(1.1);
}
.chip-active { text-shadow: 0 0 8px rgba(23,212,250,.7); }
.code-accent { color: var(--brand-magenta-bright); text-shadow: 0 0 8px rgba(242,47,137,.6); }
.swatch {
  background:
    radial-gradient(70% 90% at 50% 50%, rgba(23,212,250,.16), transparent 70%),
    repeating-linear-gradient(0deg, rgba(5,12,24,.5) 0 1px, transparent 1px 3px),
    var(--ink-950);
}
```

Tuning allowed; the techniques (fixed scanline overlay, text bloom, titlebar chrome, directional persistence trail) are the direction. Note `rgba(5,12,24,…)` is `--ink-950`.

- [ ] **Step 4: Token gate**

Run: `python Design/explorations/2026-07-07-treatments/check-tokens.py`
Expected: exit 0, `OK — 4 files clean against colors_and_type.css`

- [ ] **Step 5: Visual check**

Verify at 1440px/768px: scanlines cover the full viewport including during scroll (the overlay is `position: fixed`), headings and stat values bloom, cards carry the mono titlebar, primary-hover shows a rightward trail, magenta appears as the code cursor accent. Text must stay readable through the scanlines — if body copy shimmers illegibly, drop the scanline alpha (.4 → .25) and re-check.

- [ ] **Step 6: Commit**

```bash
git add Design/explorations/2026-07-07-treatments/phosphor-terminal.html
git commit -m "feat(design-exploration): Phosphor Terminal specimen sheet"
```

---

### Task 5: Signal Noise sheet

**Files:**
- Create: `Design/explorations/2026-07-07-treatments/signal-noise.html`

**Interfaces:**
- Consumes: `_skeleton.html`, `check-tokens.py` (Task 1).
- Produces: `signal-noise.html`, linked by the index (Task 8).

- [ ] **Step 1: Copy the skeleton**

```bash
cp Design/explorations/2026-07-07-treatments/_skeleton.html Design/explorations/2026-07-07-treatments/signal-noise.html
```

- [ ] **Step 2: Set identity text**

Replace in `signal-noise.html`:
- Title → `Signal Noise — 626 Labs treatment exploration`
- `Direction 0 of 6` → `Direction 4 of 6`
- `<h1>Skeleton</h1>` → `<h1>Signal Noise</h1>`
- Thesis → `Grain and dither: film-grain navy fields, dithered gradients, halftone accents. Analog texture on the digital duo.`

- [ ] **Step 3: Replace the treatment block**

```css
/* Signal Noise — analog grain on the digital duo */
body::before {
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 9; opacity: .55;
  mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/></svg>");
}
body {
  background:
    radial-gradient(100% 80% at 50% 0%, rgba(34,58,84,.8), transparent 70%),
    var(--bg-0);
}
/* dithered duotone band replaces the hero's hairline border */
.hero { border: 0; position: relative; overflow: hidden; }
.hero::before {
  content: ""; position: absolute; inset: 0 0 auto 0; height: 4px;
  background:
    radial-gradient(circle, rgba(23,212,250,.9) 1px, transparent 1.4px) 0 0 / 5px 4px,
    radial-gradient(circle, rgba(242,47,137,.9) 1px, transparent 1.4px) 2px 2px / 5px 4px;
}
/* halftone accent corner on cards */
.card { position: relative; overflow: hidden; }
.card::after {
  content: ""; position: absolute; right: -20px; bottom: -20px; width: 90px; height: 90px;
  background: radial-gradient(circle, rgba(242,47,137,.5) 1px, transparent 1.6px) 0 0 / 7px 7px;
  transform: rotate(15deg);
}
.cards .card:nth-child(2)::after {
  background: radial-gradient(circle, rgba(23,212,250,.5) 1px, transparent 1.6px) 0 0 / 7px 7px;
}
.swatch {
  background:
    radial-gradient(circle, rgba(23,212,250,.55) 1px, transparent 1.6px) 0 0 / 6px 6px,
    linear-gradient(135deg, rgba(23,212,250,.10), rgba(242,47,137,.10)),
    var(--bg-1);
}
```

Tuning allowed; the techniques (SVG `feTurbulence` grain overlay, dithered dot-gradients standing in for smooth gradients, halftone corner accents) are the direction. The grain SVG is monochrome — no color literals; `%23n` is a filter id reference, not a color.

- [ ] **Step 4: Token gate**

Run: `python Design/explorations/2026-07-07-treatments/check-tokens.py`
Expected: exit 0, `OK — 5 files clean against colors_and_type.css`

- [ ] **Step 5: Visual check**

Verify at 1440px/768px: visible grain across the whole viewport (subtle, not TV static — drop `opacity` toward .35 if it fights body text), dithered duotone band across the hero top, halftone corners peeking from cards (magenta/cyan/magenta), swatch reads as a dithered duotone field, no horizontal scroll.

- [ ] **Step 6: Commit**

```bash
git add Design/explorations/2026-07-07-treatments/signal-noise.html
git commit -m "feat(design-exploration): Signal Noise specimen sheet"
```

---

### Task 6: Aurora Depth sheet

**Files:**
- Create: `Design/explorations/2026-07-07-treatments/aurora-depth.html`

**Interfaces:**
- Consumes: `_skeleton.html`, `check-tokens.py` (Task 1).
- Produces: `aurora-depth.html`, linked by the index (Task 8).

- [ ] **Step 1: Copy the skeleton**

```bash
cp Design/explorations/2026-07-07-treatments/_skeleton.html Design/explorations/2026-07-07-treatments/aurora-depth.html
```

- [ ] **Step 2: Set identity text**

Replace in `aurora-depth.html`:
- Title → `Aurora Depth — 626 Labs treatment exploration`
- `Direction 0 of 6` → `Direction 5 of 6`
- `<h1>Skeleton</h1>` → `<h1>Aurora Depth</h1>`
- Thesis → `Atmosphere as elevation: layered duotone glows as spatial light, cards floating in a lit field instead of a shadowed one.`

- [ ] **Step 3: Replace the treatment block**

```css
/* Aurora Depth — elevation by light, not shadow */
body {
  min-height: 100vh;
  background:
    radial-gradient(90% 70% at 75% -20%, rgba(23,212,250,.16), transparent 60%),
    radial-gradient(80% 60% at 5% 115%, rgba(242,47,137,.13), transparent 60%),
    radial-gradient(50% 40% at 40% 55%, rgba(34,58,84,.7), transparent 75%),
    var(--ink-950);
}
.hero, .card, .stat {
  background: rgba(25,46,68,.5);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-color: rgba(255,255,255,.12);
  box-shadow: none;
}
/* the "lit from behind" featured card */
.cards { position: relative; }
.cards .card:nth-child(2) { position: relative; }
.cards .card:nth-child(2)::before {
  content: ""; position: absolute; inset: -24px; z-index: -1; border-radius: var(--r-xl);
  background: radial-gradient(60% 60% at 50% 50%, rgba(23,212,250,.22), transparent 70%);
}
.btn-primary.hover { box-shadow: 0 0 32px rgba(23,212,250,.45); filter: brightness(1.05); }
.stat-value {
  background: var(--brand-gradient);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.swatch {
  background:
    radial-gradient(70% 90% at 25% 20%, rgba(23,212,250,.35), transparent 60%),
    radial-gradient(70% 90% at 78% 80%, rgba(242,47,137,.30), transparent 60%),
    var(--ink-950);
}
```

Tuning allowed; the techniques (layered radial atmosphere, translucent blurred panels, light-behind-the-card elevation, gradient-clipped stat values) are the direction. Note `rgba(25,46,68,…)` is `--brand-navy`, `rgba(34,58,84,…)` is `--brand-navy-soft`.

- [ ] **Step 4: Token gate**

Run: `python Design/explorations/2026-07-07-treatments/check-tokens.py`
Expected: exit 0, `OK — 6 files clean against colors_and_type.css`

- [ ] **Step 5: Visual check**

Verify at 1440px/768px: page reads as a lit atmosphere (cyan top-right, magenta bottom-left), panels are translucent with visible blur, middle card glows from behind (glow must not be clipped — if it is, confirm no ancestor of `.cards` has `overflow: hidden`), stat values render in gradient text, no horizontal scroll.

- [ ] **Step 6: Commit**

```bash
git add Design/explorations/2026-07-07-treatments/aurora-depth.html
git commit -m "feat(design-exploration): Aurora Depth specimen sheet"
```

---

### Task 7: Hex Lattice sheet

**Files:**
- Create: `Design/explorations/2026-07-07-treatments/hex-lattice.html`

**Interfaces:**
- Consumes: `_skeleton.html`, `check-tokens.py` (Task 1).
- Produces: `hex-lattice.html`, linked by the index (Task 8).

- [ ] **Step 1: Copy the skeleton**

```bash
cp Design/explorations/2026-07-07-treatments/_skeleton.html Design/explorations/2026-07-07-treatments/hex-lattice.html
```

- [ ] **Step 2: Set identity text**

Replace in `hex-lattice.html`:
- Title → `Hex Lattice — 626 Labs treatment exploration`
- `Direction 0 of 6` → `Direction 6 of 6`
- `<h1>Skeleton</h1>` → `<h1>Hex Lattice</h1>`
- Thesis → `The logo's hexagon as structure: hex grids, clipped card corners, honeycomb fields, hex-node accents.`

- [ ] **Step 3: Markup delta — wrap each card**

`clip-path` clips borders, so clipped cards need a 1px wrapper that paints the border color behind them. In the `02 · Cards` section, wrap each of the three `<article class="card">…</article>` elements:

```html
<div class="hexwrap"><article class="card"> ... </article></div>
```

(All three cards. Card inner content unchanged.)

- [ ] **Step 4: Replace the treatment block**

```css
/* Hex Lattice — the logo's hexagon as structure */
:root { --hex-clip: polygon(20px 0, 100% 0, 100% calc(100% - 20px), calc(100% - 20px) 100%, 0 100%, 0 20px); }
/* clipped corners with the border preserved via a 1px painted wrapper */
.hexwrap { clip-path: var(--hex-clip); background: rgba(255,255,255,.14); padding: 1px; }
.hexwrap > .card { clip-path: var(--hex-clip); border: 0; border-radius: 0; height: 100%; }
.hero { clip-path: var(--hex-clip); border-radius: 0; }
.stat { border-radius: 0; }
/* hexagonal primary CTA and active chip */
.btn { border-radius: 0; }
.btn-primary {
  clip-path: polygon(10px 0, calc(100% - 10px) 0, 100% 50%, calc(100% - 10px) 100%, 10px 100%, 0 50%);
  padding: 12px 26px;
}
.chip, .chip-active { border-radius: 0; }
.chip-active {
  clip-path: polygon(8px 0, calc(100% - 8px) 0, 100% 50%, calc(100% - 8px) 100%, 8px 100%, 0 50%);
  border: 0; background: rgba(23,212,250,.16); padding: 6px 18px;
}
/* honeycomb field on the swatch */
.swatch {
  clip-path: var(--hex-clip); border-radius: 0;
  background-color: var(--bg-1);
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='56' height='97'><path d='M28 0 56 16.17v32.33L28 64.67 0 48.5V16.17zM28 64.67 56 80.83v16.17M28 64.67 0 80.83v16.17' fill='none' stroke='%2317d4fa' stroke-opacity='.14'/></svg>");
}
```

Tuning allowed (clip depths, hex tile geometry — the SVG path may need adjustment to tile seamlessly; verify visually). The techniques (clipped-corner silhouette, painted-wrapper borders, hexagonal CTA/chip, honeycomb texture) are the direction. Note `%2317d4fa` is `--brand-cyan` URL-encoded — the checker validates it.

- [ ] **Step 5: Token gate**

Run: `python Design/explorations/2026-07-07-treatments/check-tokens.py`
Expected: exit 0, `OK — 7 files clean against colors_and_type.css`

- [ ] **Step 6: Visual check**

Verify at 1440px/768px: cards show clipped opposite corners WITH a visible 1px border along the clipped edges, hero silhouette matches, primary button and active chip are hexagonal capsules, swatch shows a tiling honeycomb (no visible seams — adjust the SVG path if seams appear), no horizontal scroll.

- [ ] **Step 7: Commit**

```bash
git add Design/explorations/2026-07-07-treatments/hex-lattice.html
git commit -m "feat(design-exploration): Hex Lattice specimen sheet"
```

---

### Task 8: Index page + full-set gate

**Files:**
- Create: `Design/explorations/2026-07-07-treatments/index.html`

**Interfaces:**
- Consumes: all six sheets (Tasks 2–7), `check-tokens.py` (Task 1).
- Produces: the judging entry point Este opens.

- [ ] **Step 1: Write the index**

Complete file:

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Treatment exploration — 626 Labs</title>
<link rel="stylesheet" href="../../colors_and_type.css">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { padding: var(--s-16) var(--s-6); }
.wrap { max-width: 1240px; margin: 0 auto; }
.eyebrow {
  font-family: var(--font-mono); font-size: var(--t-micro); font-weight: 600;
  text-transform: uppercase; letter-spacing: .12em; color: var(--fg-muted);
}
h1 { margin: var(--s-3) 0; }
.lede { color: var(--fg-3); max-width: 60ch; margin-bottom: var(--s-12); }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--s-6); }
.dir {
  display: block; text-decoration: none; color: var(--fg-1);
  background: var(--bg-2); border: 1px solid var(--border-1); border-radius: var(--r-md);
  overflow: hidden; box-shadow: var(--inner-stroke);
}
.dir:hover { border-color: var(--border-accent); }
.dir .mini { height: 140px; border-bottom: 1px solid var(--border-1); }
.dir .meta { padding: var(--s-5); }
.dir .num { font-family: var(--font-mono); font-size: var(--t-micro); letter-spacing: .12em; color: var(--fg-muted); text-transform: uppercase; }
.dir h2 { font-size: var(--t-h4); margin: var(--s-2) 0; }
.dir p { font-size: var(--t-body-sm); color: var(--fg-2); }
.mini-circuit {
  background:
    radial-gradient(circle at 30% 40%, rgba(23,212,250,.9) 2px, transparent 3px),
    radial-gradient(circle at 70% 65%, rgba(242,47,137,.9) 2px, transparent 3px),
    linear-gradient(90deg, rgba(23,212,250,.10) 1px, transparent 1px),
    linear-gradient(0deg,  rgba(23,212,250,.10) 1px, transparent 1px),
    var(--bg-1);
  background-size: auto, auto, 32px 32px, 32px 32px, auto;
}
.mini-blueprint {
  background:
    linear-gradient(90deg, rgba(23,212,250,.06) 1px, transparent 1px),
    linear-gradient(0deg,  rgba(23,212,250,.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(23,212,250,.14) 1px, transparent 1px),
    linear-gradient(0deg,  rgba(23,212,250,.14) 1px, transparent 1px),
    var(--brand-navy-deep);
  background-size: 16px 16px, 16px 16px, 80px 80px, 80px 80px;
}
.mini-phosphor {
  background:
    radial-gradient(70% 90% at 50% 50%, rgba(23,212,250,.16), transparent 70%),
    repeating-linear-gradient(0deg, rgba(5,12,24,.5) 0 1px, transparent 1px 3px),
    var(--ink-950);
}
.mini-noise {
  background:
    radial-gradient(circle, rgba(23,212,250,.55) 1px, transparent 1.6px) 0 0 / 6px 6px,
    linear-gradient(135deg, rgba(23,212,250,.10), rgba(242,47,137,.10)),
    var(--bg-1);
}
.mini-aurora {
  background:
    radial-gradient(70% 90% at 25% 20%, rgba(23,212,250,.35), transparent 60%),
    radial-gradient(70% 90% at 78% 80%, rgba(242,47,137,.30), transparent 60%),
    var(--ink-950);
}
.mini-hex {
  background-color: var(--bg-1);
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='56' height='97'><path d='M28 0 56 16.17v32.33L28 64.67 0 48.5V16.17zM28 64.67 56 80.83v16.17M28 64.67 0 80.83v16.17' fill='none' stroke='%2317d4fa' stroke-opacity='.14'/></svg>");
}
@media (max-width: 800px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<main class="wrap">
  <p class="eyebrow">Treatment exploration · 2026-07-07 · tokens locked, treatments open</p>
  <h1>Six directions</h1>
  <p class="lede">Same tokens, same specimens, six treatments. Open each sheet, judge keep / kill / remix. Winners get an iteration round, then promotion into the design skill.</p>
  <div class="grid">
    <a class="dir" href="circuit-bloom.html">
      <div class="mini mini-circuit"></div>
      <div class="meta"><p class="num">Direction 1</p><h2>Circuit Bloom</h2><p>Traces promoted from whisper to composition.</p></div>
    </a>
    <a class="dir" href="blueprint.html">
      <div class="mini mini-blueprint"></div>
      <div class="meta"><p class="num">Direction 2</p><h2>Blueprint</h2><p>The brand as an engineering drawing.</p></div>
    </a>
    <a class="dir" href="phosphor-terminal.html">
      <div class="mini mini-phosphor"></div>
      <div class="meta"><p class="num">Direction 3</p><h2>Phosphor Terminal</h2><p>Late-night studio monitors, made literal.</p></div>
    </a>
    <a class="dir" href="signal-noise.html">
      <div class="mini mini-noise"></div>
      <div class="meta"><p class="num">Direction 4</p><h2>Signal Noise</h2><p>Analog texture on the digital duo.</p></div>
    </a>
    <a class="dir" href="aurora-depth.html">
      <div class="mini mini-aurora"></div>
      <div class="meta"><p class="num">Direction 5</p><h2>Aurora Depth</h2><p>Elevation by light, not shadow.</p></div>
    </a>
    <a class="dir" href="hex-lattice.html">
      <div class="mini mini-hex"></div>
      <div class="meta"><p class="num">Direction 6</p><h2>Hex Lattice</h2><p>The logo's hexagon as structure.</p></div>
    </a>
  </div>
</main>
</body>
</html>
```

- [ ] **Step 2: Full-set token gate**

Run: `python Design/explorations/2026-07-07-treatments/check-tokens.py`
Expected: exit 0, `OK — 8 files clean against colors_and_type.css`

- [ ] **Step 3: Scope check — nothing outside the exploration dir**

Run: `git status --porcelain`
Expected: only lines under `Design/explorations/2026-07-07-treatments/` (pre-existing untracked strays from other work — `assets/social/`, `docs/announcements/`, etc. — are fine; nothing site-owned may show as modified).

- [ ] **Step 4: Visual check**

Open `index.html` at 1440px and 768px: six cards, each mini swatch visibly distinct and evocative of its sheet, all six links resolve, no horizontal scroll.

- [ ] **Step 5: Commit**

```bash
git add Design/explorations/2026-07-07-treatments/index.html
git commit -m "feat(design-exploration): index page — six directions, side-by-side entry point"
```

---

### Task 9: Handoff for judging

**Files:** none (process step).

- [ ] **Step 1: Full verification sweep**

Run: `python Design/explorations/2026-07-07-treatments/check-tokens.py`
Expected: exit 0, `OK — 8 files clean against colors_and_type.css`

Then screenshot all seven pages (index + six sheets) at 1440px via browser/Playwright, confirming each renders its treatment (not an unstyled skeleton — a sheet whose treatment failed to apply looks identical to `_skeleton.html`; that is a bug).

- [ ] **Step 2: Present to Este**

Open `Design/explorations/2026-07-07-treatments/index.html` in his browser and hand off with the judging frame: mark each direction **keep / kill / remix** with a short note. Round 2 (variant cuts on survivors) and the promotion pass are planned separately after verdicts land — do NOT proceed into skill/token changes from this plan.
