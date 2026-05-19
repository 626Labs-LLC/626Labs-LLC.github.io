---
id: rtclickpng
product: rtclickpng
title: "How I Published an App in a Day Despite My Own Tools Coming for Me"
subtitle: "Right Click PNG shipped to the Microsoft Store on 2026-04-22 across two agent sessions. What went right, what went wrong, and what an agent going rogue actually looks like in practice."
published: 2026-04-23
tagline: "The actual fix was one line of MSBuild config. The agent that built it swore otherwise — and its own retrospective still misattributed the cause."
hero_image: /assets/thumb-rtclickpng.png
draft: true
---

## The app

**Right Click PNG** is a Windows 11 shell extension that adds two verbs to the File Explorer right-click menu:

- **Convert to PNG** — saves a `.png` next to the original
- **Copy as PNG** — puts PNG bytes on the clipboard, paste-anywhere ready

It decodes `.webp`, `.avif`, `.heic`, `.heif`, `.bmp`, `.tif`, and `.gif` locally — no online converter round-trip, no network calls at all. Free on the [Microsoft Store](https://apps.microsoft.com/detail/9PKKLK6R5WFL). MIT-licensed, [repo open on GitHub](https://github.com/estevanhernandez-stack-ed/RTClickPng).

## The wedge

PowerToys Advanced Paste does *clipboard → file* — "paste as PNG." Nobody ships the inverse: **file → clipboard as PNG.** You find out this asymmetry exists the first time you save a `.webp` from a browser and realize the third-party converter sites want twelve steps to hand it back to you in a format Windows Snipping Tool would have produced instinctively.

That's the wedge. It surfaced during `/scope` on 2026-04-21, when the brain dump connected two separate annoyances — unusable web-image formats, and the Downloads-folder archaeology you end up doing to paste one into Figma — into the same tool.

## What shipped

Three pieces, one MSIX:

- **Engine** — .NET 9 Native AOT CLI, 963 KB, ~20 ms cold start. Seven decoders (libwebp, libavif on dav1d, libheif on libde265, libspng, libjpeg-turbo, plus hand-rolled pure-C# BMP/GIF/TIFF). Two encoders — PNG with `iCCP` chunk support, JPEG with APP2 ICC splicing. EXIF orientation applied and stripped.
- **Shell Extension** — C++/WinRT DLL implementing `IExplorerCommand`. Five verbs total (Convert-PNG, Copy-PNG, Convert-JPEG, Copy-JPEG, Settings). Full visibility matrix — `.png` gets *Copy as PNG* only (so it works as a one-click paste-enable for images you already have), unsupported extensions get nothing at all.
- **Settings** — WPF window with a dark titlebar courtesy of `DwmSetWindowAttribute` + `DWMWA_USE_IMMERSIVE_DARK_MODE`. Two toggles bound to a shared settings schema; lives at `%LOCALAPPDATA%\Packages\626LabsLLC.RightClicktoPNG_wz1chhb2h2v4a\LocalState\settings.json`.

**85 tests green** — 40 xUnit (decoders, encoders, ICC, EXIF, overwrite policy) + 45 C++ (FileFilter visibility matrix). CI on `windows-latest`, Debug + Release matrix, vcpkg binary cache wired through `VCPKG_BINARY_SOURCES=x-gha,readwrite`.

`/onboard` timestamped 2026-04-21. Store listing live 2026-04-22. 47 commits on `main` across two days. The full [`/reflect` artifact lives in the repo](https://github.com/estevanhernandez-stack-ed/RTClickPng/blob/main/docs/reflection.md).

## The handoff

Around item 9 of the checklist, the Settings window started silent-exiting on activation. No Windows Error Reporting. No event-log entry. No managed-code crash log. The exe wouldn't even write a single byte to stderr that anyone could see. The `ModuleInitializer` crash logger the first agent added never fired.

Here's what the first agent tried, in order:

1. WinUI 3 — silent exit
2. WPF — silent exit
3. Shell-extension-spawned — silent exit
4. Self-contained publish vs. framework-dependent — silent exit
5. Start-tile activation vs. context-menu verb — silent exit
6. A `ShellExecuteEx("notepad.exe", "settings.json")` workaround — just ship Notepad as the Settings UI

The first agent's `/reflect` eventually documented the real fix as a Partner Center identity swap (commit `7269d18`). That sounded plausible. It was wrong.

The second agent arrived with a different first move. Before touching any code, they ran `./RTClickPng.Settings.exe` in a Git Bash shell.

stderr lit up immediately:

```text
System.Globalization.CultureNotFoundException:
  Only the invariant culture is supported in globalization-invariant mode.
   "en" is an invalid culture identifier.
   at System.Globalization.CultureInfo..ctor(...)
   at MS.Internal.FontCache.MajorLanguages..cctor()
   at System.Windows.Media.Typeface.CheckFastPathNominalGlyphs(...)
```

Root cause:

```xml
<!-- Directory.Build.props:8 -->
<InvariantGlobalization>true</InvariantGlobalization>
```

The flag was added at item 2 to strip ~2 MB of ICU globalization data from the AOT Engine — a legitimate optimization for a console CLI that doesn't need locale-aware font fallback. When the WPF Settings project was added at item 9 *hours later*, the prop cascaded into it through the shared `Directory.Build.props`. WPF's `PresentationFramework` requires ICU at startup. Without it, `MajorLanguages..cctor()` throws **before any .NET exception handler is in place** — which is why there's no WER, no Application Error event, no managed-code log. The process is spawned by `dllhost.exe` with no attached console, so stderr writes into a closed handle that goes nowhere.

Actual fix: commit `300d0b0`. A three-line override in `Settings.csproj` flipping the flag back for that one project. The Notepad workaround got reverted in the same PR.

And there was a second landmine — one the first agent hadn't seen yet. The MSIX tile icon rendered blank, and clicking the tile launched a window that flashed and vanished. `Package.wapproj` had this property still hiding in it from an earlier revert:

```xml
<EntryPointProjectUniqueName>..\Engine\Engine.csproj</EntryPointProjectUniqueName>
```

MSBuild's packaging step reads that property and silently rewrites the built `AppxManifest.xml`'s `Executable=` attribute. Every build was overriding the source manifest's `Settings\...` entry point with the engine's. Tile clicks were launching the AOT console engine, which printed usage and exited cleanly — Explorer saw a clean-exit process, showed nothing, looked like a crash.

Two silent MSBuild overrides in one repo. Neither surfaced in a log.

## Rejections and landmines survived

Between local sideload working and the Store actually accepting the package — seven distinct Partner Center rejections. Three worth naming:

1. **DisplayName mismatch** — manifest said "Right Click PNG"; the name reservation was "Right Click to PNG." Fixed the manifest; tile keeps the friendlier name via `ShortName="Right Click PNG"` on `uap:DefaultTile`.
2. **Version uniqueness** — Partner Center enforces `(Name, Version, Architecture)` uniqueness across all uploads, including rejected ones. Burned `0.1.0.0` twice before `0.1.0.1` went through.
3. **Revision-digit-must-be-zero** — Store policy: `X.Y.Z.0`. The fourth digit is reserved for OEM. Bumped to `0.1.1.0`, which became the first version to clear ingestion.

Plus two testing-and-deployment landmines that wasted hours and are documented nowhere obvious:

- **`-AllowUnsigned` silent-fails** on packages with production-format Publishers. Workaround: `Add-AppxPackage -Register` against the loose layout, which skips signature verification entirely.
- **`<Content Include="Assets\**\*.png" />`** packs images into the MSIX but doesn't stage them into `bin\<Platform>\<Config>\` for loose-layout activation. Added `<CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory>` — now the tile icon shows up during local sideload.

All documented in [`docs/ms-store-submission-playbook.md`](https://github.com/estevanhernandez-stack-ed/RTClickPng/blob/main/docs/ms-store-submission-playbook.md). Any first-time MSIX publisher is going to hit some subset of these.

## What Vibe Cartographer did vs. what I did

This was my 4th [Vibe Cartographer](https://github.com/estevanhernandez-stack-ed/vibe-cartographer) project. The plugin walked me through `/onboard → /scope → /prd → /spec → /checklist → /build → /reflect` and persisted state across the two agent sessions. The `/scope` round is where the clipboard-as-output wedge surfaced — without it, this is a file-to-file converter nobody needs. The `/reflect` artifact at `docs/reflection.md` is where the retrospective (including the miss) lives, in the first agent's own voice.

What I did: the direction on every branch point, the stack decisions, the Partner Center identity swap, the Notepad-workaround rollback, the second-agent handoff in the first place, and the "ship it" call at 15:14 CST on 2026-04-22.

What Cart did: scaffolded the artifacts, kept the build coherent across a 24-hour window and a mid-build agent swap, and refused to let the scope drift. Multi-session state was load-bearing here — if either agent had lost the thread, the ship date moves right.

## What got learned

Three patterns I'd stake on now that I wouldn't have before:

1. **Run the binary from a console before accepting anyone's root-cause theory.** Silent-exit / no-WER / no-log activation failures look like platform mysteries. Nine times out of ten they're environment — cert trust, globalization flags, DLL search paths — and the exception is waiting for you on stderr if you can find a shell that isn't `dllhost.exe`.
2. **The chronologically-earliest commit that makes the failing thing start working is the real fix — not the one that sounds most significant.** The first agent's `/reflect` attributed the fix to `7269d18` (the Partner Center identity swap) because identity stuff is exotic and felt important. Actual fix: `300d0b0`, two commits earlier, a one-line MSBuild override. Commit timestamps never lie about which change was load-bearing.
3. **Build-props cascade is real.** A flag added to `Directory.Build.props` for a legit reason on one project silently reshapes every project added to the repo afterward. Per-project overrides close the hole; the shared-props file has no way to flag which projects should inherit what. Worth an audit pass on any multi-project .NET repo before you ship.

The miss wasn't the bug. The miss was me shipping a Notepad workaround in the first place instead of forcing a real diagnostic step. That's the scar tissue this story exists to leave in memory for next time.

---

## The data behind the story

- Repo: [estevanhernandez-stack-ed/RTClickPng](https://github.com/estevanhernandez-stack-ed/RTClickPng)
- Microsoft Store: [Right Click to PNG](https://apps.microsoft.com/detail/9PKKLK6R5WFL)
- `/onboard`: 2026-04-21
- Store-live: 2026-04-22, 15:14 CST
- Commits: 47 on `main` across two days
- Tests: 85 (40 xUnit + 45 C++)
- Engine size: 963 KB AOT binary, ~20 ms cold start
- License: MIT
- Bundled native decoders: libwebp, libavif (dav1d), libheif (libde265), libspng, libjpeg-turbo — all licensed and documented in [`docs/licenses.md`](https://github.com/estevanhernandez-stack-ed/RTClickPng/blob/main/docs/licenses.md)
- Built with: [Vibe Cartographer](https://github.com/estevanhernandez-stack-ed/vibe-cartographer)
