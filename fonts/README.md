# fonts/

What `626labs.dev` serves, through `fonts.css`.

**The `.woff2` files are web subsets.** `scripts/build-fonts.py` builds them from the `.ttf` sources beside them, at the same versions but with fewer glyphs:

| Font | `.ttf` (full) | `.woff2` (served) |
|---|---|---|
| Space Grotesk | 1001 glyphs | 934 |
| Inter | 2933 | 2221 |
| JetBrains Mono | 1754 | 1524 |

The site is fine with that. **Anything that copies fonts out of the hub** (Store art, decks, video titles, the LabShare brand kit) should take the `.ttf` here, or the brand fonts in `626labs-design`, never the `.woff2`. A subset can be missing a glyph the copy needs, and nothing warns you.

EsteFont Pro sets only Este's own words. See the brand notes in the hub's `CLAUDE.md`.
