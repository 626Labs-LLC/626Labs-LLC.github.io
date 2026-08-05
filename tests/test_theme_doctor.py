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

    def __init__(self, goto_side_effect, console=(), pageerrors=()):
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
        assert len(applicable) == len(pairs), (
            f"{archetype}: only {len(applicable)} of {len(pairs)} declared pairs "
            f"resolve — the rest are silently skipped and never graded"
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
        "links": [{"color": "rgb(23, 212, 250)", "parentColor": "rgb(232, 242, 255)"}] * 8,
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
    assert "b.x" not in td._DRESS_PROBE_JS and "b.y" not in td._DRESS_PROBE_JS


def test_every_region_selector_is_the_PAGES_own_markup():
    # The design's one hard rule: a region may name a selector the PAGE ships,
    # never one the THEME must carry. Checked against both shipped files.
    needles = {
        "html, body": "<body",
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
    prose = "rgb(168, 194, 217)"          # --fg-2, the paragraph's own color
    body_color = "rgb(232, 242, 255)"     # --fg-1, body's
    assert prose != body_color
    errs = _dress_errors(_dressed(
        body={**_dressed()["body"], "color": body_color},
        links=[{"color": prose, "parentColor": prose}] * 10))
    assert any("same color as the prose they sit in" in e for e in errs), errs


def test_dress_fails_when_links_fall_back_to_the_browsers_link_color():
    # The other half, and it needs its own branch: drop the bare `a` rule too
    # and links go UA blue — different from their parent, so the first half
    # waves them through.
    errs = _dress_errors(_dressed(
        links=[{"color": "rgb(0, 0, 238)", "parentColor": "rgb(232, 242, 255)"}] * 8))
    assert any("browser's own default link color" in e for e in errs), errs


def test_every_link_is_sampled_not_just_the_first():
    errs = _dress_errors(_dressed(links=[
        {"color": "rgb(23, 212, 250)", "parentColor": "rgb(232, 242, 255)"},
        {"color": "rgb(23, 212, 250)", "parentColor": "rgb(232, 242, 255)"},
        {"color": "rgb(168, 194, 217)", "parentColor": "rgb(168, 194, 217)"},
    ]))
    assert any("1 of 3 a.inline-link" in e for e in errs), errs


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
