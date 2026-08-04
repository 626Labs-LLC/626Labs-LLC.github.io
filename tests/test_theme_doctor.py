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
    return f"""<html><head></head><body>
      <a class="skip-link" href="#main">Skip</a><nav>x</nav>
      {zones}<footer>f</footer>
      <script data-goatcounter="https://626labs.goatcounter.com/count"></script>
    </body></html>"""


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


def test_main_require_browser_implies_browser_and_fails_when_unavailable(monkeypatch, tmp_path):
    # A minimally-complete theme so we get all the way to the browser check.
    tdir = tmp_path / "themes" / "stub-theme"
    tdir.mkdir(parents=True)
    (tdir / "shell.html").write_text("<html></html>", encoding="utf-8")
    (tdir / "tokens.css").write_text("", encoding="utf-8")
    (tdir / "theme.json").write_text("{}", encoding="utf-8")

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
    tdir.mkdir(parents=True)
    (tdir / "shell.html").write_text("<html></html>", encoding="utf-8")
    (tdir / "tokens.css").write_text("", encoding="utf-8")
    (tdir / "theme.json").write_text("{}", encoding="utf-8")

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
