# TikTok: converting the ex-shop account into the 626 Labs business home

**Date:** 2026-09-15
**Scope:** Convert the existing TikTok profile formerly associated with the
closed TikTok Shop into the 626 Labs brand channel. Personal profile stays
personal and untouched. No TikTok Shop; the bio drives traffic to
626labs.dev and the Conundrum Etsy shop.

---

## The account decision, and why

**Switch the ex-shop profile to a Business Account.** Not an Organization
Account.

The Organization Account requirement (effective 2026-07-01) binds only
accounts that link a TikTok Shop official account, including relinking one
after an unlink. Since the plan carries no Shop, that rule never triggers.
A Business Account is the correct and sufficient type: free, an in-app
settings toggle, and reversible.

**The conversion is non-destructive.** Existing videos, follower count,
profile, comments, and post history all survive the type switch. Nothing
is deleted and no counter resets. That is the whole reason converting this
profile beats registering a new one: whatever audience the shop era built
carries over.

### The one tradeoff, and why it barely costs us

Business Accounts see only the Commercial Music Library in the in-app
editor. Personal accounts keep trending chart audio and viral creator
sounds. Two reasons this is close to free for 626 Labs:

1. The video pipeline in this repo is **narrated**, not trend-audio driven.
   Self-recorded and self-generated audio is unrestricted on a Business
   Account, and the ElevenLabs VO chain already produces exactly that.
2. Keeping the personal profile personal preserves trending-audio access
   for anything Este posts as himself.

Worth knowing: TikTok classifies by content purpose, not only account
type, so brand-promotional posts can hit the same sound restriction even
from a personal account. The split does not create the limitation.

---

## Profile copy

All fields drafted inside real limits: username 24 chars, display name 30
chars, bio 80 chars.

### Username (24 max; letters, numbers, `_`, `.`)

| Choice | Chars | Note |
|---|---|---|
| `626labs.dev` | 11 | **First choice.** Mirrors the domain exactly; periods are legal. |
| `626labs` | 7 | Fallback if the above is taken. |
| `626labsllc` | 10 | Second fallback. Reads more corporate than the brand does. |

### Display name (30 max; spaces and emoji allowed)

`626 Labs` — 8 chars. Do not append the tagline; it pushes past 30 and the
bio carries it better anyway.

### Bio (80 max)

**Primary, 76 chars:**

```
New ideas to old logic. Claude Code plugins, apps, merch. Tap for all of it.
```

Reuses the site's own About headline ("New ideas to old logic") and ends on
the call to action a TikTok bio needs.

**Alternate, 77 chars, tagline-forward:**

```
Modern tools for old logic. Plugins, apps, and merch. Imagine Something Else.
```

Trades the call to action for the canonical tagline. Use this one if brand
consistency outranks click-through.

---

## The one-link constraint

TikTok's bio exposes a **single** website field. Two destinations are named
(626labs.dev and the Conundrum Etsy shop), so something has to fan out.

**Recommendation: build `links.html` on 626labs.dev.** Not Linktree.

Reasons, in order of weight:

1. **Traffic stays on the domain.** Every tap lands on 626labs.dev and is
   measured by the GoatCounter pipeline already running. `data/site-stats.json`
   already logs `tiktok` as a referrer, so attribution works day one.
2. **It inherits the theme.** As a `utility`-archetype page it links the
   active theme's `archetypes/utility.css` through a render-hub-owned
   `theme-css` zone, so it rotates with the site instead of freezing in
   phosphor-blueprint.
3. **No third-party dependency** on a surface whose only job is routing
   traffic we own to destinations we own.
4. `?ref=tiktok` is already the established UTM convention in
   `docs/video-plan-store-apps.md`.

Link targets for the page: Celestia 3, RORORO, 626 Mod Launcher, the Claude
Code plugin family, the Conundrum Etsy shop, and the GitHub org.

**Bio link value:** `https://626labs.dev/links.html?ref=tiktok`

---

## The avatar gap

There is **no opaque square 626 Labs avatar** in `assets/brand/` today.
What exists:

| Asset | Size | Problem |
|---|---|---|
| `icon-transparent-512.png` | 512x512 | Has alpha. TikTok composites it, likely on white, which breaks the dark-navy field. |
| `logo-portrait-256.png` | 256x384 | Opaque but portrait, not square. TikTok crops to a circle. |
| `vibe-plugins-square-1024.png` | 1024x1024 | Opaque and square, but it is the Vibe Plugins mark, not 626 Labs. |

TikTok renders the avatar as a circle from a 200x200 source, so it needs an
opaque square with the mark centered inside the safe circle.

Two ways to close it:

- **Durable (preferred):** add a square avatar output to
  `scripts/export-brand.py`. It then reads the active theme's `raster`
  block via `scripts/raster_theme.py` and regenerates on rotation like
  every other brand raster.
- **Quick:** one-off into `assets/social/tiktok/`. Never into
  `assets/brand/`, which is a generated directory.

---

## Split of work

### Este, in-app (cannot be done from this repo)

1. Settings → Account → **Switch to Business Account**. Pick a category
   (Software / Technology fits).
2. Set username, display name, bio from the copy above.
3. Upload the avatar once generated.
4. Paste the bio link.
5. Audit shop-era posts. Anything off-brand for 626 Labs should be deleted
   or set private before the profile gets pointed at from the site.

### This repo (agent work)

1. Build `links.html` as a `utility`-archetype page in the active theme.
2. Map it in `content/page-archetypes.json` as `"utility"` so it joins the
   visual-diff sweep and gets themed on rotation.
3. Add a `tiktok` row to `content/site.json` → `contact.rows` once the
   handle is locked. There are currently **zero** TikTok references in
   `site.json`.
4. Generate the square avatar.
5. Run `render-hub.py`, then `site-doctor.py --report` (note: `--check`
   exits 1 silently).

### After merge

Request Indexing for `https://626labs.dev/links.html` in Google Search
Console → URL Inspection. Sitemap resubmission is not needed.

---

## Sources

- TikTok Shop account closure policy (closed shops cannot reopen; identity
  docs reusable) — seller-us.tiktok.com
- Organization Account requirement for Shop official accounts, effective
  2026-07-01 — seller-us.tiktok.com, ads.tiktok.com
- Account-type switch is non-destructive; Commercial Music Library
  restriction — blog.hootsuite.com, soundstripe.com
- Profile field limits (bio 80, display name 30, username 24, avatar
  200x200) — multiple 2026 character-limit references
