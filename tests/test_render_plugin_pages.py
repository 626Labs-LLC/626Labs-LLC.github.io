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
import json
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
    whole expression removes the guesswork.

    It does NOT subsume the import-order test above, which stays load-
    bearing: this pins the order of the two FILES, not that the dress's
    @import is the first rule INSIDE it. Move that @import into the middle
    of product.css and composition equality still passes while every
    generated page falls back to system fonts.
    """
    d = _archetype_dir()
    dress = (d / "product.css").read_text(encoding="utf-8")
    tokens = (d / "product-tokens.css").read_text(encoding="utf-8")
    assert _load_renderer().STYLE == dress.rstrip("\n") + "\n" + tokens


def test_list_outputs_names_every_generated_page_and_nothing_else():
    """`--list-outputs` is now the pathspec source for BOTH CI workflows'
    change-detection and `git add` lists, replacing the glob
    `vibe-* thesis-engine plugins`.

    The glob was wrong twice. It self-maintains only for ids starting
    `vibe-` — `thesis-engine` was already the counterexample and had to be
    hand-listed, so the next non-`vibe-` plugin id renders on the runner and
    is never committed. And a glob matching nothing reaches git as a literal
    pathspec, which errors, which makes `[ -n "$(…)" ]` evaluate FALSE: the
    workflow reports "no changes" instead of failing.

    So this asserts the contract those workflows rely on: exactly the pages
    build() writes, repo-relative posix paths, LF-terminated, no spaces, and
    every one of them actually on disk (git errors on a pathspec that
    matches nothing, which is the right direction but only if the list is
    honest).
    """
    import subprocess

    # BYTES, not text=True: universal-newline decoding would translate the
    # CRLF this test exists to catch straight back into LF.
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render-plugin-pages.py"), "--list-outputs"],
        capture_output=True, cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    raw = result.stdout.decode("utf-8")
    assert "\r" not in raw, (
        "CRLF in --list-outputs: a path with a trailing \\r reaches git as a "
        "different pathspec and `git add` dies on it"
    )

    listed = raw.splitlines()
    expected = sorted(
        p.relative_to(ROOT).as_posix() for p in _load_renderer().build()
    )
    assert sorted(listed) == expected
    assert len(listed) == len(set(listed))
    for rel in listed:
        assert " " not in rel, f"{rel!r} has a space; the workflows word-split this"
        assert not rel.startswith("/") and ".." not in rel
        assert (ROOT / rel).exists(), f"{rel} is listed but not on disk"

    # The glob's blind spot, pinned: ids that do not start "vibe-" must be
    # in here. If this ever drops to zero the regression is invisible again.
    assert [r for r in listed if not r.startswith("vibe-")], (
        "no non-vibe- page in the list — the glob this replaced would look "
        "correct again and the next such plugin would silently go missing"
    )


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


def _active_theme_name() -> str:
    slug = theme_registry.active_slug(theme_registry.load())
    meta = json.loads((ROOT / "themes" / slug / "theme.json").read_text(encoding="utf-8"))
    return meta["name"]


IMPRINT_LINK = '<a href="/themes.html">see all themes</a>'


def test_footer_carries_exactly_one_imprint_with_a_themes_link_and_the_active_name():
    """The footer is renderer-owned, so no theme can put a link in it. The
    imprint line is emitted here from the active theme's theme.json name,
    which is what makes it right in every month with no edit. Exactly one
    imprint, a real /themes.html link, the name as theme.json spells it,
    and the interpunct as the literal character (a `\00B7` escape once
    ate the space after it and shipped "·this"). Fails when the emission
    is removed: verified by mutation."""
    footer = _load_renderer().render_footer()
    name = _active_theme_name()
    assert footer.count('class="container imprint"') == 1
    assert footer.count(IMPRINT_LINK) == 1
    assert f"Theme: {name} · this site changes monthly · {IMPRINT_LINK}" in footer
    assert "\\00B7" not in footer and "&middot;" not in footer


def test_every_generated_page_carries_the_imprint_once():
    """The footer is shared by the 15 plugin pages and the family index;
    each carries the one imprint, and nothing else on the page links the
    gallery so the count is exactly one."""
    mod = _load_renderer()
    name = _active_theme_name()
    outputs = mod.build()
    assert len(outputs) >= 15
    for path, html in outputs.items():
        assert html.count('class="container imprint"') == 1, path
        assert html.count(IMPRINT_LINK) == 1, path
        assert f"Theme: {name} ·" in html, path
