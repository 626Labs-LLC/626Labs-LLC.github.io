#!/usr/bin/env python3
"""visual-diff.py - two-tree visual regression harness for 626labs.dev.

Serves a BASE git ref and the WORKING TREE on two local ports and compares
what a real Chromium renders from each, across three channels: full-frame
pixels, computed styles, and hover states. It answers exactly one question -
"did this branch move anything a visitor can see?" - and it answers it by
comparing two trees, never by comparing against a stored image.

Run it on demand (`workflow_dispatch`, or an opt-in PR label). NOT on every
push: a full sweep of all 39 pages at three widths measures 17.5 minutes.
NOT inside
`rotate-theme.yml`: on the 1st every pixel is SUPPOSED to move, so a pixel
gate there is either meaningless or has to be neutered until it is.

    python scripts/visual-diff.py origin/main
    python scripts/visual-diff.py HEAD --pages press.html privacy.html
    python scripts/visual-diff.py origin/main --widths 1440,390 --channels pixel
    python scripts/visual-diff.py origin/main --self-check   # base vs base

Exit codes: **0** clean, **1** at least one channel reported a difference,
**2** the run could not be made. Two, never one, for ANY failure to complete:
bad args, bad ref, no playwright, a browser that will not launch, a port that
will not bind, or a bug in this file. That split is what lets CI route 1 to
"post the differences" and 2 to "the infrastructure is broken" - and it is
why `main` catches broadly rather than by exception type, since an uncaught
Python exception would otherwise exit 1 and land in the wrong branch.


WHY TWO TREES AND NEVER GOLDEN IMAGES
-------------------------------------
A pinned Pillow is byte-stable run-to-run on one OS, but its bundled FreeType
rasterizes a few bytes differently across platforms - the same caveat CLAUDE.md
already documents for `build-og-cards.py`. Reference PNGs committed from the
ubuntu runner would diff against every Windows run forever, and the only way
to live with that is a threshold, which is the thing this harness refuses to
have. A base-vs-head comparison has no goldens to maintain, needs no
threshold, and asks the question a conformance PR actually asks.


WHAT THIS DOES NOT COVER - read this before trusting a green run
---------------------------------------------------------------
A committed harness that reads as more coverage than it has is worse than no
harness. Everything below is UNSAMPLED, and a regression in any of it comes
back clean:

  - `:focus-visible`, `:focus`, `:focus-within`, `:active`, `:visited`,
    `::selection`, `::placeholder`, `::marker`. Hover is the only state
    sampled, because hover is the one that has actually bitten this repo
    (`product.css`'s `a:hover` underline reaching 11 links across two pages
    while six resting-state gates stayed green).
  - `@media print` and `@media (forced-colors: active)`. The browser is
    never put into either, so a rule that only applies there is invisible.
    Note the asymmetry with hover-subject derivation below: a print
    stylesheet's `:hover` rules ARE collected as subjects (inclusive on
    purpose), they are simply measured in the screen state.
  - Any viewport not on the `--widths` list, any color scheme other than
    `--color-scheme`, any `prefers-reduced-motion` setting other than
    `--motion`, and any browser other than the bundled Chromium.
  - An ANIMATION's later keyframes. Every CSS animation is paused and rewound
    to t=0 before the shutter (`_FREEZE_CSS_ANIMATIONS_JS`), so what is
    compared is its first frame; a change to a keyframe at 50% is invisible
    to the pixel channel. The computed channel still sees `animation-name`
    change. This is the same trade the SMIL freeze makes, and it is strictly
    more coverage than the `--motion reduce` default it replaced, which
    collapsed the site's own transitions to 0.01ms and hid a changed
    `transition-duration` outright.
  - `:hover` rules that only apply at a viewport the hover channel does not
    visit. Hover runs at `--hover-width` alone (1440 by default) while the
    resting channels run every width, so a `:hover` inside a
    `@media (max-width: 720px)` block is enumerated as a subject and then
    measured in a state where its rule does not apply. No live rule is in
    that position today; it is one `@media` block away from being true.
  - 55 of the 80 properties, under hover. `HOVER_PROPS` is 25 - the paint and
    type core - because the hover read runs over a whole subtree per subject.
    `border-radius`, the paddings and margins, `translate`/`scale`/`rotate`
    and the grid properties are sampled at rest and not on hover.
  - The 4th and later elements of any hover signature. `--hover-cap` is 3 per
    signature (tag + sorted classes, two ancestor levels), so a page whose
    fourth `.row .rlinks a` is styled unlike the first three is unsampled
    there. This one is live, not theoretical.
  - A regression that renders differently only SOMETIMES. Two guards stand in
    front of any resting-state difference: it must reproduce on an
    independent recapture, and — for the pixel channel — the base tree must
    not differ from ITSELF at the same page and width. A difference that
    fails either guard is reported as a coverage note rather than failed. A
    rendered-SIZE change skips both. See `run_pixel_and_computed` for the
    measurements that forced them and for `--retries 0`, which disables them.
  - `:hover` rules inside a stylesheet whose `cssRules` the browser refuses
    to expose. Exactly one exists today - index.html's Bacon Trail widget
    `@import`s fonts.googleapis.com, which is cross-origin and raises
    SecurityError. It is reported as a coverage note on every run rather than
    swallowed, and it becomes a FINDING if the set of unreadable sheets
    differs between the two trees.
  - Interaction beyond a single hover: no click, no keyboard, no scroll
    position, no form state, no modal, no `:has()` state that a click opens.
  - Anything semantic. A page can be pixel-identical at every width and have
    a dead feed behind it - the live-data pages fetch, and this harness will
    happily report 0 on two identically-broken trees. Content freshness and
    feed liveness are a separate channel with absolute floors; they are not
    here.
  - The DIRECTION of a change. No two-tree diff can distinguish an intended
    redesign from an accident. This tool tells you WHAT moved and WHERE; a
    human still has to say whether it was supposed to.

And one property it does not have: it cannot run without a base ref, so it is
useless as a rotation gate even if someone wanted it there.


THE THREE CHANNELS
------------------
1. PIXEL - full-frame `full_page=True` screenshot of each tree, byte-compared
   after a size check. Filters ON (the real rendering, nothing neutralized),
   no masking, no noise envelope, no percentage threshold. A single differing
   pixel is a finding.

   SVG SMIL is frozen through `freeze-theme.py`'s shipped
   `_DETERMINISTIC_CAPTURE_INIT_SCRIPT` - IMPORTED from that file, never
   copied, so the freeze travels with it. SMIL runs on the SVG document
   timeline, which neither the frozen `performance.now`/`rAF` overrides nor
   `prefers-reduced-motion` reach; an unfrozen `<animate>` reads as up to
   1.18% "noise" at 390px and once got diagnosed as Skia raster
   nondeterminism. The init script publishes `window.__freezeSvgAnimations`
   and wires it to DOMContentLoaded/load because `add_init_script` runs at
   document-start, when no `<svg>` exists yet; this harness re-invokes it
   after the settle and immediately before the shutter, which is what
   catches SVG that page JS builds after load.

2. COMPUTED - `getComputedStyle` for every element under `<body>`, plus its
   `::before` and `::after`, over COMPUTED_PROPS, in document order. Raster-
   independent, and it is the channel that NAMES the element and property
   that moved, which a pixel count cannot.

   Position is deliberately not in the fingerprint. `getBoundingClientRect()`
   `.x`/`.y` move when content ABOVE an element resizes, so a byte-identical
   region reads as changed; the element's own box (width/height) is safe and
   is included.

3. HOVER - see the block above `collect_hover_subjects` for the derivation
   and why the obvious version of it reports false passes on exactly the
   pages that need it most.


DETERMINISM IS NOT ASSUMED, IT IS MEASURED
------------------------------------------
`--self-check` points BOTH servers at the base worktree and runs the whole
sweep. Anything it reports is capture noise, and a later diff cannot be
trusted until it reports nothing. Run it first, every time. The settle
procedure (load -> best-effort networkidle -> `document.fonts.ready` ->
`--settle-ms` -> SMIL freeze) is validated by that self-check rather than
asserted here.

Chromium is launched with `DETERMINISTIC_RASTER_ARGS` for the same reason —
determinism as a property of the capture rather than a hope about the page.
With default flags, `workflow.html` at 390px rasterizes two ways 8 pixels
apart and 6 of 10 pairwise comparisons of five loads differ; with those flags,
0 of 10. Both trees go through the identical browser, so the flags cannot
manufacture or hide a difference between them — a posture only available
because this compares two live trees and never a committed reference image.

Off-origin requests are aborted before they leave, via the shared
`browser_origin` module, so no run depends on network weather. One
substitution: mod-launcher-games.html renders its entire body from a manifest
on raw.githubusercontent.com, so that URL is answered from the committed
fixture `scripts/fixtures/mod-launcher-supported-games.json` - the same one
theme-doctor.py's browser gate uses. Both trees are served the same fixture
bytes, so the substitution is symmetric and cannot manufacture a difference.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    # Loaded two ways: `python scripts/visual-diff.py` (Python puts the
    # script's own dir on sys.path[0]) and importlib by explicit file path
    # from tests/ (it does NOT). Insert explicitly.
    sys.path.insert(0, str(SCRIPTS_DIR))
import browser_origin  # noqa: E402 - sibling module in scripts/

DEFAULT_WIDTHS = (1440, 768, 390)
DEFAULT_HOVER_WIDTH = 1440
DEFAULT_HOVER_CAP = 3
DEFAULT_SETTLE_MS = 500
DEFAULT_NAV_TIMEOUT_MS = 30000
DEFAULT_HOVER_TIMEOUT_MS = 3000
# Comfortably past this theme's slowest transition (--dur-slow, 380ms) so an
# UNSETTLED report means something really is still moving, not that the
# budget was stingy. Paid only until THREE consecutive reads agree, which for
# a subject whose transitions the read has already finished is two gaps.
DEFAULT_HOVER_SETTLE_MS = 600
DEFAULT_HOVER_SETTLE_GAP_MS = 32

# The document-timeline freeze, for the RESTING capture.
#
# `freeze-theme.py`'s init script reaches three sources of frame-to-frame
# variance - Math.random, performance.now/rAF, and SVG SMIL. It does not reach
# CSS animations, which run on the document timeline the same way SMIL runs on
# the SVG one. index.html keeps four of them alive (the hero mark's rings,
# logo and pulse), and measured base-against-ITSELF under
# `--motion no-preference`, two loads, same context, same raster flags:
#
#   as shipped                                    34,001 self-diff pixels
#   + this freeze immediately before the shutter        0
#
# Paused and rewound to t=0 rather than finished: a resting capture wants the
# page's first frame, deterministically - the same posture the SMIL freeze
# takes. (The HOVER read finishes its animations instead, because there the
# END state is the thing being measured. Different question, different call.)
#
# Deliberately NOT folded into freeze-theme.py, whose init script is a shipped
# artifact of the rotation with its own tests and its own capture-once
# thumbnail stakes. Widening it belongs in a commit that can re-verify those
# thumbnails, not in this one.
_FREEZE_CSS_ANIMATIONS_JS = """
() => {
  const live = document.getAnimations();
  for (const anim of live) {
    try { anim.pause(); anim.currentTime = 0; } catch (e) {}
  }
  return live.length;
}
"""

# Off-origin URLs answered from a committed fixture instead of aborted. One
# entry, and it is the same substitution theme-doctor.py's browser gate makes
# for the same reason: under plain isolation mod-launcher-games.html would
# only ever render its fetch-failed fallback panel, so the page with the most
# complex layout on the site would be the one page compared in its emptiest
# state. `test_off_origin_fixture_agrees_with_theme_doctors` pins the two
# together so they cannot drift apart.
_GAME_FEED_FIXTURE = ROOT / "scripts" / "fixtures" / "mod-launcher-supported-games.json"
OFF_ORIGIN_FIXTURE_NEEDLE = "626-game-manifest"


def _off_origin_fixtures() -> dict[str, tuple[str, str]]:
    """Read at call time, not import time - a unit test importing this module
    must not depend on a fixture file it never uses."""
    return {
        OFF_ORIGIN_FIXTURE_NEEDLE: (
            "application/json",
            _GAME_FEED_FIXTURE.read_text(encoding="utf-8"),
        ),
    }


# THESE TWO LISTS ARE THE COVERAGE SURFACE OF TWO CHANNELS. A property that is
# not here is not measured, and deleting one is a silent narrowing that no
# count-based test can see - `tests/test_visual_diff.py` pins an explicit floor
# set on each for exactly that reason. (Deleting `color` and the four
# `border-*-color` from HOVER_PROPS is not hypothetical: that is precisely the
# set the `.eyebrow` proof depends on, and without the floor the harness would
# report 0 differing values on the regression this whole task exists for.)
#
# Broad on purpose. Every comparison in this file is an INEQUALITY between two
# strings the browser produced - never a threshold, never a parse - so a
# property no theme ever moves costs one string compare, while a property left
# out is a place a real difference can hide. 80 properties.
COMPUTED_PROPS = (
    # paint
    "color background-color background-image background-size background-position "
    "background-repeat background-clip "
    "border-top-color border-right-color border-bottom-color border-left-color "
    "border-top-width border-right-width border-bottom-width border-left-width "
    "border-top-style border-right-style border-bottom-style border-left-style "
    "border-top-left-radius border-top-right-radius "
    "border-bottom-left-radius border-bottom-right-radius "
    "outline-color outline-width outline-style "
    "box-shadow text-shadow filter backdrop-filter opacity mix-blend-mode "
    "clip-path mask-image "
    # type
    "font-family font-size font-weight font-style line-height letter-spacing "
    "text-transform text-align text-decoration-line text-decoration-color "
    "text-decoration-style text-underline-offset white-space "
    # box - the element's OWN box only. See the module docstring on why
    # x/y are excluded and width/height are not.
    "display position z-index width height max-width overflow-x overflow-y "
    "padding-top padding-right padding-bottom padding-left "
    "margin-top margin-right margin-bottom margin-left "
    # flex / grid
    "flex-direction flex-wrap justify-content align-items gap "
    "grid-template-columns "
    # motion / transform
    "transform transform-origin transition-property transition-duration "
    "transition-timing-function animation-name "
    # svg + generated content
    "fill stroke stroke-width content cursor"
).split()

# The hover read runs over the hovered element AND its whole subtree, once per
# subject per tree, so it is the channel where property count costs the most
# wall clock. This is the paint-and-type core of COMPUTED_PROPS: everything a
# `:hover` rule realistically repaints.
HOVER_PROPS = (
    "color background-color background-image background-size background-position "
    "border-top-color border-right-color border-bottom-color border-left-color "
    "border-top-width box-shadow text-shadow filter backdrop-filter opacity "
    "transform text-decoration-line text-decoration-color text-decoration-style "
    "outline-color cursor fill stroke letter-spacing font-weight"
).split()


# --------------------------------------------------------------------------
# page list
# --------------------------------------------------------------------------
def page_list(root: Path = ROOT) -> list[str]:
    """Every public page, derived from `content/page-archetypes.json`.

    Derived rather than enumerated so a new page is covered the commit it is
    mapped to an archetype, not the commit somebody remembers to add it here.
    Sorted, so a run's order does not depend on dict insertion order in a
    JSON file two other scripts also write.
    """
    data = json.loads((root / "content" / "page-archetypes.json").read_text(encoding="utf-8"))
    return sorted(k for k in data if not k.startswith("$"))


# --------------------------------------------------------------------------
# hover-subject derivation - THE reason this file exists
# --------------------------------------------------------------------------
#
# The prior harness derived its hover subjects from each page's OWN `:hover`
# rules plus `a, button`. That is complete for a page that owns all its rules
# and EXACTLY WRONG for a page that wears a stylesheet's dress: `press.html`
# and `privacy.html` own NONE of their hover rules - `a.inline-link:hover`,
# `.nav-links a:hover`, `.nav-cta:hover`, `.footer-links a:hover` all arrive
# from the theme's `archetypes/utility.css`. So on the two pages the gate
# exists for, that derivation swept nothing and reported a confident 0. A
# false pass is the worst failure a gate has.
#
# The fix: subjects come from `document.styleSheets` - the browser's own view
# of every stylesheet the document has, inline `<style>` and `<link>` alike,
# recursing through `@media`/`@supports`/`@layer` and through `@import`ed
# sheets. Union, not the page's half of it.
#
# Three deliberate choices inside that:
#
#   - INCLUSIVE about which sheets count. A `disabled` sheet, or one whose
#     `media` never matches, still contributes its subjects. Including a
#     subject that never changes costs one extra hover; excluding one is a
#     silent hole, and holes are what this file is a fix for.
#   - A sheet whose `cssRules` cannot be read (a genuinely cross-origin
#     stylesheet raises SecurityError) is accounted for by name and COMPARED
#     between the trees: the same hole on both sides is a coverage note
#     printed on every run, a hole on one side only is a finding. Never a
#     silent skip - a skipped sheet is a false pass wearing a warning's
#     clothes. (index.html has exactly one, via the Bacon Trail widget's
#     fonts.googleapis.com @import. Failing on it unconditionally would make
#     that page red forever, and a gate that always fails is a gate nobody
#     reads.)
#   - An enumeration that returns NO linked stylesheet at all, on a document
#     that links one, IS a hard failure. That is the shape of this channel
#     regressing to the page's own rules, and it would otherwise be
#     invisible: both trees regress identically and the sweep reports PASS.
#   - The truncation below is Python, not JS, precisely so it can be driven
#     by unit tests without a browser. The JS half only enumerates
#     `selectorText`s.

_COMBINATOR_RE = re.compile(r"\s*[>+~]\s*|\s+")
# Pseudo-classes that describe a STATE the query cannot reproduce. Stripped
# from a derived subject so `querySelectorAll` can find the resting element.
_STATE_PSEUDOS = (
    "hover", "active", "focus", "focus-visible", "focus-within",
    "visited", "link", "target", "any-link",
)


def _split_selector_list(text: str) -> list[str]:
    """Split a `selectorText` on top-level commas.

    Cannot be `text.split(",")`: `:is(a, b):hover` and
    `:nth-child(2n, 1)` both carry commas inside parens, and splitting them
    produces two invalid selectors that then throw in the browser.
    """
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    quote = ""
    for ch in text:
        if quote:
            current.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in "\"'":
            quote = ch
            current.append(ch)
            continue
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(ch)
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return [p for p in parts if p]


def _split_compounds(part: str) -> list[str]:
    """A complex selector split into its compound selectors, in order.

    Combinators are dropped, not preserved - the caller only ever rejoins a
    PREFIX of this list, and a prefix ending at a compound is a valid
    descendant selector regardless of which combinator originally sat between
    them. Widening `>` to a descendant space can only ever match MORE
    elements, which is the safe direction for a subject sweep.
    """
    compounds: list[str] = []
    depth = 0
    current: list[str] = []
    quote = ""
    for ch in part:
        if quote:
            current.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in "\"'":
            quote = ch
            current.append(ch)
            continue
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if depth == 0 and (ch.isspace() or ch in ">+~"):
            if current:
                compounds.append("".join(current))
                current = []
            continue
        current.append(ch)
    if current:
        compounds.append("".join(current))
    return compounds


def _strip_state(compound: str) -> str:
    """Drop pseudo-elements and state pseudo-classes from one compound.

    Only at the TOP level - `:not(:hover)` keeps its argument, because
    removing `:hover` from inside a negation inverts what the selector means.
    An emptied compound becomes `*` (the `:hover { }` case), never "".
    """
    out: list[str] = []
    i = 0
    n = len(compound)
    while i < n:
        ch = compound[i]
        if ch != ":":
            out.append(ch)
            i += 1
            continue
        # a pseudo-element (`::before`) or pseudo-class (`:hover`)
        j = i + 1
        double = j < n and compound[j] == ":"
        if double:
            j += 1
        start = j
        while j < n and (compound[j].isalnum() or compound[j] in "-_"):
            j += 1
        name = compound[start:j].lower()
        arg = ""
        if j < n and compound[j] == "(":
            depth = 0
            k = j
            while k < n:
                if compound[k] == "(":
                    depth += 1
                elif compound[k] == ")":
                    depth -= 1
                    if depth == 0:
                        k += 1
                        break
                k += 1
            arg = compound[j:k]
            j = k
        if double or name in _STATE_PSEUDOS:
            i = j  # dropped
            continue
        out.append(":" + name + arg)
        i = j
    text = "".join(out).strip()
    return text or "*"


def hover_subject(part: str) -> str | None:
    """The queryable element selector to hover so `part` applies, or None.

    `.cover-card:hover .cover-frame` -> `.cover-card`: the subject is the
    compound that CARRIES `:hover`, and everything after it is a descendant
    the rule repaints (which is why the reader reads the whole subtree).

    When more than one compound carries `:hover`, the LAST one wins: hovering
    a descendant hovers every ancestor of it too, so the deepest subject
    satisfies all of them at once.
    """
    compounds = _split_compounds(part)
    last = -1
    for i, c in enumerate(compounds):
        if ":hover" in c.lower():
            last = i
    if last < 0:
        return None
    kept = [_strip_state(c) for c in compounds[: last + 1]]
    return " ".join(kept).strip() or None


def hover_subject_selectors(
    selector_texts, always: tuple[str, ...] = ("a", "button")
) -> list[str]:
    """Union of hover subjects across EVERY stylesheet the document has.

    `selector_texts` is every `selectorText` containing `:hover` that the
    browser reported, from every sheet in `document.styleSheets` - which is
    what makes a rule owned only by a linked stylesheet a subject on a page
    that declares no hover rule of its own.

    `always` is swept unconditionally so a page with no reachable hover rule
    at all is still measured; drop it and a stylesheet that GAINS an `a:hover`
    between the two trees has no subject to be found on.

    Order is first-seen, deduplicated - the sweep has to visit the same
    subjects in the same order in both trees.
    """
    out: list[str] = []
    for text in selector_texts:
        for part in _split_selector_list(text):
            if ":hover" not in part.lower():
                continue
            subject = hover_subject(part)
            if subject:
                out.append(subject)
    out.extend(always)
    return list(dict.fromkeys(out))


# What the enumeration calls a sheet with no href. Named once so the runtime
# floor check below and the JS that emits it cannot drift apart.
_INLINE_SHEET_LABEL = "(inline <style>)"

# The JS half: enumerate, do not interpret. Everything subtle is Python above.
_HOVER_SELECTOR_JS = r"""
(INLINE_LABEL) => {
  const selectors = [];
  const read = [];
  const unreadable = [];
  const walk = (rules) => {
    for (const rule of rules) {
      if (rule.selectorText && rule.selectorText.indexOf(':hover') !== -1) {
        selectors.push(rule.selectorText);
      }
      // grouping rules (@media/@supports/@layer/@container) expose cssRules;
      // @import exposes the imported sheet instead. The imported sheet's
      // cssRules must be read INSIDE the try - touching it in an `&&` guard
      // throws the SecurityError before the catch can see it, which is how
      // index.html's cross-origin webfont @import took the whole run down.
      if (rule.cssRules) { walk(rule.cssRules); }
      else if (rule.styleSheet) {
        let imported = null;
        try { imported = rule.styleSheet.cssRules; }
        catch (e) { unreadable.push((rule.href || '@import') + ': ' + e.name); }
        if (imported) { walk(imported); }
      }
    }
  };
  for (const sheet of document.styleSheets) {
    const label = sheet.href || INLINE_LABEL;
    let rules = null;
    try { rules = sheet.cssRules; }
    catch (e) { unreadable.push(label + ': ' + e.name); continue; }
    if (rules === null) { unreadable.push(label + ': cssRules is null'); continue; }
    read.push(label);
    walk(rules);
  }
  // The floor this channel is graded against at RUNTIME. A substring test in
  // a unit test cannot tell `document.styleSheets` from a loop over `<style>`
  // elements that kept the words in a comment, and if the enumeration ever
  // regressed that way both trees would regress identically and the sweep
  // would report PASS. Counted here, checked in Python.
  let linked = 0;
  for (const el of document.querySelectorAll('link[rel~="stylesheet" i]')) {
    if (el.disabled || !el.href) continue;
    // Recorded, not swallowed. An href this cannot parse used to be skipped
    // in silence, which LOWERS the floor the whole channel is graded against
    // — the one direction a floor must never move on its own.
    try { if (new URL(el.href, location.href).origin === location.origin) linked += 1; }
    catch (e) { unreadable.push((el.href || '<link>') + ': ' + e.name); }
  }
  return { selectors, read, unreadable, linked };
}
"""

# Locate every subject, cap by SIGNATURE so 308 anchors in three distinct
# contexts stay three contexts rather than 308 identical measurements. The
# signature is tag + sorted classes for the element and two levels of
# ancestor, so `.topnav .links a`, `.footnote a` and `.row .rlinks a` are
# three signatures even though all three are a bare <a>.
_HOVER_LOCATE_JS = r"""
([selectors, cap]) => {
  const part = (n) => {
    if (!n) return '-';
    let cls = '';
    if (typeof n.className === 'string' && n.className.trim()) {
      cls = '.' + n.className.trim().split(/\s+/).sort().join('.');
    }
    return n.tagName.toLowerCase() + cls;
  };
  const sig = (el) => {
    const p = el.parentElement;
    return [part(el), part(p), part(p && p.parentElement)].join('>');
  };
  const out = [];
  const invalid = [];
  for (const sel of selectors) {
    let nodes;
    try { nodes = document.querySelectorAll(sel); }
    catch (e) { invalid.push(sel + ': ' + e.name); continue; }
    const seen = new Map();
    for (let i = 0; i < nodes.length; i++) {
      const s = sig(nodes[i]);
      const n = (seen.get(s) || 0);
      if (n >= cap) continue;
      seen.set(s, n + 1);
      out.push({ key: sel + ' |' + s + '| #' + n, selector: sel, index: i });
    }
  }
  return { subjects: out, invalid };
}
"""

# The self-assertion and the read live in ONE evaluate, deliberately. Split
# them and a hover that silently did not take reads as "no difference".
#
# The read POLLS until three consecutive samples agree, rather than reading once
# and hoping. A base-vs-base self-check found why: index.html's
# `section.thinking .thinking-link a` came back at its RESTING colour in one
# tree and its hover colour in the other, with `matches(':hover')` true on
# both sides - the hover state was applied and the first computed read still
# raced the frame that lands it. A fixed sleep would be a guess; polling to
# agreement is a measurement, and never agreeing inside the budget is a loud
# failure instead of a value nobody can attest to.
#
# `Date.now`, not `performance.now`: the shipped init script freezes
# performance.now to a constant, so a deadline built on it never arrives.
_HOVER_READ_JS = r"""
async (el, [props, budgetMs, gapMs]) => {
  if (!el.matches(':hover')) return { hovered: false };
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  // One gap BEFORE the first sample. Two samples can agree because neither
  // of them has seen the hover land yet, and that is not stability - it is
  // the same race with a second reading on top. Measured: index.html's
  // .btn-gradient reported filter brightness(1) in one tree and
  // brightness(1.08) in the other, both "settled", on identical trees.
  await sleep(gapMs);
  // Collapse every transition and animation the hover started to its END
  // state rather than sampling somewhere along its curve. Infinite
  // animations cannot finish, so they are frozen at t=0 - the same posture
  // the SMIL freeze takes. Applied to both trees identically, and it only
  // ever makes the page more deterministic.
  for (const anim of document.getAnimations()) {
    try { anim.finish(); }
    catch (e) { try { anim.pause(); anim.currentTime = 0; } catch (e2) {} }
  }
  const read = () => {
    const nodes = [el, ...el.querySelectorAll('*')];
    const labels = [];
    const values = [];
    for (const n of nodes) {
      let cls = '';
      if (typeof n.className === 'string' && n.className.trim()) {
        cls = '.' + n.className.trim().split(/\s+/).join('.');
      }
      labels.push(n.tagName.toLowerCase() + cls);
      const cs = getComputedStyle(n);
      values.push(props.map((p) => cs.getPropertyValue(p)));
    }
    return { labels, values };
  };
  const flat = (r) => r.values.map((v) => v.join('')).join('');
  let prev = read();
  let agreements = 0;
  const deadline = Date.now() + budgetMs;
  while (Date.now() < deadline) {
    await sleep(gapMs);
    const next = read();
    if (flat(next) === flat(prev)) {
      // THREE consecutive identical samples, not two. Two is one coincidence
      // away from being a plateau on the way somewhere else.
      if (++agreements >= 2) {
        return { hovered: true, settled: true, labels: next.labels, values: next.values };
      }
    } else {
      agreements = 0;
    }
    prev = next;
  }
  return { hovered: true, settled: false, labels: prev.labels, values: prev.values };
}
"""

_COMPUTED_JS = r"""
(props) => {
  const out = [];
  const els = document.querySelectorAll('body, body *');
  for (const el of els) {
    let cls = '';
    if (typeof el.className === 'string') cls = el.className;
    else if (el.className && el.className.baseVal !== undefined) cls = el.className.baseVal;
    const rec = [el.tagName.toLowerCase(), cls];
    for (const pseudo of [null, '::before', '::after']) {
      const cs = getComputedStyle(el, pseudo);
      const vals = [];
      for (const p of props) vals.push(cs.getPropertyValue(p));
      rec.push(vals);
    }
    out.push(rec);
  }
  return out;
}
"""


# --------------------------------------------------------------------------
# the two trees
# --------------------------------------------------------------------------
def _run_git(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True
    )


@contextlib.contextmanager
def base_worktree(ref: str):
    """A throwaway detached worktree at `ref`, removed on the way out.

    Removed with `git worktree remove --force` and then, if git left anything
    behind (it does on Windows when a file is still open), with a plain
    rmtree + `git worktree prune`. A leaked worktree is a leaked checkout of
    the whole site.
    """
    resolved = _run_git(["rev-parse", "--verify", f"{ref}^{{commit}}"])
    if resolved.returncode != 0:
        raise RuntimeError(f"not a commit-ish: {ref}\n{resolved.stderr.strip()}")
    sha = resolved.stdout.strip()
    path = Path(tempfile.mkdtemp(prefix="visual-diff-base-"))
    # mkdtemp created it; `git worktree add` wants to create it itself.
    path.rmdir()
    add = _run_git(["worktree", "add", "--detach", str(path), sha])
    if add.returncode != 0:
        raise RuntimeError(f"git worktree add failed:\n{add.stdout}{add.stderr}")
    try:
        yield path, sha
    finally:
        _run_git(["worktree", "remove", "--force", str(path)])
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
        _run_git(["worktree", "prune"])


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):  # noqa: A003 - stdlib signature
        pass


@contextlib.contextmanager
def serve(directory: Path):
    """A threaded static server for `directory` on an ephemeral port.

    Threaded rather than the single-threaded `TCPServer` the other browser
    harnesses in this repo use: a full-page load pulls dozens of assets at
    once, and serialized responses turn a 3s page into a 30s one across a
    sweep of 39 pages x 3 widths x 2 trees.
    """
    def _factory(*a, **kw):
        return _QuietHandler(*a, directory=str(directory), **kw)

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _factory)
    httpd.daemon_threads = True
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()
        httpd.server_close()


# Raster determinism, as a property of the CAPTURE rather than a hope about
# the page — the same posture freeze-theme.py's init script takes for JS.
#
# Measured, not inherited. `workflow.html` at 390px renders in exactly two
# states 8 pixels apart (max channel delta 2) inside the doctrine diagram's
# stacked blur()/drop-shadow()/backdrop-filter region. Five loads, all ten
# pairwise comparisons, one browser:
#
#   default                                             6 of 10 pairs differ
#   --disable-gpu                                       6 of 10 pairs differ
#   --disable-gpu --num-raster-threads=1
#                --disable-partial-raster               0 of 10
#
# Two of the three flags are load-bearing together; `--disable-gpu` alone
# does nothing. This changes HOW the page rasterizes, not what it says, and
# both trees are captured through the identical browser — so it cannot
# manufacture or hide a difference between them. It is only safe at all
# because this harness compares two live trees and never a committed
# reference image; a golden-image harness could not take these flags without
# invalidating every golden.
DETERMINISTIC_RASTER_ARGS = (
    "--disable-gpu",
    "--num-raster-threads=1",
    "--disable-partial-raster",
)


def _import_sync_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        return None


def _deterministic_init_script() -> str:
    """`freeze-theme.py`'s capture init script, IMPORTED rather than copied.

    Copying it is how the SMIL freeze went homeless the first time: the fix
    was real, proven and written up, and lived in a file that died with the
    session. One definition, one place it can be fixed.
    """
    spec = importlib.util.spec_from_file_location(
        "_visual_diff_freeze_theme", SCRIPTS_DIR / "freeze-theme.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._DETERMINISTIC_CAPTURE_INIT_SCRIPT


# --------------------------------------------------------------------------
# capture
# --------------------------------------------------------------------------
class Tree:
    """One side of the comparison: a served directory and a browser context."""

    def __init__(self, label: str, origin: str, context, init_script: str, cfg):
        self.label = label
        self.origin = origin
        self.context = context
        self.init_script = init_script
        self.cfg = cfg

    @contextlib.contextmanager
    def open(self, page_path: str, width: int):
        page = self.context.new_page()
        page.set_viewport_size({"width": width, "height": 900})
        try:
            page.add_init_script(self.init_script)
            url = f"{self.origin}/{page_path}"
            browser_origin.block_off_origin(page, url, fulfill=_off_origin_fixtures())
            page.goto(url, wait_until="load", timeout=self.cfg.nav_timeout)
            with contextlib.suppress(Exception):
                # Best effort. Determinism is PROVEN by --self-check, not
                # asserted by this line; a page whose network never idles is
                # not a reason to fail the run.
                page.wait_for_load_state("networkidle", timeout=5000)
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(self.cfg.settle_ms)
            # After the settle, never before: the init script's own
            # DOMContentLoaded/load handlers only reach SVG that existed by
            # then, and page JS builds more.
            page.evaluate("() => window.__freezeSvgAnimations && window.__freezeSvgAnimations()")
            # Same reasoning, different timeline: CSS animations are not
            # reached by the init script at all. Last thing before the caller
            # reads anything.
            page.evaluate(_FREEZE_CSS_ANIMATIONS_JS)
            yield page
        finally:
            page.close()


# The prefix a rendered-size finding carries. Named once so the exemption in
# `run_pixel_and_computed` cannot drift away from the message it exempts.
_SIZE_FINDING = "rendered size"


def compare_pixels(base_png: bytes, head_png: bytes) -> tuple[list[str], dict]:
    """Full-frame byte comparison. No threshold, no mask, no envelope."""
    from io import BytesIO

    import numpy as np
    from PIL import Image

    with Image.open(BytesIO(base_png)) as a, Image.open(BytesIO(head_png)) as b:
        size_a, size_b = a.size, b.size
        if size_a != size_b:
            # A height change IS the finding - a pixel count over mismatched
            # frames would be arithmetic dressed as evidence.
            return (
                [f"{_SIZE_FINDING} {size_a[0]}x{size_a[1]} vs {size_b[0]}x{size_b[1]}"],
                {"size_base": list(size_a), "size_head": list(size_b), "diff_pixels": None},
            )
        arr_a = np.asarray(a.convert("RGB"), dtype=np.int16)
        arr_b = np.asarray(b.convert("RGB"), dtype=np.int16)
    delta = np.abs(arr_a - arr_b)
    mask = delta.any(axis=2)
    count = int(mask.sum())
    stats = {
        "size_base": list(size_a),
        "size_head": list(size_b),
        "diff_pixels": count,
        "max_channel_delta": int(delta.max()) if count else 0,
    }
    if not count:
        return [], stats
    ys, xs = np.nonzero(mask)
    box = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    stats["bbox"] = box
    pct = 100.0 * count / (size_a[0] * size_a[1])
    return (
        [
            f"{count} diff pixels ({pct:.3f}% of frame), max channel delta "
            f"{stats['max_channel_delta']}, bbox {box[0]},{box[1]}-{box[2]},{box[3]}"
        ],
        stats,
    )


def compare_computed(base_rec, head_rec, props, limit: int) -> tuple[list[str], dict]:
    """Named differences: element, pseudo, property, both values."""
    findings: list[str] = []
    if len(base_rec) != len(head_rec):
        findings.append(f"element count {len(base_rec)} vs {len(head_rec)}")
    compared = 0
    differing = 0
    detail: list[str] = []
    for i in range(min(len(base_rec), len(head_rec))):
        b, h = base_rec[i], head_rec[i]
        label = f"<{b[0]} class='{b[1]}'>"
        for pi, pseudo in enumerate(("", "::before", "::after")):
            bv, hv = b[2 + pi], h[2 + pi]
            for j, prop in enumerate(props):
                compared += 1
                if bv[j] != hv[j]:
                    differing += 1
                    if len(detail) < limit:
                        detail.append(f"{label}{pseudo} {prop}: {bv[j]!r} vs {hv[j]!r}")
    if differing:
        findings.append(f"{differing} of {compared} computed values differ")
        findings.extend(detail)
        if differing > limit:
            findings.append(f"... and {differing - limit} more")
    return findings, {"compared": compared, "differing": differing}


# --------------------------------------------------------------------------
# channels
# --------------------------------------------------------------------------
def _measure_resting(base: Tree, head: Tree, page_path: str, width: int, cfg,
                     keep: bool, channels: tuple[str, ...] | None = None):
    """One independent capture pair for the two resting-state channels.

    `base` and `head` may be the SAME tree — that is the within-tree control
    below, and it is why the two sides are never assumed to differ.
    """
    channels = cfg.channels if channels is None else channels
    findings: list[str] = []
    stats: dict = {}
    shots: dict[str, bytes] = {}
    records: dict[str, list] = {}
    for label, tree in (("base", base), ("head", head)):
        with tree.open(page_path, width) as page:
            if "pixel" in channels:
                shots[label] = page.screenshot(full_page=True)
            if "computed" in channels:
                records[label] = page.evaluate(_COMPUTED_JS, COMPUTED_PROPS)
    if "pixel" in channels:
        msgs, s = compare_pixels(shots["base"], shots["head"])
        stats["pixel"] = s
        for m in msgs:
            findings.append(f"pixel: {m}")
        if msgs and keep and cfg.out_dir:
            stem = page_path.replace("/", "__").replace(".html", "")
            (cfg.out_dir / f"{stem}@{width}.base.png").write_bytes(shots["base"])
            (cfg.out_dir / f"{stem}@{width}.head.png").write_bytes(shots["head"])
    if "computed" in channels:
        msgs, s = compare_computed(records["base"], records["head"], COMPUTED_PROPS, cfg.limit)
        stats["computed"] = s
        for m in msgs:
            findings.append(f"computed: {m}")
    return findings, stats


def run_pixel_and_computed(base: Tree, head: Tree, page_path: str, width: int, cfg):
    """The resting channels, with two guards on any difference they report.

    Neither guard is a threshold, a mask or an envelope. Every capture is
    full-frame with filters on and zero tolerance. Both guards exist because
    a measurement said they had to.

    GUARD 1 - REPRODUCTION. A difference is only carried forward if an
    entirely independent second capture pair also reports one.

    GUARD 2 - A WITHIN-TREE CONTROL, and this is the one that matters. If the
    pixel channel is implicated, the BASE tree is captured twice and compared
    against ITSELF at the same page and width. A tree that differs from
    itself cannot be used to attribute a difference to the other tree, so the
    pixel finding is demoted to a coverage note naming the measured
    self-difference. Computed-style findings from the same run are NOT
    demoted - that channel is unaffected by raster flicker.

    The measurement that forced guard 2: `workflow.html` at 390px renders in
    exactly two states 8 pixels apart, max channel delta 2, inside the
    doctrine diagram's stacked `blur()`/`drop-shadow()`/`backdrop-filter`
    region. Six loads per tree, all 15 within-tree pairs compared: the BASE
    tree differs from itself in 5 of 15, the head tree in 8 of 15, and the
    cross-tree pairs in 14 of 36 - the same rate. Guard 1 alone leaves that
    page failing roughly a quarter of the time with nothing changed, which is
    a flaky gate, which is a gate people learn to ignore.

    (Stated carefully, because the last time this page produced small deltas
    the "Skia raster nondeterminism" diagnosis was WRONG and the cause was a
    running SMIL animation. What is different now: the SMIL freeze is in
    place and imported from the file that owns it, the computed channel
    reports zero at every width, and the flicker reproduces base-against-base
    at the same rate as base-against-head.)

    THE COST, stated rather than buried: at a page and width where the tree is
    not bit-deterministic, the pixel channel has no signal and says so. A real
    pixel regression there is downgraded to a note. The computed channel still
    covers it and still names what moved, and a rendered-SIZE change is never
    demoted. `--retries 0` disables both guards; `--self-check` is the
    instrument for hunting nondeterminism directly.
    """
    findings, stats = _measure_resting(base, head, page_path, width, cfg, keep=True)
    if not findings or cfg.retries <= 0:
        return findings, stats, []

    reproduced = None
    for _ in range(cfg.retries):
        again = _measure_resting(base, head, page_path, width, cfg, keep=True)
        if again[0]:
            reproduced = again
            break
    if reproduced is None:
        stats["reproduced"] = False
        return [], stats, [
            f"{page_path} @{width}: a difference did NOT reproduce on recapture, so "
            f"it is reported rather than failed: {'; '.join(findings[:3])}"
        ]

    findings, stats = reproduced
    stats["reproduced"] = True
    # A rendered-SIZE change is exempt from the control. Raster flicker moves
    # pixels, never the height of the frame, so a size finding is never the
    # kind of thing a self-difference can explain away.
    demotable = [
        f for f in findings
        if f.startswith("pixel:") and not f.startswith(f"pixel: {_SIZE_FINDING}")
    ]
    if not demotable:
        return findings, stats, []

    control, control_stats = _measure_resting(
        base, base, page_path, width, cfg, keep=False, channels=("pixel",)
    )
    stats["self_control"] = control_stats.get("pixel")
    if not control:
        return findings, stats, []
    return (
        [f for f in findings if f not in demotable],
        stats,
        [
            f"{page_path} @{width}: the base tree differs from ITSELF here "
            f"({control[0][len('pixel: '):]}), so the pixel channel cannot attribute "
            f"a difference at this page and width. Demoted: "
            f"{'; '.join(demotable)}"
        ],
    )


def collect_hover_subjects(page, cap: int) -> tuple[list[dict], list[str], dict]:
    """Subjects for one tree, plus any HARNESS defect the enumeration hit.

    Returns (subjects, hard_failures, meta). `meta` carries which sheets were
    read, which could not be, and how many raw `:hover` selectors came back -
    that is the evidence the union reached the LINKED stylesheets and not only
    the page's own.

    Two failure classes, deliberately routed differently:

      - An INVALID derived selector is a defect in the truncation above, not
        a property of the site, so it is a hard failure here and fires
        regardless of what the other tree did.
      - An UNREADABLE stylesheet (a genuinely cross-origin `@import`, which
        index.html has via the Bacon Trail widget's fonts.googleapis.com
        import) is a real coverage hole but a property of BOTH trees. It
        rides in `meta` and is compared between the trees by the caller: the
        same hole on both sides is a reported note, a hole on one side only
        is a finding. Failing on it unconditionally would make index.html red
        on every run forever, and a gate that always fails is a gate nobody
        reads.
    """
    raw = page.evaluate(_HOVER_SELECTOR_JS, _INLINE_SHEET_LABEL)
    selectors = hover_subject_selectors(raw["selectors"])
    located = page.evaluate(_HOVER_LOCATE_JS, [selectors, cap])
    failures = [
        f"hover: derived subject selector is invalid, so its rule goes unsampled: {i}"
        for i in located["invalid"]
    ]
    external = [s for s in raw["read"] if s != _INLINE_SHEET_LABEL]
    if raw["linked"] and not external:
        # THE FLOOR. This is what "the union reaches the linked stylesheets"
        # looks like when it is enforced rather than asserted about the source
        # text, and it is the one guard a same-tree regression cannot hide
        # from: both trees would fall back to `a, button` together and the
        # sweep would report a clean PASS on exactly the pages this task
        # exists for. `sheets_read` in report.json is the evidence; this is
        # the check.
        failures.append(
            f"hover: the stylesheet enumeration returned no linked stylesheet, "
            f"though this document links {raw['linked']} same-origin - the hover "
            f"channel has fallen back to the page's own rules and is blind to "
            f"everything the theme owns"
        )
    meta = {
        "sheets_read": raw["read"],
        "sheets_unreadable": raw["unreadable"],
        "linked_same_origin": raw["linked"],
        "hover_rules": len(raw["selectors"]),
        "subject_selectors": len(selectors),
        "subjects": len(located["subjects"]),
    }
    return located["subjects"], failures, meta


def _hover_measure(page, subjects, cfg):
    """{key: (labels, values)} plus {key: reason} for what could not be hovered.

    Element HANDLES, not locators. A locator re-resolves its selector on every
    call, so `.q:not(:hover)` - a derived subject whose selector stops matching
    the instant the hover lands - would be hovered and then read on a
    DIFFERENT element, or time out. A handle is bound to the node.
    """
    values: dict[str, tuple[list[str], list[list[str]]]] = {}
    unreachable: dict[str, str] = {}
    hard: list[str] = []
    by_selector: dict[str, list[dict]] = {}
    for subject in subjects:
        by_selector.setdefault(subject["selector"], []).append(subject)
    for selector, group in by_selector.items():
        handles = page.query_selector_all(selector)
        for subject in group:
            key = subject["key"]
            if subject["index"] >= len(handles):
                # The DOM moved between enumeration and measurement. Loud,
                # never a skip.
                hard.append(f"hover: subject {key} vanished between locate and hover")
                continue
            handle = handles[subject["index"]]
            try:
                handle.hover(timeout=cfg.hover_timeout)
            except Exception as e:  # noqa: BLE001 - any hover failure is data
                unreachable[key] = type(e).__name__
                continue
            result = handle.evaluate(
                _HOVER_READ_JS,
                [HOVER_PROPS, cfg.hover_settle_ms, cfg.hover_settle_gap_ms],
            )
            if not result.get("hovered"):
                # Never swallowed. A hover that did not take reads as "no
                # difference" if you let it, which is a false pass.
                hard.append(f"hover: hovered {key} but the element does not match :hover")
                continue
            if not result.get("settled"):
                hard.append(
                    f"hover: {key} never held still for {cfg.hover_settle_ms}ms, so "
                    f"its hover values cannot be attested to"
                )
                continue
            values[key] = (result["labels"], result["values"])
    return values, unreachable, hard


def run_hover(base: Tree, head: Tree, page_path: str, width: int, cfg):
    findings: list[str] = []
    per_tree: dict[str, tuple] = {}
    meta: dict[str, dict] = {}
    for tree in (base, head):
        with tree.open(page_path, width) as page:
            subjects, hard, m = collect_hover_subjects(page, cfg.hover_cap)
            findings += [f"{tree.label}: {h}" for h in hard]
            values, unreachable, hard2 = _hover_measure(page, subjects, cfg)
            findings += [f"{tree.label}: {h}" for h in hard2]
            per_tree[tree.label] = (values, unreachable)
            meta[tree.label] = m

    base_values, base_unreachable = per_tree["base"]
    head_values, head_unreachable = per_tree["head"]

    # A stylesheet whose rules cannot be read is a coverage hole. The same
    # hole on both sides is reported (never hidden) but is not a difference;
    # a hole that opened on one side only is.
    unreadable_both = set(meta["base"]["sheets_unreadable"]) & set(
        meta["head"]["sheets_unreadable"]
    )
    for sheet in sorted(
        set(meta["base"]["sheets_unreadable"]) ^ set(meta["head"]["sheets_unreadable"])
    ):
        where = "base" if sheet in meta["base"]["sheets_unreadable"] else "head"
        findings.append(
            f"hover: stylesheet unreadable in {where} only, so its :hover rules "
            f"go unsampled there: {sheet}"
        )

    both_unreachable = set(base_unreachable) & set(head_unreachable)
    for key in sorted(set(base_unreachable) ^ set(head_unreachable)):
        where = "base" if key in base_unreachable else "head"
        reason = base_unreachable.get(key) or head_unreachable.get(key)
        findings.append(
            f"hover: subject {key} could not be hovered in {where} only ({reason})"
        )
    for key in sorted(set(base_values) ^ set(head_values)):
        if key in base_unreachable or key in head_unreachable:
            # Already reported, and more accurately: the subject EXISTS on
            # both sides, it just could not be hovered on one. Saying "exists
            # in base only" here would be a second finding that is also wrong.
            continue
        where = "base" if key in base_values else "head"
        findings.append(f"hover: subject {key} exists in {where} only")

    compared = 0
    differing = 0
    detail: list[str] = []
    for key in sorted(set(base_values) & set(head_values)):
        b_labels, b_vals = base_values[key]
        h_labels, h_vals = head_values[key]
        if len(b_vals) != len(h_vals):
            findings.append(
                f"hover: subject {key} subtree size {len(b_vals)} vs {len(h_vals)}"
            )
        for n in range(min(len(b_vals), len(h_vals))):
            scope = "[self]" if n == 0 else f"[descendant #{n}]"
            for j, prop in enumerate(HOVER_PROPS):
                compared += 1
                if b_vals[n][j] != h_vals[n][j]:
                    differing += 1
                    if len(detail) < cfg.limit:
                        detail.append(
                            f"{key} {scope} {b_labels[n]} {prop}: "
                            f"{b_vals[n][j]!r} vs {h_vals[n][j]!r}"
                        )
    if differing:
        findings.append(f"hover: {differing} of {compared} subtree values differ")
        findings.extend(detail)
        if differing > cfg.limit:
            findings.append(f"... and {differing - cfg.limit} more")

    stats = {
        "subjects_compared": len(set(base_values) & set(head_values)),
        "values_compared": compared,
        "differing": differing,
        "unreachable_in_both": len(both_unreachable),
        "unreadable_sheets_in_both": sorted(unreadable_both),
        "base": meta["base"],
        "head": meta["head"],
    }
    return findings, stats


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------
class Config:
    def __init__(self, args, out_dir: Path | None):
        self.channels = args.channels
        self.widths = args.widths
        self.hover_width = args.hover_width
        self.hover_cap = args.hover_cap
        self.hover_timeout = args.hover_timeout
        self.hover_settle_ms = args.hover_settle_ms
        self.hover_settle_gap_ms = args.hover_settle_gap_ms
        self.settle_ms = args.settle_ms
        self.nav_timeout = args.nav_timeout
        self.limit = args.limit
        self.retries = args.retries
        self.out_dir = out_dir


def sweep(base_dir: Path, head_dir: Path, pages: list[str], cfg, motion: str,
          color_scheme: str) -> tuple[list[str], dict, list[str]]:
    """(findings, report, coverage notes) for one motion setting.

    Notes are places the sweep could not look — an unreadable stylesheet, an
    unhoverable subject, a difference that would not reproduce. They are not
    differences and do not fail the run, and they are printed on a PASS,
    because a hole recorded only in a JSON file nobody opens is worth less
    than nothing.
    """
    sync_playwright = _import_sync_playwright()
    if sync_playwright is None:
        raise RuntimeError("playwright is not installed")
    init_script = _deterministic_init_script()

    findings: list[str] = []
    notes: list[str] = []
    report: dict = {"pages": {}}
    with serve(base_dir) as base_origin, serve(head_dir) as head_origin:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=list(DETERMINISTIC_RASTER_ARGS))
            try:
                ctx_args = {
                    "device_scale_factor": 1,
                    "reduced_motion": motion,
                    "color_scheme": color_scheme,
                }
                base_ctx = browser.new_context(**ctx_args)
                head_ctx = browser.new_context(**ctx_args)
                try:
                    base = Tree("base", base_origin, base_ctx, init_script, cfg)
                    head = Tree("head", head_origin, head_ctx, init_script, cfg)
                    for page_path in pages:
                        missing = [
                            label
                            for label, d in (("base", base_dir), ("head", head_dir))
                            if not (d / page_path).is_file()
                        ]
                        if missing:
                            if len(missing) == 2:
                                findings.append(f"{page_path}: absent from both trees")
                            else:
                                findings.append(
                                    f"{page_path}: present in "
                                    f"{'head' if missing == ['base'] else 'base'} only"
                                )
                            continue
                        page_report: dict = {}
                        for width in cfg.widths:
                            if {"pixel", "computed"} & set(cfg.channels):
                                msgs, stats, page_notes = run_pixel_and_computed(
                                    base, head, page_path, width, cfg
                                )
                                page_report[f"@{width}"] = stats
                                findings += [f"{page_path} @{width}: {m}" for m in msgs]
                                notes += page_notes
                        if "hover" in cfg.channels:
                            msgs, stats = run_hover(
                                base, head, page_path, cfg.hover_width, cfg
                            )
                            page_report[f"hover@{cfg.hover_width}"] = stats
                            findings += [
                                f"{page_path} hover@{cfg.hover_width}: {m}" for m in msgs
                            ]
                            notes += [
                                f"{page_path}: :hover rules unsampled in BOTH trees "
                                f"(stylesheet unreadable): {s}"
                                for s in stats["unreadable_sheets_in_both"]
                            ]
                            if stats["unreachable_in_both"]:
                                notes.append(
                                    f"{page_path}: {stats['unreachable_in_both']} hover "
                                    f"subject(s) unreachable in BOTH trees"
                                )
                        report["pages"][page_path] = page_report
                        print(
                            f"  {page_path}: "
                            f"{'FAIL' if any(f.startswith(page_path + ' ') for f in findings) else 'ok'}",
                            flush=True,
                        )
                finally:
                    base_ctx.close()
                    head_ctx.close()
            finally:
                browser.close()
    return findings, report, notes


def _parse_widths(text: str) -> tuple[int, ...]:
    try:
        widths = tuple(int(p) for p in text.replace(" ", ",").split(",") if p)
    except ValueError as e:
        raise ValueError(f"widths must be integers: {text}") from e
    if not widths or any(w <= 0 for w in widths):
        raise ValueError(f"widths must be positive integers: {text}")
    return widths


VALID_CHANNELS = ("pixel", "computed", "hover")


def _parse_channels(text: str) -> tuple[str, ...]:
    names = tuple(p for p in text.replace(" ", ",").split(",") if p)
    bad = [n for n in names if n not in VALID_CHANNELS]
    if bad or not names:
        raise ValueError(
            f"channels must be a subset of {','.join(VALID_CHANNELS)}: {text}"
        )
    return tuple(dict.fromkeys(names))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="visual-diff.py",
        description="Two-tree pixel / computed-style / hover comparison.",
    )
    parser.add_argument("base_ref", help="git ref to compare the working tree against")
    parser.add_argument(
        "--pages", nargs="+", default=None,
        help="repo-relative page paths (default: every page in "
             "content/page-archetypes.json). Takes one or more values, so the "
             "positional base-ref must come BEFORE it or argparse swallows the "
             "ref into this list",
    )
    parser.add_argument("--widths", default=",".join(str(w) for w in DEFAULT_WIDTHS))
    parser.add_argument("--channels", default=",".join(VALID_CHANNELS))
    parser.add_argument("--hover-width", type=int, default=DEFAULT_HOVER_WIDTH)
    parser.add_argument("--hover-cap", type=int, default=DEFAULT_HOVER_CAP)
    parser.add_argument("--hover-timeout", type=int, default=DEFAULT_HOVER_TIMEOUT_MS)
    parser.add_argument("--hover-settle-ms", type=int, default=DEFAULT_HOVER_SETTLE_MS,
                        help="budget for a hovered element's computed values to hold "
                             "still; exceeding it is a failure, not a shrug")
    parser.add_argument("--hover-settle-gap-ms", type=int,
                        default=DEFAULT_HOVER_SETTLE_GAP_MS)
    parser.add_argument("--settle-ms", type=int, default=DEFAULT_SETTLE_MS)
    parser.add_argument("--nav-timeout", type=int, default=DEFAULT_NAV_TIMEOUT_MS)
    # `no-preference` - the default browsing case, and the one with more
    # coverage. It was `reduce` for exactly as long as no-preference measured
    # nondeterministic (34,001 self-diff pixels on index.html), and that
    # turned out to be a hole in THIS file rather than a property of the
    # setting: the document-timeline freeze was applied to the hover read and
    # not to the resting capture. With `_FREEZE_CSS_ANIMATIONS_JS` in
    # `Tree.open`, no-preference self-checks at 0 across every page measured.
    # It is the better default because `reduce` collapses the site's own
    # transitions to 0.01ms, which hides a changed `transition-duration`
    # outright - the harness would report PASS on a real regression.
    parser.add_argument("--motion", default="no-preference",
                        choices=("no-preference", "reduce", "both"))
    parser.add_argument("--color-scheme", default="light", choices=("light", "dark"))
    parser.add_argument("--limit", type=int, default=20,
                        help="named differences printed per page/width/channel")
    parser.add_argument("--retries", type=int, default=1,
                        help="independent recaptures a resting-state difference must "
                             "reproduce in before it is failed (0 disables)")
    parser.add_argument("--out", default=None,
                        help="artifact directory (default: a fresh temp dir)")
    parser.add_argument("--self-check", action="store_true",
                        help="compare the base ref against ITSELF - anything it "
                             "reports is capture noise, and a real diff cannot be "
                             "trusted until this reports nothing")
    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.widths = _parse_widths(args.widths)
        args.channels = _parse_channels(args.channels)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    pages = args.pages if args.pages else page_list(ROOT)
    out_dir = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="visual-diff-"))
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = Config(args, out_dir)
    motions = ("no-preference", "reduce") if args.motion == "both" else (args.motion,)

    started = time.time()
    all_findings: list[str] = []
    all_notes: list[str] = []
    report: dict = {
        "base_ref": args.base_ref,
        "self_check": args.self_check,
        "widths": list(args.widths),
        "channels": list(args.channels),
        "pages": len(pages),
        "runs": {},
    }
    try:
        with base_worktree(args.base_ref) as (base_dir, sha):
            report["base_sha"] = sha
            head_dir = base_dir if args.self_check else ROOT
            print(
                f"base {args.base_ref} ({sha[:8]}) vs "
                f"{'ITSELF (self-check)' if args.self_check else 'working tree'}; "
                f"{len(pages)} pages, widths {','.join(str(w) for w in args.widths)}, "
                f"channels {','.join(args.channels)}",
                flush=True,
            )
            for motion in motions:
                print(f"[prefers-reduced-motion: {motion}]", flush=True)
                findings, run_report, notes = sweep(
                    base_dir, head_dir, pages, cfg, motion, args.color_scheme
                )
                all_findings += [f"[{motion}] {f}" for f in findings]
                all_notes += [f"[{motion}] {n}" for n in notes]
                report["runs"][motion] = run_report
    except Exception as e:  # noqa: BLE001 - see below
        # EVERY failure to complete the run exits 2, not just the ones raised
        # as RuntimeError. An uncaught Python exception exits 1 by default,
        # which is this tool's "differences found" code - so a browser that
        # will not launch, a port that will not bind, or a bug in the
        # comparison itself would land in CI's "post the diff" branch instead
        # of its "infrastructure is broken" branch. The traceback is printed
        # for anything that is not one of this module's own RuntimeErrors, so
        # broadening the catch cannot turn a real defect into a one-line
        # shrug.
        print(f"error: {type(e).__name__}: {e}", file=sys.stderr)
        if not isinstance(e, RuntimeError):
            traceback.print_exc()
        return 2

    elapsed = time.time() - started
    report["elapsed_seconds"] = round(elapsed, 1)
    report["findings"] = all_findings
    report["coverage_notes"] = all_notes
    (out_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print()
    if all_notes:
        # Printed on a PASS too. These are the places the sweep could not
        # look, and they are worth less than nothing if they only appear in a
        # JSON file nobody opens.
        print(f"coverage notes ({len(all_notes)}) - not differences, but not covered:")
        for n in all_notes:
            print(f"  ~ {n}")
        print()
    if all_findings:
        print(f"FAIL - {len(all_findings)} finding(s):")
        for f in all_findings:
            print(f"  - {f}")
    else:
        print("PASS - no channel reported a difference.")
    print(f"artifacts: {out_dir}")
    print(f"elapsed: {elapsed:.0f}s")
    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
