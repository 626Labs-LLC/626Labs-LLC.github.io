# Utility dress gate + a committed visual harness — approved design

**Date:** 2026-08-04
**Status:** Approved design, pre-implementation
**Depends on:** PR #96 (`feat/bespoke-conformance`), which must merge first or this work retargets.

## Why

Two loose ends from M2a.5, both raised by review and both deliberately left open there.

**press.html and privacy.html borrow their dress from the theme and state nothing of their own about it.** Unlike the six pages M2a.5 converted, they were never given a token file — they link `themes/<active>/archetypes/utility.css` and take their entire chrome from it. A second theme's `utility.css` that drops a rule silently changes or breaks them, and every existing gate stays green.

**Every verification harness built during M2a.5 lived in a scratchpad and is gone.** Three of that milestone's four most serious findings were caught only by those harnesses: a hover rule that no resting-state gate can see, an `@import` reorder that killed the type stack on 15 pages while `--check` stayed green, and a dress rule silently leaving a page. Nothing in the repo can re-run any of it.

## What the two pages actually borrow

Measured, not guessed. An earlier static pass concluded the borrowing was "narrower than everything" because both pages carry their own `<style>` (52 and 21 selectors). Measured against the live DOM during implementation, that was wrong: **49 of `utility.css`'s 50 selectors reach `press.html` and 48 reach `privacy.html`, and the pages' own styles redeclare ZERO of them.** The overlap is nil. The pages dress their own content; the theme dresses everything else. The chrome is 100 percent borrowed.

The load-bearing subset, identical across both pages:

| Selector | Properties taken from the theme |
|---|---|
| `*` | `box-sizing` |
| `html, body` | `margin`, `padding` |
| `body` | `background`, `color`, `font-family`, `font-size`, `line-height`, `overflow-x`, `-webkit-font-smoothing` |
| `a` | `color`, `text-decoration` |
| `a.inline-link` (+ `:hover`) | `color`, `border-bottom`, `transition` |
| `h1, h2, h3, h4` | `font-family`, `letter-spacing` |
| `nav.nav` | `position`, `top`, `z-index`, `background`, `border-bottom`, `backdrop-filter` |
| `header.page-hero` | `position`, `padding`, `border-bottom`, `overflow` |
| `h1.page-title` (+ `.accent`) | `color`, `font-size`, `font-weight`, `letter-spacing`, `line-height`, `margin`, gradient clip |
| `footer` | `background`, `border-top`, `padding` |
| `h1` | `text-shadow` |

Plus `utility.css`'s own `@import url('/fonts/fonts.css')` — the only source of the brand type stack on either page. All six pages M2a.5 converted self-import fonts; these two do not.

## The decision: they keep wearing it

Este's ruling (2026-08-04): press and privacy stay fully theme-dressed, so a new month actually restyles them. Freezing their chrome page-side would close the exposure by removing the dependency, but it would also make them the two pages a September theme cannot reach — which fights the stated goal that every page changes and rewards a second visit.

**So the exposure closes by verification, not by removal.** The dependency stays; the gate learns to check it.

## The gates

**1. Render them.** Add `press.html` and `privacy.html` to `BROWSER_CHECK_LIVE_PAGES`. They are already previewable and already isolated from off-origin hosts. This alone buys horizontal-scroll, console-error, and `pageerror` coverage at 1440/768/390 — none of which they have today.

**2. Gate on computed outcome, not on a selector manifest.** The obvious move is a required-rules list mirroring `REQUIRED_TOKENS`. Reject it: a selector-shaped contract is brittle (a theme setting the field on `html` instead of `body` would fail while rendering correctly) and it is exactly the junk drawer the token contract has been disciplined about avoiding. Instead, assert the *outcome* in the browser gate that step 1 is already adding: on both pages, `body` resolves a non-transparent background and a brand font stack rather than the browser default, the nav resolves a background and a stacking context, the page title resolves a non-default size and weight, the footer resolves a background, and links resolve a color distinguishable from body text. Theme-agnostic, un-gameable by a rule that does not apply, and it constrains what must be *true*, never what values it must be.

**3. Remove the font-import fragility.** `press.html` and `privacy.html` self-import `/fonts/fonts.css`, matching all six pages M2a.5 converted. `fonts.css` is a repo-global asset, not a theme asset, so depending on the theme to pull it in was always the wrong seam. Zero-pixel; the import is idempotent.

**4. Scope the reads-check per resolution group.** PR #96 follow-up 1: `check_theme_reads_only_what_it_defines` pools definitions theme-wide, but no consumer loads every theme stylesheet. Three groups actually ship — `{utility.css}` alone for these two pages, `{product.css + product-tokens.css}` for the 15 generated pages, and `{reading.css}` plus `Design/editorial.css` for about — with `{reading-tokens.css}` a separate, stricter group serving `thesis.html` and `workflow.html`. (An earlier draft of this spec paired about with `reading-tokens.css`; the code disagreed and the code was right — about's picker points at `archetypes/reading.css` only.) A name defined in `tokens.css` currently satisfies the check for a consumer that never loads it, which is precisely the utility case. Scope per group, and scope `EXTERNAL_STYLESHEETS` to the group that loads it.

**5. Test all of it.** PR #96 follow-up 2: the reads-check, `EXTERNAL_STYLESHEETS`, and the unresolved-contrast-pairs error have zero coverage today. Every gate added here ships with a test verified to fail against the un-gated implementation.

## The committed harness

`scripts/visual-diff.py` — the M2a.5 harnesses, consolidated and made re-runnable.

- **Two-tree, never golden-image.** Compares a base ref against the working tree by serving both. Committed reference images are unusable here: a pinned Pillow is byte-stable on one OS but FreeType rasterizes differently across platforms, so goldens built on ubuntu diff forever on Windows.
- **Three channels:** full-frame pixel (filters on, no masking, SMIL frozen via the shipped `freeze-theme.py` init script), computed-style, and hover.
- **The hover-subject derivation must union the linked stylesheets' `:hover` rules, not only the page's own.** As written in M2a.5 it derives subjects from the page's own rules, which false-passes on exactly the pages that need it most — press and privacy, which own none of their hover rules. This is a blocker, not a polish item.
- **Runs on `workflow_dispatch` and an opt-in PR label.** Never on every push: a full sweep is 12+ minutes. Never inside `rotate-theme.yml`: on the 1st every pixel is *supposed* to move, so a pixel gate there is meaningless.
- **Documented non-coverage,** so nobody reads a pass as more than it is: `:focus-visible`, `:active`, `::selection`, print and forced-colors stylesheets are unsampled, and no two-tree diff can distinguish an intended redesign from an accident.

## Success criteria

- A theme whose `utility.css` drops any load-bearing rule fails `theme-doctor` rather than shipping. Proven by building such a theme and watching the gate fail, the way M2a.5 proved its token-contract gap.
- press.html and privacy.html render 0-pixel identical to today under Phosphor Blueprint.
- `check_theme_reads_only_what_it_defines` catches a name deleted from `utility.css` alone. Today it does not; the deletion is reproducible in three places.
- `scripts/visual-diff.py` reproduces M2a.5's results from a clean checkout, and its hover channel fails on press/privacy when a linked stylesheet's hover rule changes.
- All existing gates stay green.

## Out of scope

- Splitting `utility.css`. Explicitly rejected above.
- Redesigning press or privacy.
- September's theme (M2b).
- The remaining PR #96 follow-ups: the silent `$( )` command substitution, `"contrastPairs": []` still exiting 0, the nav-wrap one-liner on the other five pages, and two stale comments. Cheap, unrelated, and better batched separately.

## Risks named

- **The outcome assertions could over-constrain a theme author.** A theme that deliberately wants an unstyled `body` background cannot have one. That is the correct trade for a page nobody looks at until it is broken, but the assertions must stay few and load-bearing — this is the same discipline `REQUIRED_TOKENS` needed, applied to a new surface.
- **A committed harness that nobody runs is worse than none**, because it reads as coverage. The PR label and the documented non-coverage list exist to keep its claim honest.
- **The hover derivation is the harness's one hard blocker.** Shipping it with the M2a.5 derivation would hand the next person a tool that reports false passes on the exact pages this spec is about.

## Inputs needed

None. Every decision is recorded above.
