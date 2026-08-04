import importlib.util, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("theme_doctor", ROOT / "scripts" / "theme-doctor.py")
td = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(td)

ZONES = ("hero", "hero-chips", "products", "lab-pool", "thinking", "founding",
         "stories", "lab-runs", "play", "about", "support", "contact")


def _good_html():
    zones = "\n".join(f"<!-- SITE_JSON:{z}:start --><!-- SITE_JSON:{z}:end -->" for z in ZONES)
    # Carries every `home` vocabulary class too (archetypes.VOCABULARY) so
    # this fixture also satisfies check_vocabulary when main() uses it as
    # the mocked home render — the two main()-level browser tests below
    # feed this straight into the `home` archetype's checks.
    vocab = "".join(f'<div class="{c}"></div>' for c in td.archetypes.VOCABULARY["home"])
    return f"""<html><head></head><body>
      <a class="skip-link" href="#main">Skip</a><nav>x</nav>
      {zones}{vocab}<footer>f</footer>
      <script data-goatcounter="https://626labs.goatcounter.com/count"></script>
    </body></html>"""


def _compliant_archetype_html(archetype):
    """Minimal markup satisfying both check_vocabulary and
    ARCHETYPE_CHROME's profile for `archetype` — used to build stub theme
    dirs so tests that aren't specifically probing vocabulary/chrome (the
    browser-check tests) don't trip on the per-archetype checks by
    accident."""
    classes = "".join(f'<div class="{c}"></div>' for c in td.archetypes.VOCABULARY[archetype])
    profile = td.ARCHETYPE_CHROME[archetype]
    bits = []
    if profile["skip_link"]:
        bits.append('<a class="skip-link" href="#main">Skip</a>')
    if profile["nav"]:
        bits.append("<nav>x</nav>")
    bits.append(classes)
    if profile["footer"]:
        bits.append("<footer>f</footer>")
    if profile["analytics"]:
        bits.append('<script data-goatcounter="https://626labs.goatcounter.com/count"></script>')
    return f"<html><body>{''.join(bits)}</body></html>"


def test_main_shell_html_alone_no_longer_satisfies_completeness(monkeypatch, tmp_path):
    # The legacy shell.html fallback is gone (A4): a theme carrying only
    # shell.html (no archetypes/ dir) must FAIL, naming every missing
    # archetype file — not get waved through to the render step.
    tdir = tmp_path / "themes" / "legacy-only"
    tdir.mkdir(parents=True)
    (tdir / "shell.html").write_text("<html></html>", encoding="utf-8")
    (tdir / "tokens.css").write_text("", encoding="utf-8")
    (tdir / "theme.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)

    rc = td.main(["legacy-only"])
    assert rc == 1


def test_zones_pass_when_all_present():
    assert td.check_zones(_good_html(), "") == []


def test_zones_flag_a_missing_zone():
    html = _good_html().replace("<!-- SITE_JSON:products:start --><!-- SITE_JSON:products:end -->", "")
    errs = td.check_zones(html, "")
    assert any("products" in e for e in errs)


def test_chrome_flags_missing_skip_link():
    errs = td.check_chrome(_good_html().replace('class="skip-link"', 'class="x"'), "")
    assert any("skip" in e.lower() for e in errs)


def test_chrome_flags_missing_analytics():
    errs = td.check_chrome(_good_html().replace("data-goatcounter", "data-nothing"), "")
    assert any("analytics" in e.lower() or "goatcounter" in e.lower() for e in errs)


def test_internal_links_flag_a_dead_target():
    html = _good_html().replace("<nav>x</nav>", '<nav><a href="/nope-does-not-exist.html">x</a></nav>')
    errs = td.check_internal_links(html, "")
    assert any("nope-does-not-exist" in e for e in errs)


def test_live_theme_passes_static_checks():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert td.check_zones(html, "") == []
    assert td.check_chrome(html, "") == []


class _StubPage:
    """Minimal page-like stub for _check_viewport — no real browser needed.

    goto_side_effect: exception instance to raise (navigation failure), or a
    response-like value to return (e.g. a fake with .status).
    """

    def __init__(self, goto_side_effect):
        self._goto_side_effect = goto_side_effect

    def on(self, event, handler):
        pass

    def goto(self, url, wait_until="load", timeout=15000):
        if isinstance(self._goto_side_effect, Exception):
            raise self._goto_side_effect
        return self._goto_side_effect

    def wait_for_timeout(self, ms):
        pass

    def evaluate(self, expr):
        return 0


def test_browser_navigation_failure_is_a_gate_failure_not_a_skip():
    # The page under test throwing/timing out on load is the theme's fault —
    # it must produce a failure string (gate fails), never a silent skip.
    page = _StubPage(TimeoutError("Timeout 15000ms exceeded"))
    errs = td._check_viewport(page, "http://127.0.0.1:0/", 1440)
    assert errs, "navigation failure must return a non-empty failure list"
    assert any("1440" in e for e in errs)
    assert not any("skip" in e.lower() for e in errs)


def test_browser_non_2xx_response_is_a_gate_failure():
    class _Response:
        status = 500

    page = _StubPage(_Response())
    errs = td._check_viewport(page, "http://127.0.0.1:0/", 768)
    assert any("500" in e for e in errs)


# ─── --require-browser routing (Fix 1: the unattended-rotation gate) ──────
#
# The bug this covers: rotate-theme.yml called `--browser` without ever
# installing playwright, so `_run_browser_checks` hit the ImportError branch,
# printed "browser checks skipped", and returned [] — every unattended
# rotation passed the gate with the horizontal-scroll/console-error checks
# never having run at all. `--require-browser` turns that same unavailability
# into a failure string instead of a skip.


def test_browser_unavailable_is_a_skip_without_require_browser(monkeypatch):
    monkeypatch.setattr(td, "_import_sync_playwright", lambda: None)
    errs = td._run_browser_checks("<html></html>", require=False)
    assert errs == []


def test_browser_unavailable_is_a_gate_failure_with_require_browser(monkeypatch):
    monkeypatch.setattr(td, "_import_sync_playwright", lambda: None)
    errs = td._run_browser_checks("<html></html>", require=True)
    assert errs, "playwright unavailable + --require-browser must fail, not skip"
    assert any("playwright" in e.lower() for e in errs)


def _compliant_reading_css():
    # reading's vocabulary check is CSS-selector-only for its 7 lnt-*
    # classes as of A7 (see READING_SHARED_LEAF_CLASSES / _check_archetype)
    # — the shared ed-* leaves are credited from a synthetic anchor string,
    # never from this file.
    #
    # The lnt-* set alone is no longer enough: reading.css joined tokens.css
    # and utility.css under check_required_tokens once thesis.html and
    # workflow.html started reading it with no local fallback of their own,
    # so a stub theme's reading.css has to define the full REQUIRED_TOKENS
    # set as well. Before that gate existed this fixture wrote a reading.css
    # with ZERO custom properties and the stub theme still PASSED — which is
    # exactly the hole the gate closes, and exactly why this fixture had to
    # move with it.
    #
    # It stopped needing _required_tokens_css() when the reading archetype
    # split: thesis.html and workflow.html link archetypes/reading-tokens.css
    # now, so reading.css is purely about.html's dress and carries no base
    # vocabulary. Leaving the tokens here would have this fixture assert a
    # contract the live file no longer has to meet.
    lnt_classes = [c for c in td.archetypes.VOCABULARY["reading"] if not c.startswith("ed-")]
    return "".join(f".{c} {{ }}\n" for c in lnt_classes)


def _required_tokens_css() -> str:
    """A minimal, syntactically-valid `:root` block declaring every
    archetypes.REQUIRED_TOKENS name with a throwaway value — the
    token-completeness half of a "complete" stub theme (final review
    Fix 1), alongside _make_complete_theme_dir's vocabulary/chrome-
    satisfying archetype markup below. check_required_tokens only cares
    that the name is DEFINED, not what it resolves to, so `0` is fine for
    every group (colors, fonts, durations included) — this fixture is
    exercising completeness, not contrast or rendering."""
    decls = "".join(f"{tok}: 0;\n" for tok in sorted(td.archetypes.REQUIRED_TOKENS))
    return f":root {{\n{decls}}}\n"


def _make_complete_theme_dir(tdir):
    # All four archetype files + tokens.css/theme.json — the shell.html
    # fallback is gone (A4), so a theme needs the full archetypes/ set to
    # clear theme-doctor's completeness check. A6 adds archetypes/product.css
    # + archetypes/utility.css to that completeness requirement (see
    # REQUIRED_ARCHETYPE_CSS) and adds real per-archetype chrome/vocabulary
    # checks against product.html/utility.html's own content — so the stub
    # archetype markup has to be vocabulary-and-chrome-compliant now, not
    # just present, or the browser-focused tests below (which expect the
    # static checks to pass cleanly) would trip on the new checks instead of
    # exercising what they're actually testing. A7 adds archetypes/
    # reading.css to that same completeness requirement, and reading's own
    # dress (not about.html's) is now what the vocabulary check grades.
    # The final review's Fix 1 adds one more: tokens.css AND
    # archetypes/utility.css now both have to define every
    # archetypes.REQUIRED_TOKENS name — empty strings (the pre-Fix-1
    # fixture) would now fail every stub theme at the new gate before any
    # of the checks below ever ran, so both get _required_tokens_css()
    # instead of "". archetypes/reading.css is the third file under that
    # same gate now — see _compliant_reading_css.
    #
    # archetypes/product-tokens.css is the FOURTH, added the same commit
    # conundrum.html and rororo-plugins.html started linking it with no
    # local fallback. Until then this fixture wrote archetypes/product.css
    # as the empty string — ZERO custom properties — and a stub theme
    # cleared the doctor anyway. That is the hole, demonstrated: the CSS
    # dressing the most pages of any archetype (2 linked + 15 inlined) was
    # the one the token contract never graded.
    #
    # Note the shape: product.css is a DRESS (element rules, no tokens) and
    # product-tokens.css is the vocabulary. That is the real split, so the
    # fixture models it — a stub whose product.css carried the tokens would
    # pass a gate the live theme could not.
    (tdir / "archetypes").mkdir(parents=True)
    (tdir / "tokens.css").write_text(_required_tokens_css(), encoding="utf-8")
    (tdir / "theme.json").write_text("{}", encoding="utf-8")
    for a in td.theme_registry.REQUIRED_ARCHETYPES:
        (tdir / "archetypes" / f"{a}.html").write_text(_compliant_archetype_html(a), encoding="utf-8")
    (tdir / "archetypes" / "product.css").write_text(
        "".join(f".{c} {{ }}\n" for c in td.archetypes.VOCABULARY["product"]),
        encoding="utf-8",
    )
    (tdir / "archetypes" / td.PRODUCT_TOKENS_CSS).write_text(
        _required_tokens_css(), encoding="utf-8"
    )
    (tdir / "archetypes" / td.READING_TOKENS_CSS).write_text(
        _required_tokens_css(), encoding="utf-8"
    )
    (tdir / "archetypes" / "utility.css").write_text(_required_tokens_css(), encoding="utf-8")
    (tdir / "archetypes" / "reading.css").write_text(_compliant_reading_css(), encoding="utf-8")


def test_main_require_browser_implies_browser_and_fails_when_unavailable(monkeypatch, tmp_path):
    # A minimally-complete theme so we get all the way to the browser check.
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)

    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)
    monkeypatch.setattr(td, "_import_sync_playwright", lambda: None)

    class _Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def _fake_run(*a, **kw):
        (tmp_path / "index.html").write_text(_good_html(), encoding="utf-8")
        for name in td.BROWSER_CHECK_LIVE_PAGES:
            (tmp_path / name).write_text(_good_html(), encoding="utf-8")
        return _Result()

    monkeypatch.setattr(td.subprocess, "run", _fake_run)
    monkeypatch.setattr(
        td.tempfile, "TemporaryDirectory",
        lambda *a, **kw: __import__("contextlib").nullcontext(str(tmp_path)),
    )

    rc = td.main(["stub-theme", "--require-browser"])
    assert rc == 1


def test_main_browser_alone_is_still_ergonomic_when_playwright_missing(monkeypatch, tmp_path):
    # The local convenience path: --browser without playwright installed must
    # still PASS (skip, don't fail) — --require-browser is opt-in, not implied.
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)

    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)
    monkeypatch.setattr(td, "_import_sync_playwright", lambda: None)

    class _Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def _fake_run(*a, **kw):
        (tmp_path / "index.html").write_text(_good_html(), encoding="utf-8")
        for name in td.BROWSER_CHECK_LIVE_PAGES:
            (tmp_path / name).write_text(_good_html(), encoding="utf-8")
        return _Result()

    monkeypatch.setattr(td.subprocess, "run", _fake_run)
    monkeypatch.setattr(
        td.tempfile, "TemporaryDirectory",
        lambda *a, **kw: __import__("contextlib").nullcontext(str(tmp_path)),
    )

    rc = td.main(["stub-theme", "--browser"])
    assert rc == 0


# ─── A6: vocabulary enforcement (check_vocabulary) ─────────────────────────


def test_vocabulary_flags_a_missing_required_class():
    # `product` needs 9 classes (archetypes.VOCABULARY); this HTML carries
    # only 2 of them ("top", "hero") — the rest must be named as missing.
    html = '<nav class="top"></nav><section class="hero"></section>'
    errs = td.check_vocabulary(html, "", "product")
    assert any("install" in e for e in errs)
    assert any("family-card" in e for e in errs)
    assert not any("'top'" in e or "'hero'" in e for e in errs)


def test_vocabulary_css_targeting_an_off_vocabulary_class_still_fails():
    # The theme renamed the semantic anchor instead of using the vocabulary's
    # class name (docs/theme-archetypes.md's "one rule") — CSS is present,
    # just not for the required name, so the check must not be fooled by
    # irrelevant CSS into a false pass.
    html = "<html></html>"
    css = ".hero-mast { color: red; }"
    errs = td.check_vocabulary(html, css, "home")
    assert any("'hero'" in e for e in errs)


def test_vocabulary_class_may_come_from_html_alone():
    html = "".join(f'<div class="{c}"></div>' for c in td.archetypes.VOCABULARY["utility"])
    assert td.check_vocabulary(html, "", "utility") == []


def test_vocabulary_class_may_come_from_a_css_selector_instead_of_html():
    # product's `card`/`family-card`/`section-head` are stamped onto the DOM
    # by render-plugin-pages.py at render time, not by the theme's shell —
    # the theme only has to STYLE them (see check_vocabulary's docstring).
    css = "".join(f".{c} {{ color: red; }}\n" for c in td.archetypes.VOCABULARY["product"])
    errs = td.check_vocabulary("<html></html>", css, "product")
    assert errs == []


def test_vocabulary_names_the_archetype_in_the_failure():
    errs = td.check_vocabulary("<html></html>", "", "reading")
    assert all(e.startswith("reading:") for e in errs)
    assert len(errs) == len(td.archetypes.VOCABULARY["reading"])


# ─── A6: vocabulary against the real, shipped Phosphor Blueprint artifacts ──
# (proves check_vocabulary isn't just internally consistent, it's actually
# satisfied by what the reference theme ships today)


def test_live_product_shell_passes_vocabulary():
    tdir = ROOT / "themes" / "phosphor-blueprint" / "archetypes"
    html = (tdir / "product.html").read_text(encoding="utf-8")
    inline_css = "\n".join(td.STYLE_BLOCK_RE.findall(html))
    css = inline_css + "\n" + (tdir / "product.css").read_text(encoding="utf-8")
    assert td.check_vocabulary(html, css, "product") == []


def test_live_utility_shell_passes_vocabulary():
    tdir = ROOT / "themes" / "phosphor-blueprint" / "archetypes"
    html = (tdir / "utility.html").read_text(encoding="utf-8")
    css = (tdir / "utility.css").read_text(encoding="utf-8")
    assert td.check_vocabulary(html, css, "utility") == []


def test_about_html_carries_the_full_reading_vocabulary():
    # check_vocabulary itself is archetype-agnostic and this remains true at
    # that level: about.html's real markup carries all 10 required classes.
    # A7 changed WHAT the gate (_check_archetype/main()) actually feeds
    # check_vocabulary for "reading" — see the tests below — precisely
    # because this fact alone made the gate theme-invariant (any theme's
    # reading.css passed, since about.html's markup never varies).
    html = (ROOT / "about.html").read_text(encoding="utf-8")
    assert td.check_vocabulary(html, "", "reading") == []


# ─── A7: reading's vocabulary check is CSS-selector-only for its lnt-* half ─
# About's markup is theme-invariant (same page, every theme) — crediting it
# wholesale would make ANY theme's reading.css pass, including an empty one.
# _check_archetype closes that by feeding check_vocabulary a synthetic
# anchor for the 3 shared ed-* leaves only; the 7 lnt-* classes must come
# from a real CSS selector in the THEME's own archetypes/reading.css.


def test_reading_shared_leaf_classes_are_exactly_the_ed_prefixed_ones():
    assert td.READING_SHARED_LEAF_CLASSES == {"ed-page", "ed-title", "ed-dek"}


def test_reading_gate_ignores_about_html_markup_for_lnt_classes():
    # Feeding the REAL about.html (which carries every lnt-* class in its
    # own markup) with an EMPTY css must still fail every lnt-* class — if
    # this passed, about.html's markup alone would rubber-stamp any theme.
    about_html = (ROOT / "about.html").read_text(encoding="utf-8")
    errs = td._check_archetype("reading", about_html, "", False, None)
    lnt_required = [c for c in td.archetypes.VOCABULARY["reading"] if c.startswith("lnt-")]
    assert len(errs) == len(lnt_required)
    for cls in lnt_required:
        assert any(repr(cls) in e for e in errs)
    # The 3 shared ed-* leaves are still satisfied (from the synthetic
    # anchor, not from about.html) — no ed-* class should be reported missing.
    assert not any("ed-page" in e or "ed-title" in e or "ed-dek" in e for e in errs)


def test_reading_gate_passes_when_theme_css_covers_every_lnt_class():
    about_html = (ROOT / "about.html").read_text(encoding="utf-8")
    lnt_required = [c for c in td.archetypes.VOCABULARY["reading"] if c.startswith("lnt-")]
    css = "".join(f".{c} {{ }}\n" for c in lnt_required)
    assert td._check_archetype("reading", about_html, css, False, None) == []


def test_live_reading_css_passes_vocabulary_for_the_lnt_half():
    # The real, shipped extraction (themes/phosphor-blueprint/archetypes/
    # reading.css) has to actually cover every lnt-* class as a CSS
    # selector — not just in a synthetic test fixture.
    about_html = (ROOT / "about.html").read_text(encoding="utf-8")
    css = (ROOT / "themes" / "phosphor-blueprint" / "archetypes" / "reading.css").read_text(
        encoding="utf-8"
    )
    assert td._check_archetype("reading", about_html, css, False, None) == []


# ─── A6: the CSS-artifact completeness gate (carried requirement from A5) ──
# render-plugin-pages.py does `theme_dir(active)/archetypes/product.css` and
# reads it with NO existence guard; press.html/privacy.html resolve
# archetypes/utility.css the same unguarded way. A theme rotating in without
# either would crash 15 plugin pages (product.css) or 2 utility pages
# (utility.css) at unattended-rotation time. theme-doctor must catch this
# BEFORE the theme is even rendered, not after.


def test_main_theme_missing_product_css_fails_the_gate(monkeypatch, tmp_path, capsys):
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)
    (tdir / "archetypes" / "product.css").unlink()

    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)

    rc = td.main(["stub-theme"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "archetypes/product.css" in out


def test_main_theme_missing_utility_css_fails_the_gate(monkeypatch, tmp_path, capsys):
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)
    (tdir / "archetypes" / "utility.css").unlink()

    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)

    rc = td.main(["stub-theme"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "archetypes/utility.css" in out


def test_main_theme_missing_reading_css_fails_the_gate(monkeypatch, tmp_path, capsys):
    # A7's carried requirement: about.html's client-side toggle and this
    # module's own reading gate both read archetypes/reading.css with no
    # existence guard — a theme rotating in without it must fail here,
    # before it can be queued, not 404 the toggle or crash the gate later.
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)
    (tdir / "archetypes" / "reading.css").unlink()

    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)

    rc = td.main(["stub-theme"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "archetypes/reading.css" in out


def test_main_theme_with_all_archetype_css_files_clears_completeness(monkeypatch, tmp_path, capsys):
    # A complete stub theme must get PAST the completeness gate (it may
    # still fail later, e.g. because render-hub.py --theme isn't mocked
    # here) — proves the required-files check doesn't over-fire on a theme
    # that actually has all three CSS artifacts.
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)

    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)

    td.main(["stub-theme"])
    out = capsys.readouterr().out
    assert "product.css" not in out
    assert "utility.css" not in out
    assert "reading.css" not in out


# ─── final review Fix 1: the required-tokens contract ──────────────────────
# themes.html's own <style>, plus the residual <style> of press.html,
# privacy.html (the page-specific rules left after utility.css's A4
# extraction), thesis.html and workflow.html (same shape, after their private
# :root blocks moved into reading.css), and conundrum.html and
# rororo-plugins.html (same shape again, into product.css) read the
# REQUIRED_TOKENS set via
# var(--x) and never define them — nothing before this required a theme's
# tokens.css / archetypes/product.css / archetypes/utility.css /
# archetypes/reading.css to supply
# them. The last six carry no fallback of their own at all, so for them a
# missing name is an unresolved var(), not a stale value. See
# archetypes.REQUIRED_TOKENS's docstring and docs/theme-archetypes.md, "The
# token-variable contract."


def test_required_tokens_flags_a_missing_token():
    css = ":root { --bg-0: #000; }"
    errs = td.check_required_tokens(css)
    assert any("'--fg-1'" in e for e in errs)
    assert not any("'--bg-0'" in e for e in errs)


def test_required_tokens_pass_when_all_declared():
    assert td.check_required_tokens(_required_tokens_css()) == []


def test_required_tokens_error_names_every_missing_property():
    errs = td.check_required_tokens("")
    assert len(errs) == len(td.archetypes.REQUIRED_TOKENS)
    assert all("missing required custom property" in e for e in errs)


def test_live_tokens_css_satisfies_required_tokens():
    # Proves the fix wave's own extension of Phosphor Blueprint's
    # tokens.css (previously an "append-only override" that only ever
    # redefined 5 of the 43 required properties, relying on a hardcoded
    # LOCAL fallback in index.html/themes.html for the rest) actually
    # clears the new gate — not just in a synthetic fixture.
    css = (ROOT / "themes" / "phosphor-blueprint" / "tokens.css").read_text(encoding="utf-8")
    assert td.check_required_tokens(css) == []


def test_live_utility_css_satisfies_required_tokens():
    # utility.css needed no change for this fix — it was already
    # self-contained, extracted whole from press.html back in A4.
    css = (ROOT / "themes" / "phosphor-blueprint" / "archetypes" / "utility.css").read_text(
        encoding="utf-8"
    )
    assert td.check_required_tokens(css) == []


def test_live_reading_tokens_css_satisfies_required_tokens():
    # reading-tokens.css is the third file under this gate, as of thesis.html
    # and workflow.html giving up their private :root blocks. For those two
    # the stakes are the harsher kind: no local fallback at all, so a missing
    # name is an unresolved var() on a live page, not a stale color.
    css = (
        ROOT / "themes" / "phosphor-blueprint" / "archetypes" / td.READING_TOKENS_CSS
    ).read_text(encoding="utf-8")
    assert td.check_required_tokens(css) == []


def test_live_reading_tokens_css_declares_only_tokens():
    css = (
        ROOT / "themes" / "phosphor-blueprint" / "archetypes" / td.READING_TOKENS_CSS
    ).read_text(encoding="utf-8")
    assert td.check_token_css_declares_only_tokens(css) == []


def test_token_only_gate_covers_both_split_archetypes_and_not_utility():
    # The membership itself is the finding. product and reading are split
    # because two hand-authored pages each link them for a palette alone.
    # utility.css is NOT, and that is a description of where press.html and
    # privacy.html are today — they already wear a foreign element dress
    # with no page-side statement of their own — not a position that they
    # should. Splitting it means those pages taking ownership of a dress
    # they currently borrow: real work, real pixel risk, not a fix-round
    # addendum. Pinned so the absence stays deliberate and legible.
    assert set(td.TOKEN_ONLY_CSS) == {
        f"archetypes/{td.PRODUCT_TOKENS_CSS}",
        f"archetypes/{td.READING_TOKENS_CSS}",
    }
    assert "archetypes/utility.css" in td.REQUIRED_TOKEN_CSS
    assert "archetypes/utility.css" not in td.TOKEN_ONLY_CSS


def test_main_fails_a_theme_missing_reading_tokens_css_entirely(
    monkeypatch, tmp_path, capsys
):
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)
    (tdir / "archetypes" / td.READING_TOKENS_CSS).unlink()

    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)
    rc = td.main(["stub-theme"])
    assert rc == 1
    assert f"missing archetypes/{td.READING_TOKENS_CSS}" in capsys.readouterr().out


def test_live_product_tokens_css_satisfies_required_tokens():
    # product-tokens.css is the fourth file under this gate, as of
    # conundrum.html and rororo-plugins.html giving up their private :root
    # blocks. It is also the widest-blast-radius member: two pages LINK it
    # with no local fallback, and render-plugin-pages.py concatenates it
    # into fifteen more.
    css = (
        ROOT / "themes" / "phosphor-blueprint" / "archetypes" / td.PRODUCT_TOKENS_CSS
    ).read_text(encoding="utf-8")
    assert td.check_required_tokens(css) == []


def test_live_product_tokens_css_declares_only_tokens():
    css = (
        ROOT / "themes" / "phosphor-blueprint" / "archetypes" / td.PRODUCT_TOKENS_CSS
    ).read_text(encoding="utf-8")
    assert td.check_token_css_declares_only_tokens(css) == []


def test_main_fails_a_theme_whose_product_tokens_css_drops_the_required_tokens(
    monkeypatch, tmp_path, capsys
):
    # Same regression as the reading case below, one archetype over and with
    # a bigger blast radius. An author writes a genuinely NEW product
    # vocabulary instead of copying phosphor-blueprint's, defines none of
    # the base names, and the theme rotates in unattended on the 1st.
    #
    # This test FAILS against the pre-fix theme-doctor.py, whose
    # required-token loop ran over ("utility", "reading") only — verified
    # against that implementation, where it reported rc == 0 and printed
    # "PASS stub-theme".
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)
    (tdir / "archetypes" / td.PRODUCT_TOKENS_CSS).write_text(":root { }\n", encoding="utf-8")

    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)
    monkeypatch.setattr(td.subprocess, "run", _stub_main_kwargs(tmp_path))
    monkeypatch.setattr(
        td.tempfile, "TemporaryDirectory",
        lambda *a, **kw: __import__("contextlib").nullcontext(str(tmp_path)),
    )

    rc = td.main(["stub-theme"])
    assert rc == 1
    out = capsys.readouterr().out
    assert f"archetypes/{td.PRODUCT_TOKENS_CSS}" in out
    assert "--fg-1" in out


def test_main_fails_a_theme_missing_product_tokens_css_entirely(
    monkeypatch, tmp_path, capsys
):
    # Resolved through an unguarded <link> on two live pages and read with
    # no existence guard by render-plugin-pages.py, so "absent" is a 404 on
    # the commercial page plus a FileNotFoundError across 15 others,
    # unattended on the 1st. Absent has to fail before the queue, not there.
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)
    (tdir / "archetypes" / td.PRODUCT_TOKENS_CSS).unlink()

    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)
    rc = td.main(["stub-theme"])
    assert rc == 1
    assert f"missing archetypes/{td.PRODUCT_TOKENS_CSS}" in capsys.readouterr().out


def test_main_fails_a_theme_whose_token_css_grows_an_element_rule(
    monkeypatch, tmp_path, capsys
):
    """The finding this whole split exists for, kept closed as a gate.

    conundrum.html and rororo-plugins.html link a theme file for its
    PALETTE. When they linked the DRESS instead, `a:hover { text-decoration:
    underline; text-decoration-color: var(--magenta) }` at specificity
    (0,1,1) beat `.merch-card`/`.shop-cta`/`.repo-cta`/`footer a` and put a
    magenta hover underline on 11 links across the two pages. Measured in
    Chromium; invisible to the pixel gate and the computed-style gate alike,
    because both sample the RESTING state.

    Splitting the files fixed that instance. This keeps it fixed: a future
    theme's product-tokens.css that grows `p { margin: 0 0 24px }` lands on
    both pages unattended, and check_required_tokens — which only counts
    NAMES — waves it straight through.
    """
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)
    (tdir / "archetypes" / td.PRODUCT_TOKENS_CSS).write_text(
        _required_tokens_css() + "a:hover { text-decoration: underline; }\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)
    monkeypatch.setattr(td.subprocess, "run", _stub_main_kwargs(tmp_path))
    monkeypatch.setattr(
        td.tempfile, "TemporaryDirectory",
        lambda *a, **kw: __import__("contextlib").nullcontext(str(tmp_path)),
    )

    rc = td.main(["stub-theme"])
    assert rc == 1
    out = capsys.readouterr().out
    assert f"archetypes/{td.PRODUCT_TOKENS_CSS}" in out
    assert "a:hover" in out


def test_token_only_check_does_not_trip_on_an_at_sign_inside_a_token_value():
    # The scan used to run over the whole file, so a legitimate
    # `--x: url("mailto:a@b")` was reported as "found at-rule '@b'" — a
    # false positive that blocks a valid theme, which is worse than the
    # hole it guards. At-rules are only meaningful outside a {…} block.
    css = ':root { --contact: url("mailto:este@626labs.dev"); --at: "a@b"; }\n'
    assert td.check_token_css_declares_only_tokens(css) == []


def test_token_only_check_accepts_tokens_and_rejects_everything_else():
    ok = ":root { --a: 1; --b: var(--a); }\n/* a comment { with braces } */\n"
    assert td.check_token_css_declares_only_tokens(ok) == []

    cases = [
        ("body { color: red; }", "body"),
        (":root { --a: 1; } .card { padding: 4px; }", ".card"),
        (":root { color: red; }", "color"),
        ("@media (max-width: 600px) { :root { --a: 2; } }", "@media"),
        ("@import url(x.css);\n:root { --a: 1; }", "@import"),
    ]
    for bad, needle in cases:
        errs = td.check_token_css_declares_only_tokens(bad)
        assert errs, f"{bad!r} should have been rejected"
        assert any(needle in e for e in errs), (needle, errs)


def _render_hub_previewable_pages():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "render_hub_for_doctor_test", ROOT / "scripts" / "render-hub.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return set(mod.PREVIEWABLE_THEME_CSS_PAGES)


def test_browser_checks_open_the_two_hand_authored_product_pages():
    # Not a shell the theme ships — pages the SITE ships. Before this,
    # nothing in the unattended gate stack ever rendered a real
    # hand-authored page, so the commercial Etsy surface was one the
    # rotation could never see.
    assert td.BROWSER_CHECK_LIVE_PAGES == ("conundrum.html", "rororo-plugins.html")
    previewable = _render_hub_previewable_pages()
    for name in td.BROWSER_CHECK_LIVE_PAGES:
        assert (ROOT / name).exists()
        # Each must be one render-hub.py's preview mode actually emits, or
        # main() bails with "did not emit" instead of checking it.
        assert (ROOT / name) in previewable, name


def test_main_fails_a_theme_whose_reading_tokens_css_drops_the_required_tokens(
    monkeypatch, tmp_path, capsys
):
    # The regression this gate exists for, driven through main() rather than
    # the checker: an author writes a genuinely NEW reading dress instead of
    # copying phosphor-blueprint's, defines none of the base vocabulary, and
    # the theme rotates in unattended on the 1st. Before this gate the stub
    # below PASSED — vocabulary only grades class names, and nothing else
    # looks at custom properties — putting thesis.html and workflow.html
    # live with dozens of unresolved var()s.
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)
    (tdir / "archetypes" / td.READING_TOKENS_CSS).write_text(":root { }\n", encoding="utf-8")

    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)
    monkeypatch.setattr(td.subprocess, "run", _stub_main_kwargs(tmp_path))
    monkeypatch.setattr(
        td.tempfile, "TemporaryDirectory",
        lambda *a, **kw: __import__("contextlib").nullcontext(str(tmp_path)),
    )

    rc = td.main(["stub-theme"])
    assert rc == 1
    out = capsys.readouterr().out
    assert f"archetypes/{td.READING_TOKENS_CSS}" in out
    assert "--fg-1" in out


def _stub_main_kwargs(tmp_path):
    """The subprocess.run/TemporaryDirectory monkeypatch shape every
    required-tokens main()-level test below shares: fake a successful
    render-hub.py --theme run producing what preview mode really produces —
    index.html PLUS a copy of every BROWSER_CHECK_LIVE_PAGES member. main()
    treats a missing preview copy as a hard failure (it means preview mode
    stopped emitting a page the browser gate is supposed to open), so a stub
    that writes only index.html would make every test below fail on that
    instead of on what it is actually testing."""
    class _Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def _fake_run(*a, **kw):
        (tmp_path / "index.html").write_text(_good_html(), encoding="utf-8")
        for name in td.BROWSER_CHECK_LIVE_PAGES:
            (tmp_path / name).write_text(_good_html(), encoding="utf-8")
        return _Result()

    return _fake_run


def test_main_theme_missing_a_required_token_in_tokens_css_fails_the_gate(monkeypatch, tmp_path, capsys):
    # The literal case the review named: a theme whose tokens.css doesn't
    # define every required token must fail — before it's ever queued.
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)
    css = (tdir / "tokens.css").read_text(encoding="utf-8")
    (tdir / "tokens.css").write_text(css.replace("--cyan: 0;\n", ""), encoding="utf-8")

    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)
    monkeypatch.setattr(td.subprocess, "run", _stub_main_kwargs(tmp_path))
    monkeypatch.setattr(
        td.tempfile, "TemporaryDirectory",
        lambda *a, **kw: __import__("contextlib").nullcontext(str(tmp_path)),
    )

    rc = td.main(["stub-theme"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "tokens.css" in out
    assert "--cyan" in out


def test_main_theme_missing_a_required_token_in_utility_css_fails_the_gate(monkeypatch, tmp_path, capsys):
    # Same contract, the other real consumer: press.html/privacy.html read
    # archetypes/utility.css with no fallback of their own at all.
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)
    css = (tdir / "archetypes" / "utility.css").read_text(encoding="utf-8")
    (tdir / "archetypes" / "utility.css").write_text(css.replace("--font-mono: 0;\n", ""), encoding="utf-8")

    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)
    monkeypatch.setattr(td.subprocess, "run", _stub_main_kwargs(tmp_path))
    monkeypatch.setattr(
        td.tempfile, "TemporaryDirectory",
        lambda *a, **kw: __import__("contextlib").nullcontext(str(tmp_path)),
    )

    rc = td.main(["stub-theme"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "archetypes/utility.css" in out
    assert "--font-mono" in out


# ─── final review Fix 2: queue-time gating ──────────────────────────────────
# theme-doctor's only CI invocation used to live inside rotate-theme.yml — a
# broken theme could merge into the queue green and only get caught on
# rotation morning (09:00 UTC on the 1st), when rotation aborts. Fail-safe,
# but late: the whole point of a queue is that its contents are known-good
# ahead of their own turn. Running theme-doctor's STATIC checks (no
# --browser — offline, no local server or chromium needed) against every
# theme actually in the registry, active AND queued, here in the test suite
# means a broken theme fails the PR that queues it. Parametrized over a
# fresh read of content/themes.json at collection time, so a theme added to
# the queue is automatically under test with zero code change here.


def _registered_theme_slugs() -> list[str]:
    reg = td.theme_registry.load()
    return [reg["active"], *reg.get("queue", [])]


@pytest.mark.parametrize("slug", _registered_theme_slugs())
def test_registered_theme_passes_static_theme_doctor_checks(slug, capsys):
    rc = td.main([slug])
    assert rc == 0, capsys.readouterr().out
