# -*- coding: utf-8 -*-
"""Remove Electron product files. Run from repo root: py tools/purge_electron.py"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = [
    ROOT / "electron",
    ROOT / "mini.html",
    ROOT / "src" / "mini.ts",
    ROOT / "build" / "afterPack.js",
    ROOT / "scripts" / "release.mjs",
    ROOT / "scripts" / "release-reset.mjs",
    ROOT / "src" / "components" / "UpdateDialog.vue",
]

def main() -> None:
    for path in TARGETS:
        if not path.exists():
            print("skip missing", path.relative_to(ROOT))
            continue
        if path.is_dir():
            shutil.rmtree(path)
            print("removed dir", path.relative_to(ROOT))
        else:
            path.unlink()
            print("removed file", path.relative_to(ROOT))

if __name__ == "__main__":
    main()
