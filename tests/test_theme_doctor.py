import importlib.util, sys
from pathlib import Path

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
    # exercising what they're actually testing.
    (tdir / "archetypes").mkdir(parents=True)
    (tdir / "tokens.css").write_text("", encoding="utf-8")
    (tdir / "theme.json").write_text("{}", encoding="utf-8")
    for a in td.theme_registry.REQUIRED_ARCHETYPES:
        (tdir / "archetypes" / f"{a}.html").write_text(_compliant_archetype_html(a), encoding="utf-8")
    (tdir / "archetypes" / "product.css").write_text("", encoding="utf-8")
    (tdir / "archetypes" / "utility.css").write_text("", encoding="utf-8")


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
    # theme-doctor checks `reading` against about.html, not the theme's own
    # reading.html shell — see _archetype_source's docstring in
    # scripts/theme-doctor.py for why. This sanity-checks the one artifact
    # the gate actually inspects for that archetype.
    html = (ROOT / "about.html").read_text(encoding="utf-8")
    assert td.check_vocabulary(html, "", "reading") == []


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


def test_main_theme_with_both_archetype_css_files_clears_completeness(monkeypatch, tmp_path, capsys):
    # A complete stub theme must get PAST the completeness gate (it may
    # still fail later, e.g. because render-hub.py --theme isn't mocked
    # here) — proves the new required-files check doesn't over-fire on a
    # theme that actually has both CSS artifacts.
    tdir = tmp_path / "themes" / "stub-theme"
    _make_complete_theme_dir(tdir)

    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda slug, root=None: tdir)

    td.main(["stub-theme"])
    out = capsys.readouterr().out
    assert "product.css" not in out
    assert "utility.css" not in out
