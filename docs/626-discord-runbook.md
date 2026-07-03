# 626 Labs Discord — Runbook

> **Mirror for coverage.** This file lives in two places, kept in sync:
> `626labs-hub/docs/626-discord-runbook.md` (repo-local) and
> `~/Projects/626-DISCORD-RUNBOOK.md` (estate root). Edit both.
> **Design + decisions:** `626labs-hub/docs/superpowers/specs/2026-07-03-626-discord-design.md`.
> **Dashboard decision:** `q2r0jAktCqm2vYNNBU4c` (project 626 Portfolio Hub).

## What this is

626 Labs' Discord presence: a release feed + community + answer-once-help-many support home, plus a server-agnostic release-announcement bot. **Staged** — scaffold inside Este's personal server now, build the bot to travel, stand up a dedicated 626 Labs server when there's an audience to move. Two projects:

- **Part A — server scaffold** (ships first; this runbook).
- **Part B — release bot** (its own spec + repo, next).

## Status (2026-07-03)

- [x] Design approved, spec committed, decision logged.
- [x] Discord application + bot created by Este; description + tags set (below).
- [ ] Discord MCP connected to Claude Code.
- [ ] Part A scaffolded (category + channels + roles + onboarding).
- [ ] Part B (bot) spec + build.

## The bot (identity)

- **App:** the 626 Labs release bot (Discord developer portal). A product surface, not plumbing — subtly branded 626 (cyan/magenta), installable on other servers.
- **Description (≤400 chars, as set):** "The release feed for 626 Labs, brought to where the audience lives. It watches GitHub Releases and Microsoft Store drops across the whole 626 Labs surface — native apps, Claude Code plugins, RoRoRo plugins — and posts a clean, branded announcement the second something ships. Config-driven: point it at your own repos and it runs the same feed for your server. Imagine Something Else."
- **Tags:** Releases · Notifications · Developer Tools · Automation · Gaming.
- **Token:** server-admin-level credential. **Never commit it.** User-scope config or OS keychain only — this estate has shipped live creds via `.mcp.json` more than once.

## Part A — server scaffold

### Prerequisites (human-only)

1. Discord application + bot created. *(done)*
2. Invite the bot to the personal server with **only** these permissions:
   Manage Channels, Manage Roles, Send Messages, Embed Links, Read Message History.
   *(The MCP advertises 24 perms incl. Kick/Ban/Moderate — not needed for scaffolding. Widen only if a later step requires it.)*
3. Enable gateway intents (dev portal → Bot): **Server Members** + **Message Content**. Required for the MCP to boot; more than a poster-bot needs, fine for a personal bot.

### Connect the Discord MCP (Claude Code, user scope)

- **Get the server (guild) ID:** Discord → User Settings → Advanced → **Developer Mode** on → right-click the server icon → **Copy Server ID**.
- **Add at user scope** (keeps the token out of the repo). **PowerShell (estate default) — one line, no `\` continuation:**

  ```powershell
  claude mcp add discord -s user -e "DISCORD_TOKEN=<your-bot-token>" -e "DISCORD_GUILD_ID=<your-server-id>" -- npx -y "@quadslab.io/discord-mcp"
  ```

  Quotes keep PowerShell from choking on the `=`, `@`, and `/`. (Bash/zsh: the same on one line, or use `\` — never `\` in PowerShell, it uses backtick `` ` ``.)
  Fallback: same server in the **user** MCP config, never the project `.mcp.json`.
- **Restart Claude Code** and open a fresh session — MCP servers load at startup, so the session where you added it won't see the tools; the next one will.
- **Verify:** `npx @quadslab.io/discord-mcp check`.

### Scaffold (run via the MCP once tools are live)

Create category **626 Labs** containing:

| Channel | Purpose | Access |
|---|---|---|
| `#releases` | The bot's release feed | Read-only for `@everyone` (deny Send Messages); bot posts |
| `#general` | Community + product chat | Open |
| `#support` | Help + FAQ; cuts DM load | Open; pin the FAQ |
| `#ideas` | Feature requests | Open |

- **Roles:** the bot role (perms above); optional `@builder` self-assign role. No deep hierarchy — this is a category inside a personal server.
- **Onboarding:** pin a welcome in `#general` (what 626 Labs is, the channel guide, links to 626labs.dev + the Microsoft Store). One-line header in `#releases`.
- **`#support` FAQ seed (pin):** the CAPTCHA-is-normal explainer; "update RoRoRo to 1.8 first"; install-a-plugin-from-URL steps (Plugins → Install → paste release URL → walk the consent sheet).

## Part B — release bot (next project)

Own repo, Node scheduled poller, ~hourly. **Two sources → `#releases`:**

- **GitHub Releases API** — a config list of repos: the Claude plugins (Vibe family) + the RoRoRo plugins (`rororo-ur-task`, `Ur-OCR`, `rororo-ur-afk`) + any GitHub-releasing app (RORORO).
- **Hub Store data** — `626labs-hub/content/site.json` (products with `storeUrl`) + `content/facts-supplement.json` (Store versions) for the 6 Microsoft Store apps, which never hit GitHub Releases.

Diffs against last-seen state (idempotent, no double-posts). Posts branded embeds: product, version, family tag (`plugin`/`rororo`/`store`), notes excerpt, link, 626 cyan/magenta, sparing emoji. Config-driven watch-list → channel for installability. Deployable as a scheduled Firebase Function (`guestbuzz-cineperks`) or a GitHub Action in its own repo. **Gets its own spec + implementation plan** — see the design doc's "Part B" and "Open items" (plugin repo watch-list, Function-vs-Action host, embed formatting).

## Reference

- **Design/decisions:** `626labs-hub/docs/superpowers/specs/2026-07-03-626-discord-design.md`.
- **MCP:** [HardHeadHackerHead/discord-mcp](https://github.com/HardHeadHackerHead/discord-mcp) (npm `@quadslab.io/discord-mcp`); alt [EL4CTEO/discord-mcp](https://github.com/EL4CTEO/discord-mcp).
- **Emoji policy:** on-site none; X sparing; **Discord welcome** (its own register).
- **Store cadence:** Microsoft Store / .exe drops don't appear in GitHub Releases — the hub Store data is the source of truth for those.
