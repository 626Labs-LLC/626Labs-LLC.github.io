"""Browser-free coverage for scripts/visual-diff.py.

Everything here runs without Chromium, without git and without a network. The
parts that need a browser are proven by running the harness itself (see the
task report's prove-each-channel-bites section); what a test can hold is the
derivation, the comparison arithmetic, the exit-code contract, and the handful
of source-level invariants whose violation is a silent false pass rather than
a crash.
"""
import importlib.util
import json
import re
from io import BytesIO
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("visual_diff", ROOT / "scripts" / "visual-diff.py")
vd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vd)


# ─── the page list ──────────────────────────────────────────────────────
def test_page_list_is_derived_from_the_archetype_map(tmp_path):
    """Derived, never enumerated - a page joins the sweep the commit it is
    mapped to an archetype, not the commit somebody remembers this file."""
    (tmp_path / "content").mkdir()
    (tmp_path / "content" / "page-archetypes.json").write_text(
        json.dumps({"$comment": "ignore me", "b.html": "utility", "a.html": "home"}),
        encoding="utf-8",
    )
    assert vd.page_list(tmp_path) == ["a.html", "b.html"]


def test_page_list_covers_the_live_site():
    pages = vd.page_list(ROOT)
    live = json.loads((ROOT / "content" / "page-archetypes.json").read_text(encoding="utf-8"))
    assert set(pages) == {k for k in live if not k.startswith("$")}
    # the pages this milestone exists for, and the three shapes that have
    # broken a harness before (SMIL, live fetch, the home shell)
    for page in ("press.html", "privacy.html", "workflow.html",
                 "mod-launcher-games.html", "index.html"):
        assert page in pages


# ─── selector splitting ─────────────────────────────────────────────────
def test_selector_list_splits_on_TOP_LEVEL_commas_only():
    """`text.split(',')` turns `:is(a, b):hover` into two invalid selectors,
    each of which then throws in the browser and takes the run with it."""
    assert vd._split_selector_list("a:hover, button:hover") == ["a:hover", "button:hover"]
    assert vd._split_selector_list(":is(.a, .b):hover") == [":is(.a, .b):hover"]
    assert vd._split_selector_list('[data-x="a,b"]:hover, .c') == ['[data-x="a,b"]:hover', ".c"]
    assert vd._split_selector_list(":nth-child(2n, 1):hover") == [":nth-child(2n, 1):hover"]


# ─── hover-subject truncation ───────────────────────────────────────────
@pytest.mark.parametrize(
    "selector,subject",
    [
        ("a.inline-link:hover", "a.inline-link"),
        (".nav-links a:hover", ".nav-links a"),
        (".nav-cta:hover", ".nav-cta"),
        (".footer-links a:hover", ".footer-links a"),
        # a rule that repaints a DESCENDANT: the subject is the compound
        # carrying :hover, and the reader reads the whole subtree
        (".cover-card:hover .cover-frame", ".cover-card"),
        (".publish-links a:hover span", ".publish-links a"),
        # pseudo-elements are not queryable
        (".btn:hover::after", ".btn"),
        # combinators widen to descendant, which can only match MORE
        ("nav > .cta:hover", "nav .cta"),
        (".q:hover + .r", ".q"),
        # two :hover compounds: hovering the deepest hovers its ancestors too
        (".a:hover .b:hover", ".a .b"),
        # structural pseudo-classes survive; they are queryable
        (".tab:nth-child(2):hover", ".tab:nth-child(2)"),
        (":is(.y, .z):hover", ":is(.y, .z)"),
        # the degenerate rule
        (":hover", "*"),
    ],
)
def test_hover_subject_truncation(selector, subject):
    assert vd.hover_subject(selector) == subject


def test_a_selector_with_no_hover_yields_no_subject():
    assert vd.hover_subject(".card") is None
    assert vd.hover_subject_selectors([".card", "a"], always=()) == []


def test_hover_inside_a_negation_is_left_alone():
    """Stripping `:hover` out of `:not(:hover)` inverts what the rule means.
    Only top-level state pseudos are dropped."""
    assert vd.hover_subject(".card:not(:hover)") == ".card:not(:hover)"


def test_other_state_pseudos_are_stripped_from_the_subject():
    """A subject has to be queryable in the RESTING document, so `:focus` and
    `:visited` come off with `:hover`."""
    assert vd.hover_subject("a:visited:hover") == "a"
    assert vd.hover_subject(".btn:focus:hover") == ".btn"


# ─── THE BLOCKER: the union, in unit form ───────────────────────────────
#
# privacy.html's real numbers: 0 :hover rules of its own, 4 arriving from the
# theme's archetypes/utility.css. The derivation this replaced took the page's
# own rules plus `a, button` and therefore swept nothing the theme owns.
_UTILITY_CSS_HOVER_RULES = [
    "a.inline-link:hover",
    ".nav-links a:hover",
    ".nav-cta:hover",
    ".footer-links a:hover",
]
_PRESS_OWN_HOVER_RULES = [".copy-btn:hover", ".asset-card:hover", ".dl-btn:hover"]


def test_subjects_union_the_linked_stylesheets_not_only_the_pages_own():
    """The whole reason this file exists. A page that declares NO hover rule
    still gets every subject its linked stylesheet owns."""
    page_own: list[str] = []  # privacy.html, measured
    subjects = vd.hover_subject_selectors(page_own + _UTILITY_CSS_HOVER_RULES)
    for expected in ("a.inline-link", ".nav-links a", ".nav-cta", ".footer-links a"):
        assert expected in subjects
    # and the derivation this replaced, for contrast
    assert vd.hover_subject_selectors(page_own) == ["a", "button"]


def test_a_NON_ANCHOR_rule_from_a_linked_stylesheet_is_swept():
    """The case the `a, button` fallback cannot cover, and the one a new
    monthly theme actually ships. Reproduced live against press.html and
    privacy.html: with `.eyebrow:hover` in utility.css, the old derivation
    reported a confident PASS on both pages while the regression was live.
    """
    linked = [*_UTILITY_CSS_HOVER_RULES, ".eyebrow:hover"]
    assert ".eyebrow" in vd.hover_subject_selectors(_PRESS_OWN_HOVER_RULES + linked)
    # page-own only, plus the unconditional anchors and buttons: blind
    assert ".eyebrow" not in vd.hover_subject_selectors(_PRESS_OWN_HOVER_RULES)


def test_anchors_and_buttons_are_swept_unconditionally():
    """Drop this and a stylesheet that GAINS an `a:hover` between the two
    trees has no subject on the base side to be found on."""
    assert vd.hover_subject_selectors([]) == ["a", "button"]
    assert vd.hover_subject_selectors(["a:hover"])[-2:] == ["a", "button"]


def test_subject_order_is_stable_and_deduplicated():
    """Both trees have to visit the same subjects in the same order, or the
    keys they are compared by do not line up."""
    raw = [".nav-cta:hover", "a.inline-link:hover", ".nav-cta:hover"]
    assert vd.hover_subject_selectors(raw, always=()) == [".nav-cta", "a.inline-link"]


class _StubHoverPage:
    """Answers the two hover evaluates by shape, the way the browser would."""

    def __init__(self, selectors, read, unreadable, linked=1):
        self.selectors, self.read, self.unreadable = selectors, read, unreadable
        self.linked = linked
        self.located_with = None

    def evaluate(self, script, arg=None):
        if "document.styleSheets" in script:
            return {"selectors": self.selectors, "read": self.read,
                    "unreadable": self.unreadable, "linked": self.linked}
        self.located_with = arg
        return {"subjects": [{"key": s + " |x| #0", "selector": s, "index": 0}
                             for s in arg[0]], "invalid": []}


def test_collect_hover_subjects_feeds_EVERY_sheets_selectors_into_the_derivation():
    """The wire, not the truncation: whatever the browser reported across all
    of document.styleSheets is what gets derived from. Cut it back to the
    page's own sheet and press/privacy go blind."""
    page = _StubHoverPage(
        selectors=[".eyebrow:hover", "a.inline-link:hover"],   # both from utility.css
        read=["http://x/themes/t/archetypes/utility.css", "(inline <style>)"],
        unreadable=[],
    )
    subjects, hard, meta = vd.collect_hover_subjects(page, cap=3)
    assert page.located_with[0] == [".eyebrow", "a.inline-link", "a", "button"]
    assert hard == []
    assert meta["hover_rules"] == 2
    assert meta["sheets_read"] == page.read
    assert [s["selector"] for s in subjects] == [".eyebrow", "a.inline-link", "a", "button"]


def test_an_invalid_derived_selector_is_a_HARD_failure():
    """A selector the browser rejects is a defect in the truncation above, not
    a property of the site, so it fires regardless of what the other tree did."""
    class _P(_StubHoverPage):
        def evaluate(self, script, arg=None):
            if "document.styleSheets" in script:
                return {"selectors": [], "read": [], "unreadable": [], "linked": 0}
            return {"subjects": [], "invalid": ["a::bogus: SyntaxError"]}

    _, hard, _ = vd.collect_hover_subjects(_P([], [], []), cap=3)
    assert len(hard) == 1
    assert "invalid" in hard[0] and "unsampled" in hard[0]


# ─── the runtime floor under the union ──────────────────────────────────
def test_reading_NO_linked_stylesheet_on_a_page_that_links_one_is_a_finding():
    """The only guard a same-tree regression cannot hide from. If the
    enumeration ever went back to the page's own rules, both trees would
    regress identically, the channel would fall back to `a, button`, and the
    sweep would report a clean PASS on exactly the pages this task exists
    for. A substring test on the JS source cannot see that; this can."""
    page = _StubHoverPage(selectors=[], read=[vd._INLINE_SHEET_LABEL],
                          unreadable=[], linked=1)
    _, hard, meta = vd.collect_hover_subjects(page, cap=3)
    assert len(hard) == 1
    assert "no linked stylesheet" in hard[0]
    assert "fallen back to the page's own rules" in hard[0]
    assert meta["linked_same_origin"] == 1


def test_reading_a_linked_stylesheet_satisfies_the_floor():
    page = _StubHoverPage(
        selectors=[], unreadable=[], linked=1,
        read=["http://127.0.0.1:1/themes/t/archetypes/utility.css",
              vd._INLINE_SHEET_LABEL],
    )
    _, hard, _ = vd.collect_hover_subjects(page, cap=3)
    assert hard == []


def test_a_page_that_links_nothing_does_not_trip_the_floor():
    """An all-inline page has no linked stylesheet to miss."""
    page = _StubHoverPage(selectors=[], read=[vd._INLINE_SHEET_LABEL],
                          unreadable=[], linked=0)
    _, hard, _ = vd.collect_hover_subjects(page, cap=3)
    assert hard == []


def test_the_enumeration_counts_only_SAME_ORIGIN_stylesheet_links():
    """Off-origin links are aborted by the isolation, so they can never appear
    in `sheets_read` and would make the floor fire on every run."""
    src = vd._HOVER_SELECTOR_JS
    assert 'link[rel~="stylesheet" i]' in src
    assert "origin === location.origin" in src
    assert "el.disabled" in src


class _StubHandle:
    def __init__(self, result):
        self.result = result
        self.hovered = False

    def hover(self, timeout=None):
        self.hovered = True

    def evaluate(self, script, arg=None):
        return self.result


class _StubMeasurePage:
    def __init__(self, result):
        self.result = result

    def query_selector_all(self, selector):
        return [_StubHandle(self.result)]


class _MeasureCfg:
    hover_timeout = 100
    hover_settle_ms = 600
    hover_settle_gap_ms = 32


_ONE_SUBJECT = [{"key": ".x |s| #0", "selector": ".x", "index": 0}]


def test_a_hover_that_did_not_take_is_a_hard_failure():
    """Swallow it and the subject silently contributes `no difference`, which
    is how the first version of this channel reported a confident 0 against a
    tree that provably HAD the regression."""
    page = _StubMeasurePage({"hovered": False})
    values, unreachable, hard = vd._hover_measure(page, _ONE_SUBJECT, _MeasureCfg())
    assert values == {} and unreachable == {}
    assert len(hard) == 1 and "does not match :hover" in hard[0]


def test_values_that_never_held_still_are_a_hard_failure_not_a_reading():
    page = _StubMeasurePage({"hovered": True, "settled": False,
                             "labels": ["a"], "values": [["x"] * len(vd.HOVER_PROPS)]})
    values, _, hard = vd._hover_measure(page, _ONE_SUBJECT, _MeasureCfg())
    assert values == {}
    assert len(hard) == 1 and "never held still" in hard[0]


def test_a_settled_hover_is_recorded():
    page = _StubMeasurePage({"hovered": True, "settled": True,
                             "labels": ["a"], "values": [["x"] * len(vd.HOVER_PROPS)]})
    values, _, hard = vd._hover_measure(page, _ONE_SUBJECT, _MeasureCfg())
    assert hard == []
    assert list(values) == [".x |s| #0"]


def test_an_unhoverable_element_is_recorded_rather_than_dropped():
    """Reported, then compared between the trees: unreachable in both is a
    coverage note, unreachable in one is a finding."""
    class _Boom(_StubHandle):
        def hover(self, timeout=None):
            raise TimeoutError("not visible")

    class _P(_StubMeasurePage):
        def query_selector_all(self, selector):
            return [_Boom(None)]

    values, unreachable, hard = vd._hover_measure(_P(None), _ONE_SUBJECT, _MeasureCfg())
    assert values == {} and hard == []
    assert unreachable == {".x |s| #0": "TimeoutError"}


class _FakeTree:
    def __init__(self, label):
        self.label = label

    def open(self, page_path, width):
        import contextlib

        @contextlib.contextmanager
        def _cm():
            yield self.label

        return _cm()


class _HoverCfg:
    hover_cap = 3
    limit = 5


_EMPTY_META = {"sheets_read": [], "sheets_unreadable": [],
               "hover_rules": 0, "subject_selectors": 0, "subjects": 0}


def _run_hover_with(monkeypatch, base_meta, head_meta, measured=None):
    metas = {"base": base_meta, "head": head_meta}
    measured = measured or {"base": ({}, {}), "head": ({}, {})}
    monkeypatch.setattr(
        vd, "collect_hover_subjects",
        lambda page, cap: ([], [], metas[page]),
    )
    monkeypatch.setattr(
        vd, "_hover_measure",
        lambda page, subjects, cfg: (*measured[page], []),
    )
    return vd.run_hover(_FakeTree("base"), _FakeTree("head"), "p.html", 1440, _HoverCfg())


def test_a_subject_hoverable_on_one_side_only_is_reported_once_and_correctly(monkeypatch):
    """It exists on BOTH sides - it just could not be hovered on one. Saying
    `exists in base only` alongside that is a second finding that is wrong."""
    reading = (["a"], [["x"] * len(vd.HOVER_PROPS)])
    findings, _ = _run_hover_with(
        monkeypatch, dict(_EMPTY_META), dict(_EMPTY_META),
        measured={"base": ({".x |s| #0": reading}, {}),
                  "head": ({}, {".x |s| #0": "TimeoutError"})},
    )
    assert len(findings) == 1
    assert "could not be hovered in head only (TimeoutError)" in findings[0]
    assert "exists in" not in findings[0]


def test_a_subject_that_genuinely_appeared_on_one_side_IS_reported(monkeypatch):
    """The path that catches a brand-new :hover rule in the theme."""
    reading = (["a"], [["x"] * len(vd.HOVER_PROPS)])
    findings, _ = _run_hover_with(
        monkeypatch, dict(_EMPTY_META), dict(_EMPTY_META),
        measured={"base": ({}, {}), "head": ({".eyebrow |s| #0": reading}, {})},
    )
    assert findings == ["hover: subject .eyebrow |s| #0 exists in head only"]


def test_a_stylesheet_unreadable_in_BOTH_trees_is_a_note_not_a_finding(monkeypatch):
    """index.html's cross-origin webfont @import is unreadable on every run.
    Failing on it would make the page red forever, and a gate that always
    fails is a gate nobody reads - so it is reported, every time, as a hole."""
    meta = {"sheets_read": [], "sheets_unreadable": ["https://fonts/x: SecurityError"],
            "hover_rules": 0, "subject_selectors": 0, "subjects": 0}
    findings, stats = _run_hover_with(monkeypatch, dict(meta), dict(meta))
    assert findings == []
    assert stats["unreadable_sheets_in_both"] == ["https://fonts/x: SecurityError"]


def test_a_stylesheet_unreadable_in_ONE_tree_is_a_finding(monkeypatch):
    """A hole that opened on one side is a difference in what could be looked
    at, which is exactly the thing a two-tree diff should refuse to swallow."""
    base = {"sheets_read": [], "sheets_unreadable": [],
            "hover_rules": 0, "subject_selectors": 0, "subjects": 0}
    head = dict(base, sheets_unreadable=["https://fonts/x: SecurityError"])
    findings, _ = _run_hover_with(monkeypatch, base, head)
    assert len(findings) == 1
    assert "unreadable in head only" in findings[0]


# ─── the JS the browser runs ────────────────────────────────────────────
def _js_code(src: str) -> str:
    """`src` with its `//` comments stripped. A substring test that reads
    comments is a substring test a mutation can satisfy by leaving the words
    behind in one — the review did exactly that and passed all 90 tests."""
    return re.sub(r"//[^\n]*", "", src)


def test_hover_selectors_are_collected_from_document_styleSheets():
    """Not from the page's <style> blocks, and not from files on disk -
    `document.styleSheets` IS the union of everything the document has.

    Asserted against the loop HEAD with comments stripped, because
    `for (const sheet of [...document.querySelectorAll('style')].map(s => s.sheet))
    { // was document.styleSheets` is the page-own-only derivation this task
    exists to replace and it satisfies a bare substring test. A string test
    can still be evaded by a determined refactor, which is why the real guard
    is the runtime floor in `collect_hover_subjects` — that one cannot be
    talked out of, because it asks the browser what the document links."""
    code = _js_code(vd._HOVER_SELECTOR_JS)
    assert "for (const sheet of document.styleSheets)" in code
    assert "querySelectorAll('style')" not in code
    assert "selectorText" in code


def test_an_unreadable_stylesheet_is_recorded_rather_than_skipped():
    """A sheet whose rules cannot be read is a coverage hole. Silently
    skipping it is a false pass; it is accounted for and compared instead."""
    # Read through _js_code, like its neighbours: without that, mutating the
    # handler to the exact silent skip this test is named for —
    # `catch (e) { continue; }` — left both words behind in a comment and the
    # test passed.
    code = _js_code(vd._HOVER_SELECTOR_JS)
    # Every catch must RECORD before it moves on. A bare `catch (e) { continue; }`
    # or `catch (e) {}` is the silent skip.
    catches = re.findall(r"catch\s*\([^)]*\)\s*\{([^}]*)\}", code)
    assert catches, "no catch handler found at all"
    for body in catches:
        assert "unreadable.push" in body, (
            f"a catch handler swallows the error instead of recording it: {body.strip()!r}")
    # ...and the null-rules path, which throws nothing and would otherwise be
    # the one way through.
    assert "cssRules is null" in code


def test_the_imported_sheet_is_read_inside_the_try_not_in_a_guard():
    """`rule.styleSheet && rule.styleSheet.cssRules` throws the SecurityError
    in the guard, before any catch can see it - which is exactly how
    index.html's cross-origin webfont @import took a whole run down."""
    src = vd._HOVER_SELECTOR_JS
    guard = src.index("else if (rule.styleSheet)")
    try_pos = src.index("try { imported = rule.styleSheet.cssRules; }")
    assert guard < try_pos
    assert "rule.styleSheet && rule.styleSheet.cssRules" not in src


def test_the_hover_self_assertion_shares_an_evaluate_with_the_read():
    """Split them and a hover that silently did not take reads as `no
    difference`. Both must be in the same JS source."""
    src = vd._HOVER_READ_JS
    assert "el.matches(':hover')" in src
    assert src.index("el.matches(':hover')") < src.index("getComputedStyle")


def test_the_hovered_elements_whole_subtree_is_read():
    """A hover rule can repaint a descendant (`.cover-card:hover
    .cover-frame`). Reading only the hovered element misses it."""
    assert "el.querySelectorAll('*')" in vd._HOVER_READ_JS


def test_the_hover_read_polls_on_Date_now_not_performance_now():
    """The shipped init script freezes performance.now to a constant, so a
    deadline built on it never arrives and the poll spins to its cap."""
    assert "Date.now()" in vd._HOVER_READ_JS
    assert "performance.now" not in vd._HOVER_READ_JS


def test_the_hover_read_reports_whether_it_settled():
    """An unsettled read is a value nobody can attest to, so it has to be
    distinguishable from a settled one rather than returned as if it were."""
    assert "settled: true" in vd._HOVER_READ_JS
    assert "settled: false" in vd._HOVER_READ_JS


def test_the_hover_read_waits_a_gap_BEFORE_its_first_sample():
    """Two samples can agree because neither has seen the hover land yet, and
    that is the same race with a second reading on top. Measured: index.html's
    .btn-gradient reported filter brightness(1) against brightness(1.08) on
    IDENTICAL trees, both sides claiming to have settled."""
    src = vd._HOVER_READ_JS
    assert src.index("await sleep(gapMs)") < src.index("let prev = read()")


def test_the_hover_read_requires_THREE_agreeing_samples():
    """Two is one coincidence away from being a plateau on the way somewhere
    else."""
    assert "++agreements >= 2" in vd._HOVER_READ_JS
    assert "agreements = 0;" in vd._HOVER_READ_JS


def test_the_hover_read_finishes_running_transitions_before_sampling():
    """Sampling somewhere along a transition curve is a value that depends on
    when the read happened. Infinite animations cannot finish, so they are
    frozen at t=0 - the same posture the SMIL freeze takes."""
    src = vd._HOVER_READ_JS
    assert "document.getAnimations()" in src
    assert "anim.finish()" in src
    assert "anim.currentTime = 0" in src
    assert src.index("document.getAnimations()") < src.index("let prev = read()")


def test_the_computed_probe_reads_both_pseudo_elements():
    assert "'::before'" in vd._COMPUTED_JS
    assert "'::after'" in vd._COMPUTED_JS


# ─── the property lists ARE the coverage surface ────────────────────────
#
# Every other test in this file derives its expectation from
# `len(vd.HOVER_PROPS)` / `len(vd.COMPUTED_PROPS)`, which is format, not
# behaviour: reducing HOVER_PROPS to a single property, or deleting the five
# colour properties the `.eyebrow` proof depends on, passes all of them.
# These two are the floor.
_HOVER_FLOOR = {
    # what a :hover rule repaints, and specifically the five that carry a
    # `currentColor`-derived change - the exact set the .eyebrow regression
    # was detected through
    "color", "border-top-color", "border-right-color", "border-bottom-color",
    "border-left-color", "text-decoration-color", "outline-color",
    "background-color", "background-image", "box-shadow", "text-shadow",
    "filter", "backdrop-filter", "opacity", "transform",
    "text-decoration-line", "cursor", "fill", "stroke", "font-weight",
}
_COMPUTED_FLOOR = {
    "color", "background-color", "background-image", "background-size",
    "border-top-color", "border-right-color", "border-bottom-color",
    "border-left-color", "border-top-width", "border-top-style",
    "border-top-left-radius", "outline-color",
    "box-shadow", "text-shadow", "filter", "backdrop-filter", "opacity",
    "mix-blend-mode", "mask-image",
    "font-family", "font-size", "font-weight", "line-height", "letter-spacing",
    "text-transform", "text-decoration-line", "text-decoration-color",
    "display", "position", "z-index", "width", "height", "max-width",
    "padding-top", "padding-left", "margin-top", "margin-left",
    "overflow-x", "transform", "content", "fill", "stroke",
    "transition-property", "transition-duration", "animation-name",
}


def test_hover_props_carry_their_floor():
    """Deleting `color` and the four `border-*-color` from HOVER_PROPS passes
    every count-based test in this file and makes the harness report 0
    differing values on the .eyebrow regression this task exists for."""
    missing = _HOVER_FLOOR - set(vd.HOVER_PROPS)
    assert not missing, f"HOVER_PROPS lost: {sorted(missing)}"


def test_computed_props_carry_their_floor():
    missing = _COMPUTED_FLOOR - set(vd.COMPUTED_PROPS)
    assert not missing, f"COMPUTED_PROPS lost: {sorted(missing)}"


def test_the_hover_floor_is_a_subset_of_what_is_measured_at_rest():
    """Hover samples fewer properties than rest; it must not sample a property
    the resting channel does not, or the two channels disagree about what a
    difference even is."""
    assert set(vd.HOVER_PROPS) <= set(vd.COMPUTED_PROPS)


def test_no_property_is_listed_twice():
    for name, props in (("HOVER_PROPS", vd.HOVER_PROPS),
                        ("COMPUTED_PROPS", vd.COMPUTED_PROPS)):
        assert len(props) == len(set(props)), f"{name} has duplicates"


def test_no_channel_fingerprints_where_an_element_LANDS():
    """`getBoundingClientRect().x/y` moves when content ABOVE an element
    resizes, so a byte-identical region reads as changed. The element's own
    box is safe and is measured."""
    assert "getBoundingClientRect" not in vd._COMPUTED_JS
    assert "getBoundingClientRect" not in vd._HOVER_READ_JS
    assert "width" in vd.COMPUTED_PROPS and "height" in vd.COMPUTED_PROPS
    for banned in ("top", "left", "right", "bottom"):
        assert banned not in vd.COMPUTED_PROPS


# ─── the shipped freeze, not a copy of it ───────────────────────────────
def test_the_capture_init_script_is_imported_from_freeze_theme():
    """Copied, it goes stale; copied and then fixed elsewhere, the SMIL
    freeze goes homeless again. Same string object's worth of content, read
    out of the file that owns it."""
    spec = importlib.util.spec_from_file_location(
        "_ft_for_test", ROOT / "scripts" / "freeze-theme.py"
    )
    ft = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ft)
    assert vd._deterministic_init_script() == ft._DETERMINISTIC_CAPTURE_INIT_SCRIPT
    assert "__freezeSvgAnimations" in vd._deterministic_init_script()


def test_the_browser_launches_with_deterministic_raster_flags():
    """workflow.html at 390px renders in two raster states 8 pixels apart with
    default flags — 6 of 10 pairwise comparisons of five loads differ. With
    --num-raster-threads=1 and --disable-partial-raster: 0 of 10.
    --disable-gpu alone changes nothing, so the set is not decorative."""
    assert vd.DETERMINISTIC_RASTER_ARGS == (
        "--disable-gpu", "--num-raster-threads=1", "--disable-partial-raster",
    )
    src = (ROOT / "scripts" / "visual-diff.py").read_text(encoding="utf-8")
    assert "p.chromium.launch(args=list(DETERMINISTIC_RASTER_ARGS))" in src
    assert "p.chromium.launch()" not in src


def test_the_smil_freeze_is_re_invoked_after_the_settle():
    """`add_init_script` runs at document-start, when no <svg> exists, and
    page JS builds more after load. The re-invoke is what catches those."""
    src = (ROOT / "scripts" / "visual-diff.py").read_text(encoding="utf-8")
    settle = src.index("page.wait_for_timeout(self.cfg.settle_ms)")
    freeze = src.index("window.__freezeSvgAnimations && window.__freezeSvgAnimations()")
    assert settle < freeze


def test_the_resting_capture_freezes_CSS_animations_too(monkeypatch):
    """The shipped init script reaches Math.random, performance.now/rAF and
    SVG SMIL. It does not reach CSS animations, which run on the document
    timeline. Applying the freeze to the hover read and NOT to the resting
    capture is why no-preference measured 34,001 self-diff pixels on
    index.html and why `reduce` was the default for a while."""
    src = (ROOT / "scripts" / "visual-diff.py").read_text(encoding="utf-8")
    settle = src.index("page.wait_for_timeout(self.cfg.settle_ms)")
    css = src.index("page.evaluate(_FREEZE_CSS_ANIMATIONS_JS)")
    assert settle < css
    assert "document.getAnimations()" in vd._FREEZE_CSS_ANIMATIONS_JS


def test_the_resting_freeze_REWINDS_where_the_hover_read_FINISHES():
    """Different question, different call. A resting capture wants the page's
    first frame, deterministically — the SMIL posture. The hover read wants
    the END state, because that is the thing being measured."""
    assert "anim.pause(); anim.currentTime = 0;" in vd._FREEZE_CSS_ANIMATIONS_JS
    assert "finish()" not in vd._FREEZE_CSS_ANIMATIONS_JS
    assert "anim.finish()" in vd._HOVER_READ_JS


# ─── off-origin isolation ───────────────────────────────────────────────
def test_off_origin_fixture_agrees_with_theme_doctors():
    """Both harnesses substitute the same manifest for the same host. Drifting
    apart means one of them silently compares a different page."""
    spec = importlib.util.spec_from_file_location(
        "_td_for_test", ROOT / "scripts" / "theme-doctor.py"
    )
    td = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(td)
    assert set(vd._off_origin_fixtures()) == set(td._OFF_ORIGIN_FIXTURES)
    for needle, (ctype, body) in vd._off_origin_fixtures().items():
        assert (ctype, body) == td._OFF_ORIGIN_FIXTURES[needle]


# ─── comparison arithmetic ──────────────────────────────────────────────
def _rec(tag, cls, self_vals, before_vals=None, after_vals=None):
    n = len(vd.COMPUTED_PROPS)
    fill = ["x"] * n
    return [tag, cls, self_vals, before_vals or list(fill), after_vals or list(fill)]


def test_computed_differences_name_the_element_and_the_property():
    n = len(vd.COMPUTED_PROPS)
    i = vd.COMPUTED_PROPS.index("color")
    a = ["a"] * n
    b = ["a"] * n
    b[i] = "rgb(1, 2, 3)"
    msgs, stats = vd.compare_computed([_rec("p", "lead", a)], [_rec("p", "lead", b)],
                                      vd.COMPUTED_PROPS, limit=10)
    assert stats == {"compared": 3 * n, "differing": 1}
    assert "1 of" in msgs[0]
    assert "<p class='lead'> color: 'a' vs 'rgb(1, 2, 3)'" in msgs[1]


def test_computed_reports_an_element_count_change():
    n = len(vd.COMPUTED_PROPS)
    a = ["a"] * n
    msgs, _ = vd.compare_computed([_rec("p", "", a)], [_rec("p", "", a), _rec("i", "", a)],
                                  vd.COMPUTED_PROPS, limit=10)
    assert msgs[0] == "element count 1 vs 2"


def test_computed_is_silent_on_identical_trees():
    n = len(vd.COMPUTED_PROPS)
    a = ["a"] * n
    msgs, stats = vd.compare_computed([_rec("p", "", a)], [_rec("p", "", a)],
                                      vd.COMPUTED_PROPS, limit=10)
    assert msgs == []
    assert stats["differing"] == 0


def _png(size, color):
    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def test_pixels_report_a_size_change_rather_than_a_count():
    msgs, stats = vd.compare_pixels(_png((4, 4), (0, 0, 0)), _png((4, 5), (0, 0, 0)))
    assert msgs == ["rendered size 4x4 vs 4x5"]
    assert stats["diff_pixels"] is None


def test_a_single_differing_pixel_is_a_finding():
    """No threshold, no envelope, no percentage. One pixel counts."""
    from PIL import Image

    a = Image.new("RGB", (4, 4), (0, 0, 0))
    b = Image.new("RGB", (4, 4), (0, 0, 0))
    b.putpixel((2, 3), (0, 0, 1))
    bufs = []
    for im in (a, b):
        buf = BytesIO()
        im.save(buf, format="PNG")
        bufs.append(buf.getvalue())
    msgs, stats = vd.compare_pixels(*bufs)
    assert stats["diff_pixels"] == 1
    assert stats["max_channel_delta"] == 1
    assert stats["bbox"] == [2, 3, 2, 3]
    assert msgs and "1 diff pixels" in msgs[0]


def test_identical_frames_are_silent():
    png = _png((8, 8), (17, 212, 250))
    assert vd.compare_pixels(png, png)[0] == []


# ─── the reproduction requirement ───────────────────────────────────────
class _Cfg:
    channels = ("pixel",)
    limit = 5
    out_dir = None

    def __init__(self, retries):
        self.retries = retries


_BASE, _HEAD = object(), object()


def _fake_measure(monkeypatch, script):
    """`script` is a list of (findings, stats) per call; the last repeats.
    Records whether each call was the within-tree control (base vs base)."""
    calls = []

    def fake(base, head, page_path, width, cfg, keep, channels=None):
        calls.append({"control": base is head, "channels": channels})
        return script[min(len(calls) - 1, len(script) - 1)]

    monkeypatch.setattr(vd, "_measure_resting", fake)
    return calls


def test_a_reproducing_difference_survives_a_stable_control(monkeypatch):
    calls = _fake_measure(monkeypatch, [
        (["pixel: 900 diff pixels"], {"pixel": {"diff_pixels": 900}}),
        (["pixel: 900 diff pixels"], {"pixel": {"diff_pixels": 900}}),
        ([], {"pixel": {"diff_pixels": 0}}),          # the control: base == base
    ])
    msgs, stats, notes = vd.run_pixel_and_computed(_BASE, _HEAD, "p.html", 1440, _Cfg(1))
    assert msgs == ["pixel: 900 diff pixels"]
    assert stats["reproduced"] is True
    assert notes == []
    # original capture, one independent recapture, then the base-vs-base control
    assert [c["control"] for c in calls] == [False, False, True]
    assert calls[-1]["channels"] == ("pixel",)


def test_a_difference_that_does_not_reproduce_becomes_a_NOTE_not_a_pass(monkeypatch):
    """Downgraded, never disappeared."""
    _fake_measure(monkeypatch, [
        (["pixel: 8 diff pixels"], {"pixel": {"diff_pixels": 8}}),
        ([], {"pixel": {"diff_pixels": 0}}),
    ])
    msgs, stats, notes = vd.run_pixel_and_computed(_BASE, _HEAD, "p.html", 1440, _Cfg(1))
    assert msgs == []
    assert stats["reproduced"] is False
    assert len(notes) == 1
    assert "did NOT reproduce" in notes[0]
    assert "8 diff pixels" in notes[0]


def test_a_tree_that_differs_from_ITSELF_cannot_attribute_a_pixel_difference(monkeypatch):
    """workflow.html at 390px renders in two raster states; the base tree
    differs from itself in 5 of 15 pairs. Reproduction alone leaves that page
    failing about a quarter of the time with nothing changed."""
    _fake_measure(monkeypatch, [
        (["pixel: 8 diff pixels"], {"pixel": {"diff_pixels": 8}}),
        (["pixel: 8 diff pixels"], {"pixel": {"diff_pixels": 8}}),
        (["pixel: 8 diff pixels"], {"pixel": {"diff_pixels": 8}}),   # base vs base
    ])
    msgs, stats, notes = vd.run_pixel_and_computed(_BASE, _HEAD, "p.html", 1440, _Cfg(1))
    assert msgs == []
    assert len(notes) == 1
    assert "differs from ITSELF" in notes[0]
    assert "Demoted" in notes[0]
    assert stats["self_control"] == {"diff_pixels": 8}


def test_the_control_never_demotes_a_computed_finding(monkeypatch):
    """Raster flicker moves pixels; it does not move a computed value. A
    control that demoted the computed channel too would hand back the one
    channel that still had signal."""
    both = (["pixel: 8 diff pixels", "computed: 3 of 60 computed values differ"],
            {"pixel": {"diff_pixels": 8}})
    _fake_measure(monkeypatch, [both, both, (["pixel: 8 diff pixels"], {"pixel": {}})])
    msgs, _, notes = vd.run_pixel_and_computed(_BASE, _HEAD, "p.html", 1440, _Cfg(1))
    assert msgs == ["computed: 3 of 60 computed values differ"]
    assert len(notes) == 1


def test_the_control_never_demotes_a_rendered_SIZE_change(monkeypatch):
    """A frame that changed height is not something a self-difference can
    explain away, so it skips the control entirely."""
    size = ([f"pixel: {vd._SIZE_FINDING} 390x7724 vs 390x7801"], {"pixel": {}})
    calls = _fake_measure(monkeypatch, [size, size, ([], {"pixel": {}})])
    msgs, _, notes = vd.run_pixel_and_computed(_BASE, _HEAD, "p.html", 1440, _Cfg(1))
    assert msgs == [f"pixel: {vd._SIZE_FINDING} 390x7724 vs 390x7801"]
    assert notes == []
    assert [c["control"] for c in calls] == [False, False]  # no control run at all


def test_retries_zero_turns_both_guards_off(monkeypatch):
    calls = _fake_measure(monkeypatch, [(["pixel: 8 diff pixels"], {})])
    msgs, _, notes = vd.run_pixel_and_computed(_BASE, _HEAD, "p.html", 1440, _Cfg(0))
    assert msgs == ["pixel: 8 diff pixels"]
    assert notes == []
    assert len(calls) == 1


# ─── argument handling and the exit-code contract ───────────────────────
@pytest.mark.parametrize("text,expected", [
    ("1440", (1440,)),
    ("1440,768,390", (1440, 768, 390)),
    ("1440 390", (1440, 390)),
])
def test_widths_parse(text, expected):
    assert vd._parse_widths(text) == expected


@pytest.mark.parametrize("text", ["", "abc", "0", "-1", "1440,x"])
def test_bad_widths_raise(text):
    with pytest.raises(ValueError):
        vd._parse_widths(text)


def test_channels_parse_and_dedupe():
    assert vd._parse_channels("pixel,computed,hover") == ("pixel", "computed", "hover")
    assert vd._parse_channels("hover,hover") == ("hover",)


@pytest.mark.parametrize("text", ["", "bogus", "pixel,bogus"])
def test_bad_channels_raise(text):
    with pytest.raises(ValueError):
        vd._parse_channels(text)


def test_default_motion_is_no_preference():
    """The default browsing case, and the one with more coverage. `reduce`
    collapses the site's own transitions to 0.01ms, which hides a changed
    `transition-duration` outright. It was the default only while
    no-preference measured nondeterministic (34,001 self-diff pixels on
    index.html), and that was a hole in this file — the document-timeline
    freeze reached the hover read and not the resting capture."""
    args = vd.build_parser().parse_args(["origin/main"])
    assert args.motion == "no-preference"


def test_defaults_are_the_documented_ones():
    args = vd.build_parser().parse_args(["origin/main"])
    assert vd._parse_widths(args.widths) == (1440, 768, 390)
    assert vd._parse_channels(args.channels) == ("pixel", "computed", "hover")
    assert args.self_check is False
    assert args.retries == 1
    assert args.hover_cap == 3


@pytest.mark.parametrize("argv", [
    ["origin/main", "--widths", "abc"],
    ["origin/main", "--channels", "bogus"],
])
def test_bad_arguments_exit_2_without_touching_a_browser(argv, capsys):
    assert vd.main(argv) == 2
    assert "error:" in capsys.readouterr().err


def _stub_run(monkeypatch, tmp_path, sweep_result):
    """Drive `main` past the worktree and straight into `sweep`."""
    import contextlib

    @contextlib.contextmanager
    def fake_worktree(ref):
        yield tmp_path, "0" * 40

    monkeypatch.setattr(vd, "base_worktree", fake_worktree)
    monkeypatch.setattr(vd, "sweep", sweep_result)


def test_findings_exit_1(monkeypatch, tmp_path, capsys):
    """The 0-vs-1 split had no coverage at all: every main() test asserted 2,
    and `return 1 if all_findings else 0` -> `return 0` passed the whole
    suite. That mutation turns this into a rubber stamp with CI green."""
    _stub_run(monkeypatch, tmp_path,
              lambda *a, **k: (["p.html @1440: pixel: 900 diff pixels"], {"pages": {}}, []))
    rc = vd.main(["HEAD", "--pages", "p.html", "--out", str(tmp_path / "o")])
    assert rc == 1
    assert "FAIL" in capsys.readouterr().out


def test_no_findings_exit_0(monkeypatch, tmp_path, capsys):
    _stub_run(monkeypatch, tmp_path, lambda *a, **k: ([], {"pages": {}}, []))
    rc = vd.main(["HEAD", "--pages", "p.html", "--out", str(tmp_path / "o")])
    assert rc == 0
    assert "PASS" in capsys.readouterr().out


def test_coverage_notes_alone_do_not_fail_the_run(monkeypatch, tmp_path, capsys):
    """Notes are places the sweep could not look, not differences. They print
    on a PASS and they do not change the exit code."""
    _stub_run(monkeypatch, tmp_path,
              lambda *a, **k: ([], {"pages": {}}, ["p.html: 1 subject unreachable in BOTH"]))
    assert vd.main(["HEAD", "--pages", "p.html", "--out", str(tmp_path / "o")]) == 0
    out = capsys.readouterr().out
    assert "coverage notes" in out and "PASS" in out


@pytest.mark.parametrize("exc", [
    RuntimeError("could not launch chromium"),
    OSError("could not bind port"),
    ValueError("a bug in the comparison"),
])
def test_ANY_failure_to_complete_the_run_exits_2(monkeypatch, tmp_path, capsys, exc):
    """An uncaught Python exception exits 1 by default, which is this tool's
    `differences found` code — so a browser that will not launch would land in
    CI's `post the diff` branch. Measured before the fix: a launch failure
    exited 1, an OSError from serve exited 1."""
    def boom(*a, **k):
        raise exc

    _stub_run(monkeypatch, tmp_path, boom)
    rc = vd.main(["HEAD", "--pages", "p.html", "--out", str(tmp_path / "o")])
    assert rc == 2
    assert type(exc).__name__ in capsys.readouterr().err


def test_a_bad_base_ref_exits_2(monkeypatch, capsys):
    def boom(ref):
        raise RuntimeError(f"not a commit-ish: {ref}")

    monkeypatch.setattr(vd, "base_worktree", boom)
    assert vd.main(["no-such-ref", "--pages", "press.html"]) == 2
    assert "not a commit-ish" in capsys.readouterr().err


def test_a_missing_browser_exits_2_rather_than_passing(monkeypatch, capsys, tmp_path):
    """The one thing an environment failure must never do is look like a
    clean run."""
    monkeypatch.setattr(vd, "_import_sync_playwright", lambda: None)

    import contextlib

    @contextlib.contextmanager
    def fake_worktree(ref):
        yield tmp_path, "0" * 40

    monkeypatch.setattr(vd, "base_worktree", fake_worktree)
    rc = vd.main(["HEAD", "--pages", "press.html", "--out", str(tmp_path / "o")])
    assert rc == 2
    assert "playwright is not installed" in capsys.readouterr().err


# ─── the worktree, without touching git ─────────────────────────────────
def test_the_base_worktree_is_always_removed(monkeypatch, tmp_path):
    """A leaked worktree is a leaked checkout of the whole site, and git
    leaves them behind on Windows when a file is still open."""
    calls = []

    class _R:
        returncode = 0
        stdout = "a" * 40 + "\n"
        stderr = ""

    def fake_git(args):
        calls.append(args)
        return _R()

    monkeypatch.setattr(vd, "_run_git", fake_git)
    with vd.base_worktree("HEAD") as (path, sha):
        assert sha == "a" * 40
    verbs = [a[:2] for a in calls]
    assert ["worktree", "add"] in verbs
    assert ["worktree", "remove"] in verbs
    assert ["worktree", "prune"] in verbs
    assert not path.exists()


def test_the_worktree_is_removed_even_when_the_body_raises(monkeypatch):
    calls = []

    class _R:
        returncode = 0
        stdout = "a" * 40 + "\n"
        stderr = ""

    monkeypatch.setattr(vd, "_run_git", lambda args: (calls.append(args), _R())[1])
    with pytest.raises(ZeroDivisionError):
        with vd.base_worktree("HEAD"):
            1 / 0
    assert ["worktree", "remove"] in [a[:2] for a in calls]


def test_a_bad_ref_never_creates_a_worktree(monkeypatch):
    class _Bad:
        returncode = 1
        stdout = ""
        stderr = "fatal: bad revision"

    monkeypatch.setattr(vd, "_run_git", lambda args: _Bad())
    with pytest.raises(RuntimeError, match="not a commit-ish"):
        with vd.base_worktree("nope"):
            pass


# ─── the non-coverage disclosure ────────────────────────────────────────
@pytest.mark.parametrize("phrase", [
    ":focus-visible",
    ":active",
    "::selection",
    "@media print",
    "forced-colors",
    "intended redesign from an accident",
    "never golden",
    # the three holes the review found missing from this list
    "4th and later elements of any hover signature",
    "viewport the hover channel does not visit",
])
def test_the_module_docstring_states_what_it_does_not_cover(phrase):
    """A committed harness that reads as more coverage than it has is worse
    than none, so the disclosure is pinned rather than left to erode."""
    # whitespace-normalized: the disclosure is prose and reflows
    doc = " ".join(vd.__doc__.lower().split())
    assert phrase.lower() in doc


def test_the_hover_coverage_disclosure_is_DERIVED_not_a_literal():
    """The disclosure said "53 of the 78" while the constants were 80 and 25,
    so 55 were unsampled — wrong in both numbers, repeated in five places, and
    PINNED by a substring test that made correcting it turn a test red.

    Counted from the constants here, so the sentence cannot drift from them
    again: adding a property to COMPUTED_PROPS without touching the prose
    fails this.
    """
    computed, hover = set(vd.COMPUTED_PROPS), set(vd.HOVER_PROPS)
    assert hover <= computed, sorted(hover - computed)
    doc = " ".join(vd.__doc__.lower().split())
    assert f"{len(computed - hover)} of the {len(computed)} properties, under hover" in doc, (
        f"docstring must say {len(computed - hover)} of the {len(computed)}"
    )
    assert f"`hover_props` is {len(hover)}" in doc, f"docstring must say HOVER_PROPS is {len(hover)}"


def test_no_property_is_listed_twice_in_either_channel():
    # A duplicate would inflate the "80 properties" claim without adding
    # coverage, which is how the wrong number survives review.
    assert len(vd.COMPUTED_PROPS) == len(set(vd.COMPUTED_PROPS))
    assert len(vd.HOVER_PROPS) == len(set(vd.HOVER_PROPS))


def test_the_docstring_forbids_the_two_wirings_that_would_be_wrong():
    """Never on every push (a full sweep is 12+ minutes) and never inside
    rotate-theme.yml (where every pixel is supposed to move on the 1st)."""
    doc = " ".join(vd.__doc__.split())
    assert "NOT on every push" in doc
    assert "NOT inside `rotate-theme.yml`" in doc

def test_the_workflow_itself_carries_neither_forbidden_trigger():
    # The docstring test two functions up asserts two SUBSTRINGS of a
    # docstring, which is a claim about prose. visual-diff.yml said "Adding
    # either trigger contradicts a shipped test" and it did not: adding
    # `push:` to `on:`, or a sweep step to rotate-theme.yml, left all tests
    # green. This reads the workflows.
    import yaml

    wf = yaml.safe_load((ROOT / ".github" / "workflows" / "visual-diff.yml").read_text(
        encoding="utf-8"))
    # PyYAML resolves the bare key `on` to the boolean True (YAML 1.1).
    triggers = wf.get("on", wf.get(True))
    assert set(triggers) == {"workflow_dispatch", "pull_request"}, triggers
    assert "push" not in triggers, "a full sweep is 17.5 minutes; not on every commit"

    rotate = (ROOT / ".github" / "workflows" / "rotate-theme.yml").read_text(encoding="utf-8")
    assert "visual-diff" not in rotate, (
        "on the 1st every pixel is SUPPOSED to move, so a two-tree pixel gate "
        "inside the rotation is either meaningless or neutered")


def test_the_pr_label_trigger_fires_on_a_pr_opened_with_the_label_already_on():
    # `opened` was missing, so a PR created with the label already applied did
    # not sweep until someone pushed to it again.
    import yaml

    wf = yaml.safe_load((ROOT / ".github" / "workflows" / "visual-diff.yml").read_text(
        encoding="utf-8"))
    types = (wf.get("on", wf.get(True)))["pull_request"]["types"]
    assert {"opened", "labeled", "synchronize"} <= set(types), types

