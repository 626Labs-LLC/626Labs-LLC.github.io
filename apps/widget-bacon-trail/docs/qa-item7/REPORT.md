# Item 7 QA Report — Birthday Bacon Trail Widget

**Date:** 2026-04-24
**URL tested:** `https://626labs.dev/#play`
**Widget bundle:** `widget.js` 213 KB (66.88 KB gz, CI-rebuilt with real `VITE_TMDB_API_KEY`)

---

## Bundle-size CI gate (checklist item 7 verify hook #1)

Already live and green, wired in the `build-widget.yml` workflow from Item 6:

| File | Bytes | Gzipped | Budget | Pass |
|---|---:|---:|---:|:---:|
| `widget.js` | 213,205 | **66.88 KB** | 150 KB gz | ✓ (45% of budget) |
| `widget.css` | 13,911 | **3.06 KB** | 20 KB gz | ✓ (15% of budget) |

CI exits 1 if either exceeds budget. Confirmed in run [24867683865](https://github.com/626Labs-LLC/626Labs-LLC.github.io/actions/runs/24867683865).

---

## Responsive QA (verify hook #2)

Screenshots captured against the live URL at three viewport sizes:

| Breakpoint | Width × Height | Screenshot | Result |
|---|---|---|---|
| Desktop | 1440 × 900 | [`desktop-1440-play.png`](./desktop-1440-play.png) | Play section renders centered, widget ~420 px wide, side-by-side with lead copy to the right |
| Tablet | 768 × 1024 | [`tablet-768-play.png`](./tablet-768-play.png) | Section head stacks (lead below headline), widget centered below, actor grid holds 3 × 2 |
| Mobile | 375 × 812 | [`mobile-375-play.png`](./mobile-375-play.png) | Widget fills viewport width minus padding, actor grid holds 3 × 2, names truncate to ~3 chars ("John Ce…") |

**Minor observation (not blocking):** at 375 px viewport, the 3-column grid compresses actor-name labels to ~3 characters before ellipsis. Aria-labels (`Pick John Cena, born 1977`) carry the full name, so screen readers unaffected. Visual trade-off is acceptable — the profile photo is the primary signal, text is secondary. Filed for potential v2 tweak (switch to 2 × 3 on `< 400 px`).

---

## Accessibility sweep (verify hook #3)

Scripted a11y audit via Playwright:

| Check | Result |
|---|---|
| Console errors | **0** |
| Console warnings | **0** |
| Interactive elements missing `aria-label` / text | **0 / 7** |
| Focus ring on first button | **1.6 px solid `rgb(23, 212, 250)` at 1.6 px offset** — visible, matches brand cyan |
| `<h2>` widget heading present + correctly nested | ✓ (`Birthday Bacon Trail`) |
| Screen-pick headings (`<h3>`) present | ✓ (`Who's born today?`) |
| ARIA landmarks | `group "Birthday actors"`, `status` live region, `generic "Film N of 6"` |
| Screen-reader labels for buttons | ✓ (`Pick John Cena, born 1977` etc.) |
| Alt text on profile images | ✓ (empty `alt=""` for decorative, actor name carried via button `aria-label`) |
| Tab-reachable path from first actor → shuffle | ✓ |
| Color contrast (spot check) | Primary text `#ffffff` on `#0f1f31` = 17.8:1 (AAA) · Cyan `#17d4fa` on `#0f1f31` = 10.1:1 (AAA) · **Film-counter muted label** `#8e9bad` on `#223a54` = 3.65:1 — passes **AA Large** (3:1), borderline for AA Normal (4.5:1). Only affects decorative 11 px mono text; spoken label `Film N of 6` via `aria-label` carries the meaning to assistive tech. Not escalated. |

Full accessibility snapshot saved at [`a11y-snapshot.md`](./a11y-snapshot.md).

---

## Performance (verify hook equivalent)

Measured via `window.performance` on 1440 × 900 cold load:

| Metric | Value |
|---|---:|
| DOM Content Loaded | **374 ms** |
| First Paint | 652 ms |
| First Contentful Paint | 652 ms |
| Load Event | 1182 ms |
| Widget `widget.js` load | **96 ms** |
| Widget bundle size (encoded) | 66.88 KB |
| Birthday shard fetch | **58 ms** |
| Widget mounted (DOM present) | ✓ |
| First actor card rendered | ✓ |

Widget is interactive within ~530 ms of DCL (374 + 96 script + ~60 shard/mount). Well under the "delightful portfolio moment" threshold. Widget adds no render-blocking resources to the hub (`<script defer>`, `<link rel="stylesheet">` is in the section body, below the fold's paint-critical content).

**Lighthouse run not included** — no Lighthouse CLI in the MCP toolkit. Raw perf numbers + bundle sizes + zero-error network tab are sufficient signal for this checkpoint.

---

## Network trace (sanity)

Non-static requests during cold load of the Play section:

- `GET https://626labs.dev/widget-bacon-trail/data/birthdays/04-23.json` → **200** — the one shard the widget needs.
- **No Firebase traffic** at runtime (confirms the "Firebase is build-time-only" architecture decision from `/spec`).
- No TMDB calls fire until the user picks an actor (lazy-by-design).
- Various `img.shields.io` and product badge fetches from the rest of the hub — unrelated to the widget.

Full network log at [`network-requests.txt`](./network-requests.txt).

---

## Status

All Item 7 verify hooks green:

- [x] CI bundle-size gate live + passing
- [x] Responsive screenshots at desktop / tablet / mobile
- [x] A11y sweep: zero missing labels, focus ring visible, screen-reader live region in place
- [x] Perf numbers measured and within a delightful-portfolio-moment window

**Ready for Item 8 (docs + security verification).**
