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


ARR_NONEMPTY = '{\n  "family": [\n    { "id": "a" },\n    { "id": "b" }\n  ]\n}\n'
ARR_EMPTY = '{\n  "items": []\n}\n'


def test_array_append_nonempty_is_valid_and_additive():
    import json
    out = site_cli.array_append_in_text(ARR_NONEMPTY, "family", '{ "id": "c" }')
    data = json.loads(out)
    assert [e["id"] for e in data["family"]] == ["a", "b", "c"]
    assert '{ "id": "a" }' in out  # "a" untouched


def test_array_append_empty_array():
    import json
    out = site_cli.array_append_in_text(ARR_EMPTY, "items", '{ "id": "x" }')
    assert json.loads(out)["items"] == [{"id": "x"}]


def test_set_field_in_text_scoped():
    sample = ('{ "products": [\n'
              '  { "id": "p1", "tagline": "old" },\n'
              '  { "id": "p2", "tagline": "keep" }\n] }\n')
    out = site_cli.set_field_in_text(sample, "p1", "tagline", "new")
    assert '"tagline": "new"' in out
    assert '"tagline": "keep"' in out  # p2 untouched
    assert out.count('"tagline"') == 2


def test_set_field_in_text_missing_field_raises():
    import pytest
    sample = '{ "products": [ { "id": "p1", "tagline": "x" } ] }\n'
    with pytest.raises(ValueError):
        site_cli.set_field_in_text(sample, "p1", "nope", "y")


def test_product_skeleton_shape():
    import json
    obj = json.loads(site_cli.product_skeleton("vibe-demo", "Vibe Demo", "A demo.", True))
    assert obj == {
        "id": "vibe-demo", "title": "Vibe Demo", "tagline": "A demo.",
        "description": "", "tags": [], "status": "wip",
        "repo": "", "npm": "", "install": "", "claudeCode": True, "screenshots": [],
    }
