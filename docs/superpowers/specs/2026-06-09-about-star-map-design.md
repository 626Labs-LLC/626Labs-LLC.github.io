# About Star Map — design spec

- **Date:** 2026-06-09
- **Status:** Approved (design); pending implementation plan
- **Repo:** 626Labs-LLC/626Labs-LLC.github.io (626labs-hub)
- **Author:** The Architect + Este

## Purpose

The About section's plugin list was always meant to grow into a constellation
as the family expands. This spec makes that literal: a star map panel inside
the About section where every live Vibe plugin is a star, the flagship burns
magenta, and the product family glows in the background. Stars derive from
the same source as `{{fact:live_plugin_names}}` — ship a plugin, the
constellation grows on the next render. No manual step, ever.

Reference DNA: the 626 Labs dashboard's Universe view (canvas draw loop,
glow treatment, log-scale node sizing) and Celestia 3's natal compass
(staggered line-reveal) and onboarding fly-through (kept out of scope, in
the back pocket).

## Locked decisions

| Question | Decision |
|---|---|
| What the map shows | **Hybrid** — live plugins form the named constellation (the focus); a curated set of products are brighter background stars; ~50 dust stars fill the field |
| Placement | **Framed panel** — full-width band inside `#about`, between the manifesto two-column text and the principles grid |
| Motion | **Draw-on reveal** on first scroll-into-view (stars pop staggered, lines draw themselves), settling into an ambient sky (twinkle, slow field drift, line pulse) |
| Interactivity | **Hover labels** — nearest-star hit test pins an HTML tooltip with name + version; touch = tap-for-label; no navigation |
| Architecture | **Canvas 2D + curated spine** — one canvas, vanilla JS in the static shell, deterministic procedural layout along a hand-designed spine curve |

## Panel anatomy

`render_about()` (scripts/render-hub.py) emits, between the existing
`.manifesto-inner` wrap and the `.principles` wrap:

```html
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
  <script type="application/json" id="starmap-data">{ ...see Data contract... }</script>
</div>
```

- Panel: hairline border `rgba(23,212,250,0.18)`, radius matching existing
  cards, navy radial field (`#14283f → #0f1f31`), ~340px tall desktop,
  ~240px mobile.
- Caption row: small UPPERCASE meta style (JetBrains Mono, +0.12em tracking)
  matching existing eyebrow/meta conventions. Legend dots colored cyan /
  magenta / bright-white.
- Canvas is decorative (`aria-hidden`): the paragraph directly above already
  names every live plugin via `{{fact:live_plugin_names}}`, so assistive
  tech loses nothing. No-JS visitors see the framed navy field + caption —
  acceptable; the prose carries the content.

## Data contract

### site.json (new optional block under `about`)

```json
"starMap": {
  "products": ["Celestia 3", "RORORO", "We See You at the Movies"]
}
```

- The flagship (magenta `#f22f89` star) derives from the existing
  `"flagship": true` field on the product entry in `site.json` —
  vibe-cartographer already carries it. Falls back to the first live plugin
  if no product is flagged. No duplicate config.
- `products` — curated display names for background stars (3–5 recommended).
  Editable later via admin (out of scope now).
- Presence of the `starMap` block is the feature toggle: omit it and
  `render_about()` emits no panel (clean rollback path).

### Emitted blob (`#starmap-data`)

```json
{
  "plugins": [
    {"id": "vibe-cartographer", "name": "Vibe Cartographer", "flagship": true},
    {"id": "vibe-doc", "name": "Vibe Doc", "flagship": false}
  ],
  "products": [{"name": "Celestia 3"}, {"name": "RORORO"}]
}
```

- `plugins` ordered as they appear in `site.json` (launch order) — this
  order is load-bearing: it assigns spine slots, so it must stay stable.
- Plugin set derives from the same live-plugin selection `site_facts.py`
  uses for `live_plugin_names` (`is_claude_plugin(p) and status == "live"`;
  single source of truth — the blob and the prose can never disagree).
- **Versions are not baked into the blob.** `refresh-plugin-versions.yml`
  re-renders plugin subpages only, never the root `index.html` — baking
  versions would make the daily version bump fail `render-hub.py --check`
  until a manual re-render. Instead the star map JS fetches
  `data/plugin-versions.json` once at runtime (same-origin, ~200 bytes) and
  joins versions into tooltips as progressive enhancement.
- No timestamps, no randomness — the blob must be byte-stable so
  `render-hub.py --check` stays idempotent.

## Layout: the curated spine

- A hand-designed spine curve (polyline / bezier control points in
  normalized 0–1 coords, tuned during implementation) crosses the panel —
  a gentle wave that reads designed, not scattered.
- **Slots:** N positions sampled arc-length-evenly along the curve for N
  plugins (formula-based, so growth past any count just extends sampling).
- **Assignment:** plugin i takes slot i (launch order).
- **Jitter:** each star offsets from its slot by a deterministic hash of its
  id (FNV-1a → two floats, ±3% of panel size). Organic, but identical for
  every visitor and every build.
- **Edges:** chain along the spine (slot i → i+1) plus up to two hash-picked
  cross-links for character. Deterministic.
- **Products:** fixed normalized anchor positions in the outer field
  (corners/edges, away from the spine), hash-jittered per name.
- **Dust:** ~50 faint stars from a seeded PRNG (mulberry32, fixed seed) —
  same sky for everyone. It is a map, not a screensaver.

## Motion

### Reveal (once per page load)

Trigger: IntersectionObserver at ~35% panel visibility.

| Phase | Timing | Easing |
|---|---|---|
| Dust + products fade in | 0–700ms | ease-out cubic |
| Plugin stars pop | from 400ms, ~160ms stagger, 380ms each | easeOutBack (overshoot) |
| Constellation lines draw | from ~1900ms, ~200ms stagger, 450ms each | ease-out cubic |
| Settle into ambient | after last line | — |

### Ambient (steady state)

- Per-star twinkle: alpha oscillation on independent phase/speed.
- Field drift: whole sky translates ±6px on slow sinusoids (~20s period).
- Line pulse: constellation edge opacity breathes 0.28–0.36.
- Glow via canvas `shadowBlur` (10px stars, 8px products) — the cheap trick
  the dashboard's SVG filters made expensive.

### Reduced motion / lifecycle

- `prefers-reduced-motion: reduce` → skip the timeline, render the settled
  sky, no drift; twinkle disabled (static alphas).
- The RAF loop runs only while the panel intersects the viewport
  (IntersectionObserver toggles it) — zero cost while reading the page.
- DPR capped at 2.

## Interaction

- `pointermove`: nearest-star hit test within 14px (plugins and products).
  Hit → HTML tooltip (`.starmap-tooltip`) pinned next to the star (not the
  cursor): mono uppercase, `NAME · vX.Y.Z` (version chip omitted when
  unknown — the version map comes from the runtime fetch above, so a failed
  fetch degrades to name-only tooltips). Cursor stays `default`; no
  clickability implied.
- Touch: tap = same hit test + show; tap on empty sky = dismiss.
- No click navigation (locked decision — the map is not a menu).

## Code placement + pipeline invariants

| Piece | Where | Why |
|---|---|---|
| Panel markup + JSON blob | `render_about()` in `scripts/render-hub.py` | Inside the `about` zone, rebuilt from site.json |
| `.starmap*` CSS | Static `<style>` in `index.html`, outside `SITE_JSON:` zones | Renderer never touches it |
| Star map JS (~250 lines, vanilla) | Static `<script>` in `index.html`, outside zones | Same |
| Config | `content/site.json` `about.starMap` | Single editorial source of truth |

Invariants:

- JS no-ops cleanly when `#starmap-data` is missing or `about` is disabled.
- Rendering stays deterministic end-to-end: `python3 scripts/render-hub.py
  --check` must remain byte-stable; `site-doctor --check` must pass
  unchanged. No new derived facts (the blob reuses existing derivations).
- `rebuild-hub.yml` needs zero changes — a plugin going live in `site.json`
  re-renders the blob exactly like it re-renders the prose token.
- Implementation must run `gitnexus_impact` on `render_about` before
  editing (repo rule) — expected blast radius is the about zone only.

## Performance budget

- One canvas, one RAF loop, paused off-viewport. Target <2ms/frame
  mid-range laptop at DPR 2 (the brainstorm demos ran three simultaneous
  richer scenes without strain).
- No libraries. No build step. Page weight delta: ~6–8KB minified-ish
  inline JS + CSS.

## Out of scope (deliberate)

- Click-to-navigate stars.
- Admin UI for editing `starMap` config (hand-edit site.json for now).
- The fly-through arrival (demo C) — strong candidate for a future product
  page hero, not the About section.
- Naming the constellation in copy (caption says THE PLUGIN CONSTELLATION;
  a lore name can come later without code changes).

## Verification plan

1. `python3 scripts/render-hub.py` then `--check` → byte-stable.
2. `python3 scripts/site-doctor.py --check` → passes.
3. Local serve: reveal fires once at ~35% visibility; ambient settles;
   hover labels correct (name + version vs name-only); touch tap works.
4. DevTools `prefers-reduced-motion` emulation → static settled sky.
5. Widths 360 / 768 / 1440 → panel height + caption legible, no overflow.
6. Temporarily add a fake plugin to `site.json` locally → star count grows,
   spine extends, layout stays sane; revert.
7. JS disabled → framed field + caption render, no errors.

## References

- Brainstorm artifacts (placement wireframes, three live motion demos):
  `.superpowers/brainstorm/1218-1781028912/content/` (local-only, gitignored).
- Dashboard Universe view: `Project-626Labs-1/features/Universe/` —
  canvas draw loop, glow, force-layout tunings (we use none of d3, but the
  visual treatment lineage is theirs).
- Celestia 3: `Celestia3/src/components/NatalCompass.tsx` (staggered line
  reveal), `src/components/onboarding/CelestialScene.tsx` (fly-through —
  out of scope, archived for later).
