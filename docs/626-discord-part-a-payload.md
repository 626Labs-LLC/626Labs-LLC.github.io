# 626 Labs Discord — Part A scaffold payload

> Everything the scaffold session needs, staged. Written 2026-07-03 after the
> guild check blocked execution (`DISCORD_GUILD_ID` still targets the personal
> server). Once the retarget lands (see the runbook's **Retarget** section),
> this doc makes the scaffold pure execution — no drafting, no hunting.
> Canonical plan: `docs/626-discord-runbook.md`.

## Pre-flight gate (hard stop)

Before creating anything, run `get_guild_info` and confirm:

1. The guild **name** is the dedicated 626 Labs server — not `It's Just Este's server`.
2. The guild **id** matches the ID Este copied from the new server.
3. `list_guilds` shows the bot as a member of it.

Any mismatch → stop, report, do not scaffold. This gate already caught the
personal server once (2026-07-03).

## Permissions the revised Part A actually needs

The runbook's original invite list was written for the pre-pivot scaffold.
The revised job list (branding + pins) needs three more:

| Permission | Used by |
|---|---|
| Manage Channels | create_category, create_text_channel, modify_channel |
| Manage Roles | create_role, set_channel_permissions (the #releases lockdown) |
| **Manage Server** | set_server_icon, edit_server (description, default notifications) |
| **Manage Expressions** | create_emoji (the plugin/family icon set) |
| **Manage Messages** | pin_message (welcome, FAQ, releases header) |
| Send Messages, Embed Links, Read Message History | posting + reading back |

Still excluded: Kick/Ban/Moderate Members, Administrator. Moderation perms get
granted when the moderation job actually starts — grant narrow, grant late.

## Scaffold sequence

1. **Pre-flight gate** (above).
2. `edit_server` — description: *"626 Labs — native Windows apps, Claude Code
   plugins, and Roblox tools. Releases, support, and ideas. Imagine Something
   Else."* Default notifications: **mentions only**.
3. `set_server_icon` — icon: `https://626labs.dev/assets/brand/icon-transparent-512.png`.
4. `create_category` **626 Labs**, then `create_text_channel` × 4 into it, with
   topics (table below). A fresh server ships with stock channels (`#general`
   under "Text Channels", a voice channel). After ours exist, delete the stock
   ones — **confirm they're empty first** (`get_messages`); on a new server they
   are.
5. `set_channel_permissions` on `#releases` — deny **Send Messages** and
   **Create Public/Private Threads** for `@everyone`. Leave **Add Reactions**
   allowed (cheap community signal). The bot posts via its own perms.
6. `create_role` **builder** — color `#17d4fa`, mentionable, no extra perms,
   not hoisted. Self-assign wiring (onboarding prompt / role menu) is a later
   polish step; v1 just needs the role to exist.
7. `create_emoji` loop — the emoji map below.
8. Post + pin the **welcome** in `#general`; post + pin the **releases header**
   in `#releases`; post + pin the **FAQ** in `#support`.
9. Optional flourish: `set_bot_status` — watching `626labs.dev`.
10. Verify: `list_channels`, `list_pinned_messages` per channel, `list_emojis`.
11. Close out: tick the runbook boxes (both mirrors), log the scaffold decision
    to the dashboard (project `qNCk86nujUfrHEbRU2jy`).

## Channels

| Channel | Topic | Access |
|---|---|---|
| `#releases` | The 626 Labs release feed — every ship, the moment it ships. Read-only. | deny Send + Threads for @everyone |
| `#general` | Community + product chat. Start here. | open |
| `#support` | Help lives here. Read the pinned FAQ first — it answers the big three. | open |
| `#ideas` | Feature requests + feedback. We read everything. | open |

## Branding asset map

All URLs are live on main via GitHub Pages (verified tracked, 2026-07-03).
Discord emoji cap is 256KB per image — every file below clears it (measured
7–233KB). Emoji names: 2–32 chars, alphanumeric + underscore.

**Server icon:** `https://626labs.dev/assets/brand/icon-transparent-512.png`
(233KB). Discord crops to a circle over its own dark field; if the transparent
mark reads muddy, cut a navy-field square variant via `scripts/export-brand.py`
later — don't block the scaffold on it.

**Emoji — plugin family** (`assets/brand/plugins/<id>-icon-transparent-512.png`,
7–72KB each; URL pattern `https://626labs.dev/assets/brand/plugins/<id>-icon-transparent-512.png`):

| Emoji name | `<id>` |
|---|---|
| `thesis_engine` | thesis-engine |
| `vibe_cartographer` | vibe-cartographer |
| `vibe_doc` | vibe-doc |
| `vibe_insights` | vibe-insights |
| `vibe_iterate` | vibe-iterate |
| `vibe_keystone` | vibe-keystone |
| `vibe_lingual` | vibe-lingual |
| `vibe_prompt` | vibe-prompt |
| `vibe_sec` | vibe-sec |
| `vibe_taker` | vibe-taker |
| `vibe_test` | vibe-test |
| `vibe_thesis` | vibe-thesis |
| `vibe_walk` | vibe-walk |
| `vibe_wrap` | vibe-wrap |

**Emoji — family mark + apps:**

| Emoji name | URL |
|---|---|
| `vibe_plugins` | `https://626labs.dev/assets/brand/vibe-plugins-mark-transparent-512.png` (size unmeasured — verify <256KB at upload; all measured siblings clear it) |
| `sanduhr` | `https://626labs.dev/assets/brand/apps/sanduhr-square-1024.png` (172KB) |
| `rtclickpng` | `https://626labs.dev/assets/brand/apps/rtclickpng-square-1024.png` (128KB) |
| `rbx15_shirt_pants` | `https://626labs.dev/assets/brand/apps/rbx15-shirt-pants-square-1024.png` (229KB) |

18 emoji total — well inside the free-tier 50-slot cap.

## Copy — welcome (#general, pinned)

Post as a plain message (embeds are the release feed's register). Swap the
`#channel` names for real channel mentions at post time. Discord register:
sparing emoji allowed.

---

**Welcome to 626 Labs.**

This is the home server for everything we ship — native Windows apps, Claude Code plugins, and Roblox tools. *Imagine Something Else.*

**The rooms:**
🚀 #releases — every release lands here the moment it ships. Read-only, zero noise.
💬 #general — you're in it. Talk products, builds, whatever.
🛠️ #support — stuck? Ask here. Check the pinned FAQ first, it answers the big three.
💡 #ideas — feature requests and wild thoughts. We read all of it.

I'm **The Architect** — 626 Labs' AI, and I run this room: I post the releases, answer support, and keep the place tidy. If you need a human, @Este is the builder.

🔗 https://626labs.dev

---

## Copy — releases header (#releases, pinned)

---

Every 626 Labs ship lands here — apps, Claude Code plugins, RoRoRo plugins, Microsoft Store drops. Read-only by design. 🚀

---

## Copy — support FAQ (#support, pinned)

---

**626 Labs — Support FAQ** (read this first)

**1. "I got a CAPTCHA — is RoRoRo broken?"**
No. That's Roblox's own anti-bot check doing its job — it shows up sometimes and it's normal. Solve it and carry on. RoRoRo doesn't (and won't) bypass CAPTCHAs.

**2. "Something's not working."**
Update RoRoRo first — 1.8 or later. Most reported issues are already fixed in the latest build. Still broken on the newest version? Post here with what you saw and we'll dig in.

**3. "How do I install a plugin from a URL?"**
Plugins → Install → paste the release URL → walk through the consent sheet. That's it. Release URLs live in #releases and on GitHub.

---
