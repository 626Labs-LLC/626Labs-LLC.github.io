# Overnight Cart run: the morning report, 2026-10-03

Checklist: `2026-10-03-overnight-cart-run.md` beside this file. Run 00:26 to about 01:10 Fort Worth time, unattended after the go. Every item ran from a fresh `origin/main` in its own worktree. Your checkout was never touched.

## The board

| # | Item | PR | Tier | State |
|---|---|---|---|---|
| 1 | Analytics on every public page | #164 | A | **Merged, live** |
| 2 | One-step Field Note publishing | #165 | A | **Merged, live** |
| 3 | Gotchas in CLAUDE.md | #166 | A | **Merged** |
| 4 | Flagship meta line becomes a class | #167 | A | **Merged, live** |
| 5 | Sanduhr page, true to Mac 2.2.1 | #169 | B | **Waiting on you** |
| 6 | POD pipeline banner, RBX15 tag | #168 | B | **Waiting on you** |
| 7 | Right Click PNG page | branch `feat/rtclickpng-page` | stretch | **Staged, no PR**: waits for the five screenshots |
| 8 | Docs and security | this PR | A | This |

## What went live

- **#164, analytics.** 22 of 43 public pages had no GoatCounter: every plugin storefront, `/plugins/`, Sanduhr, both Bacon Trail pages, the year in review, 404 and both legal pages. privacy.html said every page carried it, which is now true. theme-doctor requires analytics on product pages, changed in the same commit as all three themes' templates so the Nov 1 rotation still passes. Checked on the live site this morning. Visits before last night can't be backfilled.
- **#165, publishing.** `python scripts/site.py story publish <slug>` flips the draft and maps the page in one step. The rebuild workflow re-runs on the map. Publishing's private `build_hub.py` can drop its archetypes half.
- **#166, CLAUDE.md.** Four gotchas: edit site.json as text, marker order isn't vertical order, the four-chip limit, and the page-pane mod's dependency on site.json.
- **#167, refactor.** The flagship head's three inline styles became classes, and Cyan Fade dropped its `!important` override. Visual diff on Slate found zero changes. Cyan Fade renders pixel-identical at 1440 and 390.

## Waiting on you

### #169, the Sanduhr page: read this one first

Every Mac claim traces to the v2.1.0, v2.2.0 and v2.2.1 Mac release notes. Nothing came from the unmerged Sanduhr #93. The changes:
- macOS 14 or newer, universal, notarized, updates itself.
- A new "On Mac, your meters live on the desktop" section.
- The Mac download points at v2.2.1-mac.
- The retired Python build and its link are gone.
- Windows is described as .NET/WPF.

**The privacy card was wrong.** The live page says Mac credentials sit in the Keychain and are wiped on uninstall. The Sanduhr README says Mac stores them in a plaintext file readable only by your user account (`0600`), with Keychain planned, and that uninstall doesn't clear Windows Credential Manager. The PR says what's true. It also leaves four claims for you to judge: the vibrancy claim, the hero's "five glass themes / No telemetry", a toast-and-chime alerts card that reads as Windows, and the hero's generic Releases button.

### #168, the banners

The POD pipeline banner is the pipeline's own showcase output, "I Should Buy A Boat". The asset review said ship with notes:
- It reads merch-forward, and repeats Conundrum.
- The meme phrase wasn't checked for trademarks.
- It's 472 KB, against a 300 KB budget.
- The halves blend into each theme's background.

The review is posted as a comment on the PR. etsy-mcp still has no banner; nothing honest exists to use. RBX15's tag changes from `native` to `desktop`.

### `feat/rtclickpng-page`, staged

The full page: hero, problem, what it does, how it's built, offline by design, the reach map (108 installs, 44 countries), and the repo meter. "See it work" holds five labelled empty frames. Take the five shots from the plan, upload them, fill the slots, then PR it. After merge, request indexing for `https://626labs.dev/rtclickpng.html`.

Two notes from the build:
- The decoder count disagrees across sources. The reflection lists eight libraries and the Store copy a different seven. The page keeps the "7" stat but doesn't claim its list is the seven.
- The RTClickPng README's "61 total" test line is wrong: 40 + 45 = 85.

## Security and deployment

- **gitleaks** over every range the night produced (main since `b49c1ad` plus all four branches): no leaks. A separate grep for tokens, cookies, keys and personal paths found only the plan docs' prose about the AppData path.
- **Dependencies:** no `requirements.txt`, `package.json` or lockfile touched.
- **Deployment:** Pages built green on the last two merges; the two cancelled builds were superseded. Rebuild hub and the link check passed on all three runs since the first merge.

## Dashboard

Closed: the analytics task, the publishing task and the CLAUDE.md task, plus last night's Celestia map, theme queue, Store geography and installs-series tasks. Annotated with their PRs: the Sanduhr page, the banners and RBX15's "native" wording. Still open for you: the 11 screenshots.
