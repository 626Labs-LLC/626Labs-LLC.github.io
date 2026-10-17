---
title: "Sanduhr for Mac now reads your Claude Code folders, not just your Claude limits"
subtitle: "Thirty-two Mac releases took Sanduhr für Claude from a burn-rate widget to a desktop, statusline and config desk for Claude.ai and Claude Code users."
tagline: "Pace the tokens. Then see what every session loads."
published: 2026-10-16
author: "Este Hernandez"
draft: false
---



<p>Between October 2 and October 16, Sanduhr für Claude on Mac shipped 32 releases, 2.1.0 through 2.25.0. It still does its original job: it shows how fast you're burning through your Claude.ai usage so you can pace yourself. Now it also lives on your desktop, keeps each account's meters with the Claude Code folder that account belongs to, and shows you everything those folders load. You can also export that config for other coding agents.</p>

<h2>Your meters moved onto the desktop</h2>

<p>2.1.0 added <strong>Desk</strong>, a layer drawn under your windows: the clock, your Claude meters, today's meetings and a line of your own. Clicks go straight through to the desktop. On a MacBook the notch can grow into one black island with your meters on a wing. From 2.2.0, Desk draws each limit as a bar with a pace tick and its reset time. 2.3.0 made those bars warn when it matters. A meter that is nearly full with plenty of time left before reset turns red and glows. Weekly limits warn at 90% with more than a day to go. An optional pace alert tells you, for example, "Session on pace to run out at 3:40 PM." If you only want the clock and meetings, 2.15.0 added <strong>Just the Desk</strong>, which needs no Claude account.</p>

<h2>One account per Claude Code folder</h2>

<p>2.4.0 brought multiple accounts. 2.16.0 lets you link each one to a folder, for example Work to <code>~/.claude</code> and Personal to <code>~/.claude-personal</code>. Sessions in each folder then show that account's meters. A linked folder never shows another account's numbers. An account you aren't viewing is fetched at most every 5 minutes, and only while its folder is in use. Sanduhr checks that from the modification times of Claude Code's session logs and never reads their contents. Since 2.19.0 the statusline starts with the account name: <code>Personal | 5h 5% | wk 30% | …</code>.</p>

<p>Each account also gets its own data choices. Meter history keeps 30 days. An opt-in local record of your Claude Code sessions stores tokens by day, model and project, never what was written, and it outlives Claude Code's own cleanup. Your session key lives in the macOS Keychain, and you can sign in through claude.ai's own page inside Sanduhr instead of copying cookies.</p>

<h2>Above the prompt</h2>

<p>Sanduhr's meters mod draws a live band above Claude Code's prompt. It animates where a statusline can't: a sweep when a limit crosses a warning line, a shimmer near reset, a glow when it's nearly full. <strong>Combine</strong> keeps your own statusline and adds Sanduhr's segments, which you can pick and style one chip at a time. Remove puts yours back exactly as it was. Watchers, started by agents through the MCP server's <code>watch_start</code>, show CI runs and deploys as live cards on the notch or the Desk.</p>

<h2>See what every folder loads</h2>

<p>2.18.0 rebuilt Mods &amp; Config around three tabs: <strong>Catalog</strong>, <strong>By Seat</strong> and <strong>Compare</strong>. The Catalog has one card for every plugin, skill, agent, command and MCP server your folders hold. Each folder also gets an estimate of what a new session starts with, including roughly how many tokens the skill listing takes. If a folder goes over Claude Code's listing budget on a 200K-token model, you get an orange line. All of it is read from files. Nothing is fetched, run or changed.</p>

<p>The last week turned that view into tools. The <strong>Mod Studio</strong> previews the meters band with demo numbers. With a switch that is off by default, Claude can propose a mod. You read its files, run Claude Code's validator, then try it in one session before you keep it. <strong>Export Config…</strong> packs a folder's setup with <code>${NAME}</code> in place of every secret value, and <strong>Undo Import</strong> reverses an import. 2.22.0 adds an <code>any-agent/</code> folder for Codex, Gemini CLI, Cursor and VS Code, with an <code>AGENTS.md</code> and a <code>LEFT-OUT.md</code> that names what has no equivalent. <strong>Watch Words…</strong> keeps rows that name your company out of a work folder's pack. 2.24.0 can publish a kept mod to your own marketplace repo, so any machine can add it with <code>claude plugin marketplace add owner/repo</code>.</p>

<h2>Get it</h2>

<p>If you're on Mac already, Sanduhr updates itself. Choose <strong>Check for Updates…</strong> in any Sanduhr menu. Otherwise, download the latest <code>.dmg</code> from <a href="https://github.com/estevanhernandez-stack-ed/Sanduhr_f-r_Claude/releases">GitHub releases</a>. It's signed with Developer ID, notarized by Apple, Universal, and needs macOS 14 or newer. On Windows, it's free on the <a href="https://apps.microsoft.com/detail/9NH3NK2RGCF5?cid=site-home">Microsoft Store</a>. The rest is on the <a href="/sanduhr/">Sanduhr page</a>.</p>
