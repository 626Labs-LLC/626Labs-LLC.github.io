"""hub-reach-lib.mjs mirrors the widget's ranking and bounds the route search.

The node:test file is the real suite; this wrapper puts it under pytest, which
is what CI runs.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_hub_reach_lib_node_suite():
    out = subprocess.run(["node", "--test", "scripts/hub-reach-lib.test.mjs"], cwd=ROOT,
                         capture_output=True, text=True)
    if out.returncode != 0:
        print(out.stdout)
        print(out.stderr)
    assert out.returncode == 0
