# Brand treatment exploration — design spec

**Date:** 2026-07-07
**Status:** Approved design, pre-implementation
**Project:** 626 Labs — Portfolio Hub (dashboard ID `qNCk86nujUfrHEbRU2jy`)

## Purpose

The 626 Labs visual system is dark-neon done with a small set of moves: cyan/magenta glow, gradient hairlines, capsules, navy field. The vocabulary is thin — the same treatments carry every surface. This exploration widens it: six named treatment directions, rendered as directly comparable specimen sheets, judged by Este, with survivors promoted into the canonical design skill as reusable patterns.

Drivers: pure play plus a deliberate deepening of the vocabulary. This is exploration, not a rebrand.

## Constraints

- **Tokens locked.** Every color derives from existing `colors_and_type.css` tokens. Alpha variants and blends of existing tokens are allowed; new hex values are not.
- **Type stack untouched.** Space Grotesk display, Inter body, JetBrains Mono code/meta.
- **The logo and the cyan/magenta pairing are sacred** (already implied by tokens-locked, stated for the record).
- **Zero dependencies.** Static HTML with inline CSS. No frameworks, no CDN fetches beyond the Google Fonts imports the token file already uses.
- **Nothing ships.** Artifacts live outside the site render pipeline and are never referenced by `index.html` or `content/site.json`.

## The six directions

Each direction is one answer to "what else can these tokens do":

| Direction | Thesis |
|---|---|
| **Circuit Bloom** | The 6%-opacity circuit-trace whisper promoted to a compositional element: traces routing around cards, junction nodes as accents, density gradients toward focal points. |
| **Blueprint** | Schematic linework: hairline grids, dimension ticks, mono annotation labels, exploded-diagram framing. The brand as an engineering drawing. |
| **Phosphor Terminal** | CRT depth: scanlines, glow bloom, phosphor-persistence hover states, terminal chrome framing. "Late-night studio monitors" made literal. |
| **Signal Noise** | Grain and dither: film-grain navy fields, dithered gradients, halftone accents. Analog texture on the digital duo. |
| **Aurora Depth** | Atmosphere as elevation: layered duotone glows as spatial light, cards floating in a lit field instead of a shadowed one. |
| **Hex Lattice** | The logo's hexagon as structure: hex grids, clipped card corners, honeycomb empty states, hex-node data accents. |

## Specimen sheet — fixed contents

Identical per direction so comparison is apples-to-apples:

1. Direction name + one-line thesis (page header)
2. Hero block
3. 3-card grid
4. Button row — primary / secondary / ghost, with hover states rendered side-by-side as static swatches (not just `:hover`)
5. Chips / badges
6. Code block
7. Stat tile / data panel
8. One full-bleed texture swatch

Plus one `index.html` linking all six sheets for side-by-side browsing.

## File layout

```
Design/explorations/2026-07-07-treatments/
├── index.html            ← links + thumbnails for all six
├── circuit-bloom.html
├── blueprint.html
├── phosphor-terminal.html
├── signal-noise.html
├── aurora-depth.html
└── hex-lattice.html
```

`Design/` is the repo keystone's designated home for one-off design artifacts. Not under `assets/` (some of which is generated/CI-owned), not near the render pipeline.

## Process

1. **Build round 1:** all six specimen sheets + index.
2. **Judge:** Este marks each direction **keep / kill / remix**, with a short note per verdict.
3. **Round 2:** the 1–2 survivors each get 2–3 variants cut from the remix notes. Same specimen format.
4. **Converge:** Este picks final treatments.
5. **Promote** (separate implementation phase, own plan):
   - New token groups in `colors_and_type.css` (e.g. `--texture-*`, `--motif-*`) expressing the surviving treatments.
   - A "Treatments" section in the skill docs describing when and how to use each.
   - One `preview/` spec card per promoted treatment.

## Promotion — canonical-location gate

The design skill was loaded this session from a plugin cache (`~/.claude-personal/plugins/cache/626labs/...`), which may not be the writable source. **The first step of the promotion phase is resolving the canonical skill location** — the estate map says `~/.claude/skills/626labs-design/`, and config-as-code requires mirroring any global-config change into `dotclaude\`. Verify which copies exist, which is source of truth, and whether the 626labs plugin repo is in the chain, before writing a single token. No promotion writes until that's resolved.

## Quality bar

- Visual QA in the browser is the test suite; the failure mode "a direction looks bad" is the exercise working as intended.
- Token discipline is checkable: every `#` literal in a sheet must appear in `colors_and_type.css` (or be an rgba()/color-mix() of a token value).
- Sheets must render acceptably at 1440px and 768px widths; no horizontal scroll at either.

## Out of scope

- Any change to the live site, `content/site.json`, or rendered pages.
- Editorial (light-paper) layer — dark-mode UI treatments only this round.
- New iconography, logo variations, or type exploration.
- Motion beyond simple CSS hover transitions already permitted by the brand (no new animation language this round).
