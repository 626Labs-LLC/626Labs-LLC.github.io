# 626labs.dev audit, 2026-11-17

Sources: Search Console (`sc-domain:626labs.dev`, 28 days to 11-15), GoatCounter (`data/site-stats.json`, 10-18 to 11-17), `content/site.json`, and the live pages measured in Chrome at 1889px wide.

## The headline

**The portfolio is not the front door. `rororo.html` is.**

| Page | Visits, 28 days | Share |
|---|---|---|
| `/rororo.html` | 1,721 | 84% |
| `/rororo-plugins.html` | 95 | 5% |
| `/` (the portfolio) | 67 | 3% |
| `/privacy.html` | 24 | 1% |
| every other page | 16 or fewer each | |

Total 2,055. The homepage reorder was a good call and it reaches 3 visitors in 100. What the other 97 learn about 626Labs is decided by the RoRoRo page, and on that page "The lab behind it" starts at y=9,053 of 9,532px: 95% of the way down, one paragraph and one link. The nav's "The lab" link is `hideSm`, so it is gone on small screens.

## What Search Console says

305 clicks, 6,150 impressions, 5% CTR, average position 5.8.

- `rororo.html`: 260 clicks, 4,550 impressions. 85% of all Google clicks.
- Homepage: 5 clicks, 128 impressions.
- Desktop 257 clicks at 5.8% CTR. Mobile 45 clicks at 2.7% on 1,653 impressions.
- Countries by clicks: US 64, Russia 40 (11.8% CTR), Philippines 26, Indonesia 17, Brazil 15, UK 9, India 9, South Korea 8.
- Indexing: 100 indexed, 118 not. 100 of those are "Discovered, currently not indexed", 12 are "Crawled, currently not indexed". The property includes celestia. and dash., so I have not verified which host the 100 belong to. Celestia's `/learn/` pages (ranking 45 to 72 today) are the likely source.

### Queries with impressions and no clicks

| Query family | Impressions | Clicks | Position |
|---|---|---|---|
| is rororo safe / is rororo safe? / is rororo safe to use? / is it safe? | 112 | 0 | 3.6 to 10 |
| snapsnip | 27 | 0 | 5.9 |
| vibe sec / vibesec / vibe sec skill | 47 | 0 | 8.4 to 10.2 |
| game mod launcher / modlauncher / mod launcher | 32 | 0 | 7.5 to 9.5 |
| vibe coded plugins / vibeplugin | 45 | 0 | 6.1 to 12.5 |

### Pages with impressions and thin clicks

| Page | Impressions | Clicks | Position |
|---|---|---|---|
| `/plugins/` | 430 | 13 | 9.6 |
| `/mod-launcher-games.html` | 403 | 4 | 8.1 |
| `/editorial/2026-07-03-rororo-grew-a-family/` | 357 | 4 | 7.6 |
| `/rororo-trailer.html` | 227 | 2 | 6.8 |
| `/vibe-sec/` | 90 | 0 | 12.1 |

## The number nobody is celebrating

Google sent 280 visits in the GoatCounter window. **Bing sent 1,361.** Yahoo (199) and DuckDuckGo (44) both run on Bing's index, so Bing's index is behind roughly 1,600 visits, close to six times Google. The repo has no `BingSiteAuth.xml` and no `msvalidate` meta. That does not prove Bing Webmaster Tools is unset (DNS verification leaves no trace here), but if it is unset, the query data for three quarters of search traffic is unread.

## Findings, ranked by what they are worth

### 1. Give the RoRoRo page a lab strip, matched to its audience

2,014 of the window's visits were on Windows, and they searched for a Roblox tool. The lab's offer to that person is RBX15 (Roblox shirt and pants maker), the 626 Mod Launcher, the RoRoRo plugins and the games, in that order. It is not Claude Code plugins. RBX15 got 8 visits in 28 days while 1,721 Roblox players read the page next door.

- Add a "More from the lab for Roblox players" block right after "Get it" (y≈1,800), two or three cards, RBX15 first.
- Keep "The lab behind it" at the bottom for the wider story.
- Drop `hideSm` from "The lab" nav link, or swap it with "Source".

This is a `pageSpec` edit in `content/site.json`. It may need one new block type in `render-product-pages.py`'s `BLOCKS` table if `panel` plus `cta` cannot carry cards.

### 2. Answer "is RoRoRo safe?" in those words

112 impressions, zero clicks, and the page already has the answer. "The honest part" covers injection, the ban risk and provenance, and the word "safe" appears nowhere in the page spec. The search result gives a worried reader no reason to pick this listing.

- Add a question-shaped heading, "Is RoRoRo safe?", over the existing risk copy, with a two-sentence direct answer first. Keep the honesty: no injection, official client unmodified, ban risk low and not zero.
- Work the phrase into the meta description.
- Add `SoftwareApplication` JSON-LD. The page carries zero structured data today; the homepage has Organization, Person and WebSite. `pageSpec.jsonLd` already exists for the watch pages.

FAQ rich results are restricted to government and health sites since 2023, so an FAQPage block will not earn the accordion. The win is the matching heading and snippet.

### 3. Verify Bing Webmaster Tools and submit the sitemap

Ten minutes, and it can import the property from Search Console. Worth doing before any other SEO work, because the larger audience's queries live there.

### 4. Measure the click that matters

No page except `conundrum.html` fires a GoatCounter event. 1,721 people a month reach the RoRoRo page and the site cannot say how many press "Get it on Microsoft Store". The Store links carry `cid=site-product`, so Partner Center has an acquisition-side number, but the on-page rate is unknown. Add click events on the Get CTAs (Store, GitHub Releases, Homebrew) so the next change to the page can be judged.

### 5. Cut the RoRoRo home row from a spec sheet to a pitch

The homepage is 15,646px tall. The Work section is 7,104px of it. RoRoRo's row runs 262 words, about 950px, and reads as release notes: .NET 10, DPAPI, WebView2, Velopack, named-pipe IPC. Sanduhr is 135, Celestia 112, the plugins 47 to 95. A portfolio row should say what it is and why it matters in about 60 words and let the product page carry the rest.

Caution: the page-pane mod reads `products[].description` from raw `main`. Shortening is safe; renaming the field is not.

### 6. Decide what "offer" means, then say it above section 07

The contact lead asks "Got a codebase that needs rounding out? Want early access to the Dashboard?" Those are two real offers, a service and a product waitlist, and they appear once, as questions, at y=14,795 of 15,646.

- **Build work.** The founding copy argues for exact-fit software and the About copy names legacy operations, safety inspections, hotels and cinema. The proof (Safety Assistant, Lobby Engagement Suite, L.A.D.D.E.R.) sits in the Notices back page at y=13,674. If inbound build work is wanted, it needs its own short section with those three as evidence and a direct ask. If it is not wanted, the contact lead should stop implying it.
- **The Dashboard.** "How the lab runs" shows three screenshots and no action. If early access is real, the button belongs there.

This one is Este's call. Everything else here can proceed without it.

### 7. Two larger plays, each a project

- **Localized RoRoRo landing pages.** Russia, the Philippines, Indonesia, Brazil and South Korea are five of the top eight countries. Queries arrive in Cyrillic, Korean and Bengali. The app ships in six languages and the page swaps language client-side on one URL with no `hreflang`, so Google indexes English only. Static `/rororo/<lang>/` pages from the same `pageSpec` would give each language its own listing.
- **Per-game Mod Launcher pages.** One list page drew 403 impressions, including "death stranding vr mod" and "sons of the forest vr mod". The manifest holds 149 games and regenerates daily. A generated page per game is the long-tail version of what the list page is already ranking for by accident.

## What is already right

- Title and description on both key pages are specific and current. The homepage title names RoRoRo and Sanduhr, which matches where the traffic is.
- The hero leads with the live daily-user number, and the product order follows the hero.
- "The honest part" is the strongest trust copy on the site. It only needs to be findable.
- Sitemap (53 URLs), robots, canonical handling and the release-review pipeline are sound.

## What happened the same day

- **Dashboard early access: pulled** (#318, merged). Este's call: not ready to push it forward.
- **Findings 1, 2 and 4: in one PR**, `feat/rororo-front-door`, waiting on Este's read of the new copy.
- **The `SoftwareApplication` JSON-LD in finding 2 was not added.** Google requires `aggregateRating` or `review` on that type, and flags the item invalid without one. The page collects no ratings of its own, and Google's rules bar marking up ratings gathered elsewhere (the Store's). Shipping it would open a standing error in Search Console for no rich result. Revisit if the page ever collects its own reviews.
- **Search Console:** four of the five stuck pages from October are indexed. `year-in-review.html` is not, and was not re-requested (the fix there is content). `vibe-cartographer/` and `vibe-insights/` turned up as "Crawled, currently not indexed" and had indexing requested for the first time. Sitemap last read Nov 11 with all 53 URLs, so no resubmit.
- **Bing Webmaster Tools:** the site is at a sign-in wall in the lab's browser. Still Este's to verify.
