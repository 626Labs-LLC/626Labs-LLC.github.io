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


def test_screenshot_slug():
    assert site_cli.screenshot_slug("My Cool Shot!.PNG") == ("my-cool-shot", ".png")
    assert site_cli.screenshot_slug("x.jpeg") == ("x", ".jpeg")
    assert site_cli.screenshot_slug("....png") == ("shot", ".png")


def test_story_scaffold():
    fm = site_cli.story_scaffold("My First Note", "my-first-note")
    assert fm.startswith("---\n")
    assert 'title: "My First Note"' in fm
    assert "## My First Note" in fm
    assert "draft: true" in fm           # publishing fence — stays unpublished
    assert "id: my-first-note" in fm
    assert "published:" in fm            # render-hub requires title + published


def test_slugify():
    assert site_cli._slugify("My First Note!") == "my-first-note"
    assert site_cli._slugify("---") == "untitled"


# ── story publish: one step, the draft flip AND the page mapping ─────────
# Publishing used to be two files: the story's draft flip plus a hand-added
# line in content/page-archetypes.json. Forgetting the second turned the
# rebuild-hub gate red, and a fix commit touching only that file never
# re-ran it (decision 3O5ye5iWRykMr0j4me9s, pollinator 2026-09-28).

def test_publish_story_text_flips_only_the_frontmatter_draft_line():
    md = site_cli.story_scaffold("Note", "note") + "\ndraft: true appears in the body too\n"
    out = site_cli.publish_story_text(md)
    head, _, body = out.partition("---\n\n")
    assert "draft: false" in head and "draft: true" not in head
    assert "draft: true appears in the body too" in body


def test_publish_story_text_refuses_an_already_published_story():
    import pytest
    md = site_cli.publish_story_text(site_cli.story_scaffold("Note", "note"))
    with pytest.raises(ValueError):
        site_cli.publish_story_text(md)


def test_story_page_path_mirrors_render_hubs_slug_rule():
    md = site_cli.story_scaffold("Note", "note")
    assert site_cli.story_page_path(md, "2026-10-03-note.md") == "editorial/2026-10-03-note/index.html"
    with_slug = md.replace("id: note\n", "id: note\nslug: custom\n")
    assert site_cli.story_page_path(with_slug, "x.md") == "editorial/custom/index.html"
    offsite = md.replace("id: note\n", 'id: note\nexternal_url: "https://medium.com/x"\n')
    assert site_cli.story_page_path(offsite, "x.md") is None


def test_add_reading_mapping_is_a_text_edit_that_keeps_crlf_and_indent():
    src = ('{\r\n "$comment": "c",\r\n "index.html": "home",\r\n'
           ' "editorial/a/index.html": "reading",\r\n "conundrum.html": "product"\r\n}\r\n')
    out = site_cli.add_reading_mapping(src, "editorial/b/index.html")
    assert out == src.replace(
        ' "editorial/a/index.html": "reading",\r\n',
        ' "editorial/a/index.html": "reading",\r\n "editorial/b/index.html": "reading",\r\n')
    assert site_cli.add_reading_mapping(out, "editorial/b/index.html") == out


def test_publishing_every_draft_keeps_the_real_archetype_map_valid():
    """The end-to-end promise against the repo's own files: map every story
    that would get a page, and archetypes.validate() accepts the map."""
    import json
    import archetypes
    text = site_cli.PAGE_ARCHETYPES.read_bytes().decode("utf-8")
    for md_path in sorted(site_cli.STORIES.glob("*.md")):
        page = site_cli.story_page_path(md_path.read_text(encoding="utf-8"), md_path.name)
        if page:
            text = site_cli.add_reading_mapping(text, page)
    mapping = json.loads(text)
    for md_path in sorted(site_cli.STORIES.glob("*.md")):
        page = site_cli.story_page_path(md_path.read_text(encoding="utf-8"), md_path.name)
        if page:
            assert mapping[page] == "reading"


def test_rebuild_hub_reruns_on_the_archetype_map():
    yml = (ROOT / ".github" / "workflows" / "rebuild-hub.yml").read_text(encoding="utf-8")
    assert "- 'content/page-archetypes.json'" in yml
