import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import site_facts  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


def _load(name):
    return json.loads((FIX / name).read_text())


def test_number_word():
    assert site_facts.number_word(12) == "Twelve"
    assert site_facts.number_word(8) == "Eight"
    assert site_facts.number_word(99) == "99"  # past the table -> str


def test_derive_counts():
    f = site_facts.derive(
        _load("site_min.json"), _load("plugin_pages_min.json"), _load("supplement_min.json")
    )
    assert f["claude_plugins"] == 2          # vibe-alpha, thesis-beta (live + claudeCode)
    assert f["claude_plugins_word"] == "Two"
    assert f["claude_plugins_wip"] == 1      # vibe-wip
    assert f["family_count"] == 3
    assert f["windows_native_count"] == 1    # nativey (Windows tag, no claudeCode)


def test_live_plugin_names():
    f = site_facts.derive(
        _load("site_min.json"), _load("plugin_pages_min.json"), _load("supplement_min.json")
    )
    # prefixes stripped, capitalized, comma-joined, in source order
    assert f["live_plugin_names"] == "Alpha, Beta"


def test_supplement_merges_with_word_variants():
    f = site_facts.derive(
        _load("site_min.json"), _load("plugin_pages_min.json"), _load("supplement_min.json")
    )
    assert f["ms_store_releases"] == 3
    assert f["ms_store_releases_word"] == "Three"
    assert f["cmd_vibe-cartographer"] == 12
    assert f["cmd_vibe-cartographer_word"] == "Twelve"
    assert "_note" not in f  # underscore keys skipped


def test_resolve_tokens_replaces():
    out = site_facts.resolve_tokens(
        {"v": "{{fact:claude_plugins_word}} plugins", "n": ["{{fact:claude_plugins}}"]},
        {"claude_plugins_word": "Two", "claude_plugins": 2},
    )
    assert out["v"] == "Two plugins"
    assert out["n"] == ["2"]


def test_resolve_tokens_unknown_raises():
    import pytest
    with pytest.raises(KeyError):
        site_facts.resolve_tokens("{{fact:nope}}", {"claude_plugins": 2})


def test_real_facts_smoke():
    f = site_facts.facts()
    assert f["claude_plugins"] == 11       # live + claudeCode (added vibe-insights)
    assert f["family_count"] == 12         # plugin-pages family[] (added vibe-insights)
    assert f["widget_count"] == 1
    assert f["cmd_vibe-cartographer"] == 13  # derived live from data/plugin-stats.json (13 command files)
