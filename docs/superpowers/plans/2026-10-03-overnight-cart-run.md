# Overnight Cart run: the hub backlog, 2026-10-03

**What this is.** A Vibe Cartographer build checklist for one unattended night on 626labs-hub. There is no `docs/spec.md`: the spec is the hub's open dashboard tasks (project `qNCk86nujUfrHEbRU2jy`), whose descriptions already carry verified line references, plus `2026-10-03-product-pages-rtclickpng-rbx15.md` beside this file. Build mode: autonomous.

**What it can't do.** Anything that needs Este's machine or taste: the 11 screenshots, the RBX15 Store copy, Sanduhr PR #93's fixes. Those stay out.

## How every item runs

- **One item, one branch, one PR**, each from a fresh `origin/main` (the daily bots churn main from 06:00 UTC), in its own scratchpad worktree. The main checkout is never touched.
- **The gate stack, all of it, every item:** `pytest tests/ -q`; `theme-doctor slate-broadsheet --browser --require-browser` and the same for `cyan-fade` (live now and live Nov 1); `render-hub --check`; `render-plugin-pages --check`; `site-doctor --check`. Any item that touches markup also gets `visual-diff origin/main --widths 1440,390` on slate-broadsheet.
- **Merge tiers.**
  - **Tier A (merge when green):** invisible or tooling-only, proven by the gates.
  - **Tier B (PR held for Este's morning look):** anything a visitor reads or sees.
- **`content/site.json` is edited surgically**, as text-block moves, never round-tripped through `json.dumps`. It's CRLF with hand-compacted regions, and a round-trip rewrites 1,172 lines.
- **Survives a dropped connection.** Last night's DNS outage killed four agents mid-task. Each item writes its files to disk before verifying, and the run resumes at the first unchecked item.
- **Records as it goes.** Dashboard task status on each merge; a decision log for any real fork; one morning report.

## Checklist

### 1. Analytics on every page that's dark [Tier A] (~60 min)

Task `task-1790597410974-l00wz71ak`. Every plugin storefront and the Sanduhr page have never counted a visit.

- Add the GoatCounter snippet to each theme's `archetypes/product.html`: phosphor-blueprint, slate-broadsheet, cyan-fade.
- Add it to `render-plugin-pages.py`'s template. That covers the 15 plugin pages and `/plugins/`.
- Add it to the hand-authored dark pages: `sanduhr/index.html`, `bacon-trail/index.html`, `play/bacon/index.html`, `404.html`, `legal/privacy.html`, `legal/terms.html`. Re-audit for any others first.
- Flip `ARCHETYPE_CHROME["product"]` to `analytics=True` in `scripts/theme-doctor.py`, **in the same commit as all three shells**. Otherwise the queued Nov 1 rotation fails the doctor.
- Mirror PR #139's two tests: every registered theme's shell, plus every committed public page carries the snippet.
- **Accept when:** the gates are green with the flipped gate, and `grep -L goatcounter` over every public page returns only documented exclusions (the admin dashboard).

### 2. Field Note publishing becomes one step [Tier A] (~30 min)

Task `task-1790597418318-xde4u4za3`.

- Add `content/page-archetypes.json` to `rebuild-hub.yml`'s `on.push.paths`.
- `site.py story publish` (or the existing flip path) writes the `editorial/<id>/index.html: "reading"` mapping when a story's `draft` flips to false. If no flip command exists, `story new` prints the exact line to add, and a test pins it.
- **Accept when:** a test publishes a fixture story and `archetypes.validate()` stays clean with no hand edit; the workflow's paths include the file.

### 3. Three gotchas into the hub CLAUDE.md [Tier A] (~15 min)

Task `task-1789992890873-5lfvw6q3m`.

- Edit `site.json` surgically, never through `json.dumps`: CRLF, hand-compacted regions, the 1,172-line rewrite; a byte-exact round-trip gate on any block before re-serializing it.
- Zone-marker order is not vertical order: measure at 390px per theme. Slate nests the stories inside the hero rail, which put the products at y=3015 against PB's 1737.
- `render_chips` slices to `[:4]`, so a fifth hero chip never renders.
- These go in a Gotchas block next to What NOT to do.
- **Accept when:** the three rules are in, `site-doctor` is clean, and no other section moved.

### 4. The flagship meta line becomes a class [Tier A if visual-diff is clean, else B] (~45 min)

Found in the Cyan Fade build. `render_product` emits the flagship's category line with an inline `style` (mono, `--fg-muted`, tracked), so a light theme needs an `!important` override.

- `render-hub.py` emits `<div class="product-category">` instead.
- Each theme's home shell styles `.product-category` with the inline values for PB and slate, and with what it overrides today for cyan-fade. Drop cyan-fade's `!important` rule.
- **Accept when:** visual-diff against `origin/main` at 1440 and 390 on slate-broadsheet reports zero findings; cyan-fade's render is unchanged against last night's theme-shots; the gates are green.

### 5. Sanduhr page, true to what has shipped [Tier B] (~60 min)

Task `task-1791004405134-icg2pgomm`. It doesn't wait for #93: everything below is true of the released 2.2.1.

- Requirements: macOS 14 (Sonoma) or newer, not macOS 11.
- Remove the Python `sanduhr.py` link and the "Mac, Windows and Linux from source" path.
- Add what 2.2.x ships: Desk as home, the notch, meters on Desk, one Settings window, smarter alerts, self-updating. Source it from the v2.1.0-mac, v2.2.0-mac and v2.2.1-mac release notes, never from #93.
- A direct link to the latest Mac release.
- Copy through `copy-reviewer`.
- **Accept when:** every claim traces to a release note; both themes render it (doctor `--browser`); the PR lists each change against the old line.

### 6. Banners for pod-pipeline and etsy-mcp, and RBX15's tag [Tier B] (~45 min)

Tasks `task-1791004405134-l3b7qxxoh` and `task-1791004405134-4yebnjpmo` (the hub half).

- Find or cut a banner for each from existing art: the pipeline's own repo output, the Conundrum shop art, the connector page's imagery. No invented graphics.
- Place each under `assets/screenshots/<product-id>/`, uploader-named, and add a `banner` to each product.
- Swap RBX15's `native` tag for `desktop`; its description already says Electron.
- Review with the `visual-asset-reviewer` agent.
- **Accept when:** the page-pane mod's resolution (`banner`, else the plugin banner) finds an image for all 24 products; `site.json` changes only those three blocks; the gates are green.

### 7. Right Click PNG page, staged [held, stretch] (~90 min)

Build `rtclickpng.html` per the plan with its full wiring (theme-css zone, archetype mapping, repo meter, reach map, GoatCounter), with labelled screenshot slots for the five shots. Push the branch with **no PR**. It's ready for the shots the moment Este captures them. Never merged without them.

### 8. Documentation and security verification (~30 min)

- **Docs:** CLAUDE.md reflects the night (the analytics gate, the class, the publish step); the dashboard tasks are closed or annotated.
- **Secrets:** a scan over the night's combined diff (`gitleaks` if present, else `vibe-sec:scan`). Confirm no token, cookie or AppData path landed, Right Click PNG's settings crop above all.
- **Dependencies:** none added; confirm `requirements.txt` and `package.json` are unchanged.
- **Deployment:** every merged item shows a green Pages build and a green content-health run, and every bot that ran overnight succeeded.
- **Records:** decisions logged; memory updated; a morning report with each PR, its tier, what merged, what waits, and anything that failed.

## Order and budget

1, 2, 3 and 4 first, independent and Tier A, about 2.5 hours. Then 5 and 6, Tier B, about 1.75 hours. Then 7 if the night has room, then 8. About 6 hours end to end; 1 to 6 plus 8 is the commitment and 7 is the stretch.

## Stop conditions

- A gate fails twice on the same item after a real fix attempt: park the item, note it in the report, move on.
- Anything touching `content/themes.json`, the rotation workflow or a secret: stop that item; it waits for Este.
- `main` moves in a way that conflicts with an open item: rebase once; a second conflict parks it.
