# RoRoRo Ur family — launch assets

Social/X assets for the RoRoRo plugin-family launch (RoRoRo 1.8 + the three Ur plugins). Pairs with the Field Note `content/stories/2026-07-03-rororo-grew-a-family.md`.

## Cards

`cards/card-ur-ocr.png`, `cards/card-ur-task.png`, `cards/card-ur-afk.png` — 1200x675 (X summary_large_image), navy field, cyan/magenta. Each runs the "The launcher grew ___" line: eyes (OCR), hands (Task), a heartbeat (AFK).

## Icons

The family icon set lives in each plugin's own repo as `icon.png` (256x256, transparent):

- **Ur OCR** — scan frame (the mark that set the family style)
- **Ur Task** — record dot + play under a repeat arc
- **Ur AFK** — heartbeat pulse over a keyboard (shipped in `rororo-ur-afk` v0.1.1, replacing the v0.1.0 placeholder)

All three share the flat-top hexagon, cyan stroke, and the cyan+magenta swoosh at the base.

## Regenerating

`render_kit.py` (needs `playwright` Python) re-renders every icon (256/512/1024, transparent) and card (1200x675) from the inline SVG glyphs. Run it from this directory:

```
python render_kit.py
```

Output lands in `out/`. The SVG glyph source is inline in the script — edit there, not the PNGs.
