# RoRoRo Ur family — launch assets

Social/X assets for the RoRoRo plugin-family launch (RoRoRo 1.8 + the three Ur plugins). Pairs with the Field Note `content/stories/2026-07-03-rororo-grew-a-family.md`.

## Header

`header-ur-plugins-1500x600.png` — 3000x1200 (**5:2**), the family header for the X article's cover. "RoRoRo Ur Plugins", the eyes/hands/heartbeat line, and the three icons labelled OCR/Task/AFK.

## Cards

`cards/card-ur-ocr.png`, `cards/card-ur-task.png`, `cards/card-ur-afk.png` — 1200x675 (X summary_large_image), navy field, cyan/magenta. **Per-plugin identity cards** for the article body: each leads with the plugin name and its role word (Ur OCR / *Eyes.*, Ur Task / *Hands.*, Ur AFK / *A heartbeat.*) plus a one-liner. The family framing lives in the header, so the cards don't repeat it.

## Icons

The family icon set lives in each plugin's own repo as `icon.png` (256x256, transparent):

- **Ur OCR** — scan frame (the mark that set the family style)
- **Ur Task** — record dot + play under a repeat arc
- **Ur AFK** — heartbeat pulse over a keyboard (shipped in `rororo-ur-afk` v0.1.1, replacing the v0.1.0 placeholder)

All three share the flat-top hexagon, cyan stroke, and the cyan+magenta swoosh at the base.

## Regenerating

`render_kit.py` (needs `playwright` Python) re-renders every icon (256/512/1024, transparent) and card (1200x675) from the inline SVG glyphs. Run it from this directory:

```bash
python render_kit.py
```

Output lands in `out/`. The SVG glyph source is inline in the script; edit there, not the PNGs. (Header render is 3000x1200 at device-scale 2; cards are 2400x1350; icons are transparent.)
