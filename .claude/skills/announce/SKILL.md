---
name: announce
description: Draft launch announcements for a 626 Labs product across three targets — a site Field Note (written to content/stories/), an X/Twitter draft, and a Discord draft. Use when the user says "/announce", "announce <product>", "launch post for X", "write the launch copy", or wants go-to-market copy for a shipped product. Reads content/site.json + the product's latest GitHub release. Repo-local to 626labs-hub.
---

# Announce — launch copy for a 626 Labs product

Turn a shipped product into go-to-market copy in one move. Given a product,
draft a site Field Note (written into the repo), plus X and Discord drafts
(draft-only — the user posts them).

## When to use

- `/announce <product>` where `<product>` is a product `id` from
  `content/site.json` (e.g. `vibe-taker`, `celestia-3`, `vibe-test`).
- The user asks for "launch copy", "announcement", or a "launch post" for a
  shipped product.

## When NOT to use

- Long-form retrospectives — that's a hand-written Field Note, not a launch.
- Anything that posts to X / Discord automatically — this skill drafts only.

## Flow

### 1. Resolve the product

Read `content/site.json`. Find the entry in `products[]` whose `id` equals
`<product>`. Pull: `title`, `tagline`, `description`, `repo`, `install`,
`productPage`, `liveUrl`, `tags`, `npm`, `anthropicApproved`. This is the
canonical product copy — never invent product facts.

If `<product>` is missing or matches nothing, list the available ids from
`products[]` and ask the user to pick. Do not guess.

### 2. Source the release notes

GitHub Releases are the source for "what's new". Resolve the release repo
with the **same mapping the badge system uses** so the two never drift —
read the `SHIELDS_RELEASE` dict from `scripts/render-hub.py` and apply this
order:

1. If the product `id` is a key in `SHIELDS_RELEASE`:
   - if that entry has `hide: true` (e.g. `vibe-sec`), there is no release —
     go straight to degrade (2c).
   - else use its `repo` + `filter` (e.g. `vibe-test` → repo
     `estevanhernandez-stack-ed/vibe-plugins`, filter `vibe-test-v*`).
2. Else if the product's `repo` is `estevanhernandez-stack-ed/vibe-plugins`,
   use that repo with filter `<id>-v*`.
3. Else use the product's own `repo`, latest release.

Fetch with `gh`:

- No filter:
  `gh release view --repo <repo> --json tagName,name,body,publishedAt,url`
- With a `<prefix>-v*` filter:
  `gh release list --repo <repo> --json tagName,name,publishedAt -L 30`,
  pick the newest tag starting with `<prefix>`, then
  `gh release view <tag> --repo <repo> --json tagName,name,body,publishedAt,url`

**2c. Graceful degrade (common today):** if no matching release exists
(e.g. `celestia-3`, `vibe-sec`, or any product with tags but no published
Release), draft from `site.json` copy alone, omit the "what's new" section,
and say so in the closing summary. A missing release is expected, not an
error. If the repo is private or missing, skip the fetch and note it.

### 3. Draft all three

Read `references/templates.md` and `references/voice.md`. Draft the Field
Note, the X copy, and the Discord copy in their respective registers, folding
in release highlights when present.

### 4. Write the files

Use today's date (`date +%F`) for `<YYYY-MM-DD>` and the product `id` for
`<id>`.

- Site Field Note → `content/stories/<YYYY-MM-DD>-<id>-launch.md`.
  If that file already exists, warn before overwriting.
- X draft → `docs/announcements/<YYYY-MM-DD>-<id>/x.md`.
- Discord draft → `docs/announcements/<YYYY-MM-DD>-<id>/discord.md`.

The site Field Note is `draft: false`, but nothing publishes until the user
commits + pushes — the skill never commits or posts on its own.

### 5. Close

Report, in chat: the three file paths, a 2-line summary, and the next action
(review the Field Note, commit + push to publish it, paste the X and Discord
drafts). Do NOT paste the full copy back into chat — the files are the
deliverable.

## References

- `references/templates.md` — the exact shape of each of the three outputs.
- `references/voice.md` — per-channel register + the emoji policy.

Read both before drafting.
