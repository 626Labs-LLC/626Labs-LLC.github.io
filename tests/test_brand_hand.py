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


# ---- The static footer signature --------------------------------------------
# The site changes its look monthly; the 626Labs signature in Este's hand at
# the foot of each page is the one thing that doesn't. It is styled by
# /assets/logos/signature.css, outside themes/, so a rotation can't restyle it,
# and every themed page must carry it.
SIGNATURE = 'class="site-signature"'


@pytest.mark.parametrize("slug", _registered_slugs())
@pytest.mark.parametrize("archetype", ["home", "product", "utility"])
def test_theme_shells_carry_the_signature(slug, archetype):
    html = (ROOT / "themes" / slug / "archetypes" / f"{archetype}.html").read_text(encoding="utf-8")
    assert SIGNATURE in html, f"{slug}/{archetype}: no footer signature"
    assert "/assets/logos/signature.css" in html, f"{slug}/{archetype}: signature.css not loaded"


@pytest.mark.parametrize("page", ["index.html", "press.html", "privacy.html",
                                  "plugins/index.html", "vibe-doc/index.html"])
def test_rendered_pages_carry_the_signature(page):
    html = (ROOT / page).read_text(encoding="utf-8")
    footer = html[html.rindex("<footer"):html.rindex("</footer>")]
    assert SIGNATURE in footer, f"{page}: the signature must sit in the footer"
    assert "/assets/logos/signature.css" in html


def test_signature_asset_and_style_exist():
    assert (ROOT / "assets" / "logos" / "626labs-signature-bold-dark.svg").is_file()
    css = (ROOT / "assets" / "logos" / "signature.css").read_text(encoding="utf-8")
    assert "626labs-signature-bold-dark.svg" in css and "currentColor" in css


def _public_pages() -> list[str]:
    reg = json.loads((ROOT / "content" / "page-archetypes.json").read_text(encoding="utf-8"))
    return [p for p in reg if not p.startswith("$")]


@pytest.mark.parametrize("page", _public_pages())
def test_every_public_page_carries_the_signature(page):
    # Every page mapped to an archetype, hand-authored or generated. A new
    # page joins this list the commit it is mapped, so it can't ship unsigned.
    html = (ROOT / page).read_text(encoding="utf-8")
    assert SIGNATURE in html, f"{page}: no footer signature"
    assert "/assets/logos/signature.css" in html, f"{page}: signature.css not loaded"
