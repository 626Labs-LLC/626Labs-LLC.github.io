"""scripts/draft-field-note.py writes model output to content/stories/, where a
push publishes anything that is not a draft. These pin the publishing fence
through render-hub's own frontmatter parser, not a re-implementation of it.
No test here calls draft(), so none needs the SDK or a credential.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


drafter = _load("draft_field_note", "draft-field-note.py")
render_hub = _load("render_hub_for_drafter", "render-hub.py")

FIELDS = {
    "title": 'Right Click PNG says "no" to newer files',
    "subtitle": "One sentence\nthat the model\nwrapped.",
    "tagline": "Short kicker.",
    "body_html": "<p>What shipped.</p>\n<h2>Why</h2>\n<p>Because.</p>",
}
RELEASE = {"repo": "estevanhernandez-stack-ed/RTClickPng", "tagName": "v0.1.2"}


def test_draft_is_fenced_as_a_draft_by_render_hubs_parser():
    fields, body = render_hub.parse_story_frontmatter(drafter.render(FIELDS, RELEASE, "2026-10-16"))
    assert fields["draft"] is True
    assert fields["published"] == "2026-10-16"
    assert fields["author"] == "Este Hernandez"
    assert "<h2>Why</h2>" in body


def test_frontmatter_values_survive_quotes_and_newlines():
    fields, _ = render_hub.parse_story_frontmatter(drafter.render(FIELDS, RELEASE, "2026-10-16"))
    assert fields["title"] == 'Right Click PNG says "no" to newer files'
    assert fields["subtitle"] == "One sentence that the model wrapped."


def test_the_source_release_is_recorded_in_the_draft():
    text = drafter.render(FIELDS, RELEASE, "2026-10-16")
    assert "estevanhernandez-stack-ed/RTClickPng@v0.1.2" in text
    assert "site.json only" in drafter.render(FIELDS, None, "2026-10-16")


def test_body_is_one_block_per_paragraph():
    fields = dict(FIELDS, body_html="<p>One.</p><h2>Two</h2>\n<p>Three <em>x</em>.</p>")
    _, body = render_hub.parse_story_frontmatter(drafter.render(fields, RELEASE, "2026-10-16"))
    assert "<p>One.</p>\n\n<h2>Two</h2>\n\n<p>Three <em>x</em>.</p>" in body


def test_fold_keeps_each_item_once_newest_wording_oldest_release():
    # Newest first, cumulative notes, the way Sanduhr's Mac releases read.
    releases = [
        {"tagName": "v3", "publishedAt": "2026-10-16T00:00:00Z",
         "body": "- **C.** new in v3.\n\n- **B.** reworded in v3.\n\n- **A.** shipped in v1."},
        {"tagName": "v2", "publishedAt": "2026-10-12T00:00:00Z",
         "body": "- **B.** first said in v2.\n- **A.** shipped in v1."},
        {"tagName": "v1", "publishedAt": "2026-10-01T00:00:00Z",
         "body": "- **A.** shipped in v1.\n\n### Updating\n\nRestart Explorer."},
    ]
    folded = drafter.fold_release_notes(releases)
    assert folded.count("**A.**") == 1 and folded.count("**B.**") == 1
    assert "reworded in v3" in folded and "first said in v2" not in folded
    v1, v2, v3 = folded.index("### v1"), folded.index("### v2"), folded.index("### v3")
    assert v3 < folded.index("**C.**") < v2 < folded.index("**B.**") < v1 < folded.index("**A.**")
    assert "Restart Explorer." in folded


def test_folded_release_gets_the_period_prompt_and_source():
    rel = {"repo": "o/r", "tagName": "v1..v3", "count": 3, "publishedAt": "2026-10-16T00:00:00Z",
           "url": "https://github.com/o/r/releases", "body": "### v3 (2026-10-16)\n\n- **C.** x"}
    _, user = drafter.build_prompt({"id": "p", "title": "P"}, rel)
    assert "3 releases, v1..v3" in user and "ONE note about the period" in user
    assert "o/r@v1..v3" in drafter.render(FIELDS, rel, "2026-10-16")


def test_template_section_is_the_field_note_only():
    section = drafter._template_section()
    assert section.startswith("## 1.")
    assert "## 2." not in section and "X / Twitter" not in section


def test_schema_asks_only_for_the_model_written_fields():
    assert set(drafter.SCHEMA["required"]) == {"title", "subtitle", "tagline", "body_html"}
    assert "draft" not in drafter.SCHEMA["properties"]
