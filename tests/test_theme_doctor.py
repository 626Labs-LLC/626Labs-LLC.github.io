import importlib.util, re, sys
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


def _active_slug():
    """Whatever content/themes.json says is live right now."""
    return td.theme_registry.active_slug(td.theme_registry.load())


class _StubConsoleMessage:
    """A console message as _check_viewport reads one: `.type`, `.text`, and
    a `.location` dict the off-origin filter attributes it by."""

    def __init__(self, text, url, type_="error"):
        self.text = text
        self.type = type_
        self.location = {"url": url, "lineNumber": 0, "columnNumber": 0}


class _StubRoute:
    """A playwright Route as _check_viewport drives one. Records the verdict
    so a test can assert which requests were let through."""

    def __init__(self, url):
        self.request = type("R", (), {"url": url})()
        self.verdict = None

    def abort(self):
        self.verdict = "abort"

    def continue_(self):
        self.verdict = "continue"

    def fulfill(self, status, content_type, body):
        self.verdict = "fulfill"
        self.body = body


class _StubPage:
    """Minimal page-like stub for _check_viewport — no real browser needed.

    goto_side_effect: exception instance to raise (navigation failure), or a
    response-like value to return (e.g. a fake with .status).
    console: messages to hand the "console" handler after goto.
    """

    def __init__(self, goto_side_effect, console=(), pageerrors=(), metrics=None):
        self.metrics = metrics or {}
        self._goto_side_effect = goto_side_effect
        self._console = list(console)
        self._pageerrors = list(pageerrors)
        self._handlers = {}
        self.route_handler = None

    def on(self, event, handler):
        self._handlers[event] = handler

    def route(self, pattern, handler):
        self.route_handler = handler

    def goto(self, url, wait_until="load", timeout=15000):
        if isinstance(self._goto_side_effect, Exception):
            raise self._goto_side_effect
        for msg in self._console:
            self._handlers["console"](msg)
        for exc in self._pageerrors:
            self._handlers["pageerror"](exc)
        return self._goto_side_effect

    def wait_for_timeout(self, ms):
        pass

    def evaluate(self, expr):
        # Per-expression answers, so the horizontal-scroll comparison can
        # actually be driven. It returned a flat 0 for everything, which made
        # `scrollWidth > clientWidth + 1` the expression `0 > 1` in every test
        # this stub has ever backed — the check could be deleted outright and
        # the suite stayed green.
        return self.metrics.get(expr, 0)


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
    # A complete stub theme must get PAST the completeness gate — the
    # required-files check must not over-fire on a theme that has every CSS
    # artifact.
    #
    # The earlier cut of this asserted on main()'s STDOUT with subprocess.run
    # unstubbed, so main() died at the render step long before the archetype
    # loop and the three "not in out" assertions were vacuously true. It
    # passed identically with the completeness gate deleted. It now calls the
    # checker directly, which is the thing under test, and asserts the empty
    # result rather than the absence of a string.
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)
    missing = [f for f in td.REQUIRED_ARCHETYPE_CSS.values()
               if not (tdir / "archetypes" / f).exists()]
    assert missing == []
    for label in td.REQUIRED_TOKEN_CSS:
        text = (tdir / label).read_text(encoding="utf-8")
        assert td.check_required_tokens(text) == [], label


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


# ─── the archetype token append (_archetype_token_css) ────────────────────
#
# This is the only thing keeping the READING contrast check alive, and it
# shipped without coverage. archetypes/reading.css declares none of
# --fg-1/--fg-2/--fg-3/--pb-field/--pb-panel any more — they moved to
# reading-tokens.css when the archetype split — and those five names are
# exactly what theme.json's three contrastPairs are written against.
#
# The failure is silent by construction. If _archetype_token_css returns ""
# for reading (a refactor, a mistyped ARCHETYPE_TOKEN_CSS key, a theme
# naming its file something else), _applicable_contrast_pairs filters every
# pair out as "not declared here", check_contrast is handed an empty list,
# the doctor PRINTS "no declared pair's custom properties resolve —
# unverified for reading" and adds ZERO errors. The theme passes with its
# reading contrast ungraded: the rubber-stamp this module's own docstring
# calls worse than no check at all.


def test_archetype_token_css_returns_the_right_file_or_nothing():
    tdir = ROOT / "themes" / "phosphor-blueprint"
    for archetype, filename in td.ARCHETYPE_TOKEN_CSS.items():
        got = td._archetype_token_css(archetype, tdir)
        assert got, f"{archetype} resolved to an empty token stylesheet"
        assert got == (tdir / "archetypes" / filename).read_text(encoding="utf-8")
    # The archetypes with no token file of their own get "" — home is
    # dressed by its shell's inline <style> against tokens.css, and
    # utility.css is not split.
    for archetype in set(td.archetypes.ARCHETYPES) - set(td.ARCHETYPE_TOKEN_CSS):
        assert td._archetype_token_css(archetype, tdir) == ""


def test_archetype_token_css_keys_name_files_that_exist():
    # Three archetypes, not two. `utility` maps to utility.css — the same
    # file _archetype_source already passes as utility's dress — so it is
    # appended twice and therefore WINS over tokens.css. That is the point:
    # press.html and privacy.html link archetypes/utility.css and nothing
    # else, so grading them against tokens.css's ramp graded a page nobody
    # serves. Same bug this dict was created to fix for product and reading.
    tdir = ROOT / "themes" / _active_slug()
    assert set(td.ARCHETYPE_TOKEN_CSS) == {"product", "reading", "utility"}
    for archetype, filename in td.ARCHETYPE_TOKEN_CSS.items():
        assert archetype in td.archetypes.ARCHETYPES
        assert (tdir / "archetypes" / filename).exists(), filename
        # TOKEN_ONLY_CSS covers only the archetypes that were SPLIT into a
        # dress and a token file. utility.css is press.html's own dress
        # coming home and is deliberately not token-only.
        if archetype in ("product", "reading"):
            assert f"archetypes/{filename}" in td.TOKEN_ONLY_CSS
        else:
            assert f"archetypes/{filename}" not in td.TOKEN_ONLY_CSS


def test_reading_contrast_is_actually_GRADED_not_merely_unverified():
    """The regression this whole block exists for, asserted on ratios.

    Not "the doctor passes" — the doctor passes either way, which is the
    problem. This asserts that reading's declared pairs RESOLVE and produce
    real, non-zero contrast ratios, driven through _archetype_source so it
    exercises the actual wiring rather than re-implementing it.
    """
    import json

    # The ACTIVE theme, never a hardcoded slug. rotate-theme.yml runs pytest
    # AFTER it flips content/themes.json, so a slug pinned here re-verifies
    # the theme that just RETIRED while the one going live is never graded —
    # and the doctor passes either way, which is the whole reason this test
    # exists. Same discipline test_render_hub.py's token tests already use.
    tdir = ROOT / "themes" / _active_slug()
    pairs = json.loads((tdir / "theme.json").read_text(encoding="utf-8"))["contrastPairs"]
    assert pairs, "the live theme declares no contrastPairs"

    tokens_css = (tdir / "tokens.css").read_text(encoding="utf-8")
    for archetype in ("reading", "product"):
        _html, css, _zones = td._archetype_source(archetype, tdir, _good_html(), tokens_css)
        applicable = td._applicable_contrast_pairs(css, pairs)
        # GRADED, not "every declared pair applies to every archetype". An
        # earlier version asserted equality, which false-fails a theme
        # declaring one pair meaningful only to `reading` — a normal thing to
        # do, and pytest is a rotation gate. What must hold is that this
        # archetype was graded at all; main() already fails a theme where
        # NOTHING applies, and test_reading_contrast_is_actually_GRADED_not_
        # merely_unverified covers that path.
        assert applicable, (
            f"{archetype}: none of the {len(pairs)} declared pairs name custom "
            f"properties this archetype own CSS declares, so it was never graded"
        )
        for fg, bg, ratio in td.evaluate_contrast_pairs(css, applicable):
            assert ratio is not None, f"{archetype}: {fg} on {bg} did not resolve"
            assert ratio > 0, f"{archetype}: {fg} on {bg} graded {ratio}"
            assert ratio >= td.AA_MIN_RATIO, f"{archetype}: {fg} on {bg} = {ratio}"


def test_reading_contrast_goes_unverified_without_the_token_append():
    """Proof that the test above is load-bearing rather than decorative:
    with the append removed, every reading pair drops out and the doctor
    reports 'unverified' while still passing."""
    tdir = ROOT / "themes" / "phosphor-blueprint"
    import json

    pairs = json.loads((tdir / "theme.json").read_text(encoding="utf-8"))["contrastPairs"]
    reading_css_alone = (tdir / "archetypes" / "reading.css").read_text(encoding="utf-8")

    assert td._applicable_contrast_pairs(reading_css_alone, pairs) == []
    failures, advisories = td.check_contrast(
        reading_css_alone, td._applicable_contrast_pairs(reading_css_alone, pairs)
    )
    assert failures == []          # <- passes
    assert advisories                # <- while saying nothing was checked


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


def test_browser_checks_open_every_hand_authored_product_page():
    # Not a shell the theme ships — pages the SITE ships. Before this,
    # nothing in the unattended gate stack ever rendered a real
    # hand-authored page, so the commercial Etsy surface was one the
    # rotation could never see.
    #
    # All four, not two. The live-data pair was briefly held out because
    # mod-launcher-games.html fetches off-origin — but every page here
    # already loads //gc.zgo.at/count.js, so that dependency existed either
    # way and is now closed in _check_viewport instead of routed around.
    # All EIGHT hand-authored pages that link a theme stylesheet. The reading
    # pair joined for the same reason as the product four; the
    # first time this gate opened thesis.html it found a live horizontal
    # scroll at 390px, which is the argument for the tuple in one line.
    #
    # press.html and privacy.html joined last and on a stronger argument than
    # any of the six: they own NO chrome of their own, so the theme is the
    # only thing dressing them. See DRESS_OUTCOME_PAGES.
    assert td.BROWSER_CHECK_LIVE_PAGES == (
        "conundrum.html", "rororo-plugins.html", "rororo.html",
        "mod-launcher-games.html", "thesis.html", "workflow.html",
        "press.html", "privacy.html",
    )
    previewable = _render_hub_previewable_pages()
    for name in td.BROWSER_CHECK_LIVE_PAGES:
        assert (ROOT / name).exists()
        # Each must be one render-hub.py's preview mode actually emits, or
        # main() bails with "did not emit" instead of checking it.
        assert (ROOT / name) in previewable, name


# ─── third-party isolation in the browser gate ───────────────────────────
#
# The gate opens pages that all carry `<script async src="//gc.zgo.at/
# count.js">`. Unisolated, that made an unattended rotation on the 1st
# depend on a third-party host: a failed load logs a console error blamed on
# the theme, and an async script still delays the `load` event page.goto
# waits for, so a slow host eats the timeout. Both are closed by origin
# filtering, and these pin it.


def test_off_origin_classification():
    origin = "http://127.0.0.1:8000"
    assert not td._is_off_origin("http://127.0.0.1:8000/", origin)
    assert not td._is_off_origin("http://127.0.0.1:8000/assets/x.png", origin)
    assert not td._is_off_origin("http://127.0.0.1:8000", origin)
    assert td._is_off_origin("https://gc.zgo.at/count.js", origin)
    assert td._is_off_origin(
        "https://raw.githubusercontent.com/x/y/main/supported-games.json", origin)
    # A prefix that is not a path boundary is a DIFFERENT origin. Naive
    # startswith() would wave this through.
    assert td._is_off_origin("http://127.0.0.1:80001/evil.js", origin)
    # The page's own content under another scheme is never third-party.
    for u in ("data:image/png;base64,AAAA", "blob:http://x/y", "about:blank"):
        assert not td._is_off_origin(u, origin)
    # An error the browser attributed to nothing is REPORTED, never filtered.
    assert not td._is_off_origin("", origin)


def test_off_origin_requests_are_aborted_before_they_leave():
    page = _StubPage(None)
    td._check_viewport(page, "http://127.0.0.1:8000/", 1440)
    assert page.route_handler is not None, "no route installed — nothing is blocked"

    own = _StubRoute("http://127.0.0.1:8000/data/rororo-plugins.json")
    page.route_handler(own)
    assert own.verdict == "continue"

    analytics = _StubRoute("https://gc.zgo.at/count.js")
    page.route_handler(analytics)
    assert analytics.verdict == "abort"

    # The game feed is the one off-origin URL answered from a committed
    # fixture rather than aborted — otherwise the gate only ever sees
    # mod-launcher-games.html's fetch-failed fallback. Still no network:
    # the body comes off disk.
    feed = _StubRoute(
        "https://raw.githubusercontent.com/e/626-game-manifest/main/supported-games.json")
    page.route_handler(feed)
    assert feed.verdict == "fulfill"
    assert '"schemaVersion": 1' in feed.body

    # ...and nothing else off-origin gets that treatment.
    other = _StubRoute("https://raw.githubusercontent.com/e/other-repo/main/x.json")
    page.route_handler(other)
    assert other.verdict == "abort"


def test_console_errors_are_the_pages_own_not_a_third_party_hosts():
    page = _StubPage(
        None,
        console=[
            # what an unreachable/aborted gc.zgo.at produces
            _StubConsoleMessage(
                "Failed to load resource: net::ERR_NAME_NOT_RESOLVED",
                "https://gc.zgo.at/count.js"),
            _StubConsoleMessage(
                "Failed to load resource: net::ERR_FAILED",
                "https://raw.githubusercontent.com/x/y.json"),
            # the theme's own fault — must survive the filter
            _StubConsoleMessage(
                "Uncaught TypeError: x is not a function",
                "http://127.0.0.1:8000/"),
            # unattributed — reported, because a gate must never cover less
            # than it claims
            _StubConsoleMessage("something went wrong", ""),
            # not an error at all
            _StubConsoleMessage("a warning", "http://127.0.0.1:8000/", type_="warning"),
        ],
    )
    errs = td._check_viewport(page, "http://127.0.0.1:8000/", 1440)
    reported = [e for e in errs if "console error" in e]
    assert len(reported) == 2, reported
    assert any("Uncaught TypeError" in e for e in reported)
    assert any("something went wrong" in e for e in reported)
    assert not any("gc.zgo.at" in e or "ERR_" in e for e in reported)


def test_an_uncaught_page_exception_is_a_gate_failure():
    # Measured, not assumed: Chromium delivers an uncaught exception on
    # `pageerror` and NOTHING on `console`. A page whose inline script calls
    # an undefined function produced zero console messages and one pageerror
    # — so before this handler existed, _check_viewport's own docstring and
    # BROWSER_CHECK_LIVE_PAGES' comment both claimed this gate catches a page
    # "throwing" while it demonstrably did not.
    #
    # No origin filter on this channel, and that is load-bearing rather than
    # sloppy: off-origin requests are aborted, so no third-party script runs,
    # so any exception here is the page's own by construction.
    page = _StubPage(None, pageerrors=[ReferenceError_stub("x is not defined")])
    errs = td._check_viewport(page, "http://127.0.0.1:8000/", 390)
    assert any("uncaught page error at 390px" in e and "x is not defined" in e
               for e in errs), errs


class ReferenceError_stub(Exception):  # noqa: N801 — reads as the thing it stands for
    """What playwright hands a `pageerror` handler: an exception whose str()
    is the browser-side message."""


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


def test_horizontal_scroll_is_a_gate_failure():
    # The check `--require-browser` most exists to guarantee runs, and it had
    # ZERO coverage: the stub page answered every `evaluate` with 0, so
    # `scrollWidth > clientWidth + 1` was `0 > 1` in every test, and deleting
    # the check outright left the suite green.
    page = _StubPage(None, metrics={
        "document.documentElement.scrollWidth": 1700,
        "document.documentElement.clientWidth": 1440,
    })
    errs = td._check_viewport(page, "http://127.0.0.1:8000/", 1440)
    assert any("horizontal scroll at 1440px" in e for e in errs), errs
    assert any("1700" in e and "1440" in e for e in errs), errs


def test_one_pixel_of_slack_is_allowed_before_horizontal_scroll_is_reported():
    # `+ 1` in the comparison — a sub-pixel rounding difference is not a
    # sideways-scrolling page, and reporting one would make the gate cry wolf
    # on the 1st.
    page = _StubPage(None, metrics={
        "document.documentElement.scrollWidth": 1441,
        "document.documentElement.clientWidth": 1440,
    })
    assert not any("horizontal scroll" in e
                   for e in td._check_viewport(page, "http://127.0.0.1:8000/", 1440))


def test_the_browser_gate_opens_every_previewable_theme_css_page():
    # BOTH directions. The forward one (every gate page is previewable) was
    # already pinned; this is the reverse, and it is the one that matters for
    # drift: PREVIEWABLE_THEME_CSS_PAGES is DERIVED from THEME_CSS_HREFS while
    # BROWSER_CHECK_LIVE_PAGES is a hand-written literal. Add a tenth page to
    # the href map and it gets a resolution group automatically, render-hub
    # previews it, and the browser gate never opens it. Green, and silent.
    previewable = {p.name for p in _render_hub_previewable_pages()}
    listed = set(td.BROWSER_CHECK_LIVE_PAGES)
    assert previewable == listed, (
        f"previewable but never opened by the browser gate: "
        f"{sorted(previewable - listed)}; "
        f"opened but not previewable: {sorted(listed - previewable)}"
    )


def test_a_theme_may_not_hardcode_another_themes_slug(tmp_path):
    # Copy-and-retokenize is the DOCUMENTED way to build a theme, and it
    # leaves `/themes/<original-slug>/` behind in every hardcoded link.
    # render-hub copies theme shells verbatim, `_THEME_HREF_RE` strips the
    # slug before grading, and retired theme dirs are never deleted — so the
    # gate graded the new theme while the rendered page wore the old one.
    tdir = tmp_path / "aurora"
    (tdir / "archetypes").mkdir(parents=True)
    (tdir / "archetypes" / "home.html").write_text(
        '<link rel="stylesheet" href="/themes/phosphor-blueprint/tokens.css">',
        encoding="utf-8")
    errs = td.check_theme_references_only_itself(tdir)
    assert errs and "phosphor-blueprint" in errs[0], errs
    assert "archetypes/home.html" in errs[0], errs

    (tdir / "archetypes" / "home.html").write_text(
        '<link rel="stylesheet" href="/themes/aurora/tokens.css">', encoding="utf-8")
    assert td.check_theme_references_only_itself(tdir) == []


def test_the_live_theme_references_only_itself():
    tdir = td.theme_registry.theme_dir(_active_slug())
    assert td.check_theme_references_only_itself(tdir) == []


# ─── the borrowed dress, gated on a REGION DIFFERENTIAL ───────────────────
#
# press.html and privacy.html take their entire chrome from the active theme's
# archetypes/utility.css and restate none of it. Measured against the live DOM,
# 49 of that file's 50 selectors reach press.html and 48 reach privacy.html,
# and the overlap between each page's own <style> selectors and that file's is
# EXACTLY ZERO. So a second theme's utility.css that drops a load-bearing rule
# changes or breaks both pages while every other gate stays green.
#
# The core of the gate is a differential: each page is measured with its theme
# stylesheet linked and again with it disabled, and each of the page's own
# named regions has to render DIFFERENTLY. It parses no values — fingerprints
# are compared as opaque strings — which is what makes it immune both to color
# syntax it has never seen and to a theme choosing a technique it did not
# anticipate. The three element-level assertions that remain are the ones the
# differential structurally cannot see.


class _StubDressPage:
    """A page-like stub for check_page_renders_dressed: its `evaluate` hands
    back a canned measurement dict instead of driving a real browser."""

    def __init__(self, measurement):
        self._measurement = measurement
        self.calls = 0

    def evaluate(self, script, *args):
        self.calls += 1
        return self._measurement


def _regions(**overrides):
    """Every region reporting a real difference, unless a test says otherwise."""
    out = []
    for label, _sel, _scope, _props, _geom in td._DRESS_REGIONS:
        if label in overrides and overrides[label] is None:
            out.append({"label": label, "present": False, "differing": 0, "total": 0})
        else:
            out.append({"label": label, "present": True,
                        "differing": overrides.get(label, 12), "total": 12})
    return out


def _link(color="rgb(23, 212, 250)", parent_color="rgb(232, 242, 255)", **overrides):
    """One a.inline-link measurement in the shape the probe returns: the
    link's own signals and its PARENT's, so "distinguishable from the prose it
    sits in" is a comparison the judging code can actually make.

    Defaults are what phosphor-blueprint computes on press.html — a cyan link
    with a border-bottom inside --fg-1 prose. `overrides` patch the LINK's
    signals only.
    """
    base = {
        "color": None, "textDecorationLine": "none", "textDecorationColor": color,
        "textDecorationStyle": "solid", "borderBottomWidth": "0px",
        "borderBottomStyle": "none", "borderBottomColor": color,
        "backgroundColor": "rgba(0, 0, 0, 0)", "backgroundImage": "none",
        "fontWeight": "400", "fontStyle": "normal", "boxShadow": "none",
    }
    self_ = {**base, "color": color, "borderBottomWidth": "1px",
             "borderBottomStyle": "solid"}
    self_.update(overrides)
    parent = {**base, "color": parent_color, "textDecorationColor": parent_color,
              "borderBottomColor": parent_color}
    return {"self": self_, "parent": parent}


def _indistinct_link(color="rgb(168, 194, 217)"):
    """A link identical to its parent on every signal — the actual defect."""
    signals = {
        "color": color, "textDecorationLine": "none", "textDecorationColor": color,
        "textDecorationStyle": "solid", "borderBottomWidth": "0px",
        "borderBottomStyle": "none", "borderBottomColor": color,
        "backgroundColor": "rgba(0, 0, 0, 0)", "backgroundImage": "none",
        "fontWeight": "400", "fontStyle": "normal", "boxShadow": "none",
    }
    return {"self": dict(signals), "parent": dict(signals)}


def _dressed(**overrides):
    """A measurement dict shaped exactly like the live probe's return value,
    carrying values phosphor-blueprint actually computes on press.html at
    1440px (read off the browser, not invented). Tests break one field at a
    time so each assertion is exercised on its own."""
    m = {
        "regions": _regions(),
        "linkedStylesheets": 1,
        "toggledStylesheets": 1,
        "toggleTookEffect": True,
        "styleRules": 47,
        "ua": {
            "fontFamily": '"Times New Roman"',
            "headingRatio": 2.0,
            "linkColor": "rgb(0, 0, 238)",
        },
        "body": {
            "color": "rgb(232, 242, 255)",
            "fontFamily": 'Inter, system-ui, -apple-system, "Segoe UI", sans-serif',
            "fontSize": "16px",
        },
        "title": {"color": "rgb(232, 242, 255)", "fontFamily": '"Space Grotesk"',
                  "fontSize": "56px"},
        "links": [_link() for _ in range(8)],
    }
    m.update(overrides)
    return m


def _dress_errors(measurement):
    return td.check_page_renders_dressed(_StubDressPage(measurement), 1440)


def test_a_fully_dressed_page_reports_nothing():
    assert _dress_errors(_dressed()) == []


# ─── the region differential ──────────────────────────────────────────────


def test_every_region_must_render_differently_undressed():
    # One region at a time, so a single region silently dropping out of
    # _DRESS_REGIONS cannot hide behind its four neighbours.
    for label, _sel, _scope, _props, _geom in td._DRESS_REGIONS:
        errs = _dress_errors(_dressed(regions=_regions(**{label: 0})))
        assert any(f"region {label} renders identically" in e for e in errs), (label, errs)


def test_a_region_missing_from_the_page_is_a_failure_not_a_skip():
    for label, _sel, _scope, _props, _geom in td._DRESS_REGIONS:
        errs = _dress_errors(_dressed(regions=_regions(**{label: None})))
        assert any(f"region {label} is not present" in e for e in errs), (label, errs)


def test_a_page_with_no_linked_stylesheet_is_a_failure_not_a_skip():
    # Nothing to take off means the differential compares the page to itself
    # and every region reports "differs: 0" — five findings pointing at the
    # theme for something that is the page's problem. Named, and short-circuited.
    errs = _dress_errors(_dressed(linkedStylesheets=0, toggledStylesheets=0))
    assert errs and all("no linked stylesheet" in e for e in errs), errs


def test_a_browser_that_refuses_to_disable_the_sheet_is_a_failure_not_a_skip():
    errs = _dress_errors(_dressed(toggleTookEffect=False))
    assert errs and all("refused to disable" in e for e in errs), errs


def test_an_empty_stylesheet_is_named_as_such_rather_than_blamed_on_the_regions():
    # A 404 or a parse failure would otherwise be reported as five regions the
    # theme forgot to dress, which sends the next person to the wrong file.
    errs = _dress_errors(_dressed(styleRules=0))
    assert errs and all("loaded no rules at all" in e for e in errs), errs


def test_the_field_region_is_graded_on_backgrounds_and_carries_no_geometry():
    # Both halves were measured, not reasoned about. A theme carrying tokens
    # plus `* { box-sizing }` and `html, body { margin: 0 }` and NOTHING else:
    #   field on the full prop set -> 1 of 2 differ  (false pass, all 5 green)
    #   field on _FIELD_PROPS      -> 0 of 2 differ  (caught)
    # and with x/y in the fingerprint the footer of a theme with no rule at all
    # counted as dressed purely because content above it had resized.
    label, _sel, scope, props, geometry = td._DRESS_REGIONS[0]
    assert label == "the page field" and scope == "self"
    assert geometry is False, "html/body resize with their content; a rect here measures length"
    for banned in ("margin-top", "margin-left", "padding-top", "padding-left",
                   "display", "max-width", "font-size"):
        assert banned not in props, banned
    assert "background-color" in props and "background-image" in props and "content" in props
    # Every other region does carry its own box.
    assert all(r[4] is True for r in td._DRESS_REGIONS[1:])


def test_no_region_fingerprints_where_an_element_LANDS():
    # Position is a consequence of whatever sits above an element. With x/y in
    # the fingerprint, a footer whose every property was byte-identical still
    # counted as "renders differently" — measured against a theme carrying no
    # rule that paints at all.
    assert "Math.round(b.width), Math.round(b.height)" in td._DRESS_PROBE_JS
    # Not `"b.x" not in ...`: reintroducing the defect under any other
    # variable name — `const r = el.getBoundingClientRect(); row.push(r.x, r.y)`
    # — sails past a check that spells out one identifier. What must be true
    # is that NOTHING pushed into the fingerprint reads a position component
    # off a rect, whatever the rect is called.
    rect_vars = set(re.findall(r"const\s+(\w+)\s*=\s*\w+\.getBoundingClientRect\(\)",
                               td._DRESS_PROBE_JS))
    assert rect_vars, "no getBoundingClientRect call found; this test is measuring nothing"
    for var in rect_vars:
        for component in ("x", "y", "left", "top", "right", "bottom"):
            assert not re.search(rf"\b{re.escape(var)}\.{component}\b", td._DRESS_PROBE_JS), (
                f"the fingerprint reads {var}.{component} — position is a consequence of "
                f"what sits above an element, not part of its own dress")


def test_every_region_selector_is_the_PAGES_own_markup():
    # The design's one hard rule: a region may name a selector the PAGE ships,
    # never one the THEME must carry. Checked against both shipped files.
    needles = {
        "html, body, body > div": "<body",
        "nav.nav": '<nav class="nav"',
        "header.page-hero": '<header class="page-hero"',
        "main": "<main",
        "footer": "<footer",
    }
    assert {r[1] for r in td._DRESS_REGIONS} == set(needles)
    for name in td.DRESS_OUTCOME_PAGES:
        html = (ROOT / name).read_text(encoding="utf-8")
        for selector, needle in needles.items():
            assert needle in html, (name, selector)


def test_the_field_region_reaches_the_pages_own_full_bleed_overlay():
    # A theme cannot add elements to these two pages, so the surfaces it can
    # put a field on are exactly: html, body, their pseudos, and the one <div>
    # each page ships as a direct child of body. Reaching only html/body FAILED
    # a theme that moved the entire field onto that div at z-index:-1 with html
    # and body painting nothing — a correct dark page, exit 1 on both pages.
    #
    # Measured across every scratch theme, field-region differing counts:
    #   selector                 live  (a)tokens (b)resets (c)::before (d)overlay
    #   html, body               1/2   0/2 OK    0/2 OK    1/2 OK      0/2 FALSE FAIL
    #   html, body, body > div   2/3   0/3 OK    0/3 OK    1/3 OK      1/3 OK
    #   html, body, body > *     4/9   0/9 OK    0/9 OK    1/9 OK      1/9 OK
    selector = td._DRESS_REGIONS[0][1]
    assert "body > div" in selector, (
        "the field region must reach body's full-bleed overlay div, or a theme "
        "putting its field there fails a gate it should pass")
    # ...and NOT `body > *`, which also measured usable but would let a
    # background on the nav alone satisfy "the page has a field" — nav, hero,
    # main and footer each already have a region of their own.
    assert "body > *" not in selector
    for name in td.DRESS_OUTCOME_PAGES:
        html = (ROOT / name).read_text(encoding="utf-8")
        assert '<div class="pb-scanlines"' in html, name


def test_every_element_level_reading_happens_BEFORE_the_stylesheet_toggle():
    # Enforced by structure, not by the comment that used to be the only thing
    # holding it. _DRESS_PROBE_JS is a string no test executes — the stub page
    # ignores its `script` argument — so moving the element reads below the
    # toggle passed the whole suite while the real --browser run failed the
    # LIVE theme with "8 of 8 a.inline-link elements resolve the browser's own
    # default link color". Fail-loud rather than false-pass, but it aborts a
    # correct rotation with a wrong diagnosis, which costs the same.
    #
    # It cannot simply be re-ordered back: Chromium does not invalidate cached
    # :link styles when CSSStyleSheet.disabled returns to false, so a read
    # after the toggle sees an undressed link no matter what.
    js = td._DRESS_PROBE_JS
    toggle = js.index("s.disabled = true")
    for reader in ("probe.contentDocument", "const body = rd(", "const title = rd(",
                   "const inlineLinks ="):
        assert js.index(reader) < toggle, (
            f"{reader!r} reads the page AFTER the stylesheet toggle; Chromium does "
            f"not fully restore the sheet, so it would grade an undressed page")


def test_run_browser_checks_all_turns_the_dress_check_on_for_exactly_those_pages(monkeypatch):
    # THE WIRE. Everything else in this gate is worthless if this expression
    # can be cut without a test noticing: replacing
    # `dress_outcome=archetype in DRESS_OUTCOME_PAGES` with `dress_outcome=False`
    # makes the entire dress gate silently no-op for both pages, and the
    # consumer-side test below (which drives _check_viewport directly) does not
    # see it. This drives _run_browser_checks_all itself.
    seen = {}

    def fake(html_text, require=False, dress_outcome=False):
        seen[html_text] = dress_outcome
        return []

    monkeypatch.setattr(td, "_import_sync_playwright", lambda: object())
    monkeypatch.setattr(td, "_run_browser_checks", fake)
    docs = {name: name for name in ("home", "product", "reading", "utility",
                                    *td.BROWSER_CHECK_LIVE_PAGES)}
    assert td._run_browser_checks_all(docs) == []
    for name, on in seen.items():
        assert on is (name in td.DRESS_OUTCOME_PAGES), (name, on)
    # ...and it really did turn on for both, rather than for nothing at all.
    assert sorted(n for n, on in seen.items() if on) == sorted(td.DRESS_OUTCOME_PAGES)


# ─── the element-level assertions that survived ───────────────────────────


def test_dress_fails_when_body_falls_back_to_the_browsers_own_type():
    # A theme can dress all five regions and still forget font-family, which
    # leaves both pages in Times New Roman with every region still differing.
    errs = _dress_errors(_dressed(
        body={**_dressed()["body"], "fontFamily": '"Times New Roman"'}))
    assert any("browser's default type" in e for e in errs), errs


def test_any_deliberate_type_choice_passes_including_a_generic_keyword():
    # No family is required and no generic is banned. An earlier cut rejected a
    # bare `serif`/`sans-serif`, which is a theme's choice to make.
    for family in ("system-ui, sans-serif", "serif", "Georgia, serif",
                   "ui-monospace, monospace"):
        assert _dress_errors(_dressed(
            body={**_dressed()["body"], "fontFamily": family})) == [], family


def test_dress_fails_when_the_title_is_no_bigger_than_a_bare_heading():
    # An undressed <h1> computes 2.0x body text in this browser, so a title at
    # 32px on 16px body is exactly what NO dress looks like. Compared against
    # the measured UA ratio, never against 56px.
    errs = _dress_errors(_dressed(title={"fontSize": "32px"}))
    assert any("no larger, relative to body text" in e for e in errs), errs
    # 36px is this theme's clamp floor at 390px — 2.25x, the real headroom.
    assert _dress_errors(_dressed(title={"fontSize": "36px"})) == []


def test_dress_fails_when_a_link_matches_the_prose_it_sits_in():
    # THE privacy.html blindness, pinned. Its first inline link sits in
    # `main.policy p`, which the page colors --fg-2 while body is --fg-1. An
    # earlier cut compared to BODY's color and sampled only the first link, so
    # an undressed link inherited a color matching neither body's nor UA blue
    # and both halves passed — while every link on the page was identical to
    # the prose around it. This fixture is exactly that shape.
    prose = "rgb(168, 194, 217)"          # --fg-2, the paragraph own color
    body_color = "rgb(232, 242, 255)"     # --fg-1, body own
    assert prose != body_color
    errs = _dress_errors(_dressed(
        body={**_dressed()["body"], "color": body_color},
        links=[_indistinct_link(prose) for _ in range(10)]))
    assert any("identical to the prose they sit in" in e for e in errs), errs


def test_dress_fails_when_links_fall_back_to_the_browsers_link_color():
    # The other half, and it needs its own branch: drop the bare `a` rule too
    # and links go UA blue — different from their parent, so the first half
    # waves them through.
    errs = _dress_errors(_dressed(
        links=[_link(color="rgb(0, 0, 238)") for _ in range(8)]))
    assert any("browser's own default link color" in e for e in errs), errs


def test_every_link_is_sampled_not_just_the_first():
    errs = _dress_errors(_dressed(links=[_link(), _link(), _indistinct_link()]))
    assert any("1 of 3 a.inline-link" in e for e in errs), errs


def test_a_link_marked_by_any_signal_other_than_color_is_distinguishable():
    # THE OVER-CONSTRAINT this assertion used to carry silently. It compared
    # COLOR only, and the live theme dresses links with a color AND a
    # border-bottom, so nothing exercised the gap: a theme marking links by
    # underline alone at prose color — legitimate, and what WCAG prefers over
    # color alone — failed with "indistinguishable from body copy" while being
    # perfectly distinguishable. It fires inside --require-browser, so it
    # aborted the rotation.
    prose = "rgb(168, 194, 217)"
    signals = {
        "textDecorationLine": "underline",
        "borderBottomWidth": "1px",
        "borderBottomStyle": "dotted",
        "fontWeight": "600",
        "fontStyle": "italic",
        "backgroundColor": "rgba(23, 212, 250, 0.08)",
        "backgroundImage": "linear-gradient(transparent 90%, currentColor 90%)",
        "boxShadow": "inset 0 -1px currentColor",
        "textDecorationStyle": "wavy",
    }
    for signal, value in signals.items():
        link = _indistinct_link(prose)
        link["self"][signal] = value
        assert _dress_errors(_dressed(links=[link])) == [], (
            f"a link marked by {signal}={value!r} at prose color was called "
            f"indistinguishable")


def test_a_link_identical_to_its_prose_on_every_signal_still_fails():
    # The other side of the disjunction: widening the signal set must not
    # turn the assertion into one that can never fire.
    errs = _dress_errors(_dressed(links=[_indistinct_link()]))
    assert any("identical to the prose they sit in" in e for e in errs), errs


def test_a_link_whose_parent_could_not_be_read_is_not_invented_into_a_failure():
    link = _indistinct_link()
    link["parent"] = None
    assert _dress_errors(_dressed(links=[link])) == []


def test_dress_fails_when_the_page_carries_no_inline_link_at_all():
    errs = _dress_errors(_dressed(links=[]))
    assert any("a.inline-link is not present" in e for e in errs), errs


def test_dress_fails_when_the_title_is_missing():
    errs = _dress_errors(_dressed(title=None))
    assert any("h1.page-title is not present" in e for e in errs), errs


def test_dress_fails_loudly_when_the_ua_baseline_could_not_be_read():
    # Never a soft skip. Without the baseline the element-level assertions
    # silently cover less than they claim.
    errs = _dress_errors(_dressed(ua=None))
    assert any("undressed baseline" in e for e in errs), errs


def test_no_color_is_ever_parsed_only_compared():
    # THE CRITICAL this design exists to make impossible. The first cut read
    # each element's computed background and asked whether it painted, with an
    # rgb()/rgba() parser: `oklch(0.18 0.04 250)` is a fully opaque field that
    # such a parser reads as alpha 0, so a correct September theme would have
    # aborted the unattended rotation on the 1st. Every color here is in a
    # syntax that parser could not read, and the gate is silent.
    assert _dress_errors(_dressed(
        body={"color": "oklch(0.92 0.03 250)", "fontFamily": "Inter, sans-serif",
              "fontSize": "16px"},
        title={"color": "oklab(0.9 0.1 0.1)", "fontFamily": "X", "fontSize": "56px"},
        links=[{"color": "lab(62% 38 -58)",
                "parentColor": "color-mix(in oklab, white 80%, blue)"}] * 4,
    )) == []


def test_dress_failures_name_the_viewport_and_read_as_browser_findings():
    errs = td.check_page_renders_dressed(
        _StubDressPage(_dressed(title={"fontSize": "32px"})), 390)
    assert errs and all(e.startswith("browser: dress at 390px: ") for e in errs), errs


# ─── wiring ───────────────────────────────────────────────────────────────


def test_dress_outcome_pages_are_the_two_that_borrow_their_whole_chrome():
    assert td.DRESS_OUTCOME_PAGES == ("press.html", "privacy.html")
    assert set(td.DRESS_OUTCOME_PAGES) <= set(td.BROWSER_CHECK_LIVE_PAGES)
    previewable = _render_hub_previewable_pages()
    for name in td.DRESS_OUTCOME_PAGES:
        assert (ROOT / name) in previewable, name
    # ...and each must resolve the UTILITY archetype's stylesheet, which is
    # what "borrows its whole chrome" means here.
    spec = importlib.util.spec_from_file_location(
        "render_hub_for_dress_test", ROOT / "scripts" / "render-hub.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    want = "archetypes/" + td.REQUIRED_ARCHETYPE_CSS["utility"]
    for name in td.DRESS_OUTCOME_PAGES:
        assert mod.THEME_CSS_HREFS[ROOT / name] == want, name


def test_a_dress_page_the_browser_gate_never_opens_is_an_IMPORT_error():
    # A page in DRESS_OUTCOME_PAGES but not in BROWSER_CHECK_LIVE_PAGES is
    # never in the dict _run_browser_checks_all iterates, so it is handed
    # dress_outcome=False and skipped in total silence — the one failure class
    # this module refuses everywhere else. theme-doctor.py asserts the subset
    # at import; asserting the same fact here would pass with the guard
    # deleted, so this reloads the module with the invariant BROKEN and
    # requires the import itself to blow up.
    src = (ROOT / "scripts" / "theme-doctor.py").read_text(encoding="utf-8")
    broken = src.replace(
        'DRESS_OUTCOME_PAGES = ("press.html", "privacy.html")',
        'DRESS_OUTCOME_PAGES = ("press.html", "privacy.html", "not-in-the-gate.html")',
        1)
    assert broken != src, "DRESS_OUTCOME_PAGES literal moved; update this test"
    ns = {"__file__": str(ROOT / "scripts" / "theme-doctor.py"), "__name__": "td_broken"}
    with pytest.raises(AssertionError, match="BROWSER_CHECK_LIVE_PAGES"):
        exec(compile(broken, "theme-doctor.py", "exec"), ns)


def test_each_dress_page_links_exactly_one_stylesheet():
    # The differential disables every `link[rel=stylesheet]` on the page, so
    # "the page's linked stylesheets" and "the theme's dress" have to be the
    # same set. That is true today because render-hub.py owns the single
    # theme-css <link> and each page's own CSS is an inline <style>. A page
    # growing a second linked stylesheet would quietly make the differential
    # mean something else, so the premise is pinned rather than assumed.
    for name in td.DRESS_OUTCOME_PAGES:
        html = (ROOT / name).read_text(encoding="utf-8")
        links = re.findall(r'<link[^>]*rel="stylesheet"[^>]*>', html)
        assert len(links) == 1, (name, links)
        assert "/themes/" in links[0], (name, links)


def test_the_dress_check_runs_for_those_pages_and_no_others(monkeypatch):
    seen = []
    monkeypatch.setattr(td, "check_page_renders_dressed",
                        lambda page, width: seen.append(width) or [])
    td._check_viewport(_StubPage(None), "http://127.0.0.1:8000/", 1440)
    assert seen == [], "the dress check must be opt-in per page"
    td._check_viewport(_StubPage(None), "http://127.0.0.1:8000/", 768, dress_outcome=True)
    assert seen == [768]


def test_the_two_utility_pages_self_import_the_repo_global_font_stack():
    # /fonts/fonts.css is a REPO-GLOBAL asset, not a theme asset. Depending on
    # the theme's own @import for it was the single most fragile part of the
    # borrow, and the one part no assertion could ever see: if a theme drops
    # the line, body's computed font-family string is byte-identical and only
    # the @font-face rules behind it vanish.
    for name in td.DRESS_OUTCOME_PAGES:
        html = (ROOT / name).read_text(encoding="utf-8")
        style = "\n".join(td.STYLE_BLOCK_RE.findall(html))
        assert "@import url('/fonts/fonts.css');" in style, name


# ─── resolution groups: a name resolves against ONE document's stylesheets ──
# The reads-check used to pool every definition in the theme directory, but no
# consumer loads every theme stylesheet. phosphor-blueprint defines ten --pb-*
# names, archetypes/product.css reads nine of them, and tokens.css alone
# defines eight of that nine — so a definition in tokens.css satisfied a read
# in archetypes/utility.css, the one file press.html and privacy.html link.
# Both pages would render on rgba(0,0,0,0) with every gate green. These tests
# pin the scoping that closes it, and each one was watched failing against the
# pooled implementation before it was kept.

def _private_read_and_defined(text: str, group_text: dict[str, str]) -> set[str]:
    """Names this stylesheet both DEFINES and its group READS, minus the
    contracted set — the theme's own private treatment namespace, whatever it
    happens to be called.

    Derived, never spelled. `--pb-` is Phosphor Blueprint's private prefix and
    an earlier version of this file hardcoded it, so a theme naming its tokens
    `--sx-*` failed three parametrized tests for having a different taste in
    prefixes. The contract is that a theme MAY have a private namespace, not
    that it must spell it the way this month's theme spells it.
    """
    defined = set(td._parse_custom_properties(text)) - set(td.archetypes.REQUIRED_TOKENS)
    read = set()
    for body in group_text.values():
        stripped = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
        read |= set(re.findall(r"var\(\s*(--[\w-]+)", stripped))
    return defined & read


def _strip_definitions(text: str, names) -> str:
    for name in names:
        text = re.sub(r"[ \t]*" + re.escape(name) + r"\s*:[^;{}]*;\n?", "", text)
    return text


def _group_css(group_theme_labels, tdir, overrides=None):
    """The group's theme members as main() reads them — inline <style> for a
    .html shell, whole text otherwise — with any `overrides` swapped in."""
    overrides = overrides or {}
    return {
        label: overrides.get(label, td._group_stylesheet_text(tdir / label))
        for label in group_theme_labels
    }


def _live_site_css(group_site_labels):
    return {label: (ROOT / label).read_text(encoding="utf-8") for label in group_site_labels}


def _reads_errors_for_theme(tdir, overrides=None):
    """Run the reads-check over every derived group of the theme at `tdir`,
    with `overrides` (label -> replacement text) applied wherever those labels
    appear. Mirrors main()'s own loop."""
    errors = []
    for group, (theme_labels, site_labels) in td.resolution_groups(tdir).items():
        errors += td.check_theme_reads_only_what_it_defines(
            group,
            _group_css(theme_labels, tdir, overrides),
            _live_site_css(site_labels),
        )
    return errors


def _reads_errors_for_live_theme(overrides=None):
    return _reads_errors_for_theme(td.theme_registry.theme_dir(_active_slug()), overrides)


def _load_renderer(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_resolution_groups_stay_in_lockstep_with_the_code_that_serves_the_pages():
    # A TRACEABILITY PIN, not proof of derivation. Replace resolution_groups'
    # THEME_CSS_HREFS loop with a hand-written dict matching today's values and
    # this still passes — it compares two things that agree today, and cannot
    # tell how the left-hand one was computed. What it DOES catch is the moment
    # that matters: the day a source moves and a hardcoded copy does not.
    # Assertions 2 and 3 carry independent weight (containment in the real
    # concatenation; presence in the real about.html), and the parametrized
    # deletion tests below are where the scoping itself is proven.
    render_hub = _load_renderer("render-hub.py", "_t_render_hub")
    plugin_pages = _load_renderer("render-plugin-pages.py", "_t_render_plugin_pages")
    tdir = td.theme_registry.theme_dir(_active_slug())
    groups = td.resolution_groups(tdir)

    # 1. Every page render-hub.py gives a theme-css <link> is a consumer, and
    #    its group holds exactly the stylesheet that map names.
    for page, href in render_hub.THEME_CSS_HREFS.items():
        owning = [g for g in groups if page.name in g.split(", ")]
        assert len(owning) == 1, (page.name, owning)
        assert groups[owning[0]][0] == (href,), (page.name, groups[owning[0]])

    # 2. The 15 generated plugin pages get exactly what the renderer inlines.
    plugin_group = groups["plugins/*/index.html"][0]
    assert plugin_group, "the plugin-page group must not be empty"
    for label in plugin_group:
        assert (tdir / label).read_text(encoding="utf-8").strip() in plugin_pages.STYLE, label
    # ...and NOT tokens.css, which no plugin page is ever served.
    assert "tokens.css" not in plugin_group

    # 3. about.html's group is whatever its own dress zone points at.
    about_html = render_hub.ABOUT_HTML.read_text(encoding="utf-8")
    for label in groups["about.html"][0]:
        assert "/" + label in about_html, label

    # 4. index.html's group comes off the THEME's own home shell, not the
    #    site's — every theme link in that shell is in the group.
    shell = f"archetypes/{td.archetypes.archetype_for('index.html', td.archetypes.load())}.html"
    index_group = groups["index.html"][0]
    assert shell in index_group
    for label in td._page_stylesheets(tdir / shell)[0]:
        assert label in index_group, label


def test_every_required_stylesheet_lands_in_some_group():
    # The backstop that makes derived groups safe: scoping trades a pool that
    # was too wide for pools that could silently become too narrow. Repoint
    # THEME_CSS_HREFS off archetypes/utility.css and that file stops being
    # graded by anything, with no error anywhere.
    tdir = td.theme_registry.theme_dir(_active_slug())
    assert td.check_every_required_stylesheet_is_graded(td.resolution_groups(tdir)) == []
    starved = {"about.html": (("archetypes/reading.css",), ())}
    errs = td.check_every_required_stylesheet_is_graded(starved)
    assert any("archetypes/utility.css" in e for e in errs)
    assert all("grades what it reads" in e for e in errs)


def test_the_live_theme_resolves_every_group_from_within_that_group():
    assert _reads_errors_for_live_theme() == []


@pytest.mark.parametrize(
    "label,consumer,expected_reader",
    [
        ("archetypes/utility.css", "press.html, privacy.html", "archetypes/utility.css"),
        ("archetypes/product-tokens.css", "plugins/*/index.html", "archetypes/product.css"),
        ("archetypes/reading-tokens.css", "thesis.html, workflow.html",
         "archetypes/reading-tokens.css"),
    ],
)
def test_dropping_a_treatment_prefix_from_one_group_fails_that_group(
    label, consumer, expected_reader
):
    # The three-way reproduction, pinned. Deleting a stylesheet's own --pb-*
    # DEFINITIONS while keeping every read is the plausible edit when
    # retokenizing a copied theme, and check_required_tokens cannot see it —
    # --pb-* is deliberately not in the contract. Under the pooled
    # implementation each of these reported nothing (utility, reading-tokens)
    # or one name out of nine (product-tokens), because tokens.css defines
    # eight of the nine and satisfied reads in documents that never load it.
    tdir = td.theme_registry.theme_dir(_active_slug())
    original = (tdir / label).read_text(encoding="utf-8")

    # The theme's OWN private namespace, derived from what this file defines
    # and its group reads. A theme may call it --pb-*, --sx-*, or may have
    # none at all; only the last case needs help, and it gets a synthesized
    # probe rather than a skip, because a skipped gate is the failure mode
    # this file refuses everywhere else.
    group_text = {}
    for _group, (theme_labels, _site) in td.resolution_groups(tdir).items():
        if label in theme_labels:
            group_text.update(_group_css(theme_labels, tdir))
    private = _private_read_and_defined(original, group_text)
    if not private:
        probe = "--zz-private-probe"
        original += (
            "\n:root { " + probe + ": #123456; }\nbody { color: var(" + probe + "); }\n"
        )
        private = {probe}

    stripped = _strip_definitions(original, private)
    assert stripped != original, f"{label}: nothing was stripped"

    errs = _reads_errors_for_live_theme({label: stripped})
    assert errs, f"deleting {label}'s private token definitions produced no error"
    for e in errs:
        assert e.startswith(f"{expected_reader}: reads --"), e
        assert f"nothing loaded by {consumer} defines" in e, e

    # And the deletion stays invisible to the token contract, which is why
    # this check has to exist at all.
    assert td.check_required_tokens(stripped) == []


def test_only_stylesheets_the_browser_actually_applies_are_credited(tmp_path):
    # Every exclusion here is in the NARROWING direction, which is the point:
    # crediting a stylesheet the browser never applies is what licenses an
    # unresolved read. Protocol-relative is the form every analytics/CDN link
    # in this repo uses, and it is the one an origin check reading `://` alone
    # would wave through; a commented-out <link> is how a page stops loading a
    # stylesheet without deleting the line.
    page = tmp_path / "fixture.html"
    page.write_text(
        '<link rel="stylesheet" href="/Design/editorial.css">'
        "<link href='/themes/some-slug/archetypes/utility.css' rel=stylesheet>"
        '<link rel="stylesheet" href="//cdn.example.com/x.css">'
        '<link rel="stylesheet" href="https://cdn.example.com/y.css">'
        '<!-- <link rel="stylesheet" href="/Design/retired.css"> -->'
        '<link rel="stylesheet" href="/Design/paper.css" media="print">'
        '<link rel="stylesheet" href="/Design/off.css" disabled>'
        '<link rel="stylesheet" href="/Design/wide.css" media="screen and (min-width:60em)">'
        '<link rel="icon" href="/favicon-626.png">',
        encoding="utf-8",
    )
    theme, site = td._page_stylesheets(page)
    assert theme == ("archetypes/utility.css",)
    assert site == ("Design/editorial.css", "Design/wide.css")


def test_a_site_stylesheet_credits_only_the_group_that_links_it():
    # EXTERNAL_STYLESHEETS was one theme-wide tuple, so archetypes/product.css
    # could read an --ed-* name and pass on a definition in
    # Design/editorial.css that no product consumer ever loads. Site
    # stylesheets attach per group now, derived from each page's own <link>s.
    tdir = td.theme_registry.theme_dir(_active_slug())
    groups = td.resolution_groups(tdir)

    # THE PROPERTY, re-derived here with a plain regex rather than restated as
    # this theme's answer: a group's site stylesheets are exactly the
    # NON-theme stylesheets its own documents link. An earlier version pinned
    # ("widget-bacon-trail/widget.css",) as a literal, so a home shell that
    # also linked /Design/editorial.css or /fonts/fonts.css — both legitimate
    # — failed a test about scoping for having different contents.
    link_re = re.compile(r'<link[^>]+rel="stylesheet"[^>]*>')
    href_re = re.compile(r'href="([^"]+)"')

    def _site_links(html):
        out = set()
        for tag in link_re.findall(html):
            m = href_re.search(tag)
            if not m:
                continue
            href = m.group(1).split("?", 1)[0].lstrip("/")
            if href.startswith("themes/"):
                continue          # theme-owned; graded as a theme member
            if (ROOT / href).exists():
                out.add(href)
        return out

    for group, (_theme_labels, site_labels) in groups.items():
        expected = set()
        for page in group.split(", "):
            if "*" in page:
                continue          # a glob of generated pages, no single source
            source = (tdir / "archetypes" / "home.html") if page == "index.html" else (ROOT / page)
            if source.exists():
                expected |= _site_links(source.read_text(encoding="utf-8"))
        assert set(site_labels) == expected, (group, site_labels, expected)

    # about.html's dress legitimately spends five names editorial.css defines,
    # and resolves them ONLY because about.html links that file.
    tdir = td.theme_registry.theme_dir(_active_slug())
    reading_css = (tdir / "archetypes" / "reading.css").read_text(encoding="utf-8")
    editorial = {
        "Design/editorial.css": (ROOT / "Design" / "editorial.css").read_text(encoding="utf-8")
    }
    assert td.check_theme_reads_only_what_it_defines(
        "about.html", {"archetypes/reading.css": reading_css}, editorial
    ) == []
    unlinked = td.check_theme_reads_only_what_it_defines(
        "about.html", {"archetypes/reading.css": reading_css}, {}
    )
    # The property, not the five names: every read that resolves ONLY because
    # about.html links editorial.css is a name editorial.css actually defines.
    # A new reading dress spending four of them, or six, is a design choice
    # rather than a regression.
    unlinked_names = {e.split("reads ")[1].split(",")[0] for e in unlinked}
    editorial_defines = set(td._parse_custom_properties(editorial["Design/editorial.css"]))
    assert unlinked_names, "reading.css reads nothing from editorial.css to scope"
    assert unlinked_names <= editorial_defines, unlinked_names - editorial_defines

    # The other half of the scoping: the same read, in a group that does not
    # link editorial.css, is a failure no matter what editorial.css defines.
    assert td.check_theme_reads_only_what_it_defines(
        "plugins/*/index.html",
        {"archetypes/product.css": "body { font-size: var(--ed-t-body); }"},
        {},
    ) == [
        "archetypes/product.css: reads --ed-t-body, which nothing loaded by "
        "plugins/*/index.html defines and which carries no fallback"
    ]


def test_declared_contrast_pairs_that_all_filter_out_are_an_ERROR(capsys):
    # A theme mirroring another's contrastPairs but naming tokens its own CSS
    # never declares used to print "unverified" and append zero errors — four
    # archetypes could print it and the theme still rotated, unattended, with
    # contrast never graded once. The three existing _check_archetype tests
    # all pass pairs=None, so only the other branch was ever exercised.
    about_html = (ROOT / "about.html").read_text(encoding="utf-8")
    lnt = [c for c in td.archetypes.VOCABULARY["reading"] if c.startswith("lnt-")]
    css = "".join(f".{c} {{ }}\n" for c in lnt)
    # Same fixture as test_reading_gate_passes_when_theme_css_covers_every_lnt_class,
    # so contrast is the ONLY thing that can fail here. That setup call passes
    # pairs=None, the branch that DOES print the advisory, so its output is
    # drained before the real assertion runs. Without the drain this test
    # fails with the implementation intact — a false FAILURE, not a false
    # pass; the drain is scaffolding for the fixture, and the assertion below
    # is what carries the weight.
    assert td._check_archetype("reading", about_html, css, False, None) == []
    capsys.readouterr()

    pairs = [["--not-declared-fg", "--not-declared-bg"], ["--also-absent", "--nor-this"]]
    errs = td._check_archetype("reading", about_html, css, False, pairs)
    assert errs == [
        "reading: none of the 2 declared contrastPairs name custom properties "
        "this archetype's own CSS declares, so its contrast was never graded"
    ]
    # ...and it must not ALSO print the "nothing declared" advisory, which is
    # for a theme that declared nothing at all.
    assert "unverified" not in capsys.readouterr().out


# ─── index.html: the theme-authored group ─────────────────────────────────
# The home shell is the one consumer whose <link> tags belong to the THEME,
# not to the site, so index.html's group has to be derived from the theme
# under test. Both variants below were built by review, run against the real
# gate, and PASSED at exit 0 before index.html had a group — the site's
# highest-traffic page wearing the utility-dress bug.


def _stub_theme_with_home_links(tmp_path, links, extra_files=()):
    """A complete stub theme whose home shell carries `links` in its <head>."""
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)
    for name, text in extra_files:
        (tdir / name).write_text(text, encoding="utf-8")
    home = tdir / "archetypes" / "home.html"
    home.write_text(
        home.read_text(encoding="utf-8").replace("<html>", f"<html><head>{links}</head>", 1),
        encoding="utf-8",
    )
    return tdir


def _run_main_on(monkeypatch, tmp_path, tdir, argv=("stub-theme",)):
    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)
    monkeypatch.setattr(td.subprocess, "run", _stub_main_kwargs(tmp_path))
    monkeypatch.setattr(
        td.tempfile, "TemporaryDirectory",
        lambda *a, **kw: __import__("contextlib").nullcontext(str(tmp_path)),
    )
    return td.main(list(argv))


def test_a_home_only_stylesheet_reading_undefined_names_fails_the_gate(
    monkeypatch, tmp_path, capsys
):
    # Variant A: the theme adds an archetypes/home.css and links it from its
    # own shell. No map names that file, no floor requires it, and before
    # index.html had a group nothing graded it — the gate returned 0 and
    # index.html shipped on rgba(0,0,0,0).
    tdir = _stub_theme_with_home_links(
        tmp_path,
        '<link rel="stylesheet" href="/themes/stub-theme/archetypes/home.css">',
        extra_files=[(
            "archetypes/home.css",
            "body { background: var(--sx-field); color: var(--sx-ink); }\n",
        )],
    )
    assert _run_main_on(monkeypatch, tmp_path, tdir) == 1
    out = capsys.readouterr().out
    assert "archetypes/home.css: reads --sx-field" in out
    assert "archetypes/home.css: reads --sx-ink" in out
    assert "nothing loaded by index.html defines" in out


def test_reusing_the_reading_dress_on_the_homepage_fails_the_gate(
    monkeypatch, tmp_path, capsys
):
    # Variant B: a plausible reuse of the reading dress on a homepage strip.
    # reading.css IS graded — by about.html's group, where
    # Design/editorial.css resolves its five --ed-*/--font-serif reads. On
    # index.html nothing links editorial.css, so those five reads have no
    # definition and no fallback. The floor stays silent here by design (the
    # file is graded, just not by this group), which is exactly why the group
    # itself has to exist.
    tdir = _stub_theme_with_home_links(
        tmp_path,
        '<link rel="stylesheet" href="/themes/stub-theme/archetypes/reading.css">',
        extra_files=[(
            "archetypes/reading.css",
            _compliant_reading_css()
            + ".ed-pull { font-size: var(--ed-t-pull); font-family: var(--font-serif); }\n",
        )],
    )
    assert _run_main_on(monkeypatch, tmp_path, tdir) == 1
    out = capsys.readouterr().out
    assert "archetypes/reading.css: reads --ed-t-pull" in out
    assert "archetypes/reading.css: reads --font-serif" in out
    assert "nothing loaded by index.html defines" in out
    # ...and about.html's group, which DOES link editorial.css, reports
    # neither of them. Same file, two groups, two verdicts.
    assert "nothing loaded by about.html defines" not in out


def test_the_home_shell_contributes_its_STYLE_BLOCKS_and_nothing_else(
    monkeypatch, tmp_path, capsys
):
    # There is no archetypes/home.css in any shipped theme: the home dress is
    # the inline <style> block in archetypes/home.html. A var() spent there is
    # exactly as unresolved as one spent in a linked file, so the shell enters
    # its own group as a member and main() reads its <style> blocks.
    #
    # ...and ONLY its <style> blocks. The shell is a document, not a
    # stylesheet: it carries inline scripts, and CSS-shaped text inside a
    # <script> string is not a declaration the browser ever sees. Feeding the
    # raw HTML would credit that string as a definition and wave the read
    # through — which is why the same fixture asserts both halves. (Today's
    # home.html has 48 var() reads and every one is inside a <style>, so this
    # is pinned synthetically rather than observed.)
    tdir = _stub_theme_with_home_links(tmp_path, "")
    home = tdir / "archetypes" / "home.html"
    home.write_text(
        home.read_text(encoding="utf-8").replace(
            "<body>",
            "<style>body { background: var(--sx-nowhere); }</style>"
            '<script>var fake = ":root { --sx-nowhere: red; }";</script>'
            "<body>",
            1,
        ),
        encoding="utf-8",
    )
    assert _run_main_on(monkeypatch, tmp_path, tdir) == 1
    out = capsys.readouterr().out
    assert "archetypes/home.html: reads --sx-nowhere" in out
    assert "nothing loaded by index.html defines" in out


def test_the_live_home_shell_resolves_everything_it_spends():
    # The live theme's home dress is 45k of inline CSS reading 60 of its own
    # names plus the widget stylesheet's. All of it resolves inside
    # index.html's group, which is what makes grading the shell affordable.
    tdir = td.theme_registry.theme_dir(_active_slug())
    groups = td.resolution_groups(tdir)
    theme_labels, site_labels = groups["index.html"]
    assert td.check_theme_reads_only_what_it_defines(
        "index.html", _group_css(theme_labels, tdir), _live_site_css(site_labels)
    ) == []
