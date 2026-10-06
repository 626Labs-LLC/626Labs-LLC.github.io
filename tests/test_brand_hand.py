"""Este's own words, in his hand.

EsteFont Pro (Este's handwriting, added 2026-10-06) sets the lines that are
his: the homepage founding quote and About's pull quotes. Those rules live in
each theme's own files, so a theme that rebuilds them from scratch would drop
the hand without anything noticing. These tests hold every theme that is live
or queued to it. Retired themes keep the look they shipped with.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FACE = "EsteFont Pro"


def _registered_slugs() -> list[str]:
    reg = json.loads((ROOT / "content" / "themes.json").read_text(encoding="utf-8"))
    return [reg["active"], *reg.get("queue", [])]


def _rule(css: str, selector: str) -> str:
    """The body of the first rule whose selector is exactly `selector`."""
    m = re.search(r"(?m)^\s*" + re.escape(selector) + r"\s*\{([^}]*)\}", css)
    assert m, f"no `{selector}` rule"
    return m.group(1)


def test_the_face_is_self_hosted_in_both_weights():
    css = (ROOT / "fonts" / "fonts.css").read_text(encoding="utf-8")
    for weight, name in ((400, "Regular"), (700, "Bold")):
        assert re.search(
            r"font-family:\s*'EsteFont Pro';[^}]*font-weight:\s*%d;[^}]*EsteFontPro-%s\.woff2" % (weight, name),
            css,
        ), f"fonts.css has no {weight} face for {FACE}"
        assert (ROOT / "fonts" / f"EsteFontPro-{name}.woff2").is_file()


@pytest.mark.parametrize("slug", _registered_slugs())
def test_founding_quote_is_in_his_hand(slug):
    home = (ROOT / "themes" / slug / "archetypes" / "home.html").read_text(encoding="utf-8")
    body = _rule(home, "section.thinking blockquote")
    assert FACE in body, f"{slug}: the founding quote is not set in {FACE}"
    assert "italic" not in body, f"{slug}: the hand is drawn upright; don't italicize it"


@pytest.mark.parametrize("slug", _registered_slugs())
def test_about_pull_quotes_are_in_his_hand(slug):
    css = (ROOT / "themes" / slug / "archetypes" / "reading.css").read_text(encoding="utf-8")
    body = _rule(css, ".lnt-pull-quote p")
    assert FACE in body, f"{slug}: About's pull quotes are not set in {FACE}"
    assert "italic" not in body, f"{slug}: the hand is drawn upright; don't italicize it"


def test_about_default_dress_is_in_his_hand():
    html = (ROOT / "about.html").read_text(encoding="utf-8")
    assert FACE in _rule(html, ".lnt-pull-quote p")
