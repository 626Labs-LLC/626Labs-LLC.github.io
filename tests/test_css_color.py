"""css_color.to_rgb — pinned against CHROMIUM, not against itself.

Every expected value below was produced by painting the same string into a
canvas in headless Chromium and reading the pixel back
(`<scratchpad>/colorcheck.py`, 50 cases, 0 mismatched). So these tests fail if
the module drifts from the browser, which is the only authority that matters
for a gate whose job is to grade what a browser will render.

Why the module exists at all: the contrast gate understood hex and
`rgb()`/`rgba()` only, an unresolvable pair is a FAILURE by design, and
`rotate-theme.yml` aborts on a failed gate. A theme shipping an ordinary
`oklch()` palette with declared contrastPairs lost the month, unattended, while
being completely correct.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("css_color", ROOT / "scripts" / "css_color.py")
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)

_td_spec = importlib.util.spec_from_file_location("theme_doctor", ROOT / "scripts" / "theme-doctor.py")
td = importlib.util.module_from_spec(_td_spec)
_td_spec.loader.exec_module(td)


# (value, expected sRGB) — expected is what Chromium painted.
BROWSER_VERIFIED = [
    ("#abc", (170, 187, 204)),
    ("#aabbcc", (170, 187, 204)),
    ("#abcd", (170, 187, 204)),
    ("#aabbccdd", (170, 187, 204)),
    ("#17d4fa", (23, 212, 250)),
    ("rgb(23, 212, 250)", (23, 212, 250)),
    ("rgba(23,212,250,.5)", (23, 212, 250)),
    ("rgb(23 212 250 / 0.4)", (23, 212, 250)),
    ("hsl(200, 96%, 54%)", (25, 175, 250)),
    ("hsl(200 96% 54%)", (25, 175, 250)),
    ("hsl(3.5rad 96% 54%)", (25, 173, 250)),
    ("hsl(0.55turn 96% 54%)", (25, 183, 250)),
    ("hwb(200 10% 20%)", (26, 145, 204)),
    ("hwb(200 60% 60%)", (128, 128, 128)),
    ("lab(52% 40 59)", (197, 92, 10)),
    ("lab(52 40 59)", (197, 92, 10)),
    ("lch(52% 72 55)", (199, 91, 11)),
    ("lch(29% 40 300)", (75, 58, 123)),
    ("oklab(0.5 0.1 -0.1)", (129, 69, 154)),
    ("oklch(0.92 0.02 240)", (217, 231, 241)),
    ("oklch(0.18 0.04 250)", (3, 18, 34)),
    ("oklch(0.7 0.15 30)", (237, 118, 101)),
    ("oklch(70% 0.15 30)", (237, 118, 101)),
    ("oklch(0.62 0.24 29.2)", (245, 34, 24)),
    ("color(srgb 0.1 0.2 0.3)", (26, 51, 77)),
    ("color(srgb-linear 0.1 0.2 0.3)", (89, 124, 149)),
    ("color(display-p3 0.5 0.2 0.9)", (138, 44, 238)),
    ("color(rec2020 0.5 0.2 0.9)", (158, 43, 243)),
    ("color(a98-rgb 0.5 0.2 0.9)", (147, 48, 234)),
    ("color(prophoto-rgb 0.5 0.2 0.9)", (147, 0, 249)),
    ("color(xyz 0.2 0.3 0.4)", (0, 167, 164)),
    ("color(xyz-d50 0.2 0.3 0.4)", (0, 168, 189)),
    ("color-mix(in oklab, red 50%, blue)", (140, 83, 162)),
    ("color-mix(in srgb, red, blue)", (128, 0, 128)),
    ("color-mix(in srgb, red 30%, blue 70%)", (77, 0, 179)),
    ("color-mix(in oklch, oklch(0.9 0.1 20) 40%, oklch(0.2 0.05 250))", (101, 84, 127)),
    ("color-mix(in hsl, red, blue)", (255, 0, 255)),
    ("color-mix(in srgb-linear, white, black)", (188, 188, 188)),
    ("color-mix(in oklab, #17d4fa 25%, #f22f89)", (220, 110, 165)),
    ("white", (255, 255, 255)),
    ("black", (0, 0, 0)),
    ("rebeccapurple", (102, 51, 153)),
    ("darkslategray", (47, 79, 79)),
    ("oklch(0.5 0.1 none)", (144, 73, 97)),
    ("oklch(none 0.1 200)", (0, 0, 1)),
    ("lab(50% none 30)", (132, 118, 67)),
]


@pytest.mark.parametrize("value,expected", BROWSER_VERIFIED)
def test_matches_what_chromium_paints(value, expected):
    got = cc.to_rgb(value)
    assert got is not None, f"{value!r} did not resolve at all"
    # +/-1 per channel: the module rounds once at the end, the canvas rounds
    # on its own way out, and the two can disagree in the last bit.
    assert all(abs(got[i] - expected[i]) <= 1 for i in range(3)), (value, got, expected)


def test_the_modern_syntaxes_the_gate_used_to_reject_all_resolve():
    # The CRITICAL, in one place. Every one of these returned None before,
    # which check_contrast turns into a FAILURE, which aborts the rotation.
    for value in ("oklch(0.18 0.04 250)", "oklab(0.5 0.1 -0.1)", "lab(52% 40 59)",
                  "lch(52% 72 55)", "hwb(200 10% 20%)", "color(display-p3 .5 .2 .9)",
                  "color-mix(in oklab, red 50%, blue)", "rebeccapurple"):
        assert cc.to_rgb(value) is not None, value


def test_alpha_is_ignored_deliberately_and_consistently():
    # Not modelled, and the same answer whichever syntax carries it — a static
    # gate has no backdrop to composite against. Stated in the module
    # docstring; pinned here so it stays a decision rather than an accident.
    opaque = cc.to_rgb("rgb(23, 212, 250)")
    for translucent in ("rgba(23,212,250,.5)", "rgb(23 212 250 / 0.4)",
                        "rgb(23 212 250 / 40%)", "#17d4fa80"):
        assert cc.to_rgb(translucent) == opaque, translucent


def test_a_value_that_is_not_a_color_returns_none_rather_than_raising():
    for value in ("", "   ", "not-a-color", "var(--x)", "url(a.png)", "#12345",
                  "rgb(", "oklch()", "color(nonesuch 1 2 3)", "color-mix(in oklab, red)",
                  "linear-gradient(90deg, red, blue)", "inherit", "currentColor"):
        assert cc.to_rgb(value) is None, value


def test_the_contrast_gate_grades_a_modern_palette_instead_of_failing_it():
    # End to end through the gate's own entry point, which is where the
    # rotation-aborting failure came from.
    css = ":root{--fg: oklch(0.92 0.02 240); --bg: oklch(0.18 0.04 250);}"
    failures, advisories = td.check_contrast(css, [["--fg", "--bg"]])
    assert failures == [], failures
    [(fg, bg, ratio)] = td.evaluate_contrast_pairs(css, [["--fg", "--bg"]])
    assert ratio is not None and ratio > 4.5, ratio


def test_an_unresolvable_pair_is_still_a_failure_not_a_shrug():
    # The fix widened what "resolvable" means; it did not soften the verdict.
    # An ungraded check is a failed check — that ruling stands.
    css = ":root{--fg: notacolor; --bg: #000;}"
    failures, _ = td.check_contrast(css, [["--fg", "--bg"]])
    assert failures and "could not resolve" in failures[0], failures
