import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
_spec = importlib.util.spec_from_file_location("site_cli", ROOT / "scripts" / "site.py")
site_cli = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(site_cli)

SAMPLE = '''{
  "products": [
    {
      "id": "vibe-sec",
      "status": "wip",
      "tags": []
    },
    {
      "id": "vibe-x",
      "status": "live"
    }
  ]
}
'''


def test_set_status_in_text_changes_only_target():
    out = site_cli.set_status_in_text(SAMPLE, "vibe-sec", "live")
    assert '"id": "vibe-sec"' in out
    assert out.count('"status": "live"') == 2   # vibe-sec flipped + vibe-x unchanged
    assert '"status": "wip"' not in out
    # vibe-x block untouched
    assert SAMPLE.split('"id": "vibe-x"')[1] == out.split('"id": "vibe-x"')[1]


def test_set_status_in_text_not_found():
    import pytest
    with pytest.raises(ValueError):
        site_cli.set_status_in_text(SAMPLE, "nope", "live")


def test_guarded_apply_reverts_on_failure(tmp_path):
    f = tmp_path / "src.json"
    f.write_text("ORIGINAL", encoding="utf-8")
    ok, detail = site_cli.guarded_apply(
        f, "MUTATED",
        render_fn=lambda: None,
        validate_fn=lambda: (False, "boom"),
    )
    assert ok is False and "boom" in detail
    assert f.read_text(encoding="utf-8") == "ORIGINAL"   # reverted


def test_guarded_apply_keeps_on_success(tmp_path):
    f = tmp_path / "src.json"
    f.write_text("ORIGINAL", encoding="utf-8")
    ok, _ = site_cli.guarded_apply(
        f, "MUTATED",
        render_fn=lambda: None,
        validate_fn=lambda: (True, ""),
    )
    assert ok is True
    assert f.read_text(encoding="utf-8") == "MUTATED"   # kept


def test_cmd_facts_runs(capsys):
    rc = site_cli.main(["facts"])
    out = capsys.readouterr().out
    assert rc == 0 and '"claude_plugins"' in out


def test_cmd_get_unknown_section_errors():
    assert site_cli.main(["get", "definitely-not-a-section"]) == 2
