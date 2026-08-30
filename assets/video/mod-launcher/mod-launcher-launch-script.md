# TikTok: 626 Mod Launcher, your files are yours

**Runtime:** ~50s (9:16), ~53s hub cuts · **Slides:** 7 (+ title card on hub cuts) · **Voiceover:** yes (ElevenLabs voice: ItsJustEste, speed 0.93 / stability 0.45)

Built from the v0.20 Store screenshot set (`docs/store-assets/screenshots-0.20/` in 626-mod-launcher) and the 0.20 store listing copy. The Nexus browse screenshot stays OUT of the ad — the Store build is sealed-core (no Nexus integration), and the ad matches the listing it points at; the CTA page presents both builds. Overlays get typed into TikTok's text tool; slides 6-7 are brand still frames.

**v0.20 note:** the Back-up-everything slide is the v0.20 headline. v0.20 was a DRAFT release when this was cut (2026-08-30) — confirm it shipped before posting.

## The hook (slide 1, library wall with real cover art)
> Overlay text: "every game. one launcher."
> Voiceover: "Every game, every mod, one launcher. And it's built on one rule: your files are yours."

Why this hook: the library full of games people recognize (Palworld, Elden Ring, Monster Hunter Wilds) is the scroll-stopper; the rule is the brand promise in nine words. Ken Burns pushes into the cover row.

## Slides

### Slide 2 — Game mods view (toggles, Windrose with 27 mods)
- **Overlay text (add in TikTok):** "off = moved aside, not deleted"
- **Voiceover:** "Turning a mod off just moves its files aside. Off never means deleted. Flip it back, and it's right where it was."

### Slide 3 — Add game + settings (cascade)
- **Overlay text:** "Steam games found automatically"
- **Voiceover:** "It finds your Steam games automatically, and a signed game feed means new games show up without an app update."

### Slide 4 — Save snapshots panel
- **Overlay text:** "saves snapshotted before you experiment"
- **Voiceover:** "It snapshots your saves before you experiment. Bad afternoon? One click, and you're back."

### Slide 5 — Back up everything (v0.20 headline)
- **Overlay text:** "your whole setup. one file."
- **Voiceover:** "And now: back up EVERY game's mods, saves, and settings into one file. New PC? Restore exactly what you choose."

### Slide 6 — QoL frame (still)
- **Overlay text:** "no ads. no telemetry. no account."
- **Voiceover:** "No ads, no telemetry, no account. And the quality of life runs deep. Read the list!"

## CTA (slide 7, QR frame)
- **Overlay text:** "scan it, open on desktop"
- **Voiceover:** "Free on the Microsoft Store, with the full build on GitHub. Scan the code, save the page, grab it on your desktop. Six-two-six Mod Launcher. Imagine something else."

## Caption
Modding without the fear: 626 Mod Launcher never deletes your files — toggles move them aside, saves get snapshotted, and your whole setup backs up to one file. Free on the Microsoft Store. 🎮

## Hashtags
#pcgaming #modding #pcmods #skyrimmods #eldenring #palworld

Rotate the game tag per cut to match whichever games are visible in the hook.

## Links
- QR on slide 7 and the bio link: https://626labs.dev/mod-launcher-games.html?ref=tiktok. Phone visitors see a "save this for your desktop" nudge; the page carries both install paths (Store sealed-core build and the full GitHub build).
- Microsoft Store: https://apps.microsoft.com/detail/9N53V6RRJK95
- GitHub: https://github.com/estevanhernandez-stack-ed/626-mod-launcher

## Formats
`mod-launcher-launch-9x16.mp4` (TikTok, cold open) · `4x5` · `1x1` · `16x9` (hub embed) — hub cuts open with the brand title card + ident. Ken Burns push-in on the hook and the single-shot slides.

## Guardrails
- Claims come from the 0.20 store listing copy, product-features txt and README — nothing on screen that isn't shipped (or flagged as v0.20-pending above).
- The ad matches the Store listing: no Nexus-integration claims, no anti-cheat-toggle claims (both are GitHub-build features).
- Game names and cover art appear only inside real, Store-accepted app screenshots.
- No "can't get you banned" claims — the app itself warns about anti-cheat risk.

## TTS note
"six-two-six" is spelled out for the voice (digits read as six hundred twenty-six). Baseline speed 0.93 / stability 0.45; more than one round of per-line pacing fixes means switch to ElevenLabs Studio.

## Studio handoff (pacing pass)
Pacing on this one goes through ElevenLabs Studio per the escalation rule. Generate each paragraph below as its own clip (ItsJustEste, eleven_multilingual_v2), tune pauses/speed in Studio, export per paragraph, and drop the mp3s into `src/voiceover/` as `title.mp3`, `slide_01.mp3` ... `slide_07.mp3`. Then DELETE `src/voiceover/durations.json` — stale entries there override the real clip lengths; with it gone the renderer probes each mp3 directly. Re-run `python render.py <size>` per cut.

## Voiceover script (full, for ElevenLabs Studio or re-recording)
[NARRATOR]
Every game, every mod, one launcher. And it's built on one rule: your files are yours.

Turning a mod off just moves its files aside. Off never means deleted. Flip it back, and it's right where it was.

It finds your Steam games automatically, and a signed game feed means new games show up without an app update.

It snapshots your saves before you experiment. Bad afternoon? One click, and you're back.

And now: back up EVERY game's mods, saves, and settings into one file. New PC? Restore exactly what you choose.

No ads, no telemetry, no account. And the quality of life runs deep. Read the list!

Free on the Microsoft Store, with the full build on GitHub. Scan the code, save the page, grab it on your desktop. Six-two-six Mod Launcher. Imagine something else.
