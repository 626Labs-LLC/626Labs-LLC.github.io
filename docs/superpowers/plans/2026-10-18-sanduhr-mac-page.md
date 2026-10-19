# Sanduhr für Mac Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make /sanduhr/ the Mac build's page (Desk and the Claude config carry, reviewed through 2.27.0), move Windows to /sanduhr/windows/, and point the cask, the tap and the Sanduhr landing page at the hub page.

**Architecture:** Two hub PRs, then two one-file PRs in other repos. PR A teaches `release-review.py` tag families so two markers on one repo stop flagging each other. PR B is content: images into the page directories, the Windows `pages[]` entry, the rewritten `sanduhr` pageSpec, the home card, both renders. No renderer code changes; every section uses an existing block type.

**Tech Stack:** Python 3.13 (Pillow 12 for image conversion), the repo's `render-product-pages.py` / `render-hub.py` / `theme-doctor.py` / `site-doctor.py` pipeline, pytest, `gh`.

**Spec:** `docs/superpowers/specs/2026-10-18-sanduhr-mac-page-design.md`

## Global Constraints

- `content/site.json` is CRLF, edited as text only. Never `json.dumps` it. Keep two-space indentation and the surrounding style; the PR #238 diff is the model.
- Generated HTML (`sanduhr/index.html`, `sanduhr/windows/index.html`, `index.html`) is never hand-edited. Render order: `render-product-pages.py` then `render-hub.py`.
- Every product claim traces to one of: `gh release view v2.27.0-mac`, `docs/mods-and-config-spec.md`, `docs/config-transfer-spec.md`, `README.md`, `gh release view v3.4.3` (all Sanduhr repo, `origin/main`), or copy the 2.26.0 review kept on the current page.
- Banned words: `C:\Users\estev\Projects\626labs-marketing\docs\banned.md` tiers A and B. No emoji. No em-dashes except where already in kept copy; commas, periods, colons.
- No `"hand": true` on either page. The pinned heading `Desk, on a real Mac.` goes with it.
- `products[]` field names and the `sanduhr` id do not change. Values may.
- The Homebrew one-liner, verbatim everywhere: `brew install --cask estevanhernandez-stack-ed/tap/sanduhr`
- Store URL on pages: `https://apps.microsoft.com/detail/9NH3NK2RGCF5`. The home card keeps its `?cid=site-home` variant.
- Image budget: no single file over roughly 600 KB; Mac page images together under roughly 4 MB. Desktop captures become JPEG at 2000 px wide or less; UI captures stay PNG.
- The Sanduhr local clone is stale. Read sources with `git -C C:\Users\estev\Projects\Sanduhr show origin/main:<path>` and build its PR from a worktree off `origin/main`.
- Absolute paths and `git -C` for every command outside the hub. Verify `pwd` before `git`, `gh`, `python`.
- Dashboard writes carry `origin: "Dunder · Claude Code"`.

## Review Focus

1. A release tag the family regex does not match (`legacy/python-v2.3.0`, `untagged-...`) must keep today's date-only behavior, not vanish from or crash the run. Pinned in Task 1.
2. A marker on the Windows page (`v3.4.3`) must see the four-part `v3.3.0.0` as the same family (older, so ignored by date) and never see a `-mac` tag. Pinned in Task 1.
3. A visitor on a phone at 390 px must get no horizontal scroll on either page with the 2400-px-source hero showcase. Pinned by `theme-doctor --browser` in Task 6.
4. A relative `icon.png` on the nested Windows page must resolve at `/sanduhr/windows/icon.png`, not 404 into the console check. Pinned in Task 3 (the file exists and the render references it) and Task 6 (browser gate).
5. The Mac page must link the Windows page and the Windows page the Mac page, both as root-relative hrefs that survive being served from any directory. Pinned in Tasks 3 and 4.

---

### Task 1: release-review tag families (PR A)

**Files:**
- Modify: `scripts/release-review.py:85-101` (`releases_after`) and the module docstring
- Test: `tests/test_release_review.py`
- Modify: `CLAUDE.md:114` (the `release-review.yml` row)
- Add: `docs/superpowers/specs/2026-10-18-sanduhr-mac-page-design.md`, `docs/superpowers/plans/2026-10-18-sanduhr-mac-page.md` (this plan)

**Interfaces:**
- Produces: `TAG_FAMILY_RE: re.Pattern`, `tag_family(tag: str) -> str | None` (the suffix without its dash, `""` for a bare numeric tag, `None` when the tag is not `v?N.N[.N...][-suffix]`), and `releases_after()` filtered by family when the marker has one.

- [ ] **Step 1: Branch**

```bash
git -C C:\Users\estev\Projects\626labs-hub fetch origin && git -C C:\Users\estev\Projects\626labs-hub checkout -b ci/release-review-tag-families origin/main
```

- [ ] **Step 2: Write the failing tests** in `tests/test_release_review.py`, after `test_a_marker_tag_the_repo_lacks_fails_loudly`:

```python
FAMILIES = [
    rel("v2.27.0-mac", "2026-10-18T00:41:16Z"),
    rel("v2.26.1-mac", "2026-10-17T12:00:00Z"),
    rel("v2.26.0-mac", "2026-10-16T12:00:00Z"),
    rel("v3.4.3", "2026-10-11T15:36:06Z"),
    rel("v3.4.2", "2026-09-14T12:00:00Z"),
    rel("v3.3.0.0", "2026-07-19T12:00:00Z"),
    rel("v2.3.0-windows", "2026-05-06T12:00:00Z"),
    rel("legacy/python-v2.3.0", "2026-09-13T12:00:00Z"),
]


@pytest.mark.parametrize("tag,family", [
    ("v2.27.0-mac", "mac"), ("v2.3.0-windows", "windows"), ("v3.4.3", ""),
    ("v3.3.0.0", ""), ("3.4.3", ""), ("v1", None), ("legacy/python-v2.3.0", None),
    ("untagged-c6478f02e761a516871a", None),
])
def test_tag_family(tag, family):
    assert rr.tag_family(tag) == family


def test_a_suffixed_marker_sees_only_its_own_family():
    # Two pages mark one repo: the Mac page must not be flagged by v3.4.3.
    assert [r["tag_name"] for r in rr.releases_after("v2.26.0-mac", FAMILIES)] == ["v2.27.0-mac", "v2.26.1-mac"]


def test_a_bare_marker_sees_bare_and_four_part_tags_only():
    assert [r["tag_name"] for r in rr.releases_after("v3.4.2", FAMILIES)] == ["v3.4.3"]
    # v3.3.0.0 is the same family, older by date, so absent for the right reason.
    assert [r["tag_name"] for r in rr.releases_after("v3.3.0.0", FAMILIES)] == ["v3.4.3", "v3.4.2"]


def test_a_marker_outside_the_pattern_keeps_date_only_behavior():
    assert [r["tag_name"] for r in rr.releases_after("legacy/python-v2.3.0", FAMILIES)] == ["v2.27.0-mac", "v2.26.1-mac", "v2.26.0-mac"]
```

- [ ] **Step 3: Run them to see them fail**

Run: `python -m pytest tests/test_release_review.py -q -k "family or bare_marker or outside_the_pattern"`
Expected: FAIL, `AttributeError: module 'release_review' has no attribute 'tag_family'`

- [ ] **Step 4: Implement** in `scripts/release-review.py`, above `releases_after`:

```python
TAG_FAMILY_RE = re.compile(r"^v?\d+(?:\.\d+)+(?:-([A-Za-z][A-Za-z0-9]*))?$")


def tag_family(tag: str) -> str | None:
    """The tag's family: its suffix ("mac"), "" for a bare numeric tag, None
    when the tag is not a version at all. Two pages can mark one repo (the
    Sanduhr Mac and Windows pages); each sees only its own family."""
```

In `releases_after`, after `newer` is built and before the sort: when `tag_family(marker_tag)` is not `None`, keep only releases whose `tag_family` equals it. Add one sentence to the module docstring and to `releases_after`'s docstring.

- [ ] **Step 5: Run the whole file**

Run: `python -m pytest tests/test_release_review.py -q`
Expected: all PASS, including the untouched `test_releases_after_lists_newer_published_ones_newest_first` (its `v1`/`v2`/`v3` tags are outside the pattern).

- [ ] **Step 6: CLAUDE.md row.** In the `release-review.yml` row (line 114) after "Store-only releases never appear.", add: `A marker's tag family is its suffix: a page marked `@v2.27.0-mac` sees only `-mac` releases, a page marked `@v3.4.3` only unsuffixed ones, so two pages can review one repo (Sanduhr Mac and Windows).` Keep the file's CRLF.

- [ ] **Step 7: Commit and open PR A**

```bash
git add scripts/release-review.py tests/test_release_review.py CLAUDE.md docs/superpowers/specs/2026-10-18-sanduhr-mac-page-design.md docs/superpowers/plans/2026-10-18-sanduhr-mac-page.md
git commit -m "ci(release-review): a marker's tag suffix is its family, so two pages can review one repo"
git push -u origin ci/release-review-tag-families
gh pr create --title "ci(release-review): tag families for repos with two pages" --body "<what, why, the test names, the spec path>"
```

Merge when green. Do not start Task 6's PR before this is on main.

---

### Task 2: Images into the page directories

**Files:**
- Create or overwrite: `sanduhr/screenshot-*.{jpg,png}` per the spec's capture table; `sanduhr/windows/icon.png`; `sanduhr/windows/screenshot-{obsidian,aurora,ember,mint,matrix,settings-themes}.png`
- Delete: `sanduhr/screenshot-whats-new.png`
- Scratch script (not committed): `<scratchpad>/convert-shots.py`

**Interfaces:**
- Produces: the file names Tasks 3 and 4 reference by `src`.

- [ ] **Step 1: Branch**

```bash
git -C C:\Users\estev\Projects\626labs-hub fetch origin && git -C C:\Users\estev\Projects\626labs-hub checkout -b feat/sanduhr-mac-page origin/main
```

- [ ] **Step 2: Extract the Windows captures** from `origin/main:docs/screenshots/windows/` of the Sanduhr clone into `<scratchpad>/shots-win/` with `git show`, the way the Mac set already sits in `<scratchpad>/shots/`. Print each file's pixel size.

- [ ] **Step 3: Write and run the conversion script.** For each row of the spec's capture table: `desk-full`, `desk-under-files`, `desk-corner`, `desk-limit-menu` open with Pillow, convert to RGB, resize to width 2000 if wider (LANCZOS), save as JPEG `quality=82, optimize=True, progressive=True` under the page name; every other Mac capture copies byte-for-byte to its page name. Windows captures copy byte-for-byte into `sanduhr/windows/`; `sanduhr/icon.png` copies to `sanduhr/windows/icon.png`. Delete `sanduhr/screenshot-whats-new.png`.

- [ ] **Step 4: Verify the budget**

Run: `python -c "import os;d='sanduhr';fs=[(f,os.path.getsize(os.path.join(d,f))//1024) for f in os.listdir(d) if f.startswith('screenshot-')];print(*fs,sep='\n');print('total KB',sum(k for _,k in fs))"`
Expected: no file over about 600 KB, total under about 4000 KB. If a JPEG is over, lower quality to 76 before changing width.

- [ ] **Step 5: Commit**

```bash
git add sanduhr/ && git commit -m "content(sanduhr): the 2.27.0 Mac captures, and the Windows set under sanduhr/windows/"
```

---

### Task 3: The Windows page

**Files:**
- Modify: `content/site.json` (append an entry to the `pages` list that ends at line 3527, after `mod-launcher-trailer`)
- Modify: `content/page-archetypes.json:32` (add `"sanduhr/windows/index.html": "product",` beside `sanduhr/index.html`)
- Test: `tests/test_render_product_pages.py` (after `test_sanduhr_is_generated_with_its_furniture`), `tests/test_release_review.py:43`
- Generated: `sanduhr/windows/index.html`

**Interfaces:**
- Produces: the public URL `/sanduhr/windows/` that Task 4's Mac page and Task 5's home card copy may link.

- [ ] **Step 1: Write the failing test** in `tests/test_render_product_pages.py`:

```python
def test_sanduhr_windows_is_generated_beside_the_mac_page():
    assert "sanduhr/windows/index.html" in rpp.generated_pages()
    html = (ROOT / "sanduhr/windows/index.html").read_text(encoding="utf-8")
    assert '<img class="app-icon" src="icon.png"' in html and (ROOT / "sanduhr/windows/icon.png").is_file()
    assert 'href="/sanduhr/"' in html  # the Mac page, root-relative
    assert 'data-app="9NH3NK2RGCF5"' in html  # the reach map moved here
    assert '<meta name="release-reviewed" content="estevanhernandez-stack-ed/Sanduhr_f-r_Claude@v3.4.3"' in html
    assert 'class="hand"' not in html
```

And in `tests/test_release_review.py::test_the_three_pages_carry_a_marker`, add `"sanduhr/windows/index.html"` to the expected set (rename the test to `test_the_marked_pages_carry_a_marker`).

- [ ] **Step 2: Run to see it fail**

Run: `python -m pytest tests/test_render_product_pages.py -q -k sanduhr_windows`
Expected: FAIL, `assert 'sanduhr/windows/index.html' in [...]`

- [ ] **Step 3: Add the `pages[]` entry.** Shape copies `rororo-plugins` (`id`, `title`, `repo`, `productPage`, `pageSpec{meta, releaseReviewed, nav, sections, footer}`):

- `id` `sanduhr-windows`, `title` `Sanduhr für Claude`, `repo` `estevanhernandez-stack-ed/Sanduhr_f-r_Claude`, `productPage` `/sanduhr/windows/`.
- `meta.title` `Sanduhr für Claude on Windows · 626 Labs`; `meta.ogImage` `/sanduhr/icon.png`; description and ogDescription from the README's Windows section, one sentence.
- `releaseReviewed`: `["estevanhernandez-stack-ed/Sanduhr_f-r_Claude@v3.4.3"]`.
- `nav`: GitHub (repo URL), `Mac` (`/sanduhr/`), `Microsoft Store` (Store URL, `cta: true`).
- `sections`, in order:
  1. `hero` (`align: center`, `icon` `icon.png`, `eyebrow` naming Windows 10 and 11, `title` `Sanduhr für Claude`, `dek` and `fine` from the README; `get` strip: Store link `primary: true, store: true, external: true`, Setup.exe link to `releases?q=v3&expanded=true` external).
  2. `section` "pacing" heading + `lead` + `cards`: burn-rate projection, pace markers, sparklines, per-model weekly meters, Claude Usage tab and vault, threshold alerts. Copy from the current page's "Not just a mirror" cards with Mac-only phrases removed.
  3. `section` Claude Code heading + `lead` + `cards` from README: statusline, `sanduhr-mcp` (3.4.0 or later, the `widget_too_old` note in one clause), Theme Studio, themes from the terminal, and the 3.4.3 fact that Store installs now share `%APPDATA%\Sanduhr`.
  4. `section` themes heading + `gallery`: items `screenshot-obsidian.png`, `screenshot-aurora.png`, `screenshot-matrix.png`; `wide` `screenshot-settings-themes.png`. Ember and Mint are the builder's call.
  5. `section` install heading + `install` block: Store card (`pill` `Recommended`, `plat` `Windows 10 1903+ / 11`, link Store), Setup.exe card (the SmartScreen sentence, the `.msix` caveat, link to Releases), both `external: true`.
  6. `section` + `panel` (`tone: ok`): the current page's privacy panel in Windows wording only (Credential Manager; Sign Out first; delete the two folders after uninstalling; no telemetry paragraph; the policy links).
  7. `section` "Where it ended up" + `lead` + `reachMap` with `label` `Sanduhr für Claude` (moved verbatim from the Mac page).
  8. `section` + `callout` (`label` `On a Mac?`, text naming Desk and the config carry, linking `/sanduhr/`).
- `footer`: `label` `626 Labs · Sanduhr für Claude on Windows`, the same `disclaimer` the Mac page carries.

- [ ] **Step 4: Register the page** in `content/page-archetypes.json` and render.

Run: `python scripts/render-product-pages.py && python scripts/render-hub.py`
Expected: both exit 0; `sanduhr/windows/index.html` exists; `sitemap.xml` gains `https://626labs.dev/sanduhr/windows/`.

- [ ] **Step 5: Run the tests**

Run: `python -m pytest tests/test_render_product_pages.py tests/test_release_review.py -q`
Expected: PASS except `test_sanduhr_is_generated_with_its_furniture` may still pass (the Mac page is untouched yet); `test_each_marker_names_a_repo_its_page_links` passes for the new page because the hero's repo meter carries `data-repo`.

- [ ] **Step 6: Commit**

```bash
git add content/site.json content/page-archetypes.json sanduhr/windows/index.html sitemap.xml index.html tests/
git commit -m "feat(sanduhr): a Windows page at /sanduhr/windows/, reviewed through v3.4.3"
```

(Stage `index.html`, `feed.xml`, `sitemap.xml` only if the render changed them.)

---

### Task 4: The Mac page

**Files:**
- Modify: `content/site.json:592-990` (the `sanduhr` product's `pageSpec`)
- Test: `tests/test_render_product_pages.py:304-313` (`test_sanduhr_is_generated_with_its_furniture`)
- Generated: `sanduhr/index.html`

**Interfaces:**
- Consumes: Task 2's file names, Task 3's `/sanduhr/windows/`.

- [ ] **Step 1: Rewrite the pinned test** to the new page:

```python
def test_sanduhr_is_generated_with_its_furniture():
    assert "sanduhr/index.html" in rpp.generated_pages()
    html = (ROOT / "sanduhr/index.html").read_text(encoding="utf-8")
    assert '<img class="app-icon" src="icon.png"' in html
    assert 'class="hand"' not in html  # the hand is for Este's own words; nothing here is one
    assert 'class="platform-card"' not in html and 'data-app=' not in html  # the picker and the reach map moved to /sanduhr/windows/
    assert 'src="screenshot-desk-full.jpg"' in html and 'src="screenshot-desk-under-files.jpg"' in html
    assert "screenshot-whats-new" not in html
    assert 'class="stages"' in html  # how a pack travels
    assert "brew install --cask estevanhernandez-stack-ed/tap/sanduhr" in html
    assert 'href="/sanduhr/windows/"' in html
    assert html.count('class="gallery-shot"') + html.count('class="gallery-shot wide"') >= 11
    assert '<meta name="release-reviewed" content="estevanhernandez-stack-ed/Sanduhr_f-r_Claude@v2.27.0-mac"' in html
```

Run: `python -m pytest tests/test_render_product_pages.py -q -k furniture`
Expected: FAIL on the `hand` or `platform-card` assertion.

- [ ] **Step 2: Rewrite the `sanduhr` pageSpec** as a text edit of the block between `"pageSpec": {` and `"screenshots": []`. Keep `meta` keys, `releaseReviewed`, `nav`, `sections`, `footer`. Decided values:

- `meta.title` `Sanduhr für Claude for Mac — usage meters on your desktop, Claude Code mods and config · 626 Labs` (or shorter; keep `· 626 Labs`); `description` and `ogDescription` name both pillars; `ogImage` stays `/sanduhr/icon.png`.
- `releaseReviewed`: `["estevanhernandez-stack-ed/Sanduhr_f-r_Claude@v2.27.0-mac"]`.
- `nav`: GitHub, `Windows` (`/sanduhr/windows/`), `Download` (`#install`, `cta: true`).
- `sections`, in order (block types in parentheses; copy sources in Global Constraints):
  1. `hero` center, icon, eyebrow for the Mac, title `Sanduhr für Claude`, dek naming Desk and the config carry in one sentence, `fine` (notarized, Homebrew, macOS 14 or newer, no telemetry), `get` strip: `Homebrew` (`#install`, `primary: true`), `.dmg from GitHub` (`releases?q=mac&expanded=true`, external), `Windows` (`/sanduhr/windows/`).
  2. section (`showcase`): `screenshot-desk-full.jpg`, alt describing the Desk on a bare desktop with the Work account, three meters, the clock, the message line and three meetings.
  3. section, Desk heading (`lead`, `cards`, `gallery`). Cards: the current Desk cards reviewed, plus three new ones from the 2.27.0 notes: under your files, a plate behind every piece, Arrange Desk. Gallery items `screenshot-desk-meters.png`, `screenshot-desk-clock.png`, `screenshot-desk-limit-menu.jpg`; `wide` `screenshot-desk-under-files.jpg`.
  4. section, notch heading (`cards` with the notch and now-playing cards, `gallery` items `screenshot-settings-notch.png`, `wide` `screenshot-notch-wings.png`).
  5. section, config heading (`lead`, `cards` in the spec's order: the view, meters above the prompt, the carry, the wall, mod packs; then `steps` with five items `{n, text}`: Export, Pack, Import, Compare, Keep or undo). Watchers and "Claude writes your messages and themes" cards stay in this section or the Desk one, builder's call.
  6. section, widget and themes heading (`cards`: the widget when you want it, themes you can see with "seven"; `gallery` items `screenshot-widget-mac.png`, `screenshot-obsidian.png`, `screenshot-aurora.png`, `screenshot-matrix.png`, `wide` `screenshot-settings-themes.png`).
  7. section, pacing heading (`lead`, `cards`: burn-rate, pace markers, sparklines, per-model meters, usage per account, no Mica, no Python, no "five").
  8. section, alerts and settings heading (`cards`: smarter alerts, accounts, sign-in; `gallery` items `screenshot-settings-alerts.png`, `screenshot-accounts.png`, and `screenshot-meters.png` or `screenshot-menu-bar.png` only if its card survives).
  9. section with `"id": "install"` (`render_section` emits `<section id=...>` when the section carries one) and heading "Install": an `install` block with two items (Homebrew `pill: Recommended`, `plat` `macOS 14 or newer, Apple silicon and Intel`, `code` the one-liner, link to the tap repo; the .dmg card with Developer ID, notarization, Sparkle or `brew upgrade`, link to Mac releases) and a `callout` (`label` `On Windows?`, link `/sanduhr/windows/`). The nav CTA and the get strip's Homebrew link both point at `#install`.
  10. section (`panel`, `tone: ok`): the privacy panel in Mac wording only.
- `footer` unchanged except the label if desired.
- Delete from `sanduhr/`: `screenshot-menu-bar.png` and `screenshot-meters.png` if unused after this step.

- [ ] **Step 3: Render and test**

Run: `python scripts/render-product-pages.py && python scripts/render-hub.py && python -m pytest tests/test_render_product_pages.py tests/test_release_review.py tests/test_brand_hand.py -q`
Expected: exit 0, PASS.

- [ ] **Step 4: Commit**

```bash
git add content/site.json sanduhr/ tests/test_render_product_pages.py index.html sitemap.xml feed.xml
git commit -m "content(sanduhr): the Mac page, Desk and the Claude config carry, reviewed through 2.27.0"
```

---

### Task 5: The home card and the keystone

**Files:**
- Modify: `content/site.json:563` (`description`), `:593` (`meta`)
- Modify: `CLAUDE.md:58` (the `products[].pageSpec` row's "Pages that are not products" sentence) and the `Common tasks` row for release review if it names Sanduhr's single page
- Generated: `index.html`

- [ ] **Step 1: Edit the card.** `description`: one paragraph leading with Desk, then the config carry, then pacing, then "Homebrew or a notarized .dmg on Mac; free on the Microsoft Store on Windows." No Python. `meta`: `Mac: Homebrew or .dmg · Windows: free on the Store`. Tags and `storeUrl` unchanged.

- [ ] **Step 2: CLAUDE.md.** In the `pages` sentence at line 58, extend the parenthetical: `(the RoRoRo plugin marketplace, the two trailer watch pages, and the Sanduhr Windows page at /sanduhr/windows/, split from the Mac page 2026-10-18)`. In the `Where things are` gotchas or the Sanduhr-relevant row, one sentence: `/sanduhr/ is the Mac build's page and the cask's homepage; Windows lives at /sanduhr/windows/.`

- [ ] **Step 3: Render and check**

Run: `python scripts/render-hub.py && python scripts/render-hub.py --check && python scripts/render-product-pages.py --check`
Expected: exit 0 both.

- [ ] **Step 4: Commit**

```bash
git add content/site.json index.html CLAUDE.md
git commit -m "content(home): the Sanduhr card leads with Desk and names both install paths"
```

---

### Task 6: Gates, reviewers, PR B

**Files:** none new.

- [ ] **Step 1: Full gate stack**

Run, from the repo root:
```
python scripts/render-product-pages.py --check
python scripts/render-hub.py --check
python -m pytest tests/ -q
python scripts/site-doctor.py --report
python scripts/site-doctor.py --check; echo exit=$?
python scripts/theme-doctor.py <active slug from content/themes.json> --browser
```
Expected: every exit 0; `site-doctor --report` shows no dangling asset; theme-doctor PASS with the two Sanduhr pages in its browser list and no console error on either.

- [ ] **Step 2: Look at both pages.** Serve the repo root (`python -m http.server 8787`) and screenshot `/sanduhr/` and `/sanduhr/windows/` at 390 and 1440 wide with playwright into `<scratchpad>/review/`; open the four PNGs. Fix anything that reads wrong (a caption that wraps badly, a shot that is too heavy for its slot) in site.json and re-render.

- [ ] **Step 3: Reviewers.** Dispatch `copy-reviewer` on the `content/site.json` diff against `origin/main` and `visual-asset-reviewer` on the new files under `sanduhr/`. Advisory, except a real identity or secret in a capture or a tier-A banned word in copy, which block. Apply what is right; commit as `content(sanduhr): review fixes`.

- [ ] **Step 4: Push and open PR B** (after PR A has merged; rebase on `origin/main` first):

```bash
git fetch origin && git rebase origin/main
git push -u origin feat/sanduhr-mac-page
gh pr create --title "feat(sanduhr): the Mac page, and Windows at /sanduhr/windows/" --body "<the two pillars, the URL decision, the capture table, gates run, reviewer outcomes, 'New public URL for GSC Request Indexing: https://626labs.dev/sanduhr/windows/', spec path>"
```

Merge when green. Confirm `rebuild-hub.yml` passes on main (check the Actions tab; a failing run is silent) and that https://626labs.dev/sanduhr/windows/ serves.

---

### Task 7: The tap (homebrew-tap PR)

**Files:**
- Modify: `Casks/sanduhr.rb` (`desc`, `homepage`), `README.md:28` in `estevanhernandez-stack-ed/homebrew-tap`

- [ ] **Step 1: Clone into the scratchpad** (`gh repo clone estevanhernandez-stack-ed/homebrew-tap <scratchpad>/homebrew-tap`) and branch `docs/hub-is-home`.

- [ ] **Step 2: Edit.** `homepage "https://626labs.dev/sanduhr/"`. `desc "Claude.ai usage meters on the desktop, with Claude Code mods and config packs"` (under 80 characters, no leading article, no platform name, no app name). README row's homepage column: `[626labs.dev/sanduhr](https://626labs.dev/sanduhr/)`.

- [ ] **Step 3: Verify** `brew style --cask <path>` if Homebrew is reachable from this box; otherwise `ruby -c Casks/sanduhr.rb`, or skip with a note in the PR that the only changed lines are two strings.

- [ ] **Step 4: Commit, push, PR.** `docs(cask): sanduhr's homepage is 626labs.dev/sanduhr, and the desc says what it is now`.

---

### Task 8: The Sanduhr landing page and README (Sanduhr PR)

**Files:**
- Modify: `docs/index.html:6-14` (title, description, og:description), `:628-660` (the platform cards), `README.md` (the macOS install section) in the Sanduhr repo

- [ ] **Step 1: Worktree off origin/main**

```bash
git -C C:\Users\estev\Projects\Sanduhr worktree add <scratchpad>/sanduhr-landing -b docs/hub-is-home origin/main
```

- [ ] **Step 2: Edit `docs/index.html`.** `<title>` `Sanduhr für Claude — usage meters on your Mac desktop, and your Claude Code setup carried`; meta description and og:description: the two pillars, then "Also on Windows." Platform section: the macOS card first, its primary action `See it on 626labs.dev` to `https://626labs.dev/sanduhr/` with `Latest .dmg` kept as the second action and the Keychain claim corrected (the README says Keychain on release builds; the card still says plaintext); the Windows card gains a `626labs.dev/sanduhr/windows/` action; the Cross-platform card's two links point at the `legacy/python-v2.3.0` tag (`.../blob/legacy/python-v2.3.0/sanduhr.py`) since the files left `main` on 2026-09-13.

- [ ] **Step 3: Edit `README.md`.** Under "### macOS — native SwiftUI", first line after the heading: `The Mac build's page, with Desk and the Claude config carry in pictures: [626labs.dev/sanduhr](https://626labs.dev/sanduhr/).`

- [ ] **Step 4: Verify** every edited href resolves (`curl -sI` each, expect 200), then commit, push, PR: `docs: the Mac build's home is 626labs.dev/sanduhr; the landing page points there`. Remove the worktree after merge.

---

### Task 9: Close the loop

- [ ] **Step 1: Sanduhr issue #120.** Comment: which shots are now live and where (the table), that the themes strip (item 16) is closed, and the follow-up shot list for the config pillar: Mods & Config open on a folder with a kept mod, the Export Config sheet, Compare on import.

- [ ] **Step 2: Dashboard.** `manage_decisions log` on project `qNCk86nujUfrHEbRU2jy`: the ship, PR numbers, the three repos touched, the cask repoint. `manage_projects update` on the hub project only if its `version` tracks the site.

- [ ] **Step 3: Memory.** Update `project-theme-rotation.md`'s sibling for Sanduhr or write `project-sanduhr-pages-split.md`: the URL layout, the tag-family rule, the config-shot follow-up, and the Windows fold-back trigger. One line in `MEMORY.md`.

- [ ] **Step 4: Ship report to Este** ending with the GSC line: `Request Indexing: https://626labs.dev/sanduhr/windows/` (and `/sanduhr/` re-request, since its content changed).
