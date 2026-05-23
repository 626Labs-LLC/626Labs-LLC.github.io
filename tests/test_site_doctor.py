import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

# site-doctor.py has a hyphen (matches render-hub.py convention) — load by path.
_spec = importlib.util.spec_from_file_location(
    "site_doctor", ROOT / "scripts" / "site-doctor.py"
)
site_doctor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(site_doctor)


def test_prose_check_passes_when_consistent():
    fcts = {"cmd_vibe-cartographer": 12, "cmd_vibe-cartographer_word": "Twelve"}
    text = "Twelve slash commands walk you from idea to ship."
    assert site_doctor.check_prose(text, fcts, source="x") == []


def test_prose_check_fails_on_stale_count():
    fcts = {"cmd_vibe-cartographer": 12, "cmd_vibe-cartographer_word": "Twelve"}
    text = "Eleven slash commands walk you from idea to ship."
    failures = site_doctor.check_prose(text, fcts, source="x")
    assert failures and "slash commands" in failures[0]


def test_prose_check_ignores_other_plugin_command_counts():
    # "Two commands" / "Three commands" belong to other plugins — must NOT trip
    # the cartographer slash-commands rule.
    fcts = {"cmd_vibe-cartographer_word": "Twelve"}
    assert site_doctor.check_prose("Two commands when a mode is too much.", fcts, "x") == []
    assert site_doctor.check_prose("Three commands. One flow.", fcts, "x") == []


def test_asset_existence_flags_missing(tmp_path):
    obj = {"a": "/assets/exists.png", "b": "/assets/missing.png", "c": "https://x.com/y.png"}
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "exists.png").write_bytes(b"x")
    failures = site_doctor.check_assets(obj, root=tmp_path)
    assert any("missing.png" in f for f in failures)
    assert not any("exists.png" in f for f in failures)
    assert not any("x.com" in f for f in failures)  # remote URLs ignored
