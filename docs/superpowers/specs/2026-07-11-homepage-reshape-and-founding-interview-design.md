# Homepage reshape + founding interview — approved design

**Date:** 2026-07-11
**Status:** Approved design (sub-projects A + B), pre-implementation
**Scope:** Rebalance 626labs.dev away from plugin-weight and toward the company story: collapse 14 plugin cards to one family card, move the plugin thesis onto /plugins/, and run the founding interview that will source the About The Lab flagship (sub-project C, specced separately once the transcript exists).

## Context

The homepage products grid carries 23 cards, 14 of them Vibe plugins — the site
reads as a plugin catalog with a company attached. Este's directive (2026-07-11):
one plugin card on the main page, the thesis demoted off the homepage crown, and
a new headline piece about 626 Labs itself — an About "better than any other
founder's website," styled like "a legacy website from a company that's been
around for a thousand years, but in the year 3026."

A family page already exists: `/plugins/` (rendered by
`scripts/render-plugin-pages.py` from `content/plugin-pages.json`, alongside the
14 per-plugin pages). Este: "the plugin page is already pretty good, but we can
touch it up for more individual context. The thesis can be on the plugin page."

## Decisions (brainstormed 2026-07-11)

1. **Demotion target:** homepage section 02 ("The thinking behind it" — the
   Self-Evolving Plugin Framework essay). The founding story will take the
   editorial crown (sub-project C).
2. **About shape:** small summarizing section at the bottom of the main page +
   a full **About The Lab** piece as its own surface.
3. **Interview mode:** guide first, then live — I draft the question arc, Este
   reviews, we run it live one question at a time; verbatim transcript captured.
4. **Design path for the legacy treatment:** mini bake-off — 3 specimen sheets
   of distinct "millennium institution, 3026" directions, judged on identical
   sample content (the PB exploration pattern, scoped down).
5. **Plugin collapse destination:** the existing `/plugins/` page. No new page.

## Sub-project A — The consolidation (site work, ships first)

### Grid collapse

- The 14 plugin entries (`vibe-cartographer`, `vibe-iterate`, `vibe-insights`,
  `vibe-keystone`, `vibe-doc`, `vibe-test`, `vibe-thesis`, `thesis-engine`,
  `vibe-sec`, `vibe-taker`, `vibe-wrap`, `vibe-walk`, `vibe-prompt`,
  `vibe-lingual`) stop rendering as individual grid cards. One **Vibe Plugin
  Family** card replaces them; grid goes 23 → 10.
- **Presentation-level collapse.** `products[]` stays intact — site facts
  (`{{fact:claude_plugins}}` etc.), doctor prose pins, the About star-map
  derivation, and the 14 per-plugin pages keep working untouched. The collapse
  is a render-hub grouping rule configured in site.json (e.g. a `familyCard`
  object naming the folded ids + the card's own copy/tags/sigil), so curation
  stays data, not code.
- The family card links to `/plugins/` via the product-foot mechanism
  (`productPage` + `productPageLabel`), gets its own PRODUCT_SIGILS entry, and
  family-level tags. Card copy is count-free in prose; any count shown derives
  from facts at render time, never hand-baked.

### The thesis moves home

- Section 02's content (site.json `thinking` key: eyebrow, headline, lead,
  quote, paragraphs, cta, artifacts) migrates into `content/plugin-pages.json`
  and renders on `/plugins/` as the page's editorial spine — the framework
  essay sits above/alongside the family it describes.
- Homepage section 02 toggles off via the existing `sections` mechanism
  (`sections.thinking.enabled: false`); the `thinking` key is removed from
  site.json once migrated (render main() already guards with
  `if "thinking" in content`). The freed slot stays clean until sub-project C
  places the founding story.

### The touch-up — more individual context on /plugins/

- Each plugin's entry on `/plugins/` grows a short story beat: why it exists
  and what it pairs with in the family — two lines max per plugin, sourced from
  existing per-plugin page copy (no invented claims). Exact layout decided
  against the current page structure at plan time; the page's existing look is
  "already pretty good" (Este) — touch up, don't redesign.

### Guardrails

- BOTH renderers re-run and commit their outputs: `scripts/render-hub.py`
  (index.html) and `scripts/render-plugin-pages.py` (/plugins/ + per-plugin
  pages). The two-renderer gotcha is documented estate knowledge; render-hub
  `--check` alone is not sufficient — gate on `site-doctor.py --check` exit 0.
- pytest suite; site-doctor `--report` for human-readable verification.
- Playwright pass: 10-card grid renders sanely at desktop + mobile, family
  card foot links `/plugins/`, thesis renders on /plugins/, homepage no longer
  shows section 02, no dangling anchors to `#thinking` (nav links checked).
- Ship = branch + PR + doctor CI. No new public URLs expected (no indexing
  list needed); if any URL is added anyway, the ship report ends with it.

## Sub-project B — The founding interview (publishing suite)

- New work: `626Labs-Publishing/works/2026-07-11-founding-interview/`,
  scaffolded from `studios/BlogStudio` per the umbrella convention. BlogStudio's
  Field Notes persona re-bootstrapped for a reflective founder-profile register
  (less code-snippet, more narrative; same Runnable Truth / Earned Hook /
  Recognizable Voice pillars).
- **Guide:** `interview/founding-interview-guide.md`, following the build-day
  interview convention (guide + answers/transcript pair). The question arc
  covers, at minimum: the founding moment and what preceded it; the 626 number
  and the 817/Fort Worth roots; the two sparks (the internal AI-applications-lab
  proposal → Pricescout as evidence); the origin values beneath the operating
  tenets (Legitimize, Allow-them-to-do-it-themselves, Well-put-together,
  Humanely); the machines-as-colleagues working style; the product family as a
  body of work; and the thousand-year self-image — why a lab that ships fast
  wants to read like an institution that has always existed.
- **Session:** run live in a Claude Code session, one question at a time,
  follow-ups welcome, Este may skip or redirect any thread. Verbatim capture to
  `interview/founding-interview-transcript.md` (his words unedited; my
  questions kept for context).
- **Outputs consumed by C:** the transcript is the single source for the About
  The Lab piece AND the new headline article. Nothing publishes from B itself.

## Sub-project C — About The Lab (committed, specced after B)

Not designed here; recorded so the campaign shape is on paper:

- Mini bake-off: 3 specimen sheets of "millennium institution, year 3026"
  directions on identical sample content (PB-exploration pattern, scoped to 3);
  can run parallel to B since it judges on sample content.
- Deliverables after B: full About The Lab surface + small summarizing About
  section at the bottom of the homepage + the founding story taking the freed
  section-02 crown. Gets its own spec → plan → implementation cycle once the
  transcript exists.

## Out of scope

- Deleting or restructuring `products[]` data (the collapse is presentation).
- Redesigning `/plugins/` (touch-up only).
- Any change to the 14 per-plugin pages.
- Sub-project C's page/section design (post-interview spec).
- New brand treatments outside the C bake-off.

## Inputs needed

- A: none — all material exists in-repo.
- B: Este's review of the interview guide, then a live session on his calendar.
