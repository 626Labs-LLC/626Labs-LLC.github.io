"""asset-kind.mjs decides which release assets count as people getting an app.

The raw download_count on ROROROblox was ~99% installed copies polling
manifests. If a manifest name slips into the installer bucket, the audience
number inflates again without any error, so the names are pinned here.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def kinds(names):
    js = (
        "import {assetKind} from './scripts/asset-kind.mjs';"
        f"console.log(JSON.stringify({json.dumps(names)}.map(assetKind)))"
    )
    out = subprocess.run(["node", "--input-type=module", "-e", js], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_manifests_are_polling():
    names = ["known-issues.json", "known-issues.json.sig", "roblox-compat.json",
             "roblox-compat.json.sig", "plugins-catalog.json", "releases.win.json",
             "RELEASES"]
    assert set(kinds(names)) == {"polling"}


def test_installers_and_updates():
    assert kinds(["RORORO-win-Setup.exe", "RORORO-win-Portable.zip",
                  "RORORO-Sideload-x64-1.24.0.0.msix", "plugin.zip"]) == ["installer"] * 4
    assert kinds(["RORORO-1.31.0-delta.nupkg", "RORORO-1.31.0-full.nupkg"]) == ["update"] * 2


def test_unknown_assets_are_other():
    assert kinds(["dev-cert.cer", "notes.txt"]) == ["other", "other"]
