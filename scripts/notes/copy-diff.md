# 626labs.dev — copy revisions

Side-by-side of what changed and why. Voice patterns I pulled from your Smaug Jr doc: em-dash setup-then-aside, "mostly" / "pretty" hedges, concrete verbs, dry-dev-to-dev rather than marketing, a little "you'll recognize this pain" phrasing.

Nothing styling or structural changed — only the prose. Same HTML skeleton, same gradient, same card layout.

---

## Layout fixes

Two CSS issues fixed alongside the copy pass:

**Container max-width: 1100px → 1400px.** Paired with a `.container.narrow` variant (880px) used on the hero so headline + tag stay tightly centered. Hero breathes, products grid uses the full width of wide monitors. Horizontal padding bumped from 24px to 32px for a bit more edge margin.

**Install command no longer scrolls sideways.** Was `white-space: nowrap; overflow-x: auto;` which forced a scrollbar inside the card. Replaced with `white-space: normal; overflow-wrap: anywhere; word-break: break-word;` + `line-height: 1.5`. Now the `/plugin marketplace add ...` command wraps to multiple lines inside the box — still monospace, still readable, no scrollbar.

Side effect on wide screens: at 1400px+ the products grid will flow up to 4 cards per row instead of 3. The two flagship plugin cards still visually pair via their gradient border regardless.

---

## Structural change — plugins are now the lede

Vibe Cartographer and Vibe Doc were buried as regular cards below a Sanduhr flagship. Given the install numbers, that was backwards. They're now the two flagship cards up top (side by side in the grid), and Sanduhr moves into the regular grid as the third card. Coming-soons still at the bottom.

No download stat plastered on the page — the npm shields do the talking.

---

## Hero tag

**Before:**
> Open-source Claude Code plugins and a native Claude usage widget with burn-rate monitor, for builders who want AI-assisted workflows that actually land in production.

**After:**
> Open-source Claude Code plugins for turning a vibe-coded afternoon into an app that actually holds up in production — planning, docs, tests, security. Plus a native desktop widget for pacing your Claude.ai usage.

Why: puts the plugins first (they're the lede now), frames the arc as "vibe-coded afternoon → app that holds up in production" which is the real story — vibe coding your way to a stable app. Sanduhr keeps a mention but in the "plus" position.

---

## Products lead

**Before:** Everything 626 Labs ships.
**After:** What we've shipped so far.

Why: "so far" implies there's more coming, reads less like a boast.

---

## Sanduhr für Claude (now a regular card, not flagship)

**Tagline** (kept): *Pace yourself on claude.ai.*

**Before:**
> Native desktop widget that turns your Claude.ai subscription usage into something you can actually pace yourself by — burn-rate projection, pace markers, sparkline trends, and five hand-tuned glass themes. Mac + Windows. Microsoft Store listing in review.

**After:**
> Native desktop widget that shows how fast you're burning through your Claude.ai usage, so you can pace yourself instead of finding out you're out of tokens at 11pm. Burn-rate projection, pace markers, sparkline trends, and five hand-tuned glass themes. Mac + Windows — Microsoft Store listing is in review.

Why: "turns your X into something you can Y" is classic marketing scaffolding. Replaced with a concrete pain ("out of tokens at 11pm") that makes the use-case vivid. Also tightened now that it's a regular-sized card instead of flagship.

---

## Vibe Cartographer

**Tagline** (kept): *Plot your course from idea to shipped app.*

**Before:**
> A Claude Code plugin for vibe coding with purpose and direction — 11 slash commands walk you from onboarding through reflection, with self-evolving memory built in.

**After:**
> Vibe coding with a map. Eleven slash commands walk you from first idea to shipped app — onboard, scope, PRD, spec, checklist, build, iterate, reflect — and the plugin remembers where you left off so you don't lose the thread between sessions.

Why: the original buries the fact that it's 8 actual named commands. Listing them is more credible than "with purpose and direction." Also reframed "self-evolving memory" as the more human "remembers where you left off so you don't lose the thread."

---

## Vibe Doc

**Tagline** (kept): *Close the documentation vacuum.*

**Before:**
> AI-powered documentation gap analyzer. Scans your codebase, classifies what you've built, and generates the ADRs, runbooks, threat models, and specs you're missing.

**After:**
> Point it at your codebase and it tells you which docs you're missing — ADRs, runbooks, threat models, specs — then writes them. Basically, the documentation pass you keep meaning to do.

Why: "AI-powered [noun] analyzer" is the most marketing sentence on the page. Cut it. The last line reframes the product around the user's guilt about their own docs — that's where the pitch actually lives.

---

## Vibe Test

**Tagline** (kept): *Tests that match what your app actually does.*

**Before:**
> Reads a vibe-coded app, classifies its maturity tier, and generates the tests it genuinely needs — smoke, behavioral, edge, integration, performance — proportional to deployment risk.

**After:**
> Reads your app, figures out how mature it actually is, and writes the tests it actually needs — smoke, behavioral, edge, integration, performance. More coverage the closer you get to production, instead of a blanket 100% rule that nobody keeps.

Why: "classifies its maturity tier" → "figures out how mature it actually is" (plain). "Proportional to deployment risk" → "more coverage the closer you get to production" + a friendly dig at the 100% coverage doctrine.

---

## Vibe Sec

**Tagline — changed:**
- Before: *Fix the AI-prototyped security gaps.*
- After: *Close the gaps AI prototyping leaves behind.*

The old tagline worked but read a little awkward ("AI-prototyped" as a compound adjective). The new one mirrors the Vibe Doc "close the vacuum" cadence and scans better.

**Before:**
> Security scanner for vibe-coded apps. Detects the predictable gaps AI prototyping leaves behind — secrets, auth, input validation, dependencies — and generates fixes proportional to your app's deployment context.

**After:**
> The security gaps AI prototyping leaves behind are pretty predictable — leaked secrets, sketchy auth, missing input validation, stale dependencies. Vibe Sec finds them and writes the fix, scaled to where your app actually runs.

Why: leads with the honest observation ("pretty predictable") instead of the product, which is more you. Named the gaps with adjectives ("sketchy auth", "stale deps") so they read as real problems rather than categories.

---

## About 626 Labs

**Before:**
> Building native desktop apps and open-source Claude Code plugins. Builder mentality — ship then polish. Native over Electron, Python over JavaScript, and talking it through over spec'ing it out.

**After:**
> Native desktop apps and open-source Claude Code plugins, mostly. Builder mentality — ship then polish. Native over Electron, Python over JavaScript, talking it through over spec'ing it out. Things get released when they work, not when they're pretty.

Why: added "mostly" (Smaug doc voice tic), tightened the triplet by dropping the "and", and the last line makes the ship-then-polish thing more personal.

---

## What I didn't touch

- `Ship what you vibe-code` — already strong, would be a crime to mess with.
- All taglines except Vibe Sec — kept the italics/cyan subhead pattern because it's a nice visual rhythm and the lines work.
- Footer, styling, HTML structure, meta tags.

If any of the rewrites feel too far off, tell me which and I'll dial it back toward the original.
