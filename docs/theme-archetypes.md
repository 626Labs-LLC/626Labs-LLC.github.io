# Theme archetypes — the contract every theme signs

> **Scope note (2026-08-05).** This document covers the four archetypes and
> the token contract. It PREDATES several mechanisms that now gate a rotation
> and does not describe them: `resolution_groups` and the per-group reads
> check, `GRADED_THEME_CSS`, `check_page_renders_dressed` /
> `DRESS_OUTCOME_PAGES` (the region differential over press.html and
> privacy.html), `check_theme_references_only_itself`, and
> `scripts/visual-diff.py`. For those the source is the record —
> `scripts/theme-doctor.py`'s module docstring is the map — and `CLAUDE.md`
> carries the short version.


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

### The product archetype file — the CSS half is live, the HTML shell stays inert

`themes/phosphor-blueprint/archetypes/product.html` exists as of A4,
extracted verbatim from `vibe-cartographer/index.html`'s `<style>` block,
`nav.top`, hero/work/brain/install/family scaffolding, and footer —
tokenized (`{{PRODUCT:HEAD}}`, `{{PRODUCT:NAV_CURRENT}}`,
`{{PRODUCT:HERO}}`, `{{PRODUCT:WORK}}`, `{{PRODUCT:BRAIN}}`,
`{{PRODUCT:INSTALL}}`, `{{PRODUCT:FAMILY}}`, `{{PRODUCT:FOOTER}}`) the same
way A3 tokenized `reading.html`. **No code resolves this file** —
`render-plugin-pages.py` owns the markup for its 15 pages directly (the
hero/work/brain/install/family shape *is* the product archetype's
vocabulary in practice, not a stand-in for it), and A5's scope was
narrowed to CSS only: retrofitting `render-plugin-pages.py` onto the
`product.html` shell's tokenized zones would mean rebuilding its
Python-side rendering (per-plugin sections, the terminal block, capability
chips, JSON-LD) as template substitution for no visual gain. `product.html`
stays what A4 called it: structural completeness for
`theme_registry.REQUIRED_ARCHETYPES`, not a live template.

The CSS half is different. As of A5, `render-plugin-pages.py` imports
`theme_registry` and reads its page CSS from
`themes/<active-theme>/archetypes/product.css` at render time — no longer
a literal Python string, no longer theme-blind. The 15 pages
(`plugins/index.html` + the 14 plugin pages) still get that CSS **inlined**
in a `<style>` block, same "no-build" idiom the file has always used —
only the CSS's *source* moved from a hardcoded constant to the active
theme's file, so a theme rotation's `product.css` reaches these pages on
the very next render with no code change. `themes/phosphor-blueprint/
archetypes/product.css` is that extraction: Phosphor Blueprint's current
plugin-page CSS, byte-for-byte, moved out of the `.py` file and into the
theme's own directory.

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

### A7 — `archetypes/reading.css`, the About easter egg, and a gate that actually differentiates

A3 flagged a real gap for A7 to close: the toggle it was asked to build
needs a CSS *artifact* to point a `<link>` at, but a theme's reading dress
was an HTML shell (`reading.html`, Field Notes only) plus a theme-agnostic
base (`editorial.css`) — no per-theme stylesheet existed. A7 adds
`themes/<slug>/archetypes/reading.css`: a real, standalone stylesheet
dressing vocabulary-conformant reading markup, extracted **verbatim** from
`about.html`'s own inline `<style>` block (the Long Now Terminal
treatment) — the one artifact in the repo that actually dresses the full
`reading` vocabulary today. About's own inline `<style>` stays the live,
authoritative source for its unconditional default; `reading.css` is a
point-in-time snapshot of it, kept in sync by hand the next time About's
dress changes (same accepted-drift posture A4 used extracting
`utility.css` from `press.html`). It is **not** linked from `reading.html`
— Field Notes stay theme-agnostic on purpose, per A3's finding above.

**A real, pre-existing gap this extraction surfaced:** `lnt-main` (a
required `reading` vocabulary class) had no CSS selector anywhere in the
repo — not in About's own `<style>`, not in `editorial.css`. It had always
been silently satisfied by the old, theme-invariant vocabulary check
(About's markup carries the class; the old check credited markup alone).
Fixed at the source with a single, zero-visual-effect rule added to
About's own `<style>` (`.lnt-main { display: block; }`, exactly matching
`<main>`'s UA default) before extracting `reading.css`, so both files stay
honest and in sync — not silently patched around in the theme's copy alone.

**Selecting "Phosphor Blueprint" in the toggle looks identical to About's
own default today, and that's correct, not a bug.** Phosphor Blueprint is
626labs.dev's only live theme right now, and the Long Now Terminal dress
was designed and shipped during its era — there is no second, differently
designed reading dress yet for the pixels to diverge against. The swap is
still real (a genuine `<link>` replaces the inline `<style>`'s effective
rules, verifiable in the DOM/network panel); the pixels only diverge once
a later theme ships its own, different `reading.css`.

**The gate, fixed to actually differentiate (the carried A6 finding).** A6
shipped `reading`'s vocabulary check against `about.html` because no
theme-owned artifact existed yet to check instead — and flagged, explicitly,
that this made the check theme-**invariant**: any theme's (nonexistent)
reading dress passed, forever, because About's markup never varies. Now
that `reading.css` is real, `_check_archetype` (`scripts/theme-doctor.py`)
splits the vocabulary in two, matching the split this doc already draws
between "shared" and "theme-owned" classes:

- The 3 shared `ed-*` leaves (`ed-page`/`ed-title`/`ed-dek`) are credited
  from a **synthetic** anchor string, not from About's real markup — they're
  styled by the theme-agnostic `editorial.css`, so no theme is expected to
  redeclare them, but crediting About's actual markup for them (theme-
  invariant, same as the pre-A7 approach) would have blurred the line with
  the check below.
- The 7 `lnt-*` structural classes (About's own shape, with **no** base
  stylesheet backing them at all) are checked **CSS-selector-only** against
  the THEME's own `archetypes/reading.css` — About's markup is no longer
  credited for these. A theme whose `reading.css` is empty, or drops a
  selector, now fails the gate by name (`reading: vocabulary missing
  required class 'lnt-record' ...`), proven live against a scratch theme
  during A7 (7/10 classes failed with an empty `reading.css`; only the
  shared `ed-*` leaves still passed).

Completeness also extended: `REQUIRED_ARCHETYPE_CSS` now includes
`"reading": "reading.css"`, joining `product.css`/`utility.css` (A6) — a
theme rotating in without it fails before it's ever queued, matching the
carried-requirement posture A5/A6 established for the other two.

**The easter egg itself.** Discovery is a keyboard sequence — typing "626"
anywhere on the page (no input focus needed) — chosen because it's an
unlabeled, on-brand mark (626 is the lab's own exchange-code numbering,
already all over this page's own archive stamps) rather than a visible
control, honoring "easter egg, not a menu." It opens a small, lazily-built
picker (not present in the DOM until found) listing every dress
`content/themes.json` currently offers: About's own default (`css: null`,
always item 0, marked with a leading `>` when active) plus the live theme plus every
archived theme newest-first — **not** the queue, which isn't meant for
public preview ahead of its own rotation. Picking a dress swaps (or
removes) a `<link id="about-dress-override">`, persists the choice to
`localStorage['about-dress']`, and a second small script re-applies a
stored non-default choice before first paint on later visits (no flash).
Escape, or picking "Long Now Terminal" from the open panel, always returns
to the default — a fresh visitor (nothing stored) sees zero difference
from the page as authored.

The list itself is renderer-owned, not hand-maintained: `scripts/
render-hub.py`'s `render_about_theme_dresses()` fills a single narrow
`SITE_JSON:about-theme-toggle` zone in `about.html` (a JSON `<script>` tag)
from `theme_registry.load()` fresh every run — the same governance
`UTILITY_CSS_HREFS`/`render_theme_css_link()` (A4) already established for
`press.html`/`privacy.html`/`themes.html`: one small renderer-owned seam in
an otherwise hand-authored page, not a full render-pipeline page. Since a
`<script type="application/json">` tag has zero visual footprint, this
doesn't touch the 0-pixel gate — confirmed screenshot-identical against
`origin/main` at 1440/768/390 with the zone, the registry, and the toggle
scripts all present.

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

### The utility archetype file, and the CSS split that made it real

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
today, as opposed to `404.html`/`legal/*` which don't (below).

**First pass (review-flagged as an inertness gap):** all three pages'
HTML stayed hand-authored, and `utility.html`/a first cut of the CSS
extraction had zero live consumers — meaning `press.html`/`privacy.html`
would have stayed frozen in whatever the Phosphor Blueprint dress looked
like today, forever, even after the site rotates to a different theme in
September. That's a real gap in "the whole site rotates" and not one of
the founder's sanctioned exclusions (those are the six bespoke pages,
`404.html`, and `legal/*`).

**The fix — a real, load-bearing `archetypes/utility.css`:**
`press.html`'s shared chrome CSS (base tokens, resets, nav, page-hero,
footer, and the Phosphor Blueprint treatment layer — drift and all) is
now extracted into a standalone stylesheet, diffed byte-for-byte against
`privacy.html`'s copy before extraction to confirm it's genuinely
shared. `press.html` and `privacy.html` each had their inline `<style>`
block trimmed down to *only* their page-specific rules (`press.html`'s
`.copy-block`/`.asset-grid`, `privacy.html`'s `.tldr`) and now link
`archetypes/utility.css` instead. That link lives inside a
`<!-- SITE_JSON:theme-css:start/end -->` zone that `scripts/render-hub.py`
owns and recomputes from `content/themes.json`'s active slug on every
run (`UTILITY_CSS_HREFS` / `render_theme_css_link()`) — the same
governance the `themes` gallery zone already had, just for a stylesheet
link instead of card markup. A theme rotation in September now actually
reskins these two pages, because the href they carry is never hardcoded.

**Why the "drift" is not a bug to fix:** the CSS moved verbatim, so the
pixels don't change even though the bytes do (an inline `<style>`
becoming a `<link>` is exactly the sanctioned kind of byte change — the
gate is visual identity, not byte identity). `press.html`'s unconditional
`h1 { text-shadow }` and its `nav.nav` without the z-index/scanline bump
`tokens.css` gives `index.html` are now simply what Phosphor Blueprint's
`utility` dress *is* — a different archetype is allowed to look different
from the `home` dress. September designs its own `utility.css` and can
make different choices.

**Why `themes.html` keeps `tokens.css`, not `utility.css`:** it already
linked `tokens.css` with no inline duplication (the one utility page that
was correctly wired before this task), so it also gets a `theme-css` zone
— but pointed at `tokens.css`, not `utility.css`. Switching it to
`utility.css` would have **changed its pixels**: `utility.css`'s
unconditional `h1 { text-shadow }` doesn't apply to `themes.html` today
(`tokens.css`'s `header.hero h1` never matched `.page-hero` either, so
`themes.html`'s `h1.page-title` currently has *no* bloom at all — a real,
pre-existing difference from `press.html`/`privacy.html`, not something
this task introduced), and `press.html`'s `.page-lead` is
`max-width: 60ch` where `themes.html`'s own copy is `62ch`. Forcing
`themes.html` onto `utility.css` would have fixed the inertness gap by
introducing a visible regression — not an acceptable trade. It still
rotates correctly; it just rotates its own way.

`utility.html`, the HTML shell, still has **no live render-hub.py
consumer** — the three pages' markup stays hand-authored, only their
stylesheet `<link>` is renderer-owned. That split (dynamic CSS href,
static HTML) is deliberate: there's still no `SITE_JSON:`-style data
source for these pages' *content*, and utility pages still have no
shared component CSS layer the way reading pages share
`Design/editorial.css` (each page's body-specific CSS — `press.html`'s
`.copy-block`/`.asset-grid`, `privacy.html`'s `.tldr`,
`themes.html`'s `.theme-card` gallery — stays page-specific). Building a
real HTML renderer for these pages is still future work; the CSS-link
governance was the piece that was actually load-bearing for "the whole
site rotates," and it's done.

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

## Vocabulary enforcement — closed (A6, A7)

`scripts/archetypes.py`'s `validate()` only ever checked the page->
archetype *mapping* (every mapped page exists, every archetype value is
known, every on-disk public page is mapped) — never class presence. That
split was deliberate from A1: enforcing that a theme's actual dress
carries each archetype's required classes is `theme-doctor.py`'s job
(`check_vocabulary`, `scripts/theme-doctor.py`), not `archetypes.py`'s.

- **A6** built that enforcement for `home`/`product`/`utility` — a
  required class must appear as a literal HTML class or a CSS selector in
  the theme's own dress — plus the `archetypes/product.css` +
  `archetypes/utility.css` completeness gate. `reading` was checked too,
  but against `about.html` (the only artifact that carried the full
  vocabulary at the time), which made that one archetype's result
  theme-**invariant** — flagged explicitly as A7's job to fix.
- **A7** closed it: `reading.css` now exists per theme (see the A7
  subsection above), `reading`'s vocabulary check is CSS-selector-only for
  its `lnt-*` half, and `archetypes/reading.css` joined the completeness
  gate. All four archetypes now get a real, theme-differentiating
  vocabulary check.

## The token-variable contract — closed (final review Fix 1)

The vocabulary above is the markup-side contract: a theme can't rename a
required *class*. Nothing equivalent existed for CSS *custom properties*
until this fix wave — the final whole-branch review flagged it as a real,
undocumented, ungated gap. `themes.html`'s gallery CSS and `press.html`'s/
`privacy.html`'s own page-specific residual CSS (the rules left after
`utility.css`'s extraction — `.copy-block`/`.asset-grid`/`.tldr` and
friends) read roughly forty custom properties via `var(--x)` and never
define any of them. Nothing required a theme's `tokens.css`,
`archetypes/product-tokens.css`, `archetypes/utility.css` or
`archetypes/reading.css` to supply them — a
September theme could rename or drop one, pass every existing gate
(vocabulary only checks class names; chrome/links don't look at custom
properties at all), and silently break ten pages:
`themes.html`/`index.html` (which each carry a hardcoded LOCAL `:root`
fallback, cascade-earlier than the theme's own `<link>`, so a missing token
doesn't error — it just keeps showing the OUTGOING theme's stale value
forever) and `press.html`/`privacy.html`/`thesis.html`/`workflow.html`/
`conundrum.html`/`rororo-plugins.html`/`rororo.html`/
`mod-launcher-games.html`
(which carry no fallback at all, so a missing token is a straight unresolved
`var()`). `product-tokens.css` carries the widest blast radius of the
four: four pages LINK it, and `render-plugin-pages.py` concatenates it into
fifteen more.

`archetypes.REQUIRED_TOKENS` (`scripts/archetypes.py`) closes it: the exact
set of custom-property names, derived the same way `VOCABULARY` was — by
reading the real, shipped CSS, not designing in the abstract — union of
every `var(--x)` in `themes.html`'s inline `<style>` plus the residual
`<style>` blocks of `press.html`, `privacy.html`, `thesis.html`,
`workflow.html`, `conundrum.html`, `rororo-plugins.html`, `rororo.html`
and `mod-launcher-games.html`.
`scripts/theme-doctor.py`'s `check_required_tokens()` fails
a theme whose `tokens.css`, `archetypes/product-tokens.css`,
`archetypes/utility.css` **or**
`archetypes/reading-tokens.css` doesn't define every one of them — all four
(`REQUIRED_TOKEN_CSS`), because all four are real, unguarded consumers
today: `tokens.css` for
`themes.html`/`index.html`, `utility.css` for `press.html`/`privacy.html`,
`reading-tokens.css` for `thesis.html`/`workflow.html`, `product-tokens.css` for
`conundrum.html`/`rororo-plugins.html`/`rororo.html`/
`mod-launcher-games.html` plus the fifteen pages concatenated
from it (their only source of these
properties, with no local fallback of their own).

> **`reading-tokens.css`, not `reading.css`.** This paragraph named the dress
> where the contract means the token file, and `CLAUDE.md` repeated it. They
> are different files with different jobs: `archetypes/reading.css` is
> about.html's Long Now Terminal dress, while `archetypes/reading-tokens.css`
> is the palette `thesis.html` and `workflow.html` link. `REQUIRED_TOKEN_CSS`
> is the record — read it from the source if prose and code ever disagree
> again.

A theme missing even one
fails before the archetype loop runs, named by property
(`tokens.css: missing required custom property '--cyan'`).

### Why the product archetype ships two CSS files

`archetypes/product.css` is an element **dress**: it styles `body`, `a`,
`a:hover`, `h1, h2, h3`, `section.hero`, `.card`, `.btn`, `.brand img`,
`footer`. Those selectors are written for the markup
`render-plugin-pages.py` generates. `archetypes/product-tokens.css` is the
**vocabulary** — custom-property definitions and nothing else.

The split exists because all four bespoke product pages —
`conundrum.html`, `rororo-plugins.html`, `rororo.html`,
`mod-launcher-games.html` — are hand-authored: they keep their own layout,
and the spec for this milestone is that these pages **recolor monthly,
they do not re-layout**. A token file is a recolor; a dress is a
re-layout. They link the token half only.

The dress's reach onto each page was measured, not assumed. It is **158
style rules carrying 180 selectors**, and every one of those selectors was
queried against the page's live DOM. 31 match `rororo.html` and 20 match
`mod-launcher-games.html` with its feed loaded. One of each is `:root` —
vocabulary, which is precisely what these pages link the token file for.
The remaining **30 and 19 are dress**: `body`, `a`, `a:hover`,
`h1, h2, h3`, `.btn`, `.btn-primary`, `.btn-ghost`, `.install-grid`,
`.install-card`, `.install-card h3`, `.eyebrow`, `.pb-scanlines`, and the
`.brand img` stabilizer group. Each page already declares its own rule for
the one **class** selector in that list it depends on, `.pb-scanlines` —
the rule whose silent disappearance a token-completeness gate cannot see,
and which the reading split nearly deleted.

This was measured before it was decided. Linking the dress into both pages
and neutralising it property-by-property was tried: it needed eleven
page-side rules to hold 0-pixel, and it still shipped a live regression
that no resting-state gate could see. `a:hover { text-decoration:
underline; text-decoration-color: var(--magenta) }` has specificity
(0,1,1), which outranks `.merch-card`, `.shop-cta`, `.repo-cta` (all
(0,1,0)) and `footer a` (0,0,2) — 11 links across the two pages grew a
magenta hover underline. Pixel harnesses and computed-style probes sample
the **resting** state; hover is out of frame by construction.

Two gates keep the split honest, and they catch different things.
`check_required_tokens` catches a **missing name**.
`check_token_css_declares_only_tokens` (`TOKEN_ONLY_CSS`) catches an
**extra rule** — any selector other than `:root`, any non-token declaration
inside `:root`, any style-carrying at-rule. Without the second, a future
theme's `product-tokens.css` can grow `p { margin: 0 0 24px }` and land it
on both pages unattended on the 1st.

`render-plugin-pages.py` concatenates the two for its own 15 pages, **dress
first**. That order is load-bearing, not cosmetic: `product.css` opens with
`@import url('/fonts/fonts.css')`, and CSS requires `@import` to precede
every rule but `@charset`/`@layer`. Tokens-first silently drops the import
— measured at 1,321,489 changed pixels on `plugins/index.html` and a height
change on every one of the 15, with no error emitted anywhere.
`tests/test_render_plugin_pages.py` pins it.

Four names — `--bg-2`, `--dur-med`, `--r-xl`, `--fg-muted` — were admitted
later, when `thesis.html`/`workflow.html` and then
`conundrum.html`/`rororo-plugins.html` gave up their private token blocks. The test
for admission was narrow on purpose: **is a sibling of that token's own
scale already required?** `--bg-0`/`--bg-1` were, so a page reading `--bg-2`
is reading a hole in a scale the contract already half-covers. Same for
`--dur-med` next to `--dur-fast` and `--r-xl` next to the other five radius
steps. Same again for `--fg-muted`, the fourth member of a four-member
alias family whose other three (`--fg-1`/`--fg-2`/`--fg-3`) were all
already required, and whose underlying value (`--text-mute`) was required
too — the contract already obliged every theme to have the color and merely
declined to name the alias the pages read. Completing a scale the contract
already commits to is the contract
working; every theme in the repo already defined all four, so admission
cost nobody anything. `--shadow-2` failed the same test — no shadow-scale
name is in the set — and stays out, documented as a page-to-theme coupling
rather than promoted on the strength of two pages' usage.

The `--pb-*` family is deliberately **excluded**, and it is now read by
**six** pages rather than one — every hand-authored page that links a theme
stylesheet except `privacy.html` and `rororo-plugins.html`. That count is
the paragraph a from-scratch theme author most needs, because excluded from
the contract means a theme can satisfy all 47 required names and define not
one `--pb-*`. The original case: `press.html`'s
`.asset-preview` background reads `var(--pb-field)`, Phosphor Blueprint's
own treatment-layer token (defined in both `tokens.css`'s and
`utility.css`'s "Phosphor Blueprint — treatment layer" section, never in
the shared base). It's a real, live coupling — a pre-existing leak of
theme-specific naming into a "page-specific" residual rule that arguably
shouldn't be there at all — but it isn't a base-vocabulary name any future
theme is obligated to define under that exact prefix, so it's out of
`REQUIRED_TOKENS`. Flagged here as a known finding, not fixed: retrofitting
`press.html`'s `.asset-preview` onto a theme-neutral name is unrelated scope
this fix wave didn't touch.

`thesis.html`, `workflow.html`, `conundrum.html`, `rororo.html` and
`mod-launcher-games.html` extend that same coupling, and knowingly. Each
reads between five and nine `--pb-*` names in its own treatment rules
(`--pb-field`, `--pb-grid-fine`, `--pb-grid-coarse`, `--pb-scanline`,
`--pb-bloom-cyan`, and on the three product pages also `--pb-hairline`,
`--pb-panel-border`, plus `--pb-panel`/`--pb-trail` on two of them). Those
names now resolve from the theme rather than a private copy — the coupling
moved from "unreachable" to "theme-owned" — but they remain
Phosphor-Blueprint-specific and out of `REQUIRED_TOKENS`. A theme built by
mirroring `themes/phosphor-blueprint/`, which is what the build
instructions say to do, inherits them.

**And a theme written from scratch no longer breaks those pages, which it
used to.** Excluding a name from the contract while pages read it bare is a
gate that grades a strict subset of what the pages need: a from-scratch
theme defining all 47 required tokens passed `theme-doctor --browser
--require-browser` (an unresolved `var()` logs no console error and causes
no horizontal scroll), rotated in unattended, and then
`body { background: <gradients>, var(--pb-field) }` went
invalid-at-computed-value-time and resolved to **transparent** — five pages
rendering light-grey text on browser-default white, every gate green.

Every `--pb-*` read now carries a fallback. Structural ones fall through to
the contracted token behind them (`var(--pb-field, var(--bg-0))`,
`var(--pb-hairline, var(--border-1))`); decorative ones fall through to
`transparent` or `none`, so the treatment simply does not appear rather
than painting Phosphor Blueprint's cyan over a theme that never asked for
it. The three product pages express this as page-local `--page-*` aliases
declared once and read many times; the reading pair and `press.html` inline
the fallback at their two or three read sites. Pinned by
`test_no_converted_page_renders_broken_under_a_contract_satisfying_theme`,
which parses every `var()` on every converted page and requires each name
to be contracted, page-declared, or fallback-guarded.

The same round removed the other half of that defect: no converted page
redefines a contracted token any more. `conundrum.html`, `rororo.html` and
`mod-launcher-games.html` each carried
`:root { --bg-0: var(--pb-field); --border-1: var(--pb-hairline); … }`
*after* the theme's `<link>`, so a new theme could define those three
perfectly and still not reach the page —
"a copy the rotation cannot reach", one indirection deeper than the private
`:root` blocks it replaced. Pinned by
`test_no_converted_page_overrides_a_contracted_token`.

### The 47 required tokens, grouped, and why each group matters

| Group | Tokens | Why required |
|---|---|---|
| Backgrounds | `--bg-0`, `--bg-1`, `--bg-2` | Page and card-surface fields. Undefined = transparent surfaces over whatever's behind them. |
| Foreground / text | `--fg-1`, `--fg-2`, `--fg-3`, `--fg-muted`, `--text`, `--text-sec`, `--text-dim`, `--text-mute` | Body/heading/secondary/meta text colors. `--fg-*` is what markup actually uses; `--text*` is what `--fg-*` resolves through (see `--fg-1: var(--text)` in `tokens.css`) — both layers are read directly somewhere in the seven pages, so both are required. Undefined = unreadable (browser default, usually black-on-black here). |
| Brand color + accent | `--cyan`, `--cyan-pale`, `--magenta`, `--magenta-pale`, `--navy-deep`, `--navy-mid`, `--navy-hi`, `--ink-950`, `--ok`, `--brand-gradient`, `--brand-gradient-soft` | The nav CTA, links, status pills, the two-tone gradient underline — the site's actual brand identity. Undefined = the pages stop looking like 626 Labs at all, not just "wrong theme." |
| Borders + panel effects | `--border-1`, `--border-2`, `--border-accent`, `--inner-stroke` | Card/nav/footer hairlines and the inset highlight every panel uses. Undefined = flat, seamless panels with no separation. |
| Typography | `--font-display`, `--font-body`, `--font-mono` | The three-typeface stack (Space Grotesk / Inter / JetBrains Mono) every heading, body line, and meta label is set in. Undefined = browser default serif/sans, breaking the brand's whole type identity. |
| Motion | `--dur-fast`, `--dur-med`, `--ease-out` | Every hover/transition's duration and easing curve. Undefined = instant, jarring state changes (CSS transition properties silently no-op without a valid duration). |
| Spacing scale | `--s-2` … `--s-16` (9 steps) | Every padding/gap/margin value in the gallery cards, nav, footer, and page-hero. Undefined = collapsed layout (padding/gap resolve to nothing). |
| Radius scale | `--r-xs`, `--r-sm`, `--r-md`, `--r-lg`, `--r-xl`, `--r-pill` | Every rounded corner — cards, pills, buttons. Undefined = square corners everywhere, a small but immediately-visible "something's broken" tell. |

Phosphor Blueprint's own `tokens.css` was, until this fix, an "append-only
override" that only ever redefined `--bg-0`/`--bg-1`/`--bg-2`/`--border-1`/
`--border-2` — the other 38 required properties were silently covered by
`index.html`'s and `themes.html`'s own hardcoded local `:root` fallback, not
by the theme file at all. **This is exactly the gap the review flagged**,
and PB itself was the proof: run the new gate against PB's tokens.css as it
shipped, and it fails 38 of the 43 required at the time. The fix extended
`tokens.css` to be
self-contained — the same full base block `archetypes/utility.css` already
carried (verified value-for-value identical against both `index.html`'s and
`themes.html`'s hardcoded copies before the edit, so this is additive only,
confirmed zero pixel change) — with the existing treatment-layer `:root`
kept exactly as-is, still winning the cascade for the five properties it
overrides. `archetypes/utility.css` needed no changes: it was already
self-contained (0 missing), because it was extracted, in full, from
`press.html` back in A4 — the pattern `tokens.css` is only now catching up
to.

**The finding, stated plainly:** `tokens.css`'s "append-only, base system
stays intact" framing was only ever true because something else — page-
local hardcoded CSS, never itself a theme-owned artifact — was silently
doing the "intact base" work. A September theme designed against
`tokens.css`'s old docstring alone (redefine what you want to change, ignore
the rest) would have shipped broken, not by a mistake in its own file, but
by trusting a contract that was never actually enforced. `REQUIRED_TOKENS`
makes `tokens.css` (and `utility.css`) the real, self-sufficient source of
truth the docstring always claimed them to be.

## Screenshots and the self-dressing gallery (A8)

Every theme gets one deterministic PNG at `assets/themes/<slug>.png`
(1440x900) — `capture_theme_screenshot(slug, out_path)` in
`scripts/freeze-theme.py`, alongside `freeze()` since the rotation workflow
already invokes this file and the two capabilities are otherwise unrelated.
Deterministic means fixed viewport, `document.fonts.ready` awaited,
`reduced_motion="reduce"` (Playwright emulates the media query
`index.html`'s own CSS already collapses every animation/transition under),
AND a Playwright `add_init_script` that runs before any page script:
`Math.random` is replaced with a fixed-seed generator and the animation
clock is frozen (`performance.now()` returns a constant, and every
`requestAnimationFrame` callback is handed that same constant). Reuses
theme-doctor.py's own harness shape (a local static server serving the
repo root, `render-hub.py --theme <slug> --out <tmp>` for the preview)
rather than inventing a second one, without a runtime import dependency
between the two files.

**The contract, for whoever adds a theme with dynamic content next:** a
capture's determinism must never depend on what happens to be visible in
the 1440x900 viewport, or on a page's own JS correctly gating its
randomness/timing behind `prefers-reduced-motion`. It's enforced at the
capture layer instead — `_DETERMINISTIC_CAPTURE_INIT_SCRIPT` neutralizes
`Math.random`/`performance.now`/`requestAnimationFrame` for every page this
function loads, unconditionally. Proven honestly: capturing the same theme
twice with `full_page=True` (which pulls in sections a viewport-only
thumbnail never renders — Phosphor Blueprint's own home archetype has two
real, unconditional sources of frame-to-frame variance below the fold, an
unseeded `Math.random()` shuffle in the Lab section and a
`performance.now()`-driven canvas reveal in the About star map) and
sha256-comparing: identical. A viewport-only capture (what the gallery
thumbnail actually uses) was already identical before this fix too, purely
because those two sections happened to sit below the fold — the
`full_page=True` proof is what makes determinism a property of the capture
mechanism rather than of today's layout.

**Path convention:** `/assets/themes/<slug>.png`, keyed by slug alone — a
theme's screenshot is captured once (retiring OR going live, whichever
happens first) and never recaptured; an archived theme's card keeps
pointing at the same file forever. `themes.html`'s cards
(`render-hub.py`'s `_theme_thumbnail_href`/`_render_theme_card`) show the
`<img>` when that file exists and render cleanly without one otherwise —
Phosphor Blueprint had none until this task's manual first capture.

**CLI:** `python scripts/freeze-theme.py --screenshot <slug> <out_path>`,
alongside the existing `<YYYY-MM>` freeze form.

**Rotation wiring:** `rotate-theme.yml`'s freeze step captures the retiring
theme (the slug read fresh off the registry before rotation touches it);
a new step after "Render the new active theme" captures the incoming one.
Playwright installs earlier in the job now (both captures need it, not
just the theme-doctor browser gate).

**Carried requirement closed (flagged by A5):** `rotate-theme.yml` never
called `render-plugin-pages.py` — a live rotation would rotate the registry
and re-render `index.html`/`themes.html`/etc. but leave the 15 per-plugin
pages dressed in whichever theme was active the last time someone ran that
script by hand (they inline CSS from the active theme's
`archetypes/product.css`, per A5). Now wired into the same "Render the new
active theme" step, with its own `--check` drift gate alongside
`render-hub.py --check`.

**A second, related gap found and fixed the same way:** auditing what a
rotation actually writes vs. what the workflow committed turned up that
`press.html`/`privacy.html` (their `theme-css` link, A4) and `about.html`
(its easter-egg theme registry, A7) are ALSO rewritten by `render-hub.py`
on every rotation, but were never in the `git add` list — so a live
rotation would update them on the runner's disk and never persist it. Both
gaps closed in the same commit: the plugin pages (via a self-maintaining
`vibe-*`/`thesis-engine`/`plugins` glob, so a future plugin doesn't need a
hand-edit here) and `press.html`/`privacy.html`/`about.html` join the
commit list, alongside `assets/themes` for the new screenshots.
