"""Every public page counts its visits.

Field Notes shipped without GoatCounter from May to September (PR #139),
because theme-doctor never checked the reading shell. The product archetype
had the same blind spot, larger: until 2026-10-03, all 15 plugin pages,
/plugins/, the Sanduhr page, both Bacon Trail pages, the year in review,
404 and both legal pages shipped dark, while privacy.html told visitors
"every page on 626labs.dev" loads it. These two tests are PR #139's pair,
widened to the whole site: every registered theme's product shell carries
the snippet (the doctor's gate now requires it), and every committed public
page does.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import archetypes  # noqa: E402

SNIPPET = 'data-goatcounter="https://626labs.goatcounter.com/count"'


def _registered_slugs() -> list[str]:
    reg = json.loads((ROOT / "content" / "themes.json").read_text(encoding="utf-8"))
    return [reg["active"], *reg.get("queue", [])]


@pytest.mark.parametrize("slug", _registered_slugs())
def test_every_registered_themes_product_shell_carries_goatcounter(slug):
    shell = ROOT / "themes" / slug / "archetypes" / "product.html"
    assert SNIPPET in shell.read_text(encoding="utf-8"), (
        f"themes/{slug}/archetypes/product.html has no GoatCounter; "
        "ARCHETYPE_CHROME['product'] requires it, so this theme fails the doctor")


def test_every_committed_public_page_carries_goatcounter():
    dark = sorted(
        p for p in archetypes._public_pages(ROOT)
        if SNIPPET not in (ROOT / p).read_text(encoding="utf-8")
    )
    assert not dark, (
        f"{len(dark)} public page(s) ship without GoatCounter, so their visits "
        f"go uncounted and privacy.html's 'every page' is false: {dark}")


def test_the_product_archetype_gate_requires_analytics():
    import importlib.util
    spec = importlib.util.spec_from_file_location("td_analytics", ROOT / "scripts" / "theme-doctor.py")
    td = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(td)
    assert all(profile["analytics"] for profile in td.ARCHETYPE_CHROME.values()), (
        "every archetype's chrome profile requires analytics; one turned it off")
