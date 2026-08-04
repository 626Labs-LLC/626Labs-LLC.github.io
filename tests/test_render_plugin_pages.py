"""The product archetype's CSS is TWO files now, concatenated by this
renderer. These pin the two properties that split depends on.

Why the split exists at all: conundrum.html and rororo-plugins.html are
hand-authored product pages that link the theme for its PALETTE. They must
not inherit the element DRESS, whose bare `body`/`a:hover`/`section.hero`/
`.card`/`.btn` selectors are written for the templates in this file. The 15
pages this renderer generates need both halves, so it concatenates them —
and the concatenation has exactly two ways to go wrong.
"""
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import theme_registry  # noqa: E402


def _load_renderer():
    spec = importlib.util.spec_from_file_location(
        "render_plugin_pages", ROOT / "scripts" / "render-plugin-pages.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _archetype_dir() -> Path:
    slug = theme_registry.active_slug(theme_registry.load())
    return ROOT / "themes" / slug / "archetypes"


def _strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def test_style_keeps_the_font_import_as_the_very_first_rule():
    """Failure mode 1: wrong concatenation order.

    product.css opens with `@import url('/fonts/fonts.css')`. CSS requires
    @import to precede every rule but @charset/@layer, so putting the token
    file first makes the browser silently DROP it — the whole brand type
    stack stops loading and all 15 pages reflow to fallback fonts. That is
    not hypothetical: tokens-first was tried and measured at 1,321,489
    changed pixels on plugins/index.html plus a height change on every
    page, with no error anywhere.

    Nothing else catches it. render-plugin-pages.py --check compares
    rendered bytes against rendered bytes, so a reordered STYLE is
    self-consistently "up to date"; theme-doctor's token gate only counts
    names. This is the check.
    """
    style = _strip_comments(_load_renderer().STYLE)
    imports = [m.start() for m in re.finditer(r"@import\b", style)]
    assert imports, "STYLE lost its @import entirely"
    first_rule = re.search(r"[^\s]", style)
    assert style[first_rule.start():].startswith("@import"), (
        "STYLE must open with @import — a rule ahead of it makes the browser "
        "drop the font import and every generated page falls back"
    )
    # And it must not be preceded by a brace anywhere.
    assert "{" not in style[: imports[0]], (
        "a CSS rule precedes the @import in STYLE; the import will be ignored"
    )


def test_style_is_exactly_the_dress_then_the_tokens():
    """Composition equality, not spot-checks.

    An earlier cut asserted two needles and two length bounds. That passes
    unchanged if the join becomes `dress + "\\n\\n" + tokens`, or if the
    `.rstrip("\\n")` is dropped, or if either half is concatenated twice —
    every one of which changes the bytes committed to 15 pages. Pinning the
    whole expression removes the guesswork, and it subsumes the import-order
    test above as a side effect (the dress leads, so its @import leads).
    """
    d = _archetype_dir()
    dress = (d / "product.css").read_text(encoding="utf-8")
    tokens = (d / "product-tokens.css").read_text(encoding="utf-8")
    assert _load_renderer().STYLE == dress.rstrip("\n") + "\n" + tokens


def test_product_css_and_tokens_agree_on_every_shared_name():
    """Failure mode 2: the two files drifting apart on a shared name.

    They deliberately overlap — product-tokens.css has to be COMPLETE
    against archetypes.REQUIRED_TOKENS, and product.css independently
    defines some of the same palette names for its own rules. Identical
    values are what make the concatenation order irrelevant to everything
    except the @import above. Let one drift and the 15 generated pages
    silently take whichever file is concatenated last, while the two
    LINKING pages take the token file's value — the same name rendering
    two different colors on two halves of the same archetype.
    """
    d = _archetype_dir()

    def props(path):
        out = {}
        for m in re.finditer(
            r"(--[\w-]+)\s*:\s*([^;}]+)", _strip_comments(path.read_text(encoding="utf-8"))
        ):
            out[m.group(1)] = m.group(2).strip()
        return out

    dress, tokens = props(d / "product.css"), props(d / "product-tokens.css")
    shared = sorted(set(dress) & set(tokens))
    assert shared, "expected the two files to share palette names"
    mismatched = {k: (dress[k], tokens[k]) for k in shared if dress[k] != tokens[k]}
    assert not mismatched, (
        f"product.css and product-tokens.css disagree on {sorted(mismatched)}: "
        f"{mismatched}"
    )
