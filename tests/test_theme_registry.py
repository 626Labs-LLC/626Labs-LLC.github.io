import json, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import theme_registry as tr


def _reg():
    return {"active": "a", "queue": ["b", "c"], "archive": []}


def test_rotate_promotes_and_archives():
    out = tr.rotate(_reg(), "2026-09")
    assert out["active"] == "b"
    assert out["queue"] == ["c"]
    assert out["archive"] == [
        {"slug": "a", "month": "2026-09", "url": "/themes/archive/2026-09/"}
    ]


def test_rotate_is_pure():
    reg = _reg()
    tr.rotate(reg, "2026-09")
    assert reg == _reg()


def test_rotate_empty_queue_raises():
    with pytest.raises(ValueError, match="queue is empty"):
        tr.rotate({"active": "a", "queue": [], "archive": []}, "2026-09")


def test_validate_flags_missing_theme_dir(tmp_path):
    (tmp_path / "themes").mkdir()
    errs = tr.validate({"active": "ghost", "queue": [], "archive": []}, root=tmp_path)
    assert any("ghost" in e for e in errs)


def test_validate_flags_duplicate_queue(tmp_path):
    for slug in ("a", "b"):
        d = tmp_path / "themes" / slug
        d.mkdir(parents=True)
        for f in ("shell.html", "tokens.css", "theme.json"):
            (d / f).write_text("x", encoding="utf-8")
    errs = tr.validate({"active": "a", "queue": ["b", "b"], "archive": []}, root=tmp_path)
    assert any("duplicate" in e.lower() for e in errs)


def test_real_registry_is_valid():
    assert tr.validate(tr.load()) == []
