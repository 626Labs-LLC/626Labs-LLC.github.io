# Sanduhr für Mac: its own page, and one home for the Mac build

Design, 2026-10-18. Brainstormed with Este; decisions logged to the dashboard
(17XbyotBSP7Ojf31Lt0z, I5FL75fRcltqD6for43p, 6gLvSu1W82pGbrSIMXNx, NzkIIpQap6fGsiRMscmB).

## Intent

The Mac build of Sanduhr has outrun the Windows build. Mac is at 2.27.0 with
Desk, the notch, accounts, the Claude Code integration, Mods & Config and
config packs; Windows is at 3.4.3 with the widget, the statusline, the MCP
server and Theme Studio, and none of the desktop surfaces. One shared page
at /sanduhr/ has been describing both through "On Mac, ..." qualifiers while
its Windows half ages. Thirteen fresh Mac captures landed in the Sanduhr repo
this morning (PR #278, from 2.27.0 in demo mode), and the page is two Mac
releases behind its review marker.

So: **/sanduhr/ becomes the Mac page.** Windows gets its own page at
/sanduhr/windows/ until it catches up. And the Mac build's three public
surfaces, GitHub, Homebrew and the hub, converge on the hub page as the one
home. Este's words for what a Mac visitor should walk away with: **Desk, and
Claude config portability and view.**

## Goals

- A /sanduhr/ page that leads with Desk in pictures and the Claude config
  view-and-carry in words, reviewed through `v2.27.0-mac`, so the open
  release-review issue clears.
- A /sanduhr/windows/ page that says what the Windows build is today, reviewed
  through `v3.4.3`, with the Store install front and center.
- The cask, the tap README and the Sanduhr GitHub Pages landing page all point
  at https://626labs.dev/sanduhr/ as the Mac build's home.
- The release-review bot stops conflating the two tag families.

## Non-goals

- No new renderer block types. Everything here is expressible with the blocks
  `render-product-pages.py` already has (`hero`, `lead`, `cards`, `gallery`,
  `showcase`, `steps`, `install`, `callout`, `panel`, `cta`, `reachMap`).
- No second home-row card. One "Sanduhr für Claude" card, linking to /sanduhr/.
- No repo split. The Sanduhr repo stays one repo with two tag families.
- No new screenshots captured for this ship. The Claude config pillar ships in
  words; its shots are a follow-up (see "Follow-ups").
- Not a redesign of the GitHub Pages landing page. Re-point its links and
  fix its title and description; leave its layout alone.

## Anti-goals (a page that does these has failed, even if it renders)

- Claims a feature the 2.27.0 release notes, the Mods & Config spec or the
  packs spec do not support. Every sentence about the product traces to one
  of those three or to copy already on the page that the 2.26.0 review kept.
- Shows a real account, email, org, meeting or secret. The 2.27.0 set was
  captured in demo mode on a clear desktop (PR #278's commit message says so);
  do not add any capture that was not.
- Breaks any existing link into /sanduhr/. The URL keeps every inbound link,
  including Google's index, the README, the cask and Sanduhr issue #120.
- Leaves a page or the home card with a dead or looping call to action. The
  current page's "Open the full landing page" CTA points at a page that will
  itself point back here; it goes.
- Ships a desktop capture at its source weight. `desk-full.png` and
  `desk-under-files.png` are 5.2 MB each at 2400x1558.

## Constraints (repo rules that bind this work)

- `content/site.json` is CRLF with hand-compacted regions. Edit it as text,
  move blocks verbatim, never round-trip through `json.dumps`. The 2.26.0
  review PR (#238) is the model: a few dozen lines in, a few out.
- The generated HTML is never hand-edited. Both pages come out of
  `scripts/render-product-pages.py`; `index.html` out of `render-hub.py`.
- Banned words: `626labs-marketing/docs/banned.md`, tiers A and B. No emoji on
  any surface here. Em-dashes minimal; commas, periods, colons.
- EsteFont Pro sets Este's own words only. Nothing on either page is in his
  voice as a quotation, so neither page uses `"hand": true`. (The current
  page sets it on the "Desk, on a real Mac." heading; that was wrong by the
  rule and does not carry over.)
- `products[]` fields `id`, `title`, `tagline`, `description`, `status`,
  `tags[].label`, `meta`, `productPage`, `liveUrl`, `storeUrl`, `banner` are
  read by the page-pane mod off raw `main`. Their values may change; their
  names and the entry's `id` may not.
- Every new public page needs its line in `content/page-archetypes.json`
  (archetype `product`), or `archetypes.validate()` fails the render.
- `render-product-pages.py` runs before `render-hub.py`; the sitemap is drawn
  from the page tree.
- The tap repo and the Sanduhr repo are not this repo. The local Sanduhr clone
  at `C:\Users\estev\Projects\Sanduhr` is 844 commits behind `origin/main`
  with untracked files; branch from `origin/main` after a fetch, never pull
  over it. Use `git -C` with absolute paths throughout.

## Decided

### URLs and the home row

- `/sanduhr/` is the Mac page. The product entry's `productPage` does not
  change.
- `/sanduhr/windows/` is the Windows page: a `pages[]` entry with `id`
  `sanduhr-windows`, `productPage` `/sanduhr/windows/`, `repo`
  `estevanhernandez-stack-ed/Sanduhr_f-r_Claude`, and its own `pageSpec`,
  the same shape as `rororo-plugins`. It renders to `sanduhr/windows/index.html`.
- The home row stays one card. Its `productPage` link lands on the Mac page.
  Its `storeUrl` stays, so the Store badge pair still renders; the `meta` line
  changes to name both paths, Mac by Homebrew or .dmg, Windows free on the
  Store. The `description` is rewritten to lead with Desk and the config
  carry and to drop the Python build (removed from the repo 2026-09-13; the
  README says so). Tags keep `macOS` and `Windows`. The `install` field stays
  null: `render-hub.py` labels it "Install in Claude Code", which a brew line
  is not.
- The one-line Homebrew install, used everywhere a command is shown:

  ```
  brew install --cask estevanhernandez-stack-ed/tap/sanduhr
  ```

  It taps implicitly, so one line replaces the README's two.

### The Mac page

The page is two pillars, in this order, with the rest supporting.

**Hero.** Centered, app icon, title "Sanduhr für Claude", eyebrow naming the
platform ("On your Mac" or close), a dek that says the two pillars in one
breath: your claude.ai meters living on the desktop, and your Claude Code
setup seen and carried. `fine` line: notarized, Homebrew, macOS 14+, no
telemetry. The get strip: Homebrew (primary, anchors to the install section),
the .dmg from GitHub Releases filtered to Mac, and Windows pointing to
/sanduhr/windows/. Nav: GitHub, Windows, and a Download CTA.

**Showcase, right under the hero: `desk-full`.** The Desk on a bare desktop,
2400x1558, is the new hero image. The widget capture that was the hero moves
down to the widget section.

**Pillar one: Desk.** Heading in the spirit of "Your meters live on the
desktop." The existing Desk cards carry over, reviewed against 2.27.0 and
extended with what 2.27.0 added: the Desk can sit under your desktop files
(the Clicks option, off by default; meetings, watchers, now playing and the
account name keep their clicks through a click layer), a plate behind every
piece (on for new installs), and Arrange Desk hiding and showing pieces with
one write on Done. Gallery: `desk-meters`, `desk-clock`, `desk-limit-menu`;
wide shot `desk-under-files`. `desk-corner` is available if the builder wants
a fourth; the three-wide strip plus one wide is the shape.

**The notch**, as its own short section or the tail of Desk: the existing
notch card, `notch-wings` as the wide shot, `settings-notch` beside it for the
wing and strip choices. The 2.27.0 note that the Notch page leads with "Needs
the Desk." is a fact about Settings, not a feature; do not promote it.

**Pillar two: the Claude Code setup, seen and carried.** Heading in the
spirit of "Your Claude Code setup, seen and carried." No pictures yet, so the
section has to work in words. Lead: one Settings page per Claude Code folder
that reads everything first. Cards, in this order:

1. The view: what each folder actually loads, agents, skills, commands,
   plugins, MCP servers and settings, from which file and why one wins. Reads
   first, writes only through receipts with exact undo.
2. Meters above the prompt (2.27.0's opening row): one row per folder with
   its state and a switch; the statusline that combines with yours; the notch
   glow when a session needs you; the MCP server. This is the existing "Claude
   Code, from Sanduhr" card, re-led.
3. The carry: Export Config reads a folder into a pack, a description plus
   the plain files that travel; secrets travel as names marked needs a value;
   `CARRY.md` lists what to set by hand. Import opens it into any folder as a
   Compare view with a checkbox per difference, and one Undo Import takes the
   whole import back.
4. The wall: a folder marked work never exports into a personal one, and the
   control is absent, not disabled.
5. Mod packs: the smallest config pack. Export a kept mod, open it anywhere,
   review before it lands. A mod pack is also a one-plugin marketplace that
   works without Sanduhr. Claude can propose mods and config too; nothing
   lands until you review it.

Then a `steps` block, "How a pack travels": Export, the pack, Import, Compare,
Keep or Undo. Five stage pills, one clause each.

**The widget and its themes.** The existing "widget, when you want it" and
"themes you can see" cards, then a gallery of `widget-mac`, `theme-obsidian`,
`theme-aurora`, `theme-matrix` (all 680 px square, captured at one size with
one content, as issue #120 asked) and `settings-themes` as the wide or fourth
shot. The "Five themes. Or infinite." section is replaced by this; its April
captures are superseded.

**Pacing.** The "Not just a mirror of the numbers" cards carry over with the
cross-platform claims removed: no Mica, no "Win11", no Python, and no
"five hand-tuned themes": the Mac ships seven (see "Mac themes" below).
Per-model meters, burn-rate, pace markers, sparklines, the Claude Usage page
and the per-account vault stay.

**Alerts and settings.** The existing alerts card plus `settings-alerts`. The
three 2.4.0 Settings captures (Accounts, General, Desk Meters) stay only
where a card they illustrate survives and the pane they show has not been
reorganized by a later release note the builder can find; when in doubt,
drop the capture and keep the card. `whats-new.png` (2.4 to 2.6) is dated
and goes.

**Install.** An `install` block with two cards: Homebrew (recommended pill,
the one-line command, a link to the tap) and the .dmg (GitHub Releases filtered
to Mac, the Developer ID and notarization line, updates itself through
Sparkle or `brew upgrade`). A third card or a `callout` under it: "On
Windows?" pointing to /sanduhr/windows/ with the Store named.

**Privacy panel.** The existing panel, Mac wording only: Keychain, Sign Out,
Reset Sanduhr, the MCP sharing switches. The Windows sentences move to the
Windows page.

**Dropped from this page:** the platform picker section, the CTA to the GitHub
Pages landing page, the reach map (Store installs by country is a Windows
number; it moves).

**Marker:** `releaseReviewed` becomes `["estevanhernandez-stack-ed/Sanduhr_f-r_Claude@v2.27.0-mac"]`.

### The Windows page

Shorter, honest about what it is. Hero: icon, title, eyebrow "On Windows",
dek from the README's Windows section, get strip with the Store primary (with
`store: true`) and the Setup.exe from Releases filtered to `v3`. Nav: GitHub,
Mac, Store CTA.

Sections: the widget's pacing cards (shared claims only); a Claude Code
section from the README (statusline, `sanduhr-mcp` 3.4.0+, Theme Studio,
themes from the terminal), with the 3.4.3 note that Store installs now share
the real `%APPDATA%` folders; a themes gallery from the Sanduhr repo's
`docs/screenshots/windows/` (the five themes and `settings-themes`), copied
into `sanduhr/windows/`; an install block (Store recommended, Setup.exe with
the SmartScreen sentence, the `.msix` caveat); the privacy panel in Windows
wording (Credential Manager, the two folders to delete); the reach map (its
`label` stays "Sanduhr für Claude" so the existing install data keys match);
and a callout pointing to the Mac page for Desk and the config carry.

`releaseReviewed`: `["estevanhernandez-stack-ed/Sanduhr_f-r_Claude@v3.4.3"]`.

Register it: `"sanduhr/windows/index.html": "product"` in
`content/page-archetypes.json`.

### Images

Copied into the page directories under the existing `screenshot-<name>`
convention, so `sanduhr/screenshot-desk-full.jpg` and so on. Desktop captures
(`desk-full`, `desk-under-files`, `desk-corner`) become JPEG at a width of
2000 px or less, the way `screenshot-desk-corner.jpg` already is; UI captures
stay PNG. No single file over roughly 600 KB; the Mac page's images together
under roughly 4 MB. Superseded files in `sanduhr/` are deleted in the same
PR so `site-doctor` has nothing dangling and the directory says what the page
uses. The hub's `assets/sanduhr-card-shot.png` (the home card banner) is not
in scope; it still reads correctly.

### release-review: tag families

`scripts/release-review.py`'s `releases_after()` compares publish dates and
nothing else. With two markers on one repo, the `-mac` page would list every
Windows release and the Windows page every Mac release, forever.

Fix: infer the family from the marker tag. A tag matching
`^v?\d+(\.\d+)+(-[A-Za-z][A-Za-z0-9]*)?$` has a suffix or none; only published
releases whose tag carries the same suffix (or, for a bare marker, no suffix)
count as "after." A marker that does not match the pattern keeps today's
behavior. Pinned by tests in `tests/test_release_review.py`: a `-mac` marker
ignores `v3.4.3`, a bare marker ignores `v2.27.0-mac`, an unsuffixed repo is
unchanged. The CLAUDE.md row for `release-review.yml` gets one sentence.

This ships as its own PR before the page PR, so the first daily run after the
split is clean.

### The other two repos

After the hub PR is live (GitHub Pages serving /sanduhr/windows/):

- **homebrew-tap**, `Casks/sanduhr.rb`: `homepage` becomes
  `https://626labs.dev/sanduhr/`; `desc` is rewritten to name what the app is
  now, within Homebrew's conventions (short, no article, no app name, no
  trademarked product name as the subject). The README's Casks table homepage
  column follows. One PR.
- **Sanduhr**, `docs/index.html`: `<title>`, the meta description and
  `og:description` stop leading with "Windows 11 and macOS" and say the Mac
  build's two pillars with Windows named second; the Mac column's primary
  action gains the hub page link; the Windows column links /sanduhr/windows/.
  `README.md`'s macOS section gains one line pointing at the hub page. One PR.
  The landing page's layout, sections and Windows captures stay.

### Sequencing

1. Hub PR A: release-review tag families (script, tests, CLAUDE.md row).
2. Hub PR B: images, the Mac page, the Windows page, the archetype line, the
   home card, both renders, CLAUDE.md "What's where" row for the `pages`
   list naming `sanduhr-windows`. Gates: `render-product-pages.py --check`,
   `render-hub.py --check`, `pytest tests/ -q`, `site-doctor.py --check`,
   plus `copy-reviewer` on the site.json diff and `visual-asset-reviewer` on
   the new images. Ship report lists the new public URL for GSC Request
   Indexing: https://626labs.dev/sanduhr/windows/.
3. Tap PR and Sanduhr PR, after B is live.
4. Comment on Sanduhr issue #120: what is now live, and the follow-up shot
   list below.

## Sources and verified facts (answers to the builder check)

**Where the product truth lives.** All in the Sanduhr repo at `origin/main`
of `C:\Users\estev\Projects\Sanduhr` (fetched 2026-10-18; read with
`git show origin/main:<path>`, never from the stale working tree):

- 2.27.0 release notes: `gh release view v2.27.0-mac -R estevanhernandez-stack-ed/Sanduhr_f-r_Claude`
- Mods & Config spec: `docs/mods-and-config-spec.md`
- Packs spec: `docs/config-transfer-spec.md`
- Windows facts: `README.md` (the Windows and Claude Code integration
  sections) and `gh release view v3.4.3`
- Mac captures: `docs/screenshots/mac/`; Windows captures:
  `docs/screenshots/windows/` (aurora, ember, matrix, mint, obsidian,
  settings-themes). A copy of the Mac set is already extracted at
  `C:\Users\estev\AppData\Local\Temp\claude\c--Users-estev-Projects-626labs-hub\c1872199-8595-483c-aaf4-61c87b8d60bd\scratchpad\shots\`.

**The Mac captures, with their page names.** Every source is PNG, every one
is from the 2.27.0 set in PR #278 (`settings-alerts`, `settings-notch` and
`settings-themes` included). Where a page file already exists under the same
name it is overwritten in place, so indexed image URLs survive; `.jpg` names
stay `.jpg`.

| Source | px | KB | Page file | Note |
|---|---|---|---|---|
| desk-full.png | 2400x1558 | 5268 | sanduhr/screenshot-desk-full.jpg | new, hero showcase |
| desk-under-files.png | 2400x1558 | 5311 | sanduhr/screenshot-desk-under-files.jpg | new, wide shot |
| desk-corner.png | 2000x820 | 2120 | sanduhr/screenshot-desk-corner.jpg | overwrites |
| desk-limit-menu.png | 1000x1200 | 1086 | sanduhr/screenshot-desk-limit-menu.jpg | overwrites |
| desk-meters.png | 820x460 | 492 | sanduhr/screenshot-desk-meters.png | new |
| desk-clock.png | 900x440 | 510 | sanduhr/screenshot-desk-clock.png | new |
| notch-wings.png | 1100x130 | 125 | sanduhr/screenshot-notch-wings.png | overwrites |
| settings-notch.png | 1520x1416 | 556 | sanduhr/screenshot-settings-notch.png | new |
| settings-alerts.png | 1520x1416 | 611 | sanduhr/screenshot-settings-alerts.png | new |
| settings-themes.png | 1520x1416 | 290 | sanduhr/screenshot-settings-themes.png | new |
| widget-mac.png | 680x684 | 197 | sanduhr/screenshot-widget-mac.png | overwrites |
| theme-obsidian.png | 680x684 | 192 | sanduhr/screenshot-obsidian.png | overwrites |
| theme-aurora.png | 680x684 | 208 | sanduhr/screenshot-aurora.png | overwrites |
| theme-matrix.png | 680x678 | 202 | sanduhr/screenshot-matrix.png | overwrites |

Not carried: `whats-new.png` (2.4 to 2.6, dated). Candidates to delete from
`sanduhr/`: `screenshot-whats-new.png`, and any of `screenshot-accounts.png`,
`screenshot-menu-bar.png`, `screenshot-meters.png` the page stops using.

`desk-under-files.png` was looked at: the desktop files are Budget.xlsx,
Design review.key, Launch checklist.pages, Logo draft.png, Notes.txt and
Q3 plan.numbers; the account line says Work; the meetings are Design review,
Pairing: notch glow and Ship 2.3. Invented, as the commit says.

**One repo on two pages is safe.** `refresh-repo-activity.mjs` collects repos
into a `Set` (line 66), so two `data-repo` meters for one repo fetch once.
`render_repo_meter` renders per page from the entry's `repo`, so each page
gets its own meter; nothing keys pages by repo. `theme-doctor` takes its page
list from `generated_pages()` and serves nested pages at their own path
(`_served_path`), so `sanduhr/windows/index.html` joins the gate without
wiring. The Windows page's icon: copy `sanduhr/icon.png` to
`sanduhr/windows/icon.png` and keep the relative `icon.png` src, matching how
the Mac page and theme-doctor's nested-path test already work.

**Tag families in the Sanduhr repo**, every shape that exists: `vN.N.N-mac`
(37), `vN.N.N-windows` (6, all April and May 2026, the last one
`v2.3.0-windows` on 2026-05-06), bare `vN.N.N` (4, `v3.4.0` through
`v3.4.3`), four-part `vN.N.N.N` (3, `v3.1.0.0` through `v3.3.0.0`),
`untagged-...` and `legacy/python-v2.3.0`. Under the regex in "release-review:
tag families," the Windows page's bare `v3.4.3` marker is in the same family
as `v3.4.x` and the four-part tags (no suffix), and apart from `-mac` and
`-windows`. Nothing in the `-windows` family is newer than the marker, so the
split changes nothing for the Windows page today; if a future Windows release
is tagged `-windows` again, move the marker to it and the family follows.
A marker whose family has no later release reports clean even when another
family does: that is the point.

**Mac themes:** seven built in (`mac/Sources/Sanduhr/Models/Theme.swift`):
Obsidian, Aurora, Ember, Mint, Matrix, Blueprint, 626 Labs. The card may say
seven, or say nothing numeric; "five" is wrong for the Mac.

**Reviewer agents** (`copy-reviewer`, `visual-asset-reviewer`) are advisory
on style findings and blocking on one class only: a real identity, secret,
email, org or calendar entry in a capture, or a banned tier-A word in copy.

**The Store URL** for the Windows page's primary link is the product's
existing `storeUrl` without the `?cid=site-home` suffix:
`https://apps.microsoft.com/detail/9NH3NK2RGCF5`, the value the current page
already uses in its nav CTA and platform badge.

## Left to the builder

- Exact headings, deks, card bodies and captions, within the voice rules and
  the source-traceability anti-goal.
- Which of the 2.4.0 Settings captures survive, by the rule above.
- JPEG quality and exact widths, within the size budget.
- Section order inside the supporting half (widget, pacing, alerts, install)
  as long as Desk is first, the config pillar is second, and install and
  privacy are at the bottom.
- The cask `desc` wording.
- Whether the Windows page's Claude Code section is one card group or two.

## Follow-ups (not this ship)

- Captures for the config pillar, to file on Sanduhr issue #120: Mods & Config
  open on a folder with a kept mod (the "Meters above the prompt" view), the
  Export Config sheet with its checkboxes, and Compare on import. Wire them
  into pillar two when they land.
- When Windows ships a Desk-class surface, decide whether /sanduhr/windows/
  folds back or stays.
- If Store click-through from the home card drops after the Store badge moves
  below the fold on the product page, revisit the card's primary action.
