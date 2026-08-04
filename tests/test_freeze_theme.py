import importlib.util, sys
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
    (d / "tokens.css").write_text(":root{--x:#fff}", encoding="utf-8")
    (d / "shell.html").write_text("<html></html>", encoding="utf-8")
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
