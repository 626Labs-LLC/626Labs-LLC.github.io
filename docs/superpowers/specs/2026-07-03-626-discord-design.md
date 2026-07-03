# 626 Labs Discord — server scaffold + release bot — design

> **Date:** 2026-07-03 · **Status:** approved (brainstorm, 626labs-hub seat)
> **Scope:** two decomposed projects — (A) a 626 Labs home in Este's personal Discord server, scaffolded now; (B) a server-agnostic release-announcement bot, built after this design. Part A and Part B each get their own implementation plan; Part A ships first.

## Context

626 Labs ships to a gaming-adjacent, Discord-native audience; GitHub is foreign to them. The goal is a landing spot for releases, community, and answer-once-help-many support (the RoRoRo "is it broken / what's a CAPTCHA" load already lands in Discord DMs). Prior plan: personal server first (no audience to seed a branded server yet), a real bot (not a webhook) that becomes a portable, installable portfolio artifact. This design confirms the staged approach and settles the architecture.

Related memory: `project-discord-release-channel`, `626-windows-deployment-cadence` (Store releases don't hit GitHub Releases), `feedback-emoji-launch-caveat` (Discord register allows sparing emoji).

## Decisions (locked with Este, 2026-07-03)

| Fork | Decision |
|---|---|
| Server home | **Staged.** Scaffold in Este's personal server now; build the bot server-agnostic so it travels; stand up a dedicated 626 Labs server when there's an audience to move. |
| Channel layout | **Lean unified.** One 626 Labs category: `#releases`, `#general`, `#support`, `#ideas`. No per-product split yet. |
| Bot delivery | **Scheduled poller.** Diff-against-last-seen, post branded embeds. No inbound webhook. |
| Watch scope | Claude plugins (Vibe family) + RoRoRo plugins (ur-task, ur-ocr, ur-afk) + the 6 Microsoft Store apps. |
| Store signal | **Hub-data-driven.** The bot reads the hub's tracked Store data (`content/site.json` / `content/facts-supplement.json`) for Store versions, since Store drops never touch GitHub Releases. |

## Part A — server scaffold (personal server, now)

**Structure.** One category, **626 Labs**, four channels:

- **`#releases`** — read-only for members; the bot is the only poster. The release feed.
- **`#general`** — community + product chat.
- **`#support`** — help and FAQ; the answer-once-help-many surface that cuts DM load. Seed with a pinned FAQ (the CAPTCHA-is-normal explainer, "update RoRoRo first," install-from-URL steps).
- **`#ideas`** — feature requests and feedback.

**Roles.** Minimal: a bot role (the 626 Labs bot, with Manage Channels/Roles during scaffold, Send Messages + Embed Links + Read Message History for posting), and an optional `@builder` self-assign role. No elaborate hierarchy for a personal-server-hosted category.

**Onboarding.** A pinned welcome message in `#general` (what 626 Labs is, what the channels are for, links to the site + Store) and a one-line `#releases` header. Keep it light.

**Execution.** Via the Discord MCP ([HardHeadHackerHead/discord-mcp](https://github.com/HardHeadHackerHead/discord-mcp) — works with Claude Code, 134 admin tools, or [EL4CTEO/discord-mcp](https://github.com/EL4CTEO/discord-mcp)). Once the bot app exists and is invited, the scaffold runs live from a Claude Code session (or Este drives it in Claude Desktop). A Discord **bot cannot create a server** — only a user can — so the empty category lives inside the personal server Este already owns; the MCP fills it.

## Part B — release bot (own repo, server-agnostic)

**Shape.** A Node scheduled poller, its own repo, deployable as a scheduled **Firebase Function** (Este's `guestbuzz-cineperks` project already hosts Functions) with a GitHub-Action-in-own-repo fallback for zero-hosting portability. Runs ~hourly.

**Two sources → `#releases`:**

1. **GitHub Releases API** for a config list of repos (Claude plugins + RoRoRo plugins + any GitHub-releasing app such as RORORO). Poll latest release/tag per repo, diff against last-seen.
2. **Hub Store data** (`content/site.json` products with `storeUrl` + `content/facts-supplement.json` Store versions) for the 6 Microsoft Store apps. When a Store version changes in the hub's tracked data, the bot posts it. Store cadence is irregular and human-verified; tying it to the hub data keeps the site and the announcement in lockstep.

**State.** Last-seen release ids / versions persisted per source. Firestore if deployed as a Function; a committed JSON state file if run as a GitHub Action. Idempotent: a restart never double-posts.

**Post format.** Branded Discord embed: product name, version, a **family tag** (`plugin` / `rororo` / `store`), a release-notes excerpt, the release/Store link, and a 626 cyan/magenta accent color. Sparing emoji allowed (Discord register). Never posts the same release twice.

**Config-driven for portability.** A config maps watch-targets → destination channel, so another server admin forks/deploys the bot, sets their own repos + bot token, and installs it. v1 config covers the 626 sources; the shape is generic.

**Identity.** A dedicated Discord application + bot, subtly branded 626 (cyan/magenta), its own name — a product surface, not plumbing.

## Sequencing

1. **Part A now.** Blocked only on Este creating the Discord application + bot token and inviting it to the personal server. Then scaffold the category/channels/roles/onboarding via the MCP.
2. **Part B next.** Its own spec + implementation plan + repo, built after Part A gives it a place to post.

## Dependencies (human-only steps)

- **Este:** create a Discord application + bot at the Discord developer portal, copy the bot token, invite the bot to the personal server with the scaffold + post permissions above.
- **Este:** decide whether the scaffold runs from Claude Code (connect the Discord MCP to a session with `claude mcp add`, using the bot token) or from Claude Desktop.

## Open items (resolve in the Part B spec)

- Exact repo watch-list for the Claude-plugin family (which orgs/repos; some plugins are marketplaced under `estevanhernandez-stack-ed`, some under `626Labs-LLC`).
- Firebase Function vs GitHub Action as the v1 host (both viable; Function chosen by default, Action noted as leaner-portable).
- Release-notes excerpt length + formatting; how a family tag maps to embed color/emoji.
- Whether `#support` seeds a bot-driven FAQ command in v1 or stays hand-pinned.

## Out of scope (v1)

- The dedicated branded 626 Labs server (staged for when there's an audience to move).
- Slash-command configuration UI / hosted dashboard for other-server admins (config-file only in v1).
- Secondary triggers (manual posts, site.json prose diffs beyond Store versions).
- Two-way support (ticketing, bot answering questions) — `#support` is human-run in v1.
