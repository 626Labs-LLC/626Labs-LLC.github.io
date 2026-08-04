# Theme archetypes — the contract every theme signs

626labs.dev rotates its whole visual identity monthly, and the rotation is
a **hard pivot**: a new theme owes nothing to the outgoing one, shares no
tokens, no layout assumptions, nothing. Hand-authoring 39 page shells per
month per theme is not a plan. Instead, a theme designs **four archetype
dresses** — `home`, `product`, `reading`, `utility` — and every one of the
site's 39 public pages wears exactly one of them.

This document is the vocabulary side of that contract: the real class
names each archetype's markup carries today, what each one means, and
the rule that makes the whole system work. `scripts/archetypes.py`
encodes it as `VOCABULARY`; `content/page-archetypes.json` is the mapping
from page to archetype; `scripts/theme-doctor.py` (a later task) is the
gate that enforces it.

## The one rule

> **A theme varies CSS and structural arrangement. A theme never invents
> a new class name for an existing semantic element.**

If a page's install section is `.install`, every theme's CSS targets
`.install` — a theme can turn it into a terminal window, a numbered list,
a dark card with a glow, whatever the month calls for, but it doesn't get
to rename the section wrapper to `.setup` because that reads better this
month. The class name is the semantic anchor; the dress is everything
built on top of it. This is what lets one shell + twelve months of CSS
stand in for 39 hand-authored pages: the markup's meaning is stable, only
its appearance moves.

The vocabulary below was **read off real pages**, not designed in the
abstract. Where a page doesn't yet carry the vocabulary its archetype
requires (noted per-archetype below), that's a known gap for a later
migration task to close — not a reason to invent an idealized class name
nobody's markup uses.

---

## `home` — the flagship (1 page: `index.html`)

The single-page marketing shell: hero, product grid, Field Notes, Lab,
Play, Support, Contact. One page, so the vocabulary is exactly what
`index.html` uses today.

| Class | Means |
|---|---|
| `nav` | the sticky top navigation bar |
| `hero` | the opening masthead (`<header class="hero" id="top">`) |
| `section` | the base wrapper every content block below the hero shares — always paired with a second, section-specific class, e.g. `class="section field-notes"` |
| `products` | the product grid wrapper |
| `product` | one product card inside `.products` |
| `field-notes` | the Field Notes section wrapper |
| `field-note` | one Field Note teaser card |
| `lab` | the Lab / marketplace teaser section |
| `lab-runs` | the Lab Runs list section |
| `play` | the Play (Bacon Trail) teaser section |
| `support` | the Support / sponsor section |
| `contact` | the Contact section |
| `footer-inner` | the footer's content wrapper (the `<footer>` tag itself carries no class) |

Evidence: every class above appears literally in `index.html`
(`grep -oE 'class="[^"]*"' index.html`), most of them multiple times.

---

## `product` — plugin & standalone-product landing pages (22 pages)

The 14 Claude Code plugin pages (`vibe-*/index.html`,
`thesis-engine/index.html`) share one rendered template
(`scripts/render-plugin-pages.py`); `vibe-cartographer/index.html` is the
evidence page. `plugins/index.html` (the catalog) and the 7 standalone
product pages (`conundrum.html`, `rororo.html`, `rororo-plugins.html`,
`mod-launcher-games.html`, `bacon-trail/index.html`,
`play/bacon/index.html`, `sanduhr/index.html`) are also `product`
archetype but each currently ships **bespoke, non-conforming markup**
(their own one-off class names — `topnav`, `feature-grid`, `merch-card`,
etc.) — a later migration task (`product-standalone`) retrofits them onto
this vocabulary. Don't be surprised the required classes below don't
already appear on `conundrum.html`; they're the target, not today's state
for every page in the bucket.

| Class | Means |
|---|---|
| `top` | the nav bar |
| `hero` | the plugin's hero block (name, tagline, install CTAs) |
| `install` | the install / quickstart section |
| `brain` | the feature-grid section ("what it does") |
| `card` | one generic feature/info card, reused across `brain`, `install`, and cross-sell grids |
| `family` | the plugin-family cross-sell section |
| `family-card` | one cross-sell card inside `.family` |
| `work` | the workflow / how-it-works section |
| `section-head` | the eyebrow+title heading pattern reused at the top of every major section |

Evidence: `vibe-cartographer/index.html`, cross-checked against
`vibe-doc/index.html` (near-identical class list — confirms the shared
template, not a coincidence).

---

## `reading` — long-form and editorial pages (10 pages)

**This is the vocabulary exercised hardest.** A later task adds an easter
egg on `about.html` that swaps *every* theme's reading dress onto that
one page's markup, so the classes below have to be exactly what
`about.html` carries — get this wrong and the toggle produces garbage on
the one page most likely to be screenshotted.

`about.html`'s body is built from two layers, both real, both present in
its markup today:

- **`ed-*`** — the shared editorial base defined in `Design/editorial.css`
  ("Extends colors_and_type.css for longform reading: theses + Field
  Notes"). `about.html` uses three of these directly: `ed-page` (body),
  `ed-title` (h1), `ed-dek` (standfirst). The six Field Note pages under
  `editorial/*/index.html` and the `editorial/index.html` catalog use the
  fuller `ed-*` set (`ed-shell`, `ed-nav`, `ed-article`, `ed-body`,
  `ed-meta`, `ed-pull`, `ed-next`, `ed-pager`, …) for their own chrome and
  body flow.
- **`lnt-*`** — About's own treatment layer ("Long Now Terminal," the
  2026-07-12 bake-off winner), not defined in `editorial.css` at all —
  it's inline in `about.html`, and it's where the page's actual
  *structure* lives: nav, header/frontispiece, the record-by-record
  content loop, pull-quotes, footer.

The required vocabulary below takes the `ed-*` leaf classes (page/title/
dek — genuinely shared with Field Notes) plus the `lnt-*` structural
classes that carry About's actual shape, because those are what the
toggle has to hook into:

| Class | Means |
|---|---|
| `ed-page` | reading-mode page marker, on `<body>` — shared with Field Notes |
| `lnt-nav` | the nav bar |
| `lnt-header` | the masthead / frontispiece header wrapper |
| `ed-title` | the page's H1 — shared with Field Notes |
| `ed-dek` | the standfirst / subtitle line under the title — shared with Field Notes |
| `lnt-main` | the main content wrapper |
| `lnt-record` | one titled section of the piece (About has seven, each with its own `id`) — the repeating structural unit an article's H2 sections map onto |
| `lnt-prose` | one body paragraph inside a record |
| `lnt-pull-quote` | a pulled-quote callout inside a record |
| `lnt-footer` | the footer |

`about.html` also carries a richer optional layer worth knowing about but
not required of every reading page: `lnt-eyebrow`/`lnt-rail` (kicker
metadata above a record's heading), `lnt-frontispiece`/`lnt-epigraph-wrap`
(About-specific archive framing), `lnt-artifact-card` (a distinct
file-record block used in About's closer), `lnt-tag`, `lnt-frame`
(corner-reticle decoration). A theme's reading dress may style these when
present but must not require them — Field Notes and `thesis.html`/
`workflow.html` won't necessarily have an artifact card or a frontispiece.

**Known gap:** `thesis.html` and `workflow.html` currently use neither
`ed-*` nor `lnt-*` — fully bespoke, page-specific class names (`axiom`,
`tenet-section`, `apparatus`, `chain`, `topnav`, …), zero overlap with
this vocabulary. The Field Note article pages
(`editorial/*/index.html`) and the `editorial/index.html` catalog use
`ed-*` but not `lnt-*`. All of these are mapped `reading` in
`content/page-archetypes.json` because that's their correct *target*
archetype — the retrofit onto this vocabulary is later-task work (the
reading renderer / migration task), not something this contract pretends
has already happened.

---

## `utility` — single-purpose pages (6 pages)

`press.html`, `privacy.html`, `themes.html`, `404.html`,
`legal/privacy.html`, `legal/terms.html`. The loosest archetype by
design: these pages have nothing in common content-wise (a press kit, a
legal document, a theme gallery, an error screen), so the required
vocabulary is just enough chrome to read as "part of the site," not a
content shape.

| Class | Means |
|---|---|
| `nav` | the nav bar — same name/shape as `home`'s, since utility pages share the plain-chrome family with `index.html` |
| `page-hero` | the page's header block |
| `page-title` | the page's H1 |
| `page-meta` | a metadata line under the title (last-updated, byline, etc.) |
| `footer-inner` | the footer's content wrapper — same as `home` |

Evidence: `press.html`, cross-checked against `privacy.html` and
`themes.html` (all three share `nav`/`nav-brand`/`nav-inner`/`nav-links`/
`nav-cta`, `page-hero`/`page-hero-bg`/`page-hero-inner`/`page-title`/
`page-meta`, and `footer-inner`/`footer-links`/`footer-meta`).

**Known gap — the biggest one in this contract:** three of the six
utility pages carry **none** of the required vocabulary today.
`404.html` is intentionally chromeless (no nav, no footer, no
page-hero — a lost user isn't shown site structure they've already
failed to find). `legal/privacy.html` and `legal/terms.html` are
minimal, hand-rolled documents with no nav/footer/page-hero at all,
visually unrelated to `privacy.html` despite the similar name. See the
open question below.

---

## Vocabulary sizes

| Archetype | Required classes | Pages mapped |
|---|---|---|
| `home` | 13 | 1 |
| `product` | 9 | 22 |
| `reading` | 10 | 10 |
| `utility` | 5 | 6 |

39 pages total (`admin-dashboard.html` excluded as an internal tool; see
`scripts/archetypes.py` for the full exclusion list — design references,
SDD scratch, announcement drafts, and theme infrastructure are never
"public pages" in the first place).

## Open question for A4 / A6

Should `404.html`, `legal/privacy.html`, and `legal/terms.html` be
migrated to carry the full `utility` chrome (nav + page-hero + footer),
or should the `utility` contract carve out an explicit
"chrome-optional" exception for pages that are deliberately standalone
(an error screen, a document meant to stand outside the site's normal
navigation)? Left for whoever picks up A4/A6 — flagging it here rather
than silently forcing 100% conformance or silently excluding them from
validation.
