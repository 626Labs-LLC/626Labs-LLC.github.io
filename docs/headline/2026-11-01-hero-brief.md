# New homepage hero: decision brief

## What the hero has to do

Your homepage is not where people find you. It got **60 of 1,601 tracked hits** (about 4%) from Oct 2 to Nov 1. **/rororo.html got 1,318 (82%)**, nearly all from search, mostly Bing. Two things follow. First, the hero speaks to second-click visitors: RoRoRo players checking who made the thing, builders arriving from a plugin page, Sanduhr or GitHub, and peers following a Discord or X link. Second, rewriting the hero alone barely moves the numbers. The bigger lever is the path from /rororo.html to the lab: a band on the RoRoRo page that says who built it and links home, plus the homepage title and meta description Bing shows in results.

The hero's job is still real, because it is your identity page for anyone who looks. The current one leads with three categories ("Astrology engines, dev tools, streetwear."). That shows no proof and no center, and it never names the product 82% of your traffic came for. The fix is to open with one usage number people can check, name RoRoRo first, and turn the shelf list into range ("same bench") rather than a jumble. *Imagine Something Else.* keeps the identity job.

Two mechanical notes before the directions:

- **Only 4 chips render** (`render_chips` slices `[:4]`). Chip labels are free text, so `celestia 3 · conundrum` renders as one chip and is a legitimate way around the limit.
- **Don't wire a live DAU number into render-time `{{fact:}}` tokens.** The store-analytics bot writes daily and doesn't trigger a rebuild. A token derived from `data/store-analytics.json` would make `render-hub.py --check` drift every morning and trip site-doctor and the rotation gate. You have two clean options. One is a static number with a date on it ("Oct 2026"). The other is a runtime fill in the browser, like the repo meter. Don't build a third.

---

## Direction A: proof from habit

| Field | Copy |
|---|---|
| Eyebrow | 626Labs LLC · Fort Worth, TX *(unchanged; it is the legal-entity trust signal)* |
| Headline | Software people leave running. |
| Accent | Imagine Something Else. |
| Subhead | RoRoRo, the free Windows multi-launcher for Roblox, went from 142 to 299 daily Store users in a month. The same bench ships Sanduhr for your claude.ai limits, 21 open-source Claude Code plugins, Celestia 3 and the Conundrum streetwear line. One builder, Fort Worth. |
| Deployed | RoRoRo 299 daily Store users, Oct 2026 · Sanduhr Mac v2.39 · 6 Microsoft Store apps · 21 plugins |
| Chips | `rororo · 299 daily` · `sanduhr · v2.39` · `vibe plugins · 21` · `celestia 3 · conundrum` |
| CTAs | See the work (#work) / Get RoRoRo (Store link) *(replaces Try Celestia 3)* |

**Why it works.** Retention imagery: an app left open in the tray is stronger proof than a download, and it implies trust without saying the word. The headline is a claim about the whole lab. The first sentence of the subhead pays it off with a number Microsoft reports, not you, inside the five-second window. "Same bench" lets the other shelves read as range.

**Who it wins and who it costs.** It wins the RoRoRo arrival (their app is named first, free, and on the Store), the cold visitor (a picturable product plus a number), and the skeptic (no hype words). It costs a little with the Celestia and Conundrum audience, who get one clause and half a chip. The headline also fits RoRoRo and Sanduhr far better than merch or astrology, so it is a lab claim propped up by two products.

**Grafts.** Retention frame from attention-psych-3. "Off the same bench" from portfolio-keeper-1. The packed fourth chip and dated DAU from the portfolio-balance judge. I dropped "actually" from the original headline, because it reads as defensive. "Doubled" became "from 142 to 299", which is more checkable and doesn't overstate a noisy daily series that peaked at 334.

---

## Direction B: small place, wide reach

| Field | Copy |
|---|---|
| Headline | Built in Fort Worth. Installed in 139 markets. |
| Accent | Imagine Something Else. |
| Subhead | That's RoRoRo, a free Windows multi-launcher for Roblox, on the Microsoft Store from the US to the Philippines to Brazil, rated 4.41 from 17 ratings. One builder also ships Sanduhr, 21 Claude Code plugins, Celestia 3 and a streetwear line. |
| Deployed | RoRoRo in 139 Store markets · Sanduhr in 77 · 6 Microsoft Store apps · 21 plugins |
| Chips | `rororo · 4.41 on the Store` · `sanduhr · mac + windows` · `vibe plugins · 21` · `celestia 3 · conundrum` |

**Why it works.** Local origin set against global reach. A city name next to a big countable number opens a "how did that happen" gap, and it rewards readers who root for small outfits. It is two beats, not a triad, so it avoids the rule-of-three tell (proposed Tier D in banned.md).

**Who it wins and who it costs.** It wins cold visitors, peers, recruiters and press, and it is the most memorable line in the set. Your visitor mix backs it up: Philippines 180, France 104 and the UK 93 are all real. It costs on proof of use, because a market count measures reach, not activity. It also gives builders nothing they recognize until the subhead.

**Grafts.** Shape from attention-psych-5. The rating chip from roblox-player-1. "Used" became "Installed", because 139 is markets with at least one install, so "used" overclaims. Keep "markets", never "countries": the countries version was disqualified. The subhead has to tie 139 to RoRoRo by name ("That's RoRoRo"), or the line implies all six apps reach that far.

---

## Direction C: cadence as proof (builder-first)

| Field | Copy |
|---|---|
| Headline | Shipping every week, from one desk in Fort Worth. |
| Accent | Imagine Something Else. |
| Subhead | RoRoRo, the free Roblox multi-launcher with 299 daily Store users, hit v1.35 on Oct 26. Sanduhr shipped v2.37, v2.38 and v2.39 between Oct 29 and Nov 1. Plus 21 open-source Claude Code plugins, Celestia 3 and Conundrum. The release pages are public. |
| Deployed | RoRoRo v1.35 (Oct 26) · Sanduhr v2.39 (Nov 1) · 6 Microsoft Store apps · 21 Claude Code plugins |
| Chips | `sanduhr · v2.39` · `rororo · v1.35` · `vibe-test · live` · `celestia 3 · conundrum` |

**Why it works.** Maintenance is the proof. Builders judge a tool by its release cadence, and dated versions answer "is this abandoned" faster than any adjective. "The release pages are public" invites checking: it says the claim can be proven wrong.

**Who it wins and who it costs.** It wins the Claude Code builder and the half-sold GitHub visitor. It is also the only direction that ties naturally into the release-review machinery you already run. It costs on shelf life: one quiet fortnight and the headline is false. "Every week" is accurate for Sanduhr but only "weekly-ish" for RoRoRo. The dates also go stale within days, unless the meta line follows `data/plugin-versions.json`-style data or the release-review pass picks it up. Roblox players get tempo but less reassurance.

**Grafts.** Falsifiability line and dated versions from claude-builder-2 and roblox-player-1. The DAU number is pulled into the subhead so the cadence claim isn't carrying the trust work alone.

---

## Direction D: fix the path, not just the hero

Not a homepage headline. It is a decision about where the copy goes.

- **On /rororo.html** (generated from its `pageSpec`), add a short band below the fold or above the footer: *"The lab behind RoRoRo. 626Labs LLC is one builder in Fort Worth. Same bench: Sanduhr, 21 open-source Claude Code plugins, Celestia 3, Conundrum."* Link it to the homepage.
- **Homepage `<title>` and meta description:** name RoRoRo and the lab together, so Bing's snippet confirms searchers are on the right site before they click.

**Why it works.** It meets the 82% where they actually land. "The lab behind RoRoRo" names their path and stops the wrong-site bounce. As a homepage headline it confuses everyone who didn't arrive from RoRoRo, which is why it scored 18.5. On the RoRoRo page it costs nothing.

**Who it wins and who it costs.** It wins the RoRoRo search audience, by a wide margin, and it routes them into the rest of the lab. It costs nothing on the homepage. It is extra work on a second generated page, so it needs a pass from `render-product-pages.py` and site-doctor.

**Grafts.** Orientation line from roblox-player-4. Trust detail from roblox-player-2 and attention-psych-4 ("free, native on Windows, encrypted local account vault"), which belongs on the RoRoRo page more than in the homepage hero.

---

## Recommendation

**Ship A on the homepage and D on /rororo.html together.**

A is the only direction that does all three jobs at once. It names RoRoRo first for the arrivals, puts a third-party usage number inside five seconds for the skeptics, and holds the other shelves together as one lab without turning the site into a Roblox tool shop. That answers "don't lose focus on anything" better than B (reach, no proof of use) or C (only true while the cadence holds). D is where the traffic actually is. Without it, the new hero is a good line that about 60 people a month read.

Keep B's headline in reserve. It is the strongest social and OG-card line in the set ("Built in Fort Worth. Installed in 139 markets.") and works well as an X or Discord post or the homepage OG title, even if it is not the H1.

**What would change my mind:**

- **If the homepage referrers turn out mostly builders** (GitHub, plugin pages, the Claude Code mod), go with C. Pull GoatCounter's referrers for `/` alone before shipping; 60 hits is enough to see the mix.
- **If 299 was a spike** (the window peaked at 334, and Store data lags 2-3 days), A's number gets shaky. Lead with the rating instead (`4.41 from 17 ratings`) and soften the headline.
- **If you'd rather the hero speak in first person,** cold-visitor-4's "I build the apps" frame beats all of these on the "is there a real human" test. It is a departure from the brand's second-person voice, and that call is yours.

---

## Open questions only you can answer

1. **Store install total (about 4,950):** lifetime or a 30-day sliding window? Until that is settled, no direction quotes it. (Your memory notes the Store API silently ignores `startDate`, so it may be a window.)
2. **142 and 299:** single-day readings or averages, and which dates exactly? "From 142 to 299 in a month" should rest on the two exact days, and the copy should date it.
3. **Is 4.41 from 17 ratings the global figure or one market's?** Store ratings can be split by market. The chip must match what a click on the Store shows.
4. **Is RoRoRo for Mac (rororo-mac, 555 installers) public enough to claim on the homepage?** If it is, "Windows multi-launcher" undersells it. If it isn't, leave it out.
5. **The secondary CTA:** are you OK retiring "Try Celestia 3" for "Get RoRoRo", or should Celestia keep the button?
6. **"Free" scope:** are all six Store apps free (RBX15, Mod Launcher, Right Click to PNG, SnapSnip)? If any are paid, "free" stays attached to RoRoRo by name only.
7. **Refresh owner:** any hero carrying a DAU number or version needs a refresh rule. That means a dated static number you re-read monthly (possibly at the theme rotation on the 1st), or a runtime fill. Which one?