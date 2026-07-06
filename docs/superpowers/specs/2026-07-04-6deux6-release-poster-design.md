# 6deux6 — the 626 Labs release poster — design

> **Date:** 2026-07-04 · **Status:** approved (brainstormed live with Este, all forks settled)
> **Lineage:** Part B of the 626 Discord plan. Part A (dedicated server + The Architect)
> shipped 2026-07-03/04 — see `docs/626-discord-runbook.md` and
> `docs/superpowers/specs/2026-07-03-626-discord-design.md`. This spec supersedes the
> original Part B sketch where they differ (host, Store signal, identity).

## What this is

A lean, installable Discord bot that posts 626 Labs releases to `#releases` on the
626Labs server — and, by config, to anyone else's server. It polls GitHub Releases
and the Microsoft Store, diffs against last-seen state, and posts one branded embed
per new version. It never speaks otherwise, never listens, and holds no permissions
beyond posting.

The powerful identity (The Architect, broad perms) stays home on 626's own server;
6deux6 is the separate minimal-perm identity built to travel.

## Decisions (locked 2026-07-04)

| Fork | Decision |
|---|---|
| Name | **6deux6** — 626 with the deux pivot; brand-as-name for an artifact that wanders other people's servers. Renamed from Noctis in the dev portal (done, 2026-07-04). |
| Identity | Reuses the Noctis Discord application, ID `1475660206099927164` (created 2026-02-24). Public key unused (no interaction webhooks). Bot token enters GitHub repo secrets at deploy time — never chat, never committed. |
| Host | **GitHub Action** in the poster's own repo, hourly cron. Zero hosting, fork-and-run portability. Firebase Function noted as a later option; source stays host-agnostic (state behind a small interface). |
| Store signal | **displaycatalog** — `https://displaycatalog.mp.microsoft.com/v7.0/products?bigIds=<ProductId>&market=US&languages=en-us`, unauthenticated, returns exact package versions (verified against all 6 apps 2026-07-04). Product IDs seeded from site.json `storeUrl`s. |
| Transport | **REST-only.** A poster receives nothing: no gateway, no intents, no discord.js. Bare `fetch` → `POST /channels/{id}/messages` with the bot token. |
| Double-announce rule | Each watch target has exactly **one** source in config. RORORO (in both the Store and GitHub) watches displaycatalog — its audience installs from the Store. |
| State | `state.json` committed back to the repo after each successful run, retry+rebase push loop (the pattern the hub's six bots prove). |
| Repo | **`6deux6`**, public, under `estevanhernandez-stack-ed`. |
| Voice | **Hybrid** (locked 2026-07-04): voice-crafted templates as the deterministic base; optional Claude blurb pass (Haiku) when an `ANTHROPIC_API_KEY` secret is present. The voice ships as a swappable `voice.md` — bring-your-own-personality is part of the portability story. |

## Architecture

One small Node program (no framework, ESM, Node 20+), run by a scheduled workflow:

```text
config.json ─→ poller ─→ [github.js | displaycatalog.js] ─→ diff vs state.json
                                                                │ new versions
                                                        embed builder ─→ discord.js*
                                                                │ success
                                                        state writer ─→ commit+push
```

*`discord.js` here is a ~40-line module of ours (REST post + retry), not the npm package.*

### Modules

- **`src/sources/github.js`** — latest release per `owner/repo` via the public Releases
  API (`GITHUB_TOKEN` from the workflow covers rate limits). Returns
  `{ version, url, notes, publishedAt }` or null for repos with no releases yet.
- **`src/sources/displaycatalog.js`** — versions per Store product ID; parses
  `PackageFullName`s (`_1.8.0.0_` → `1.8.0.0`), takes the highest. Returns
  `{ version, url }` where url is the product's `apps.microsoft.com/detail/<id>` page.
  No release notes exist on this source; embeds omit the excerpt.
- **`src/diff.js`** — pure function: `(targets, state, fetched) → newReleases[]`.
  A release is new iff `state[target.id].version !== fetched.version` and fetched is
  non-null. First-ever run seeds state WITHOUT posting (see cold start).
- **`src/embed.js`** — pure function: release → Discord embed JSON (format below).
- **`src/discord.js`** — REST post with the bot token; 429-aware (honors
  `retry_after`), fails loudly on 4xx.
- **`src/voice.js`** — the personality layer. If `ANTHROPIC_API_KEY` is set, calls
  Claude (small tier — Haiku; model id in config with a current default) with
  `voice.md` + the release notes + product context, and returns a 1–2 sentence
  in-voice blurb (hard cap 300 chars, post-truncated if the model runs long). On any
  failure — key absent, timeout, 4xx/5xx — returns null and the embed builder falls
  back to the template excerpt path. The LLM can delay a post by one API call; it
  can never block one.
- **`src/state.js`** — read/write `state.json`; the workflow commits it back with a
  retry+rebase loop identical to the hub bots'.
- **`src/index.js`** — orchestration + `--dry-run` flag (prints embeds, writes no
  state, posts nothing).

### Cold start

On first run (empty state), every target would look "new." Instead: seed
`state.json` with current versions and post nothing. Announcements begin with the
first release that lands *after* adoption. This also makes onboarding a new watch
target silent — it announces from its next release, not its whole history.

### Idempotency invariants

1. State advances per-target only after that target's embed POST returns 2xx.
2. A crashed or rate-limited run leaves un-posted targets un-advanced — the next
   hourly run retries them.
3. A version can never post twice: the diff is equality-based against committed
   state, and the state commit races are resolved by the retry+rebase push.
4. Re-running an already-clean hour is a no-op (fetch, diff → empty, exit 0).

## Watch-list (v1 config seed)

- **GitHub Releases source:** the 14 hub `plugin-repos.json` entries (Vibe family +
  thesis-engine), plus `rororo-ur-task`, `Ur-OCR`, `rororo-ur-afk` (RoRoRo plugin
  family), plus `626-mod-launcher`.
- **displaycatalog source:** the 6 Store apps — Sanduhr für Claude `9NH3NK2RGCF5`,
  RBX15 Shirt+Pants `9MV9G4XFJ8S0`, Right Click PNG `9PKKLK6R5WFL`, SnapSnip
  `9PBX8F5TR0VR`, RORORO `9NMJCS390KWB`, 626 Mod Launcher `9N53V6RRJK95`.
- 626 Mod Launcher appears on BOTH lists intentionally: the GitHub repo releases
  pre-Store builds and the Store entry trails; they're distinct targets with distinct
  ids (`mod-launcher-gh`, `mod-launcher-store`) so each announces its own channel of
  availability. RORORO is Store-only per the double-announce rule.

## Embed format

- **Title:** `<product> <version>` (e.g. `RORORO 1.8.0`), linked to the release/Store page.
  Version display normalization: strip a leading `v` from GitHub tags (`v1.2.0` → `1.2.0`);
  strip one trailing `.0` from 4-part Store versions (`1.8.0.0` → `1.8.0`). State stores the
  RAW source version — normalization is display-only, so it can never cause a re-post.
- **Accent color by family tag:** `plugin` → cyan `#17d4fa`, `rororo` → magenta
  `#f22f89`, `store` → violet `#8552c2` (the gradient's midpoint).
- **Description:** notes excerpt — first meaningful paragraph, hard cap 300 chars,
  ellipsis on truncation. Store targets (no notes) get the product's one-line blurb
  from config instead.
- **Footer:** `6deux6 · the 626 Labs release feed` + family tag.
- Sparing emoji allowed (Discord register): 🚀 prefix on the title, nothing else.

## Voice + personality

The 626 publishing voice is a first-class component, not decoration:

- **`voice.md`** — a distilled voice prompt committed in the repo: builder-to-builder,
  second person, punchline first, no corporate speak (the banned-words list rides
  along), sparing emoji, "Imagine Something Else." as the registered closer. Distilled
  from the estate's publishing + announce skills at build time. Forkers replace this
  one file to give the bot THEIR voice — the personality is config, not code.
- **Templates carry the voice on their own.** Title patterns ("`<product> <version>`
  just shipped"), a per-family flavor line, and the footer are written in-voice so a
  keyless fork or an API outage still sounds like the brand, just less bespoke.
- **The blurb pass adds the bespoke layer.** With a key present, `voice.js` writes the
  embed description from the actual release notes — what shipped, why it matters, one
  or two sentences, in-voice. The template excerpt is the always-there floor.
- **Boundary:** 6deux6's personality lives in its copy. It does not converse, react,
  or hold presence (REST-only — presence requires a gateway connection it doesn't
  have). On the 626 server, conversation is The Architect's job; 6deux6 is the byline.
- **Portal surfaces:** the app's About/description carries the release-feed copy and
  tagline (human-set in the dev portal — the API doesn't expose app descriptions to
  the bot itself).

## Config shape

```json
{
  "channelId": "1522754011915227153",
  "targets": [
    { "id": "vibe-sec", "source": "github", "repo": "estevanhernandez-stack-ed/vibe-sec", "family": "plugin" },
    { "id": "rororo", "source": "displaycatalog", "productId": "9NMJCS390KWB", "family": "rororo",
      "blurb": "The Roblox multi-launcher you can recommend on camera." }
  ]
}
```

Secrets: `DISCORD_TOKEN` (repo secret, required) and `ANTHROPIC_API_KEY` (repo
secret, optional — presence enables the voice blurb pass). `channelId` is plain
config — channel IDs aren't secrets. A stranger forks the repo, edits `config.json`,
sets one secret (two if they want the LLM voice), enables the workflow. That is the
entire install. Config gains a `voice` block: `{ "model": "<current-haiku-id>",
"maxChars": 300 }` — the enabled/disabled switch is simply whether the key exists.

## Error handling

- Source fetch failure for one target → log, skip that target, continue the run
  (state untouched for it).
- Discord 429 → honor `retry_after` once, then defer to next run.
- Discord 4xx (bad token / missing access) → fail the workflow run loudly; this is
  a configuration error a human must see.
- Malformed `PackageFullName` (no version match) → treat as fetch failure for that
  target, log the raw string for diagnosis.
- Voice pass failure (timeout, quota, bad key) → log, fall back to the template
  excerpt, post anyway. The announcement never waits on the personality.

## Testing

- Unit: `diff.js` (new/same/null/cold-start cases, the never-double-post invariant),
  `embed.js` (families, truncation, notes-less Store targets), version parsing in
  `displaycatalog.js`, `voice.js` fallback chain (no key / API error / over-long
  blurb → cap) with the Claude call mocked.
- Fixtures: canned GitHub + displaycatalog JSON responses; no live calls in tests.
- Integration: `node src/index.js --dry-run` against real config = the local dev
  loop and the pre-merge smoke test.

## Identity assets + human-only steps

- **Icon:** brand-style app icon, distinct from The Architect's brain mark — navy
  field, neon cyan/magenta, up-arrow "ship it" motif. Built by script in the 6deux6
  repo (`scripts/build-icon.py`, PIL, export-brand conventions); Este uploads to the
  dev portal (App Icon) — bots can't set their own app icon via API.
- **Description (dev portal):** reuse the release-feed copy from the runbook's bot
  identity section — it was written for this role.
- **Este, at deploy time:** upload icon; invite 6deux6 to the 626Labs server via
  `https://discord.com/oauth2/authorize?client_id=1475660206099927164&scope=bot&permissions=84992`
  (View/Send/Embed/Read History only); grant it a Send allow on `#releases` (the
  @everyone lockdown silences bots without their own overwrite — runbook gotcha 7);
  put the bot token in the repo's `DISCORD_TOKEN` secret.

## Verification readiness (pre-wide-launch, not pre-build)

Discord app verification gates growth past ~75 servers and grants the trust badge —
irrelevant for The Architect's bot (one server forever), future-required for 6deux6.
The portal checklist (seen 2026-07-04) needs three things:

1. **Team ownership** — Este creates a "626 Labs" Team in the dev portal and
   transfers 6deux6 (and the other 626 apps) into it. One-time, covers all apps.
2. **Terms of Service + Privacy Policy links** — two short pages hosted on the hub
   at `626labs.dev/legal/`, drafted during the 6deux6 build. 6deux6's honest privacy
   story: it stores no user data whatsoever — no message content, no user IDs; its
   only state is public product version numbers in a public JSON file.
3. Everything else (install link, 2FA, language) already passes.

None of this blocks the v1 build — verification is submitted when the bot goes
public-installable.

## Out of scope (v1)

- Slash commands, two-way anything, moderation — 6deux6 posts, full stop.
- Hosted config UI for other-server admins (fork + edit config.json is v1).
- Announcement crossposting automation (#releases is an announcement channel; if
  auto-publish is wanted later it's one extra REST call — noted, not built).
- The hub's `site.json` prose diffs and Field Note triggers (the hub has its own
  pipelines; 6deux6 reads only GitHub + displaycatalog).
