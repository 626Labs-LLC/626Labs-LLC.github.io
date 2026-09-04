# Paper and Ink — judging packet (2026-09-03)

Three homepage sheets, one specimen, one contract. This is October's theme.
The verdict below is what the eleven-file build starts from. Hard stop:
a doctored theme in `content/themes.json`'s `queue` before **2026-10-01
09:00 UTC**, or the rotation no-ops again the way it did on September 1st.

## How to view

Fonts, `/Design/editorial.css` and `/Design/colors_and_type.css` are
root-absolute. Opening a sheet via `file://` silently falls back to system
fonts. Serve the repo root and browse from there:

```
python -m http.server 8631
```

(from `C:\Users\estev\Projects\626labs-hub`)

- Gallery: http://localhost:8631/Design/explorations/2026-09-03-paper-and-ink/index.html
- The Broadsheet: http://localhost:8631/Design/explorations/2026-09-03-paper-and-ink/sheet-broadsheet.html
- The Monograph: http://localhost:8631/Design/explorations/2026-09-03-paper-and-ink/sheet-monograph.html
- The Field Manual: http://localhost:8631/Design/explorations/2026-09-03-paper-and-ink/sheet-field-manual.html

Six full-page screenshots (1440 and 390 per sheet) sit beside the sheets
as `shot-<slug>-<width>.png`, committed, for a static pass.

All three render the identical specimen (`specimen.md`): the real hero,
the first ten products in site order, the founding block, four Field
Notes, nav, footer, and the wayfinding dateline. Every string verified
verbatim in every sheet, 49 of 49. Judge the treatment, not the words.

## The rubric

1. **Alive, not broken.** A visitor who saw August's black CRT lands on
   this. Do they read a second studio, or a stylesheet that lost its
   background? This is the whole point of the rotation.
2. **The wayfinding contract.** "Theme: October 2026 · this site changes
   monthly · see all themes" must be findable at 390px without scrolling.
   It is the one thing all three share, and it is what turns the seam
   into the story.
3. **Twenty-four products, not ten.** The specimen shows ten. The site has
   twenty-four and every one has a dark CRT screenshot. Which structure
   still works at that count?
4. **The build is a lift, not a rewrite.** The winner becomes eleven files
   and four archetype dresses in under four weeks. Vocabulary reuse and
   proximity to the existing type stack matter.
5. **AA and no h-scroll, verified.** Not aspirational. See below.

## The case for each

**The Broadsheet** is the most complete commitment to its tradition, and
the only one whose answer to the wayfinding contract is structural rather
than decorative: the sentence *is* the dateline, the line every newspaper
prints under its masthead, so the monthly seam is the second thing the
page says. The masthead could be set in metal. The Field Notes front rail
is a genuinely good use of a sidebar. Three-column listings under real
column rules, reversed folio tabs, drop caps, and a founding section that
reads like a features page. At 390 it collapses to one column cleanly and
the dateline is still line two. Shortest page of the three at 2,570px.
**Where it under-delivers:** it shows exactly one dark raster (the
flagship) and leaves the other nine as text-only listings, so it never
proves how nine screenshots sit on newsprint, which is the question rubric
3 asks. And some of its "second studio" contrast is borrowed from density
that matches Phosphor Blueprint's, just lit differently. It is the
safest read at first glance and the least tested at product count.

**The Monograph** is the most severe departure, which was its brief, and
its hero is the most beautiful single screen in the round. Its plate mat
is the best raster framing of the three: a mat one shade lighter than the
page lifts the dark block so it reads as mounted work rather than a hole.
The founding band on deep paper is a real beat. **Where it under-delivers:**
ten plates two-up at 1440 is five rows of dark rectangles, the wall the
spec warned about, and the page runs 7,632px, three times the Broadsheet.
At 390 the plates collapse to a list with thumbnails the size of a stamp,
which is honest, but the thesis (air, one idea per screenful) evaporates
on a phone and what remains is a plain list. The dateline is a colophon
line under the nav: present, findable, and the quietest of the three.
This is the catalog for a lab with four products. The lab has twenty-four.

**The Field Manual** is the most authored, and the one whose structure is
built for rubric 3. Table 1 is a real answer to twenty-four products: a
specification table scales where plates do not, and it reflows at 390
into a stacked ledger without a scroll. The document-control stamp is the
most distinctive dateline in the round and it is unmissable at every
width: rotated magenta on desktop, straight and full-width on a phone.
The tradition is carried all the way through, not only in the header:
numbered paragraphs, a boxed Note for the pull quote, Field Notes as a
record of changes, a printer's color strip in the footer. Two-face type
(Space Grotesk heads, serif body) sits closest to the brand's existing
stack, which makes the build the easiest lift of the three.
**Where it under-delivers:** nine plates three-up is still a lot of ink
on paper, and its implementer said so first. The gradient placeholder is
prettier than the real screenshots will be inside those mats. And a 1962
manual can read cold to a first-time visitor; the paper grain and the
letterpress emboss carry the warmth, and whether they carry enough is the
call only a judge can make.

## Three build-time facts every sheet surfaced, independently

These are not reasons to prefer any sheet. They are what the winner's
build inherits, found three times over.

- **Source Serif 4 is not self-hosted.** `fonts/` carries Space Grotesk,
  Inter and JetBrains Mono. Every sheet's serif is Georgia on Windows.
  Either self-host Source Serif 4 (SIL OFL, a download not a license) or
  the display face is a fallback in production.
- **`colors_and_type.css` fights a light theme.** It paints `h1` white
  and `p` in a light ink for the dark site. The Monograph's first render
  shipped an invisible headline. The theme's `tokens.css` must pin
  heading and paragraph ink; the doctor's dress differential would catch
  the miss, but not the diagnosis.
- **`--ed-ink-3` on deep paper with grain fails.** 4.25:1. Two sheets
  found it separately and both avoided the combination. The build should
  not use caption ink on `--ed-paper-deep` where any texture is
  composited over it.

## Verification, this session

- `check-tokens.py`: **PASS** on all three, re-run by the judge's own
  hand, not taken from the reports. Every color is a `var()` of a base
  token or a raw color bound to exactly one `--pi-<slug>-*` declaration.
- **AA:** each sheet computed and documented every `--pi-*` token against
  every paper tone it touches, inline in its header comment, WCAG 2.1
  relative luminance. Lowest text pair in the round: Broadsheet link ink
  on deep paper with grain, 4.99:1. Nothing under 4.5.
- **No horizontal scroll** at 1440, 768 and 390 on all three, measured as
  `scrollWidth === clientWidth` in Chromium with no `overflow-x: hidden`
  on the page. Zero console errors, zero page errors, all nine captures.
- **Dateline in the first viewport at 390** on all three, measured:
  Broadsheet y=191, Monograph y=89 to 136, Field Manual y=158 to 223.
- **`--ed-link` is never text** on any sheet.

## Verdict

For each sheet, one of:

- **KEEP** — build this direction as October's theme.
- **KILL** — out.
- **REMIX** — the shape holds, but [name the element] needs a pass, or
  pull [named element] from another sheet into this one.

```
broadsheet:     REMIX — keep the structure; take the type system from the
                Field Manual; move the ground to slate grey with the ink
                inverted; the dateline no longer has to sit up top.
monograph:      KILL
field-manual:   KILL as a direction; its type system survives in the remix.
```

**Verdict (Este, 2026-09-03):** "Themes don't need to be up top. I like
Broadsheet, but the font from Field Manual. I also would prefer a darker
background. Maybe slate grey."

Three named changes, one of which (the ground) changes the palette's
premise from paper to slate, so a remix sheet is built and judged before
the eleven-file theme: `sheet-slate-broadsheet.html`. The wayfinding
contract relaxes from "first viewport at 390" to "present on every page";
a newspaper's imprint lives on the editorial page, not page one.

Mark this file up or say it in chat. One REMIX worth naming so it is on
the table: the Field Manual's structure (table, plates, stamp, record of
changes) with the Broadsheet's masthead and front rail carried in. That
pairs the round's best answer to product count with its best first
screen. Whether that is one theme or two ideas fighting is the call.

The judge's lean, labeled as such and not a thumb on the scale: the
Field Manual is the strongest fit for what the lab actually is and the
only sheet built for twenty-four products; the Broadsheet is the
strongest first impression. The Monograph is the most beautiful and the
least suited to this site's inventory.
