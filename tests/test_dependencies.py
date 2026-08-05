"""Every third-party module this repo imports must be DECLARED.

Why this file exists. `tests/test_visual_diff.py` imported `yaml` to parse
`.github/workflows/*.yml`, PyYAML was not in `requirements.txt`, and every
workflow installs exactly `pip install -r requirements.txt pytest`. The suite
was green on a developer machine that happened to have PyYAML and RED in CI
with `ModuleNotFoundError`. The same shape sits in `rotate-theme.yml`, so the
unattended rotation would have aborted on every theme from 2026-09-01 onward,
and `rebuild-hub.yml` would have failed its gate on any push to `content/**`.

A local `pytest` is not the gate. This test is the part of the gate that can
run locally: it fails on the machine that has the module, which is the only
machine where the mistake is invisible.
"""
import ast
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = ROOT / "requirements.txt"

# Installed by its own workflow step, never from requirements.txt, and every
# importer of it degrades deliberately when it is absent (see
# theme-doctor.py's `_import_sync_playwright` and `--require-browser`).
INSTALLED_SEPARATELY = {"playwright"}

# Provided by the test runner itself.
TEST_ONLY = {"pytest", "_pytest", "py"}

# (script, module) pairs exempt because the script is a run-on-demand local
# tool no workflow invokes and no test imports, so declaring its dependency
# would make five CI jobs install a library none of them uses.
#
# The exemption is per PAIR and requires a reason, so it cannot quietly become
# a place to put a real miss. Nothing under tests/ may appear here: a test's
# dependency is by definition one CI needs, which is the whole defect this
# file exists for.
ON_DEMAND_ONLY = {
    ("build-fonts.py", "fontTools"):
        "builds woff2 from source TTFs; run by hand after changing a TTF, "
        "never by CI. The script's own docstring names the install line.",
}


def _declared() -> set[str]:
    names = set()
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        name = re.split(r"[=<>!~\[]", line, maxsplit=1)[0].strip().lower()
        if name:
            names.add(name)
    # Distribution name -> the module name it actually installs. Only the ones
    # that differ need an entry.
    aliases = {"pyyaml": "yaml", "pillow": "pil"}
    return {aliases.get(n, n) for n in names} | names


def _python_sources():
    for folder in ("scripts", "tests"):
        for path in sorted((ROOT / folder).rglob("*.py")):
            if "__pycache__" not in path.parts:
                yield path


def _top_level_imports(path: Path) -> set[str]:
    """Every module name imported anywhere in `path`, including inside
    functions — `import yaml` sat inside two test bodies, which is exactly
    where an undeclared import hides from a reader skimming the header."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:  # pragma: no cover - a broken file fails elsewhere
        return set()
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                out.add(node.module.split(".")[0])
    return out


def _is_stdlib(name: str) -> bool:
    if name in sys.stdlib_module_names:
        return True
    # Sibling modules in scripts/, imported by bare name because theme-doctor
    # and friends put SCRIPTS_DIR on sys.path.
    return (ROOT / "scripts" / f"{name}.py").exists()


@pytest.mark.parametrize("path", list(_python_sources()), ids=lambda p: p.name)
def test_every_third_party_import_is_declared_in_requirements(path):
    declared = _declared()
    undeclared = sorted(
        name for name in _top_level_imports(path)
        if not _is_stdlib(name)
        and name.lower() not in declared
        and name not in INSTALLED_SEPARATELY
        and name not in TEST_ONLY
        and (path.name, name) not in ON_DEMAND_ONLY
        and not (ROOT / f"{name}.py").exists()
    )
    assert not undeclared, (
        f"{path.relative_to(ROOT).as_posix()} imports {undeclared}, which "
        f"requirements.txt does not declare. Every workflow installs exactly "
        f"`pip install -r requirements.txt pytest`, so this passes locally and "
        f"fails in CI — and inside rotate-theme.yml it aborts the rotation."
    )


def test_the_workflows_all_install_from_requirements_rather_than_ad_hoc():
    """A workflow that runs pytest must install the declared set. If one grows
    its own `pip install <thing>` instead, the declaration above stops being
    the single source of truth and this test stops meaning anything."""
    for wf in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        text = wf.read_text(encoding="utf-8", errors="replace")
        if "pytest tests/" not in text and "-m pytest" not in text:
            continue
        assert "-r requirements.txt" in text, (
            f"{wf.name} runs pytest without installing requirements.txt"
        )


def test_pyyaml_specifically_is_declared():
    """Named on its own because it is the one that went red, and because a
    parametrized failure is easy to read past."""
    assert "yaml" in _declared(), (
        "PyYAML backs the workflow-parsing tests that pin the two visual-diff "
        "wirings; undeclared, it took PR CI red while local pytest stayed green"
    )


def test_the_on_demand_exemptions_stay_small_and_reasoned():
    """An allowlist without a rule becomes a drawer. Two rules: nothing under
    tests/ may be exempt (a test's dependency is by definition one CI needs),
    and every entry carries a reason."""
    for (script, module), reason in ON_DEMAND_ONLY.items():
        assert (ROOT / "scripts" / script).exists(), script
        assert not script.startswith("test_"), script
        assert len(reason) > 40, (script, module, "exemptions need a real reason")
        # ...and the script has to state the dependency itself, so someone
        # running it locally is not left to guess.
        text = (ROOT / "scripts" / script).read_text(encoding="utf-8")
        assert module.lower() in text.lower(), (script, module)
