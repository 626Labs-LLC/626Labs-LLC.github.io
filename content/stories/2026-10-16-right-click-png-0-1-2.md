---
title: "Right Click PNG 0.1.2 gets one tidy menu entry and stops overwriting your originals"
subtitle: "Right Click PNG adds Convert to PNG and Copy as PNG to the Windows File Explorer right-click menu, and 0.1.2 cleans up that menu and protects the files you already have."
tagline: "One menu entry, and your originals stay put."
published: 2026-10-16
author: "Este Hernandez"
draft: false
---



<p>Right Click PNG 0.1.2 is out on the Microsoft Store, and it fixes the two things you'd notice first: where the commands live in your right-click menu, and what happens to files that are already in the format you asked for. The menu is now <strong>one Right Click to PNG entry</strong>, with the app icon, in both the modern menu and <em>Show more options</em>. And a file that's already the target format now gets skipped instead of re-saved over itself.</p>

<p>If you haven't met it: Right Click PNG is a C++/WinRT shell extension backed by a .NET 9 AOT engine. It decodes <code>.webp</code>, <code>.avif</code>, <code>.heic</code>, <code>.bmp</code>, <code>.tif</code> and <code>.gif</code> locally with seven bundled decoders, and drops Convert to PNG and Copy as PNG right where you already click. It went from idea to Microsoft Store in 24 hours, built with Vibe Cartographer.</p>

<h2>The menu stops scattering</h2>

<p>In the classic menu, the commands used to land wherever Windows put them: iconless, wedged between other apps' entries, easy to miss. Now Convert to PNG, Copy as PNG and Settings all sit in a single submenu under one branded entry, and that entry looks the same whether you're in the Windows 11 menu or the old one behind <em>Show more options</em>. One place to look, every time.</p>

<h2>Your originals are off limits</h2>

<p>This one mattered more. Select a batch of images that includes a <code>.jpg</code>, send them all through <em>Convert to JPEG</em>, and the old build would re-save that <code>.jpg</code> over itself. Same story for a <code>.png</code> in a mixed selection sent through <em>Convert to PNG</em>. Now files already in the target format are skipped. Underneath that, the engine itself refuses to write any file onto itself, so the guarantee doesn't depend on the menu getting the selection logic right.</p>

<h2>Quieter and steadier</h2>

<p>The settings app used to write a log on every launch. Now it only logs when something goes wrong, and it keeps that log in the app's own folder, so uninstalling takes it with it. The old per-launch log gets deleted on first run, so you don't have to go hunting for it.</p>

<p>There's also a stability fix you shouldn't ever see: the menu extension no longer tells Windows it can be unloaded while File Explorer is still using it.</p>

<h2>Updating</h2>

<p>The Store delivers 0.1.2 automatically. If it reports that the update failed, restart File Explorer (or sign out and back in) and retry. Windows can't replace the menu extension while it's loaded, and Explorer is usually holding it.</p>

<p>What hasn't changed: no network calls, no telemetry, no account. The full policy is in <a href="https://github.com/estevanhernandez-stack-ed/RTClickPng/blob/main/PRIVACY.md">PRIVACY.md</a>, and the full changelog is on <a href="https://github.com/estevanhernandez-stack-ed/RTClickPng/releases/tag/v0.1.2">GitHub</a>.</p>

<p>Get Right Click PNG on the <a href="https://apps.microsoft.com/detail/9PKKLK6R5WFL?cid=site-home">Microsoft Store</a>.</p>
