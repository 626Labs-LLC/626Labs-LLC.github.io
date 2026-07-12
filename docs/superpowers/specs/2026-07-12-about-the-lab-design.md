# About The Lab — approved design (sub-project C)

**Date:** 2026-07-12
**Status:** Approved design, pre-implementation
**Scope:** The founding story ships: a full About The Lab page built as an heirloom, its condensed cut reclaiming homepage section 02, the existing About section (06) refocused as the door, and a 3-sheet treatment bake-off that decides the page's look. Completes the campaign begun in `2026-07-11-homepage-reshape-and-founding-interview-design.md`.

## Source of truth

- **The transcript is the sole biographical source:**
  `626Labs-Publishing/works/2026-07-11-founding-interview/interview/founding-interview-transcript.md`
  (complete, 2026-07-12, with `PriceScoutalpha.ipynb` — the founding-night notebook — beside it).
  Every biographical claim in every deliverable traces to a transcript line; if a fact is
  missing, ask Este — never infer.
- **Privacy rules on record:** the full phone number in Q7 never publishes (the 626
  exchange is the public story); the employer stays unnamed (titles may appear per Q12).
- **Design directives on record:** the thousand-year frame is LINEAGE, not corporate
  longevity — the page is an heirloom for the house (Q25); "soften the institution
  feel" (Q26); succession is a proven pattern — Stage Productions carried forward by
  the siblings (Q28).

## Decisions (2026-07-12 brainstorm)

1. **One piece, two cuts.** The founding story is written once. Full cut = the About
   The Lab page. Condensed cut = homepage section 02 (eyebrow, headline, pull-quote,
   a few paragraphs, a door to the page). One voice; no drift between tellings.
2. **Parallel with real excerpts.** The bake-off sheets use actual transcript material
   (keystone quotes + the founding-night passage) as specimen content while the full
   prose drafts in parallel in the publishing work. Sheets are judged doing their
   real job.
3. **Hard gates:** Este reviews and approves the prose before it touches the site;
   Este picks the treatment (keep/kill/remix) before the page builds.

## Part 1 — The piece

- Drafted in `works/2026-07-11-founding-interview/` under its persona (reflective,
  first-person-interviewer heritage, transcript-only sourcing). Draft lives in the
  work (e.g. `01_POSTS/2026-07-XX-about-the-lab/body.md` per BlogStudio convention)
  until approved; nothing publishes from the publishing work itself.
- **Full cut (the page):** the arc the transcript gave — the house that shouldn't have
  had a Nintendo; the 626 exchange read off unpainted northside buildings; the founding
  night pinned to the hour (August 8th, 3:45 pm report → 10:45 pm command line; broke
  45 minutes later; certainty at end of week one); the four values through their scenes
  (the Bose cabinet, the "too smart for the job" dismissal, workers/users/builders,
  erase workflows not jobs); machines as colleagues ("best effort is the standard");
  the arsenal answer to the junk-drawer charge; the close — succession already proven
  once (Stage Productions, the siblings), "maybe that 7 can be 8, even one more is a
  win." Keystone quotes render as pull-quotes: "I build tools, because care doesn't
  always scale"; monkey's paw or favorite genie; the Q30 exchange as the epigraph
  (including the call breaking up).
- **The founding artifact:** `PriceScoutalpha.ipynb` is featured on the page as a
  primary source (displayed as an artifact — name, date, size, one framed cell or a
  rendered thumbnail; exact form decided in the winning treatment). The notebook
  itself is NOT committed to the hub repo unless Este explicitly approves publishing
  it; default is to feature it without hosting the raw file.
- **Condensed cut (section 02):** ~200-300 words + one pull-quote + the door link.
  Same source text, cut down — not rewritten.
- **Copy rules:** house voice rules apply (no emoji, no banned corporate words);
  count-free prose except facts tokens; the piece may use "I" — it is Este's story,
  first person is correct for the heirloom register.

## Part 2 — The bake-off

- Location: `Design/explorations/2026-07-12-about-treatments/` — index gallery +
  per-direction sheets + token checker, the PB-round mechanics, scoped to 3 sheets.
- All three sheets render IDENTICAL specimen content: real transcript excerpts
  (keystone quotes, the founding-night passage, one values scene, the artifact block,
  the epigraph). Rubric line one: "soften the institution." WCAG AA contrast gates
  every sheet.
- Draft directions (final names/theses at plan time; the sheets argue for themselves):
  1. **The Family Ledger** — heirloom registry: paper-warm light surface, engraved
     rules, folio numbers, ledger tables, an "est." mark.
  2. **The Foundation Wall** — institutional warmth: museum-placard captions,
     donor-wall typography, the monument softened.
  3. **The Long Now Terminal** — the 3026 records-room read: institutional futurism
     bridging PB's vocabulary without scanlines; light "archive" surface.
- Este judges keep/kill/remix. The winner becomes the About The Lab treatment. Retired
  sheets stay in the exploration folder for future remixing (PB-round precedent).
- The About treatment is editorial-register and distinct from PB (PB is dark-surfaces-
  only and never editorial, per the standing brand rule). If the winner earns adoption
  beyond this page, promotion to the design skill is a separate follow-up, not part
  of C.

## Part 3 — The surfaces

- **`about.html` at the repo root.** Hand-authored shell in the winning treatment with
  renderer-owned zones for the prose (so future edits flow through site.json/admin
  where sensible; exact zone split decided at plan time — at minimum the condensed
  metadata and any listy content derive; the long prose may be static-in-shell like
  other editorial pages). Sitemap picks it up automatically. **The ship report ends
  with the GSC Request Indexing URL** (`https://626labs.dev/about.html`) per the
  standing workflow rule.
- **Section 02 returns:** new top-level site.json key `founding` (eyebrow, headline,
  quote, paragraphs, door link) rendered into the dormant thinking zone's slot by a
  new render-hub function, with its own `sections.founding` toggle and section id
  (anchors: nav may gain a "Story" link or leave nav unchanged — decided at plan
  time). Eyebrow numbering heals: 01 → 02 → 03.
- **Section 06 refocuses as the door:** trimmed summary paragraphs (door copy sourced
  from the approved piece), star map and stack stay, add a "read the whole story"
  link to about.html. Admin-editable as today.
- **Gates and verification:** both renderers + pytest + site-doctor as always;
  Playwright pass on about.html (desktop/mobile, door links, artifact block) and the
  healed homepage numbering; ship via PR held for Este (flagship surface, same
  courtesy as #83).

## Build order

1. Bake-off sheets (agent work, parallel) + prose draft (publishing work, parallel).
2. Este: approve/edit prose; judge treatment.
3. Page + section 02 + section 06 door built from approved prose in winning treatment.
4. PR (held), merge, GSC Request Indexing for about.html.

## Out of scope

- Publishing the raw notebook file (default: feature, don't host — Este may override).
- Promoting the winning treatment into the design skill (follow-up if earned).
- Any Field Note / feed syndication of the founding story (one piece two cuts — a
  syndicated third cut is a later call).
- Issue #84's admin cleanup (separate fast-follow).
- Touching the interview transcript (it is a frozen source).

## Inputs needed

- Este's prose review (hard gate) and treatment verdict (keep/kill/remix).
- Nothing else — all source material exists.
