# Homepage Reshape + Founding Interview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse 14 plugin cards into one flagship family card (grid 23 → 10), move the plugin-framework thesis from homepage section 02 onto /plugins/, add per-plugin story beats there, and stand up the founding-interview work in the publishing suite.

**Architecture:** Presentation-level collapse — `products[]` stays intact; `render_products()` learns a grouping rule driven by a new site.json `pluginFamily` config. The thesis content migrates from site.json's `thinking` key into content/plugin-pages.json and renders on /plugins/ via render-plugin-pages.py. Sub-project B scaffolds `works/2026-07-11-founding-interview/` from BlogStudio and authors the interview guide. Spec: `docs/superpowers/specs/2026-07-11-homepage-reshape-and-founding-interview-design.md`.

**Tech Stack:** Python 3.11 (two renderers + pytest), hand-written HTML edits (static shells only), publishing-suite markdown.

## Global Constraints

- **Branch:** `feat/homepage-reshape` from fresh `origin/main` (`git fetch origin && git checkout -b feat/homepage-reshape origin/main`). Daily bots churn main.
- **Working dir:** `C:\Users\estev\Projects\626labs-hub` for A tasks; `C:\Users\estev\Projects\626Labs-Publishing` for B tasks. Absolute paths / `git -C` when crossing.
- **Commit trailer (every commit):** `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`; conventional commits; no emoji anywhere.
- **Do NOT delete or restructure any of the 14 plugin entries in `products[]`** — the collapse is render-level only. Site facts, doctor pins, star map, and per-plugin pages must keep deriving from them.
- **`/plugins/` is a touch-up, not a redesign** (Este: "already pretty good"). New sections follow the page's existing style variables and card idioms.
- **Count-free prose:** never hand-bake plugin counts into copy. The plugins page already derives its count (`num_word(len(family))`); keep that pattern.
- **TWO renderers, both gated:** any change to content/plugin-pages.json requires `python scripts/render-plugin-pages.py` AND the final gate is `python scripts/site-doctor.py --check` exit 0 (`--report` for humans — bare `--check` fails silently). render-hub `--check` alone is not sufficient.
- **No hand-edits inside `SITE_JSON:` zones** in index.html; static-shell edits (navs) are allowed.
- **Thinking-zone contract:** after this ships, site.json has NO `thinking` key, `sections.thinking.enabled` is `false`, and the zone renders empty. main() must not crash on the absent key.
- **A ships as a PR held for Este's eyes-on** (homepage identity change); B produces drafts only — the live interview session is scheduled with Este, never simulated.

## File map

| File | Action | Responsibility |
|---|---|---|
| `scripts/render-hub.py` | Modify | `render_products(products, plugin_family)` grouping; flagship head honors `productPage`; always-substitute thinking zone; family sigil/category/preview entries |
| `tests/test_render_hub.py` | Modify | Grouping unit tests |
| `content/site.json` | Modify | New top-level `pluginFamily`; hero `secondaryCta` retarget; `sections.thinking.enabled: false`; delete `thinking` key |
| `content/plugin-pages.json` | Modify | New `thesis` key (migrated content); `beat` field on all 14 `family[]` entries |
| `scripts/render-plugin-pages.py` | Modify | Render thesis section + beats on `/plugins/` |
| `index.html`, `plugins/index.html`, `sitemap.xml` | Regenerated | By the renderers — never hand-edited (except index.html static navs) |
| `index.html` (static nav, 2 spots), `conundrum.html`, `press.html`, `privacy.html` | Modify | Retarget `#thinking` anchors |
| `works/2026-07-11-founding-interview/` (Publishing) | Create | BlogStudio scaffold + persona + interview guide |

---

### Task A1: render_products grouping (TDD)

**Files:**
- Modify: `scripts/render-hub.py` (`render_products` at ~line 739; flagship head block at ~line 687-706; main() thinking zone at ~line 1745)
- Test: `tests/test_render_hub.py` (append)

**Interfaces:**
- Consumes: `render_product(p)` (existing, renders one card).
- Produces: `render_products(products: list[dict], plugin_family: dict | None = None) -> str`. `plugin_family` shape: `{"memberIds": [str], "card": {product-shaped dict}}`. The family card renders IN PLACE of the first member encountered; all other members are skipped; non-members render unchanged in order. `None`/missing config → identical output to today. Also: flagship cards whose dict has `productPage` render the head link to it with `productPageLabel` (falling back to today's "Open repo" + repo behavior); main() always substitutes the thinking zone, empty when the key is absent.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_render_hub.py`)

```python
# ─── plugin-family grouping ─────────────────────────────────────────

def _products():
    mk = lambda i: {"id": i, "title": i, "description": "d", "tags": [], "status": "live"}
    return [mk("celestia-3"), mk("vibe-cartographer"), mk("vibe-doc"),
            mk("rororo"), mk("vibe-test"), mk("conundrum")]


def _family():
    return {
        "memberIds": ["vibe-cartographer", "vibe-doc", "vibe-test"],
        "card": {"id": "vibe-family", "title": "The Vibe Plugin Family",
                 "description": "One playbook.", "tags": [], "status": "live",
                 "flagship": True, "repo": "estevanhernandez-stack-ed/vibe-plugins",
                 "productPage": "plugins/", "productPageLabel": "Meet the family"},
    }


def test_family_grouping_collapses_members_in_place():
    html = render_hub.render_products(_products(), _family())
    assert html.count('<article class="product') == 4          # 3 non-members + 1 family card
    assert "The Vibe Plugin Family" in html
    assert html.index("celestia-3") < html.index("The Vibe Plugin Family") < html.index("rororo")
    for member in ("vibe-doc", "vibe-test"):
        assert f"<h3>{member}</h3>" not in html


def test_family_grouping_absent_config_is_identity():
    prods = _products()
    assert render_hub.render_products(prods) == render_hub.render_products(prods, None)
    assert render_hub.render_products(prods).count('class="product') == 6


def test_family_flagship_head_links_product_page():
    html = render_hub.render_products(_products(), _family())
    assert 'href="plugins/"' in html
    assert "Meet the family" in html
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_render_hub.py -k family -v`
Expected: FAIL — `TypeError: render_products() takes 1 positional argument but 2 were given` (and/or missing assertions).

- [ ] **Step 3: Implement**

Replace `render_products` (line ~739):

```python
def render_products(products: list[dict], plugin_family: dict | None = None) -> str:
    """Product cards, with an optional presentation-level family collapse.

    plugin_family = {"memberIds": [...], "card": {...}} folds every member
    into one card, emitted at the FIRST member's grid position. products[]
    data is never mutated — facts, star map, and plugin pages keep deriving.
    """
    if not plugin_family:
        return "\n\n".join(render_product(p) for p in products)
    members = set(plugin_family.get("memberIds") or [])
    out, family_emitted = [], False
    for p in products:
        if p.get("id") in members:
            if not family_emitted:
                out.append(render_product(plugin_family["card"]))
                family_emitted = True
            continue
        out.append(render_product(p))
    return "\n\n".join(out)
```

In the flagship head block (line ~687-706), make the head link productPage-aware — replace the hardcoded repo anchor:

```python
        if p.get("productPage"):
            head_link = (
                f'<a class="product-link" href="{attr(p.get("productPage"))}">'
                f'{esc(p.get("productPageLabel") or "Open product page")} '
                '<svg class="ic arrow" viewBox="0 0 24 24"><path d="M7 17L17 7M7 7h10v10"/></svg></a>'
            )
        else:
            head_link = (
                f'<a class="product-link" href="https://github.com/{attr(p.get("repo", ""))}">'
                'Open repo '
                '<svg class="ic arrow" viewBox="0 0 24 24"><path d="M7 17L17 7M7 7h10v10"/></svg></a>'
            )
```
and interpolate `{head_link}` where the `<a class="product-link">…</a>` literal sat.

In main(): change the products call and the thinking zone —

```python
    out = substitute_zone(out, "products",
                          render_products(content["products"], content.get("pluginFamily")))
    ...
    out = substitute_zone(
        out, "thinking",
        render_thinking(content["thinking"]) if "thinking" in content else "")
```
(the thinking substitution replaces the current `if "thinking" in content:` guard so an absent key EMPTIES the zone instead of leaving stale content hidden in the DOM).

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/ -v` — all pass (existing 36 + 3 new). Then `python scripts/render-hub.py` — expect "index.html rebuilt": vibe-cartographer's flagship card already carries `productPage`, so its head link flips from "Open repo" to its product page. This interim drift is accepted-by-design (it's a correct improvement and the card folds away entirely at Task A4). Then `python scripts/render-hub.py --check` — exit 0. Commit the regenerated index.html with the two source files.

- [ ] **Step 5: Commit**

```bash
git add scripts/render-hub.py tests/test_render_hub.py
git commit -m "feat(render): plugin-family grouping + productPage-aware flagship head

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task A2: Family card identity — sigil, category, flagship preview

**Files:**
- Modify: `scripts/render-hub.py` (`PRODUCT_SIGILS` dict end ~line 286; `PRODUCT_CATEGORY_LABELS` ~line 353; `FLAGSHIP_PREVIEWS` ~line 288-360 region)

**Interfaces:**
- Consumes: the dict formats already in the file (LOOK at existing entries first and match exactly — sigils are `<svg class="ic-lg ic" viewBox="0 0 24 24">` path strings; previews are HTML blocks keyed by id).
- Produces: entries keyed `"vibe-family"` in all three dicts, consumed by Task A4's card config.

- [ ] **Step 1: Add the three entries**

Sigil (constellation — the family as connected stars, echoing the About star map):

```python
    "vibe-family": (
        # Constellation — the family as connected stars
        '<svg class="ic-lg ic" viewBox="0 0 24 24">'
        '<path d="M5 19l6-8 4 3 4-9"/>'
        '<path d="M5 19h.01M11 11h.01M15 14h.01M19 5h.01"/></svg>'
    ),
```

Category label: `"vibe-family": "SPEC-DRIVEN · SELF-EVOLVING · ONE PLAYBOOK",` (match the existing constant's string style — inspect the current vibe-cartographer entry and mirror its tone/format).

Flagship preview: study `FLAGSHIP_PREVIEWS["vibe-cartographer"]` (terminal mock + bullets) and write a family variant — same wrapper classes, terminal shows a family-flavored beat (`$ claude … /plan → /build → /wrap` style lines listing 3-4 plugin verbs), bullets name the family's jobs (plan, iterate, document, test, secure). Reuse the existing CSS classes verbatim; no new styles.

- [ ] **Step 2: Verify + commit**

Run: `python -m pytest tests/ -q` (pass; nothing consumes the entries yet) and `python -c "import importlib.util as i; s=i.spec_from_file_location('rh','scripts/render-hub.py'); m=i.module_from_spec(s); s.loader.exec_module(m); print('vibe-family' in m.PRODUCT_SIGILS, 'vibe-family' in m.FLAGSHIP_PREVIEWS)"` → `True True`.

```bash
git add scripts/render-hub.py
git commit -m "feat(render): vibe-family card identity — constellation sigil, category, preview

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task A3: The thesis moves to /plugins/ + per-plugin beats

**Files:**
- Modify: `content/plugin-pages.json` (new `thesis` key; `beat` on all 14 `family[]` entries)
- Modify: `scripts/render-plugin-pages.py` (`render_index` ~line 752; family-card loop ~line 756-765)
- Regenerated: `plugins/index.html`

**Interfaces:**
- Consumes: site.json's current `thinking` object (eyebrow, headline, lead, quote, paragraphs, cta, artifacts) — copy the CONTENT verbatim from `content/site.json` before Task A4 deletes it. Do not rewrite the essay.
- Produces: `/plugins/` renders the thesis section below the family grid; each family card shows its `beat`. Task A4 relies on the thesis being live here before it removes the homepage section.

- [ ] **Step 1: Migrate the thesis content**

Add to `content/plugin-pages.json` (top-level key, sibling of `family`): `"thesis": { ... }` — paste the exact object currently at site.json's `thinking` key (all fields: eyebrow → retitle to fit the page, e.g. `"The playbook"`, keep headline/lead/quote/paragraphs/cta/artifacts verbatim). The paragraphs contain raw HTML (`<strong>`) — plugin-pages.json already renders prose fields as raw HTML per its `$comment`; keep them unescaped like existing prose fields.

- [ ] **Step 2: Author the 14 beats**

Add `"beat": "<two lines max>"` to each `family[]` entry. Source each beat from that plugin's own page copy in the same file (`plugins[<id>].subhead` / `sections` — condense, don't invent). Voice: 626 working register, why-it-exists + what-it-pairs-with. Example shape (write all 14 for real): `"beat": "Maps an idea to a shipped v1 in eight steps. Hands the baton to vibe-iterate the day users show up."`

- [ ] **Step 3: Render them**

In `render_index`: (a) in the family-card loop add below the role/caps block —
```python
        beat_html = f'\n              <div class="fc-beat">{f["beat"]}</div>' if f.get("beat") else ""
```
interpolated after `{caps_html}` (beats are trusted content from our own JSON — raw HTML allowed like sibling prose fields); (b) after the family-grid section HTML, add a thesis section built from `data.get("thesis")` — eyebrow + h2 (headline) + lead + blockquote (quote) + paragraphs + cta link + artifact cards, using the page's existing `section-head`/`eyebrow`/container classes and a small `fc-beat`/`thesis` style block appended to `STYLE` (match the page's existing CSS variable usage; no new palette values). Collapse to nothing when `thesis` is absent.

- [ ] **Step 4: Render + verify + commit**

Run: `python scripts/render-plugin-pages.py` → `plugins/index.html` rebuilt (per-plugin pages unchanged). Then `python scripts/site-doctor.py --report` → PASS; `grep -c "fc-beat" plugins/index.html` → 14; the thesis headline appears once. Eyeball at `http://localhost:8631/plugins/` (`python -m http.server 8631`, then stop it).

```bash
git add content/plugin-pages.json scripts/render-plugin-pages.py plugins/index.html
git commit -m "feat(plugins): thesis moves home + per-plugin story beats

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task A4: Flip the homepage — site.json config + anchor retargets

**Files:**
- Modify: `content/site.json` (add `pluginFamily`; hero.secondaryCta.href; sections.thinking.enabled false; DELETE `thinking` key)
- Modify: `index.html` static navs (lines ~1695 and ~2806, outside zones), `conundrum.html:248`, `press.html:555,787`, `privacy.html:424,589`
- Regenerated: `index.html` zones

**Interfaces:**
- Consumes: A1's `pluginFamily` contract, A2's `vibe-family` entries, A3's live thesis on /plugins/.
- Produces: the shipped 10-card grid. The `pluginFamily.card` is product-shaped and flagship.

- [ ] **Step 1: site.json edits**

Add top-level (sibling of `products`):

```json
"pluginFamily": {
  "memberIds": ["vibe-cartographer", "vibe-iterate", "vibe-insights", "vibe-keystone",
                "vibe-doc", "vibe-test", "vibe-thesis", "thesis-engine", "vibe-sec",
                "vibe-taker", "vibe-wrap", "vibe-walk", "vibe-prompt", "vibe-lingual"],
  "card": {
    "id": "vibe-family",
    "title": "The Vibe Plugin Family",
    "description": "One coordinated family of Claude Code plugins — planning, iteration, docs, tests, security, research authoring — installed independently, composed when present. Every plugin follows the same Apache-licensed playbook: self-repair, self-teach, self-evolve, so the tenth run beats the first. {{fact:claude_plugins}} plugins, one spine.",
    "tags": [
      {"label": "Claude Code", "tone": "cyan"},
      {"label": "plugin family", "tone": "magenta"},
      {"label": "self-evolving", "tone": "cyan"},
      {"label": "Live", "tone": "live"}
    ],
    "status": "live",
    "flagship": true,
    "repo": "estevanhernandez-stack-ed/vibe-plugins",
    "npm": null, "install": null, "storeUrl": null,
    "productPage": "plugins/",
    "productPageLabel": "Meet the family",
    "banner": null,
    "meta": "Claude Code · Apache-2.0 spec · one playbook",
    "screenshots": []
  }
}
```
(The `{{fact:claude_plugins}}` token keeps the count derived — an unknown token fails the render loudly, so verify it resolves.)

Then: `hero.secondaryCta.href`: `"#thinking"` → `"/plugins/"` (label stays "Read the thesis" — that's where it lives now). `sections.thinking.enabled`: `false` (add the key inside the existing `sections` object). Delete the entire top-level `thinking` key. Validate: `python -c "import json; json.load(open('content/site.json', encoding='utf-8'))"`.

- [ ] **Step 2: Static anchor retargets**

- `index.html` nav (~1695) and footer nav (~2806): `href="#thinking"` → `href="plugins/"`, label "Thinking" stays. These sit OUTSIDE zones — hand-edit is correct here.
- `conundrum.html:248`: the nav link labeled "Field Notes" points at `index.html#thinking` (mislabeled since birth). Find the Field Notes section's actual id in index.html (the section between the `SITE_JSON:stories` markers, ~line 2484 — grep `<section` there for its `id=`), and point the link at `index.html#<that-id>`.
- `press.html:555,787` and `privacy.html:424,589`: `index.html#thinking` → `plugins/`, labels stay "Thinking".

- [ ] **Step 3: Render + full gates**

```bash
python scripts/render-hub.py
python scripts/render-hub.py --check
python scripts/render-plugin-pages.py
python -m pytest tests/ -v
python scripts/site-doctor.py --report
```
Expected: index.html rebuilt; `--check` exit 0; all tests pass; doctor PASS (facts still derive — `claude_plugins` unchanged at 14). Asserts:
`grep -c 'class="product' index.html` → grid shows 10 cards (some matches are CSS/JS — count `<h3>` card titles instead if ambiguous: `grep -c "<h3>" index.html` within the products zone should be 10);
`grep -c 'The Vibe Plugin Family' index.html` → ≥1; `grep -c 'href="#thinking"' index.html` → 0; the thinking zone between its markers is empty and the section carries `hidden`.

- [ ] **Step 4: Commit**

```bash
git add content/site.json index.html conundrum.html press.html privacy.html plugins/index.html sitemap.xml
git commit -m "feat(site): one family card — grid 23 -> 10, thesis crown freed

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
(Include plugins/index.html / sitemap.xml only if the renderers actually changed them this task.)

---

### Task A5: Browser verification + PR (held for Este)

**Files:** none — verify and ship.

- [ ] **Step 1: Playwright pass** (serve `python -m http.server 8631` from repo root)

1. Homepage desktop 1280 + mobile 390 screenshots: 10 cards, family flagship card renders with preview, no section-02 gap artifacts (section hidden, no stray whitespace band), Field Notes rail intact.
2. Click-path checks: family card head link → `/plugins/`; hero "Read the thesis" → `/plugins/`; nav "Thinking" → `/plugins/`.
3. `/plugins/`: thesis section renders below the grid; 14 beats visible; per-plugin links still work (spot-check 3).
4. conundrum.html nav "Field Notes" lands on the stories section.
5. Console: no errors on either page.

- [ ] **Step 2: Push + PR — DO NOT MERGE**

```bash
git push -u origin feat/homepage-reshape
gh pr create --title "feat(site): homepage reshape — one plugin family card, thesis moves to /plugins/" --body "$(cat <<'EOF'
Grid 23 -> 10: the 14 Vibe plugins collapse into one flagship family card (constellation sigil, terminal preview, Meet the family -> /plugins/). The Self-Evolving Plugin Framework thesis leaves homepage section 02 and becomes the editorial spine of /plugins/, which also gains a two-line story beat per plugin. products[] data untouched — facts, star map, and all 14 plugin pages derive exactly as before.

Presentation-level collapse per spec: docs/superpowers/specs/2026-07-11-homepage-reshape-and-founding-interview-design.md

**Este, eyes-on before merge:** this changes the homepage's identity. Screenshots in the PR thread; the freed section-02 crown stays empty until the founding story (sub-project C) claims it.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
gh pr checks --watch
```
Post the four screenshots as a PR comment (`gh pr comment --body` with uploaded images, or reference scratchpad paths in the report). Expected: doctor CI green; PR stays open for Este.

---

### Task B1: Scaffold the founding-interview work (Publishing repo)

**Files:**
- Create: `C:\Users\estev\Projects\626Labs-Publishing\works\2026-07-11-founding-interview\` (from `studios\BlogStudio`)

- [ ] **Step 1: Scaffold per the umbrella convention**

Copy `studios/BlogStudio` → `works/2026-07-11-founding-interview/` (the convention is clone-the-studio-then-bootstrap; follow `studios/BlogStudio/.claude/skills/bootstrap/SKILL.md` — run its steps non-interactively using these answers: org = 626 Labs, work = founding interview, adapters = none yet, persona register = reflective founder-profile). Fill the work's `CLAUDE.md` persona: Field Notes pillars (Runnable Truth, Earned Hook, Recognizable Voice) kept, register shifted — first-person-interviewer, narrative over code snippets, no invented facts, transcript is the only source of biographical claims.

- [ ] **Step 2: Create the interview scaffold + README**

`mkdir interview` inside the work; add `README.md` stating: what this work is, the guide/transcript convention (mirrors `works/2026-05-28-build-day/interview/`), and that outputs feed sub-project C (About The Lab + headline article, specced separately).

- [ ] **Step 3: Commit** (if the works/ tree is git-tracked — the umbrella is orchestrator-only; check for a `.git` in the work after scaffold. If BlogStudio's clone carries one, commit there; if not, files-on-disk is the convention — say which happened in the report.)

---

### Task B2: Author the interview guide

**Files:**
- Create: `works\2026-07-11-founding-interview\interview\founding-interview-guide.md`

- [ ] **Step 1: Write the guide** — semi-structured, ~24-30 questions across these seven arcs (each arc: 3-5 questions with intent notes + follow-up prompts, Critical-Incident-Technique style like the build-day guide):

1. **Before the founding** — what Este was building/doing when the idea formed; the moment the lab became inevitable.
2. **The name and the ground** — 626, the 817, Fort Worth roots; why the outsider stance is load-bearing.
3. **The two sparks** — the internal AI-applications-lab proposal; Pricescout as the evidence that changed the argument.
4. **The values under the tenets** — Legitimize, Allow-them-to-do-it-themselves, Well-put-together, Humanely; where each came from in lived experience.
5. **Machines as colleagues** — the working style (agents, personas, the Architect); what it feels like day-to-day; what outsiders get wrong about it.
6. **The body of work** — plugins, apps, games, merch as one portfolio; what ties a sock shop to a security scanner.
7. **The thousand-year frame** — why a fast-shipping lab wants to read like an institution that has always existed; what 626 Labs looks like from 3026 looking back.

Each question written out in full, ending with a reflexivity-check bookend pair (opening: "what should I have asked", closing: "what did we miss") per the build-day methodology.

- [ ] **Step 2: Deliver for review** — the guide goes to Este for review (spec gate). The live session is scheduled by him; the transcript lands as `interview/founding-interview-transcript.md` during that session. NOT part of this plan's execution.

---

## Self-review notes

- **Spec coverage:** grid collapse (A1/A2/A4), presentation-level guarantee (A1 identity test + constraint), thesis migration (A3 content + A4 removal, ordered so the thesis is never homeless), touch-up beats (A3), section toggle + empty zone (A1 main() + A4), anchor retargets incl. the conundrum mislabel (A4), both-renderers gate (A3/A4), Playwright + held PR (A5), B scaffold + guide (B1/B2). C explicitly out of scope per spec.
- **Known judgment points left to implementers:** exact FLAGSHIP_PREVIEWS family markup (must mirror existing entry's classes), the 14 beat texts (sourced from existing copy, rule given), stories-section id (discovered by grep at A4 Step 2 — deliberate, the id is unverified tonight).
- **Type consistency:** `pluginFamily` shape identical in A1 tests, A1 implementation, and A4 config; `vibe-family` id consistent across A2 dicts and A4 card; `productPage: "plugins/"` matches A1's flagship-head test.
