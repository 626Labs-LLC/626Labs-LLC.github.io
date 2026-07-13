# About The Lab — judging packet (2026-07-12)

Sub-project C's execution stops here. Three treatment sheets and two prose
drafts are ready for the two gates only Este can clear: the treatment
verdict and prose approval. Nothing in C7-C9 (the real `about.html`, the
homepage section, the site door) runs until both land.

## How to view

Fonts and `/Design/editorial.css` are root-absolute — opening a sheet via
`file://` silently falls back to system fonts, not the shipped stack.
Serve the repo root and browse from there:

```
python -m http.server 8631
```

(from `C:\Users\estev\Projects\626labs-hub`)

- Gallery: http://localhost:8631/Design/explorations/2026-07-12-about-treatments/index.html
- The Family Ledger: http://localhost:8631/Design/explorations/2026-07-12-about-treatments/sheet-family-ledger.html
- The Foundation Wall: http://localhost:8631/Design/explorations/2026-07-12-about-treatments/sheet-foundation-wall.html
- The Long Now Terminal: http://localhost:8631/Design/explorations/2026-07-12-about-treatments/sheet-long-now-terminal.html

For a static pass without spinning up a server, six screenshots (desktop
1440 + mobile 390, full page, per sheet) are in this session's scratchpad:

```
C:\Users\estev\AppData\Local\Temp\claude\c--Users-estev-Projects-626labs-hub\c59b3b8b-8640-4ac5-8995-4f37ddcc8b1b\scratchpad\
  sheet-family-ledger-1440.png       sheet-family-ledger-390.png
  sheet-foundation-wall-1440.png     sheet-foundation-wall-390.png
  sheet-long-now-terminal-1440.png   sheet-long-now-terminal-390.png
```

All three sheets render the identical seven-section specimen
(`specimen.md`) — epigraph, founding night, the name, a values scene,
three keystone quotes, the artifact block, a lineage close, every passage
a verbatim transcript excerpt. The only variable across sheets is chrome:
type, color, motif, structure. Judge the treatment, not the words — the
words are a separate gate (see Prose review, below).

## The rubric

1. **Soften the institution.** The founding directive from the interview
   (Q26): the page should not read like a corporate About page.
2. **Heirloom, not monument.** Q25/Q28 — this is a record kept for the
   house and handed down, not a permanence claim for its own sake.
   Stage Productions is the proof this already works: it outlived its
   founder once, carried by the siblings.
3. **Would a 2026-descendant feel addressed?** The closing line of the
   prose ("in a thousand years none of this may matter much, but...")
   is the actual thesis of the piece. A treatment that only illustrates
   that sentence is doing less than one built around it.
4. **AA + no h-scroll, verified.** Not aspirational — confirmed live this
   session, see below.

## The case for each direction

**The Family Ledger** — a household record book: folio numbers (Fol. I
through VII), an oxblood EST. 626 seal stamped at an angle like a real
ink stamp, a founding-night events table that breaks the first week down
entry-by-entry against the clock, an "Acct. no. 626" tag, inscription
cards for the keystone quotes with a colored spine instead of a border.
This is the most literal read of rubric 2 — a ledger is a thing a
household keeps, not a thing an institution mounts. It's also the
warmest of the three on sight: small-caps serif openers, warm paper, a
table that reads like it was actually kept by hand rather than
generated. Where it under-delivers is rubric 3 — nothing in the chrome
gestures past the present day; a descendant reading it in 2026 gets the
same ledger anyone reads it today.

**The Foundation Wall** — seven mounted plaques, brass corner rivets, a
tracked donor-line date or exchange number under every title, exhibit-
label captions under every quote, "Wing I of VII · permanent
collection" in the header. This is the direction most in tension with
its own brief. Its stated softening move is real — warm bronze ink
instead of cold marble, brass instead of gold — but the *form* it
softens is a donor wall, and a donor wall is an institution-coded object
whichever hue it ships in. The case for it: it's the most visually
authoritative of the three, and if the point is to make "built to be
inherited" feel earned rather than asserted, a mounted plaque
communicates permanence in a way neither sibling does. The risk is
rubric 1 and rubric 2 pulling against each other inside the same sheet —
this is the treatment most likely to read as monument first, heirloom
second.

**The Long Now Terminal** — a records room retrieving the founding file
from a thousand years out: monospace rec-ids (Rec 626.001 through .007),
a large cyan "02026" retrieval-year numeral in the frontispiece, a
"Retrieved 02026-07-12" stamp repeating on every record, corner-reticle
scan marks framing each passage and card. This is the only direction
built structurally around rubric 3 rather than illustrating it after the
fact — the whole page's apparatus performs the closing line instead of
just quoting it. It's also the sheet that took the base-layer AA finding
most seriously (see below) rather than inheriting the gap silently. What
it trades away is some of the warmth Family Ledger has for free — an
archive terminal is cooler and more procedural than a ledger by design,
so it nails "future descendant" harder than it nails "heirloom."

## One base-layer note before you judge color

`--ed-link` (the shared editorial cyan, `#0FA8C9` on `#F7F5F0` paper)
fails AA — 2.58:1, under even the 3:1 large-text floor, despite its own
comment in `editorial.css` claiming "AA contrast on paper." This is a
pre-existing defect in the shared base layer, not something any of the
three sheets ships live:

- Family Ledger and Foundation Wall never touch it — their own
  `--at-ledger-*` / `--at-wall-*` tokens carry every piece of colored
  text.
- Long Now Terminal's own direction explicitly called for "restrained
  cyan links from `--ed-link`," and its implementer caught the failure
  before using it — every colored element on that sheet routes through
  a new AA-safe `--at-lnt-cyan-ink` (5.23:1+ on both paper tones)
  instead, with the finding documented inline in the sheet's own header
  comment.

Whichever direction wins, its C7 build inherits this as an open
constraint: either fix `--ed-link` at the editorial-layer source, or
keep routing colored text around it the way the Long Now Terminal
already does. Not a reason to prefer or exclude any one sheet — it's
sitewide, not treatment-specific.

## Verification, this session

- `check-tokens.py` — **PASS** on all three sheets. Every color literal
  is either a `var()` of an `--ed-*`/`--at-*` token or a raw color bound
  to exactly one `--at-<slug>-*` declaration inside the sheet's own
  `:root`. No loose hex/rgb/hsl anywhere else.
- No horizontal scroll on any sheet at 1440 or 390 — confirmed live via
  `document.documentElement.scrollWidth === clientWidth` at both
  breakpoints on all three, not eyeballed from a screenshot.
- AA contrast — each sheet computed and documented its own new
  `--at-*` tokens against every paper tone it actually touches, inline
  in its `<style>` header comment, using the same WCAG 2.1
  relative-luminance formula throughout. Re-checkable by hand from those
  comments; nothing here is asserted without a number behind it.

## Verdict

For each sheet, one of:

- **KEEP** — ship this direction as-is into C7.
- **KILL** — this direction is out.
- **REMIX** — the shape holds, but [name the element] needs a pass first.

```
family-ledger:      KEEP / KILL / REMIX —
foundation-wall:    KEEP / KILL / REMIX —
long-now-terminal:  KEEP / KILL / REMIX —
```

Mark this file up directly (or say it in chat) — the verdict is what C7
builds from. A REMIX note can also pull an element from a losing sheet
(e.g. the ledger table, the reticle frame, the brass caption line) into
the winner; say so if that's the call.

## Prose review (parallel, same gate)

Two prose drafts wait at the same gate — edits welcome on both, and
whatever text comes back approved is what C7-C9 ship, not what's on disk
now. All three files live at:

```
C:\Users\estev\Projects\626Labs-Publishing\works\2026-07-11-founding-interview\01_POSTS\2026-07-12-about-the-lab\
  body.md            full cut, ~1,800 words, 7 sections + epigraph, 3 keystone pull-quotes
  condensed-cut.md    every sentence lifted verbatim from body.md (trims only, no rewrites), ~260 words, doors to /about.html
  claims-audit.md     every claim in both cuts traced to a question number + verbatim transcript line, plus the deletions log and a privacy/verification checklist
```

`claims-audit.md` is worth a skim even if the prose itself reads clean —
it's the record of what got cut for length and why, and the checklist at
its end is the receipt that no phone number, employer name, or medical
detail survived into either cut.
