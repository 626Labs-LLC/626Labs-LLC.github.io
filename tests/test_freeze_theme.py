import importlib.util, pathlib, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("freeze_theme", ROOT / "scripts" / "freeze-theme.py")
fz = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fz)


def _site(tmp_path):
    (tmp_path / "content").mkdir()
    (tmp_path / "content" / "themes.json").write_text(
        '{"active":"t","queue":[],"archive":[]}', encoding="utf-8")
    d = tmp_path / "themes" / "t"
    d.mkdir(parents=True)
    # freeze() only ever reads root/index.html + the local stylesheets it
    # links — it never checks theme-dir completeness, so no archetypes/
    # files are needed here (that's theme_registry/theme-doctor's job).
    (d / "tokens.css").write_text(":root{--x:#fff}", encoding="utf-8")
    (d / "theme.json").write_text('{"name":"T","slug":"t"}', encoding="utf-8")
    (tmp_path / "index.html").write_text(
        '<html><head><link rel="stylesheet" href="/themes/t/tokens.css"></head>'
        '<body><main>hi</main></body></html>', encoding="utf-8")
    return tmp_path


def test_freeze_creates_archive_with_noindex_and_banner(tmp_path):
    out = fz.freeze("2026-09", root=_site(tmp_path))
    html = (out / "index.html").read_text(encoding="utf-8")
    assert 'name="robots"' in html and "noindex" in html
    assert "September 2026" in html
    assert (out / "tokens.css").exists()


def test_freeze_rewrites_stylesheet_to_local_copy(tmp_path):
    out = fz.freeze("2026-09", root=_site(tmp_path))
    html = (out / "index.html").read_text(encoding="utf-8")
    assert 'href="tokens.css"' in html
    assert "/themes/t/tokens.css" not in html


def test_freeze_refuses_to_overwrite(tmp_path):
    root = _site(tmp_path)
    fz.freeze("2026-09", root=root)
    try:
        fz.freeze("2026-09", root=root)
        assert False, "expected refusal"
    except FileExistsError:
        pass


def _add_stylesheet_link(root, href):
    idx = root / "index.html"
    html = idx.read_text(encoding="utf-8")
    html = html.replace("</head>", f'<link rel="stylesheet" href="{href}"></head>')
    idx.write_text(html, encoding="utf-8")


def test_freeze_copies_and_rewrites_additional_local_stylesheets(tmp_path):
    # A local stylesheet outside the active theme dir (e.g. the base
    # /Design/*.css layer) must also get localized — that's the point of
    # the review finding: a later retokenize of /Design/*.css must not be
    # able to silently repaint an archived month.
    root = _site(tmp_path)
    (root / "Design").mkdir()
    (root / "Design" / "colors_and_type.css").write_text(":root{--y:#000}", encoding="utf-8")
    _add_stylesheet_link(root, "/Design/colors_and_type.css")

    out = fz.freeze("2026-09", root=root)
    html = (out / "index.html").read_text(encoding="utf-8")
    assert 'href="colors_and_type.css"' in html
    assert "/Design/colors_and_type.css" not in html
    assert (out / "colors_and_type.css").read_text(encoding="utf-8") == ":root{--y:#000}"


def test_freeze_excludes_widget_bacon_trail_stylesheet(tmp_path):
    # Explicitly out of scope per the 2026-08-03 review: an interactive
    # widget's CSS, not a design surface. It resolves inside the repo but
    # must be left linking live, untouched and uncopied.
    root = _site(tmp_path)
    (root / "widget-bacon-trail").mkdir()
    (root / "widget-bacon-trail" / "widget.css").write_text("body{color:red}", encoding="utf-8")
    _add_stylesheet_link(root, "/widget-bacon-trail/widget.css")

    out = fz.freeze("2026-09", root=root)
    html = (out / "index.html").read_text(encoding="utf-8")
    assert 'href="/widget-bacon-trail/widget.css"' in html
    assert not (out / "widget.css").exists()


# ─── capture_theme_screenshot / --screenshot CLI ───────────────────────
#
# Real browser capture is exercised manually (see the task report) the same
# way theme-doctor.py's own --browser checks are — content-health.yml's
# pytest job never installs playwright, so these tests only exercise the
# "playwright unavailable" degrade path, matching test_theme_doctor.py's
# established pattern of monkeypatching the lazy-import guard rather than
# requiring a real browser in the automated suite.

def test_capture_theme_screenshot_raises_when_playwright_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(fz, "_import_sync_playwright", lambda: None)
    try:
        fz.capture_theme_screenshot("phosphor-blueprint", tmp_path / "shot.png")
        assert False, "expected RuntimeError"
    except RuntimeError as e:
        assert "playwright" in str(e).lower()


# ─── SMIL freeze ───────────────────────────────────────────────────────
#
# SVG SMIL runs on the SVG document timeline: prefers-reduced-motion does not
# gate it and the init script's rAF override does not reach it. That was
# found by misreading a pulsing <circle> on workflow.html as raster noise for
# most of a task. These two tests exist so the fix cannot quietly fall back
# out of the shipped harness, which is exactly where it spent its first
# round — in a scratch file, while this module still promised "animations
# off."


def test_deterministic_init_script_freezes_svg_animations():
    s = fz._DETERMINISTIC_CAPTURE_INIT_SCRIPT
    assert "pauseAnimations()" in s
    assert "setCurrentTime(0)" in s
    # Published on window, because add_init_script runs at document-start
    # when no <svg> exists yet — the capture re-invokes it later.
    assert "window.__freezeSvgAnimations" in s
    # And wired to both document-ready milestones, so a capture that never
    # re-invokes it still freezes everything present by load.
    assert "DOMContentLoaded" in s
    assert "'load'" in s


def test_capture_freezes_svg_animations_immediately_before_the_shutter(tmp_path, monkeypatch):
    """The call ORDER is the whole point: freeze after the settle (so SVG
    built by page JS is caught) and before screenshot() (so the frame that
    lands on disk is the frozen one). A refactor that keeps the call but
    moves it above the settle, or drops it entirely, passes every other test
    in this file."""
    order = []

    class _Page:
        def add_init_script(self, script):
            order.append("init:" + ("smil" if "pauseAnimations" in script else "other"))

        def goto(self, *a, **kw):
            order.append("goto")

        def evaluate(self, expr):
            order.append(
                "freeze" if "__freezeSvgAnimations" in expr else f"evaluate:{expr}"
            )

        def wait_for_timeout(self, ms):
            order.append("settle")

        def screenshot(self, path, full_page=False):
            order.append("screenshot")
            pathlib.Path(path).write_bytes(b"png")

        def close(self):
            pass

    class _Browser:
        def new_page(self, **kw):
            return _Page()

        def close(self):
            pass

    class _Chromium:
        def launch(self):
            return _Browser()

    class _PW:
        chromium = _Chromium()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(fz, "_import_sync_playwright", lambda: (lambda: _PW()))
    monkeypatch.setattr(fz, "_render_theme_home", lambda slug: "<html></html>")

    out = tmp_path / "shot.png"
    fz.capture_theme_screenshot("phosphor-blueprint", out)

    assert "init:smil" in order, "init script registered without the SMIL freeze"
    assert "freeze" in order, "capture never invoked window.__freezeSvgAnimations"
    assert order.index("freeze") > order.index("settle"),         "freeze must run AFTER the settle — page JS injects SVG"
    assert order.index("freeze") < order.index("screenshot"),         "freeze must run BEFORE the shutter"


def test_screenshot_cli_requires_slug_and_out_path():
    assert fz.main(["--screenshot"]) == 2
    assert fz.main(["--screenshot", "only-slug"]) == 2
    assert fz.main(["--screenshot", "slug", "out", "extra"]) == 2


def test_screenshot_cli_reports_error_when_playwright_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(fz, "_import_sync_playwright", lambda: None)
    out_path = tmp_path / "shot.png"
    rc = fz.main(["--screenshot", "phosphor-blueprint", str(out_path)])
    assert rc == 1
    assert not out_path.exists()
    assert "playwright" in capsys.readouterr().err.lower()


def test_screenshot_cli_writes_file_on_success(tmp_path, monkeypatch):
    # capture_theme_screenshot itself is mocked out — this only proves the
    # CLI wiring (arg parsing, success path, printed confirmation), not the
    # real browser pipeline (covered by the manual determinism proof).
    calls = []

    def _fake_capture(slug, out_path):
        calls.append((slug, out_path))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b"fake-png")
        return out_path

    monkeypatch.setattr(fz, "capture_theme_screenshot", _fake_capture)
    out_path = tmp_path / "nested" / "shot.png"
    rc = fz.main(["--screenshot", "phosphor-blueprint", str(out_path)])
    assert rc == 0
    assert out_path.read_bytes() == b"fake-png"
    assert calls == [("phosphor-blueprint", out_path)]


def test_freeze_flattens_colliding_basenames(tmp_path):
    # Two stylesheets named tokens.css in different directories must not
    # clobber each other in the flat archive dir — deterministic flatten
    # (path with "/" -> "__") kicks in only for the colliding basename.
    root = _site(tmp_path)
    (root / "Design").mkdir()
    (root / "Design" / "tokens.css").write_text(":root{--z:#123}", encoding="utf-8")
    _add_stylesheet_link(root, "/Design/tokens.css")

    out = fz.freeze("2026-09", root=root)
    html = (out / "index.html").read_text(encoding="utf-8")
    assert 'href="themes__t__tokens.css"' in html
    assert 'href="Design__tokens.css"' in html
    assert (out / "themes__t__tokens.css").read_text(encoding="utf-8") == ":root{--x:#fff}"
    assert (out / "Design__tokens.css").read_text(encoding="utf-8") == ":root{--z:#123}"
