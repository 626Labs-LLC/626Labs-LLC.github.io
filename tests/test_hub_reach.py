"""hub-reach-lib.mjs mirrors the widget's ranking and bounds the route search;
refresh-hub-reach.mjs is the weekly job built on it.

The node:test files are the real suites; this wrapper puts them under pytest,
which is what CI runs.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("suite", ["scripts/hub-reach-lib.test.mjs", "scripts/refresh-hub-reach.test.mjs"])
def test_hub_reach_node_suite(suite):
    out = subprocess.run(["node", "--test", suite], cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        print(out.stdout)
        print(out.stderr)
    assert out.returncode == 0
