# Build story: the Fable window — the constellation

> Source notes for the "3 days with Fable" article. Grounded in real sessions and the 626labs-hub commit log. Window: 2026-06-09 to 2026-06-12.
>
> **By the numbers (626labs-hub):** 2 Fable sessions, 1.3M tokens — the smallest and most self-contained build of the window. One marquee design feature, start to finish, in an afternoon.

## The frame

The About page on 626labs.dev needed a centerpiece. Not a chart, not a hero image — something that *is* the portfolio. The answer: a star map. The plugins form a constellation (the flagship a magenta star), the curated products sit behind them as brighter background stars, the whole thing draws itself on, then settles into an ambient twinkle.

## The decision that made it cheap to keep

The interesting call here wasn't visual, it was architectural. Three ways to build a constellation:

1. **SVG / CSS animation** with glow filters on every node.
2. **Hand-authored constellation art.**
3. **Canvas 2D with a curated-spine procedural layout.**

Chose 3, and the reasons are the story. SVG glow filters across dozens of continuously-animating nodes is the known-expensive path — the dashboard's Universe view hit exactly that wall and grew a canvas renderer to escape it. Hand-authored art reintroduces the **manual-drift problem** the hub's whole fact-token pipeline exists to kill: every new plugin would mean hand-editing the art.

Canvas with a deterministic, hash-jittered spine gets designed-looking layout *and* automatic growth. The stars derive from the same live-plugin source as the `{{fact:...}}` tokens. So shipping a new plugin grows the constellation with **zero manual steps** — the map updates itself.

## The build

A clean afternoon arc on 6/09, every beat in the commit log:

- `docs(specs): about star map design spec` + implementation plan with amendments.
- `feat(about): emit star map panel + data blob from render_about` — the renderer produces both the panel and its data.
- `fix(render): starMap toggle reads only a dict as enabled` — the feature flag is structural, not truthy.
- `feat(about): star map panel styles`, then the centerpiece: `feat(about): star map canvas — spine layout, reveal, ambient, tooltips`.
- Review follow-ups landed same-day: touch-device tooltips, IntersectionObserver hardening, legend wrapping on narrow panels.
- `docs: star map surface in repo guide` — documented so the next agent inherits it.

Motion was validated live against three options via brainstorm-companion demos before a line of canvas was written; hover labels only, no navigation, so it reads as a sky and not a menu.

## What the window left

A self-growing constellation on the About page, built canvas-2D in one session, that costs nothing to maintain because it reads from the same source of truth as the rest of the site. The smallest Fable build of the three days, and the one that will quietly keep updating itself every time a new star ships.
