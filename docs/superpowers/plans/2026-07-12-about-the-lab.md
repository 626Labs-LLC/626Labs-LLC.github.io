# About The Lab Implementation Plan (sub-project C)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the founding story — a 3-sheet treatment bake-off, the prose (one piece, two cuts), then about.html + homepage section 02 + the section 06 door, gated on Este's prose approval and treatment verdict.

**Architecture:** Sheets extend the existing editorial layer (`Design/editorial.css`, `--ed-*` tokens) with per-direction `--at-*` tokens, judged on identical real transcript excerpts. Prose drafts in the publishing work under the transcript-only sourcing rule. Site surfaces build only after both human gates. Spec: `docs/superpowers/specs/2026-07-12-about-the-lab-design.md`.

**Tech Stack:** Hand-written HTML/CSS (sheets + page), Python (checker, renderer, pytest), publishing-suite markdown.

## Global Constraints

- **Branch:** `feat/about-the-lab` from fresh `origin/main`. Commit trailer everywhere: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`; conventional commits; no emoji.
- **Source of truth:** `C:\Users\estev\Projects\626Labs-Publishing\works\2026-07-11-founding-interview\interview\founding-interview-transcript.md`. Every biographical claim traces to a transcript line. If a fact is missing, STOP and ask — never infer.
- **Privacy (absolute):** the full ten-digit phone number in Q7 NEVER appears in any deliverable — the "626 exchange" story is the public part. The employer is never named (role titles like "Area General Manager," "CIO," "CFO" are fine per Q12).
- **Design directives (from the transcript, binding):** the page is an HEIRLOOM — lineage, not corporate longevity (Q25); "soften the institution feel" (Q26); succession is proven — Stage Productions carried by the siblings (Q28).
- **Sheets:** extend `Design/editorial.css` (--ed-*) + `Design/colors_and_type.css` base tokens; new values only as `--at-<slug>-*` custom properties declared in the sheet's own `:root`; WCAG AA contrast for all text; no horizontal scroll at 1440/768/390; no emoji; identical specimen content across all three.
- **Execution stops after Task C6.** Tasks C7-C9 run ONLY after Este approves the prose and picks the treatment. Do not simulate his verdicts.
- **Both renderers + pytest + `site-doctor.py --check` gate any site change** (`--report` for humans). Never hand-edit inside SITE_JSON zones. GitNexus MCP unavailable this session — renderer edits stay additive-function-scoped as in prior efforts.
- **Ship report for C9 ends with:** `https://626labs.dev/about.html` for GSC Request Indexing.

## File map

| File | Task | Responsibility |
|---|---|---|
| `Design/explorations/2026-07-12-about-treatments/specimen.md` | C1 | The identical judging content, curated once |
| `.../check-tokens.py`, `.../index.html` | C1 | Token gate + judging gallery |
| `.../sheet-family-ledger.html` | C2 | Direction 1 |
| `.../sheet-foundation-wall.html` | C3 | Direction 2 |
| `.../sheet-long-now-terminal.html` | C4 | Direction 3 |
| Publishing `01_POSTS/2026-07-12-about-the-lab/body.md`, `condensed-cut.md`, `claims-audit.md` | C5 | The piece, two cuts, claim audit |
| `.../judging-README.md` + screenshots (scratchpad) | C6 | Este's judging packet |
| `about.html` | C7 | The heirloom page (static editorial, class-3 root page) |
| `content/site.json` (`founding` key, `about` door), `scripts/render-hub.py` (`render_founding`), `index.html` (zone markers, static), `tests/test_render_hub.py` | C8 | Homepage surfaces |
| — | C9 | Verify + PR (held) |

---

### Task C1: Bake-off scaffold — specimen pack, token checker, gallery skeleton

**Files:**
- Create: `Design/explorations/2026-07-12-about-treatments/specimen.md`, `check-tokens.py`, `index.html`

**Interfaces:**
- Produces: `specimen.md` — the EXACT content every sheet renders; `check-tokens.py <sheet.html>` exits 0/1; `index.html` gallery with three placeholder rows (each sheet task fills its own row).

- [ ] **Step 1: Curate the specimen pack** — read the transcript and extract VERBATIM (typos preserved) into `specimen.md` with these sections and nothing else:
  1. *Epigraph* — the Q30 exchange: "You are going to do it. You know you can, now just do it." + the follow-up ("He would just ask how and I would pretend that the call was breaking up and leave").
  2. *Founding night* — from Q1: the sentence beginning "So I finished my last maual report August 8th at 3:45..." through "...11 months later." Plus the Q11 answer (the 45-minute break, the 3-day bug) in full.
  3. *The name* — from Q7: from "626, i think this part of the number is called the exchange..." through "...the house, the heart." EXCLUDING the first sentence that contains the full phone number (privacy rule — verify no 10-digit or 7-digit number appears anywhere in specimen.md).
  4. *A values scene* — the Q16 answer (the father, the Bose clone) in full.
  5. *Keystone quotes* (pull-quote specimens): "I build tools, because care doesn't always scale"; "How do I want them to remember me, like a monkey's paw or their favorite genie"; "It's not a drawer it is an arsenal of repositories".
  6. *Artifact block* — factual card copy: "PriceScoutalpha.ipynb — the founding night's notebook. August 8th, 3:45 pm to 10:45 pm. 300 KB. Preserved."
  7. *A lineage close* — from Q25: "In a thousand years none of this may matter much..." through "...then that is it" + from Q28: "My kids will inherit it the same way each of my siblings is carrying on Stage Productions."
  Guard at top of file: `<!-- SPECIMEN — verbatim transcript excerpts. Do not edit wording. No phone numbers, no employer name. -->`

- [ ] **Step 2: Write check-tokens.py** — standalone, no deps:

```python
#!/usr/bin/env python3
"""Token gate for the about-treatment sheets.

A sheet passes when every color literal it uses is either (a) a var() of an
--ed-* / --brand-* / --ink-* / --at-<slug>-* token, or (b) a raw color that
appears ONLY inside the sheet's own :root { } block defining --at-* tokens.
Raw hex/rgb/hsl anywhere else fails. Usage: check-tokens.py sheet.html
"""
import re, sys
from pathlib import Path

src = Path(sys.argv[1]).read_text(encoding="utf-8")
root_blocks = re.findall(r":root\s*\{[^}]*\}", src)
declared = "\n".join(root_blocks)
body = src
for b in root_blocks:
    body = body.replace(b, "")
COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|hsla?\([^)]*\)")
loose = [m for m in COLOR.findall(body)]
bad_decl = [m for m in COLOR.findall(declared)
            if not re.search(r"--at-[a-z0-9-]+\s*:\s*" + re.escape(m), declared)
            and not re.search(r"--ed-|--brand-|--ink-", declared)]
if loose:
    print(f"FAIL {sys.argv[1]}: {len(loose)} raw color(s) outside :root --at-* declarations:")
    for m in sorted(set(loose)):
        print("  ", m)
    sys.exit(1)
print(f"PASS {sys.argv[1]}: colors confined to declared tokens.")
```
(If the implemented regex proves too loose/strict against a real sheet, tighten it in THIS task's scope and document the change — the contract is the docstring, not the draft regex.)

- [ ] **Step 3: Gallery skeleton** — `index.html`: minimal light page (editorial tokens via relative `../../editorial.css` import if resolvable when served from repo root; otherwise inline the needed few) titled "About The Lab — treatment bake-off (2026-07-12)", intro line ("Three directions, one specimen, rubric line one: soften the institution"), and three placeholder card rows with slugs `family-ledger`, `foundation-wall`, `long-now-terminal` (name + one-line thesis + link, each filled in by its sheet's task).

- [ ] **Step 4: Verify + commit** — `python Design/explorations/2026-07-12-about-treatments/check-tokens.py` on a tiny inline test string is impractical; instead verify it fails on a scratch file containing a loose `#123456` and passes on one with the hex inside `:root { --at-test-x: #123456; }`. Grep specimen.md: zero matches for `[0-9]{7}` (no phone fragments). Commit:
```bash
git add Design/explorations/2026-07-12-about-treatments/
git commit -m "feat(design): about-treatment bake-off scaffold — specimen, token gate, gallery

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Tasks C2 / C3 / C4: The three sheets (one task each, sequential)

**Files (per task):**
- Create: `Design/explorations/2026-07-12-about-treatments/sheet-<slug>.html`
- Modify: `.../index.html` (fill own gallery row only)

**Interfaces:**
- Consumes: `specimen.md` (render ALL seven sections, verbatim), `check-tokens.py`, `Design/editorial.css` tokens (link it via `/Design/editorial.css` when served from repo root — mirror how the sheet is meant to be viewed: `python -m http.server 8631` at REPO ROOT, browse `/Design/explorations/2026-07-12-about-treatments/sheet-<slug>.html`; fonts are root-absolute).
- Produces: one self-contained-except-shared-CSS sheet that a judge can open and feel the direction.

Direction briefs (each sheet takes ONE):

- **C2 `family-ledger` — The Family Ledger.** An heirloom registry: `--ed-paper` warm surface, engraved hairline rules, folio numbers in the margins, a ledger-style entry table (date · entry · initials) rendering the founding-night timeline, small-caps section openers, an "EST." mark. Type: editorial serif body (whatever editorial.css establishes; if it has no serif stack, declare `--at-ledger-serif: Georgia, 'Times New Roman', serif` and note it as a promotion candidate). Feel: a document a family keeps in a fireproof box, typeset in 3026.
- **C3 `foundation-wall` — The Foundation Wall.** Museum-placard institutional warmth: wide-margin plaques (cards with inset borders), donor-wall typography (tracked-out small caps for names/dates), captions under every quote like exhibit labels, a subtle brass/bronze accent declared as `--at-wall-brass` (AA-checked on paper). Feel: the lobby wall of an institution that is proud, not cold.
- **C4 `long-now-terminal` — The Long Now Terminal.** The 3026 records-room read: LIGHT surface (this is the editorial register — no PB scanlines, no dark field), monospace metadata rails (record ids, retrieval dates like "RETRIEVED 3026-07-12"), archive-catalog headers, restrained cyan links from `--ed-link`, generous whitespace. Institutional futurism that a PB fan recognizes as kin without one scanline. Declare any new values as `--at-lnt-*`.

Steps (identical per task):
- [ ] **Step 1:** Build the sheet: all seven specimen sections in the direction's voice — epigraph treatment, founding-night passage as body prose, the name section, the values scene, all three pull-quotes (styled as the direction's quote form), the artifact card, the lineage close. Verbatim text from specimen.md — zero wording edits.
- [ ] **Step 2:** Gate: `python .../check-tokens.py .../sheet-<slug>.html` → PASS. AA check: for every text/background token pair used, compute contrast (implementer computes ratios for the declared `--at-*` values against their backgrounds and lists them in an HTML comment atop the sheet; every body-text pair ≥ 4.5:1, large-display pairs ≥ 3:1).
- [ ] **Step 3:** Serve from repo root, verify: fonts load (no system-font fallback — check computed font-family via Playwright if available, else note structural-only), no horizontal scroll at 1440/768/390 (Playwright resize or CSS review), all seven sections present (`grep` count section markers).
- [ ] **Step 4:** Fill own row in index.html (name, one-line thesis, link). Commit `feat(design): <direction> sheet` + trailer.

---

### Task C5: The prose — one piece, two cuts (fable-tier writer)

**Files (Publishing repo, files-on-disk, no git):**
- Create: `C:\Users\estev\Projects\626Labs-Publishing\works\2026-07-11-founding-interview\01_POSTS\2026-07-12-about-the-lab\body.md` (full cut), `condensed-cut.md`, `claims-audit.md`

**Interfaces:**
- Consumes: the transcript (sole source) + the work's CLAUDE.md persona.
- Produces: the two cuts Este reviews; C7/C8 consume the APPROVED versions verbatim.

- [ ] **Step 1: Full cut** (~1,200-1,800 words), first person (it is Este's story), heirloom register, arc per the spec: the house that shouldn't have had a Nintendo → the exchange read off unpainted buildings → the founding night to the hour (worked at 10:45, broke at 11:30, certainty end of week one) → the values through their scenes (Bose cabinet; "too smart for the job"; workers/users/builders; erase workflows not jobs) → machines as colleagues ("best effort is the standard") → the arsenal → the close: Stage Productions already carried by the siblings; "maybe that 7 can be 8, even one more is a win." Pull-quotes: care-doesn't-scale, monkey's-paw/genie, arsenal. Epigraph: the Q30 exchange verbatim including the broken call. House voice rules; no emoji; the artifact (PriceScoutalpha.ipynb) referenced in an artifact block.
- [ ] **Step 2: Condensed cut** — 200-300 words + ONE pull-quote + a closing door line ("Read the whole story" pointing at /about.html). Cut from the full text, not rewritten.
- [ ] **Step 3: Claims audit** — `claims-audit.md`: a table, one row per biographical claim in either cut → the transcript question (Q#) and quoted line it traces to. Any claim without a row gets deleted from the draft. Verify: zero occurrences of any 7+ digit number; zero employer names; the word "vasectomy" and the seventh child are PERSONAL-tier facts — include only if a transcript line supports and the framing is the one Este used ("Lucky number 7" is on record; medical detail stays out of the published cuts — cite the motivation without the surgery).
- [ ] **Step 4:** Report DONE. **No publication step — Este reviews these files directly.**

---

### Task C6: Judging packet

**Files:**
- Create: `Design/explorations/2026-07-12-about-treatments/judging-README.md`; screenshots to the session scratchpad.

- [ ] **Step 1:** Run `check-tokens.py` on all three sheets (all PASS). Serve repo root; Playwright screenshots of each sheet at 1440 and 390 (6 files, scratchpad).
- [ ] **Step 2:** `judging-README.md`: how to view (serve from repo root — fonts are root-absolute), the rubric (1. soften the institution; 2. heirloom not monument; 3. would a 3026 descendant feel addressed; 4. AA + no h-scroll verified), one-paragraph case FOR each direction, and the verdict format (keep/kill/remix, PB-round style). Commit + push branch; report ends with sheet URLs + prose file paths for Este.
- [ ] **STOP. Execution halts here for Este's two gates: prose approval (edits welcome — the approved text is what ships) and treatment verdict.**

---

### Task C7 (post-gate): about.html

**Files:**
- Create: `about.html` (repo root)

**Interfaces:**
- Consumes: the WINNING sheet's treatment (its `--at-*` block + patterns) and the APPROVED full cut verbatim.
- Produces: the live page C8's door links to.

- [ ] **Step 1:** Build `about.html` as a hand-authored class-3 root page (same class as thesis.html/workflow.html — static editorial, NO SITE_JSON zones; the essay changes rarely and through the same review rigor): head with title "About the Lab · 626 Labs", description from the condensed cut's first sentence, canonical `https://626labs.dev/about.html`, og:image `https://626labs.dev/assets/brand/medium-header-1500x600.png` (existing brand fallback — a bespoke OG card is a follow-up); the winning treatment's styles (link `/Design/editorial.css` + inline the sheet's `--at-*` block and structural CSS); standard top nav (match press.html's nav pattern, links Home / Plugins / the Field Notes anchor); the approved full cut with its pull-quotes, artifact block (name/date/size — the raw .ipynb is NOT hosted), epigraph; footer + GoatCounter snippet (copy the exact block from press.html).
- [ ] **Step 2:** Verify: serve, no h-scroll at 1440/768/390, zero console errors, `python scripts/render-hub.py` (sitemap gains /about.html), `--check` clean after committing the regenerated sitemap.xml, doctor `--report` PASS (watch the dangling-asset walk — any image referenced must exist).
- [ ] **Step 3:** Commit `feat(site): about.html — About the Lab, the founding story` + trailer (include sitemap.xml).

---

### Task C8 (post-gate): homepage surfaces — founding key, render_founding, the door

**Files:**
- Modify: `content/site.json`, `scripts/render-hub.py`, `index.html` (static zone markers), `tests/test_render_hub.py`

**Interfaces:**
- Consumes: the APPROVED condensed cut.
- Produces: `render_founding(founding: dict) -> str`; site.json key shape below; section 06 door.

- [ ] **Step 1 (TDD):** tests first:
```python
def _founding():
    return {"eyebrow": "02 · The founding", "headline": "It started with a Nintendo",
            "quote": "I build tools, because care doesn't always scale",
            "paragraphs": ["<strong>First</strong> para.", "Second para."],
            "door": {"label": "Read the whole story", "href": "about.html"}}

def test_founding_renders_section_with_door():
    html = render_hub.render_founding(_founding())
    assert 'id="founding"' in html and 'href="about.html"' in html
    assert "Read the whole story" in html and "care doesn" in html

def test_founding_paragraphs_render_raw_html():
    assert "<strong>First</strong>" in render_hub.render_founding(_founding())
```
Run focused → FAIL (no attribute). Implement `render_founding` mirroring the retired `render_thinking`'s section structure (same classes: `section thinking`-style wrapper is fine to reuse or clone as `section founding` — match what the static CSS already styles; check index.html's static styles for the old `.thinking` rules and reuse those class names so no new CSS is needed, with `id="founding"`). Paragraphs raw HTML (site.json convention), eyebrow/headline/quote escaped, door via `attr()`/`esc()`.
- [ ] **Step 2:** Static shell: in index.html, at the dormant thinking zone's location, add `<!-- SITE_JSON:founding:start --><!-- SITE_JSON:founding:end -->` markers (the thinking markers STAY, dormant — additive, no removal). main(): `out = substitute_zone(out, "founding", render_founding(content["founding"]) if "founding" in content else "")`; add `"founding": "founding"` to SECTION_IDS; `--check` list unchanged (index.html covers it).
- [ ] **Step 3:** site.json: add `founding` key (approved condensed cut in the Step-1 shape; eyebrow numbered `02 · ...` so numbering heals) + `sections.founding: {"enabled": true}` + section 06 door: trim `about.paragraphs` to the approved door copy and add the story link (inspect `render_about` first: if it renders a link field, use it; else append the door as the final paragraph's closing sentence with an inline `<a href="about.html">`).
- [ ] **Step 4:** Gates: render (index rebuilt), `--check` 0, full pytest (42+2), `render-plugin-pages.py` no-op, doctor `--report` PASS. Assert: `grep -c 'id="founding"' index.html` = 1; eyebrow sequence on the page reads 01, 02, 03... (grep the eyebrow strings in order).
- [ ] **Step 5:** Commit `feat(site): the founding story takes the crown — section 02 healed` + trailer.

---

### Task C9 (post-gate): verify + PR (held for Este)

- [ ] **Step 1:** Playwright: homepage (founding section renders, numbering healed, door works), about.html (desktop+mobile screenshots, epigraph + artifact block present, nav/footer links resolve), section 06 door link. Zero console errors.
- [ ] **Step 2:** Push; `gh pr create` — title `feat(site): About the Lab — the founding story ships`, body: what shipped, the two gates already passed (prose approved, treatment: <winner>), screenshots note, and the trailer `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. `gh pr checks --watch` green. **Do NOT merge.**
- [ ] **Step 3:** Report ends with: `https://626labs.dev/about.html` — GSC URL Inspection → Request Indexing after merge.

---

## Self-review notes

- **Spec coverage:** specimen/privacy (C1), three directions + AA + identical content (C2-4), one-piece-two-cuts + claims audit + personal-tier judgment (C5), judging packet + hard stop (C6), page as class-3 static + artifact-not-hosted + sitemap/GSC (C7), founding key + healed numbering + door (C8), held PR (C9). Notebook hosting, treatment promotion, syndication, #84 all excluded per spec.
- **Known deferred-by-design:** exact sheet CSS (creative work, briefed not dictated); render_about door mechanics (inspect-then-choose, both branches specified); checker regex may be tightened within C1.
- **Type consistency:** `founding` key shape identical in C8's fixture, implementation notes, and site.json step; slugs `family-ledger`/`foundation-wall`/`long-now-terminal` consistent across C1 gallery, C2-4 filenames, C6 packet.
