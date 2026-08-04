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

### The product archetype file — structural completeness, zero consumers

`themes/phosphor-blueprint/archetypes/product.html` exists as of A4,
extracted verbatim from `vibe-cartographer/index.html`'s `<style>` block,
`nav.top`, hero/work/brain/install/family scaffolding, and footer —
tokenized (`{{PRODUCT:HEAD}}`, `{{PRODUCT:NAV_CURRENT}}`,
`{{PRODUCT:HERO}}`, `{{PRODUCT:WORK}}`, `{{PRODUCT:BRAIN}}`,
`{{PRODUCT:INSTALL}}`, `{{PRODUCT:FAMILY}}`, `{{PRODUCT:FOOTER}}`) the same
way A3 tokenized `reading.html`. Unlike `home.html`/`reading.html`, **no
code resolves this file today** — `scripts/render-plugin-pages.py` (which
generates the 14 plugin pages + `plugins/index.html`) has zero
theme-awareness of any kind: it doesn't import `theme_registry`, doesn't
link `tokens.css`, and duplicates the Phosphor Blueprint override block
inline exactly like every plugin page ships today. Wiring
`render-plugin-pages.py` to resolve `product.html` and replace that
duplication with a real `tokens.css` link is **A5's job** ("plugin
renderer" per the milestone ledger) — A4 only needed the file to exist so
theme completeness (`theme_registry.REQUIRED_ARCHETYPES`,
`theme-doctor.py`) can require all four archetypes with the `shell.html`
fallback gone.

**The bespoke standalone pages do not participate, this milestone or
any future one this doc can promise.** `conundrum.html`, `rororo.html`,
`rororo-plugins.html`, `mod-launcher-games.html` (plus `thesis.html` /
`workflow.html` in the `reading` bucket) are the controller's explicit
M2a scope cut — see "Known gap" above and the SCOPE RULING under
`reading`. A4 did not extract from them, did not retrofit their markup
onto the `product`/`reading` vocabulary, and did not change a single byte
in any of the six files. They stay hand-authored, bespoke, and out of
this contract's live enforcement until each is touched for its own
reasons.

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

**SCOPE RULING (Este, M2a):** `thesis.html` and `workflow.html` stay fully
bespoke through this milestone — hand-built layouts, unrewritten, migrated
to this vocabulary the next time either is touched for its own reasons.
The `reading` migration task (A3) covered `about.html`,
`editorial/index.html`, and the six generated Field Note pages only.

### The `reading` archetype file, and About's per-page dress override

`themes/phosphor-blueprint/archetypes/reading.html` is the theme's reading
shell, and it exists for exactly one live consumer today:
`scripts/render-hub.py`'s `render_story_pages()` resolves it (via
`theme_registry.theme_dir(slug) / "archetypes" / "reading.html"`) and fills
it per Field Note with `{{READING:HEAD}}` / `{{READING:ARTICLE_HEADER}}` /
`{{READING:BODY}}` / `{{READING:PAGER}}` tokens. Extracted verbatim from the
Field Note template that used to be hardcoded as an f-string in
`render_story_page()` — a straight relocation, not a redesign (matching
A2's precedent for `home.html`): rendering the six existing local Field
Notes through it reproduces every one of them **byte-for-byte**
(`render-hub.py` reports "6 Field Note page(s) already current" on a clean
run). Because Field Note pages are always fully regenerated
(`STORY_PAGE_MARKER` forbids hand-editing them), the `{{READING:...}}`
tokens are consumed whole and never appear in the shipped HTML — unlike
`home.html`'s `SITE_JSON:` comment markers, which have to survive in
`index.html` because that file is diffed against itself and partially
hand-edited outside its zones. Two different substitution mechanisms for
two genuinely different lifecycles, not an inconsistency.

`editorial/index.html` is **not** wired through this shell — it's a
hand-curated catalog page (Theses list, Field Notes list, deliverable
cards), the same category of genuinely bespoke per-page content as
`thesis.html`/`workflow.html`, just not called out as such before now.
It stays hand-authored, unchanged, in this milestone.

**About's per-page dress override — the honest resolution the task brief
asked for.** `about.html` is not, and does not become, a consumer of
`themes/<slug>/archetypes/reading.html` at render time. It is a static,
hand-authored file with no render-hub.py involvement at all — the same as
it was before this task. That absence *is* the override: About's Long Now
Terminal treatment (its own inline `<style>` block, `lnt-*` classes over
the shared `ed-page`/`ed-title`/`ed-dek` leaf classes) is what ships by
default, unconditionally, and A3 changes none of it — confirmed
0-pixel-identical against `origin/main` at 1440/768/390. The contract this
override has to honor is markup-shape, not render-pipeline participation:
About's `lnt-*` structure already **is** the full `reading` vocabulary
(see the class table above), which is what lets a later task (A7) swap a
different theme's reading dress onto that exact markup via a client-side
stylesheet swap — About doesn't need to run through `reading.html`'s
Python substitution for that swap to work; it needs its markup to carry
the vocabulary's hooks, which it already did before this task and still
does after it.

`editorial.css` (the shared `ed-*` token/component base every reading page
links) is, today, **theme-agnostic** — one stylesheet, unchanged by which
theme is active in `content/themes.json`. `themes/phosphor-blueprint/
archetypes/reading.html` does not link `themes/phosphor-blueprint/
tokens.css` for exactly this reason: `tokens.css` sets a bare `body`
background (the drafting-grid/scanline field) that would have overridden
`editorial.css`'s bare `body` background (the warm paper field) on every
reading page, breaking the 0-pixel gate for no requested change. Reading
pages entering the monthly theme rotation for real — i.e. `tokens.css`
actually re-skinning Field Notes/About the way it already re-skins
`index.html` — is future work, not something this task's 0-pixel gate
permits it to do as a side effect.

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

**Known gap, now resolved — see "Chrome-optional pages" below:** three of
the six utility pages carry **none** of the required vocabulary today.
`404.html` is intentionally chromeless (no nav, no footer, no
page-hero — a lost user isn't shown site structure they've already
failed to find). `legal/privacy.html` and `legal/terms.html` are
minimal, hand-rolled documents with no nav/footer/page-hero at all,
visually unrelated to `privacy.html` despite the similar name.

### The utility archetype file, and why press/privacy/themes stay hand-authored

`themes/phosphor-blueprint/archetypes/utility.html` exists as of A4,
extracted from `press.html` (the brief's designated reference) —
nav/page-hero/footer are byte-identical across `press.html`,
`privacy.html`, and `themes.html` (verified with `diff`, not assumed),
tokenized as `{{UTILITY:HEAD}}`, `{{UTILITY:EYEBROW}}`,
`{{UTILITY:PAGE_TITLE}}`, `{{UTILITY:PAGE_LEAD}}` (optional —
`privacy.html` has none), `{{UTILITY:PAGE_META}}`, `{{UTILITY:BODY}}`,
`{{UTILITY:FOOTER_LINKS}}`. This is the same "extract, never redesign"
posture A2/A3 used for `home.html`/`reading.html`.

`press.html`, `privacy.html`, and `themes.html` were the task's real
migration set — the three utility pages that actually carry chrome
today, as opposed to `404.html`/`legal/*` which don't (below). All three
were considered, all three were the extraction source, and **all three
stay hand-authored, zero bytes changed** — the same non-participation
call A3 made for `about.html`/`editorial/index.html`, for a related but
distinct reason:

- **No data source drives regeneration.** `press.html` and `privacy.html`
  carry zero `SITE_JSON:`-style zones — nothing in `content/site.json`
  feeds their content, so there's no legitimate trigger for Python to
  regenerate them (unlike `index.html`'s zones or the Field Notes'
  markdown source).
- **No shared component CSS layer exists to build a real shell on top
  of.** Reading pages share `Design/editorial.css`; utility pages don't
  have an equivalent — each of the three carries its own large,
  page-specific `<style>` block (`press.html`'s `.copy-block`/
  `.asset-grid`, `privacy.html`'s `.tldr`, `themes.html`'s
  `.theme-card` gallery) that would have to travel wholesale with any
  render step, which is architecturally close to "the file already is
  its own shell."
- **A concrete regression risk, found and not routed around:**
  `press.html` and `privacy.html` currently duplicate the Phosphor
  Blueprint override CSS *inline* (not linked to `tokens.css`), and that
  duplicated copy has **diverged** from `tokens.css` — `press.html`'s
  copy applies `text-shadow` to every `h1` unconditionally, `tokens.css`
  scopes it to `header.hero h1` (a selector that wouldn't match
  `h1.page-title`); `tokens.css` additionally sets `nav.nav { z-index:
  70 }` and a `nav.nav::after` scanline overlay that `press.html`'s
  inline copy never picked up. Swapping the inline block for a
  `tokens.css` `<link>` — the obvious "de-duplicate" move — would have
  **changed rendered pixels** (losing the H1 bloom on the page title,
  gaining a scanline strip on the nav) and failed the 0-pixel gate. Not
  attempted here; flagged for whoever eventually wires a live utility
  renderer, since it's real, pre-existing CSS drift independent of this
  task. `themes.html` already links `tokens.css` correctly and has no
  such drift — it's the one utility page today that's already correctly
  wired to theme rotation.

`utility.html` is therefore a **structural/vocabulary reference with
zero live consumers**, same posture as `product.html` above — it exists
so theme completeness can require all four archetype files, and models
the target shape (including linking `tokens.css` instead of duplicating
it) for whichever later task builds a real content-extraction mechanism
for these three pages.

### Chrome-optional pages — the open question, resolved

**Controller ruling (M2a):** `404.html`, `legal/privacy.html`, and
`legal/terms.html` get **no chrome retrofit**. They carry no nav,
page-hero, or footer today, and adding any of it would change how they
look — a 404 page showing full site navigation undercuts the "you've
already failed to find it" design intent, and the legal documents were
deliberately built to stand outside the site's normal chrome. The
`utility` archetype's required vocabulary (`nav`/`page-hero`/
`page-title`/`page-meta`/`footer-inner`) applies only to the three
pages that already carry chrome — `press.html`, `privacy.html`,
`themes.html`. `404.html` and `legal/*` are a permanent, explicit
"chrome-optional" carve-out in this contract, not a deferred migration
item the way `thesis.html`/`workflow.html` are in `reading` — nobody is
expected to retrofit them later for conformance's own sake. A future
change to how 404 or legal pages *should* look is a deliberate design
decision to make on its own terms, not a drive-by side effect of a
theme-archetype task.

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

## A6 — still open

Vocabulary *enforcement* (theme-doctor checking a theme's rendered output
actually carries each archetype's required classes) is intentionally not
built yet — `scripts/archetypes.py`'s `validate()` checks the page->
archetype mapping only (every mapped page exists, every archetype value
is known, every on-disk public page is mapped), not class presence. That
split is deliberate, confirmed by this doc's own framing throughout: A6
is where a theme's dress gets checked against the vocabulary tables
above.
