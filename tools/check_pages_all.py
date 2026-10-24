#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render every page in chunks and report near-empty / heavily-filled pages."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "build" / "业余无线电实用数学物理-书稿.pdf"
WORK = ROOT / "build" / "_pages"
def _existing(paths):
    for item in paths:
        if not item:
            continue
        p = Path(item)
        if p.exists():
            return p
    return None


def _dsh_resources():
    local = os.environ.get("LOCALAPPDATA")
    return Path(local) / "Programs" / "DeepSeek Harness" / "resources" if local else None


_DSH = _dsh_resources()
NODE = _existing([
    os.environ.get("DSH_NODE"),
    shutil.which("node"),
    _DSH / "runtime" / "primary-runtime" / "dependencies" / "node" / "bin" / "node.exe" if _DSH else None,
])
CLI = _existing([
    os.environ.get("DSH_OFFICE_CLI"),
    _DSH / "app.asar.unpacked" / "dsh" / "node_modules" / "@deepseek-ai"
    / "libreoffice-kit" / "lib" / "cli.js" if _DSH else None,
])


def ink_ratio(path: Path) -> float:
    image = Image.open(path).convert("L")
    w, h = image.size
    pixels = image.load()
    dark = 0
    total = 0
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            total += 1
            if pixels[x, y] < 245:
                dark += 1
    return dark / total


def main():
    if WORK.exists():
        import shutil
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True, exist_ok=True)
    try:
        from pypdf import PdfReader
        page_count = len(PdfReader(str(PDF)).pages)
    except Exception:
        data = json.loads((ROOT / "build" / "_page_count.json").read_text()) if (
            ROOT / "build" / "_page_count.json").exists() else {}
        page_count = data.get("pages")
    if not page_count:
        raise SystemExit("cannot determine PDF page count")
    print(f"PDF pages: {page_count}")
    rows = []
    for start in range(1, page_count + 1, 40):
        end = min(start + 39, page_count)
        out = WORK / f"chunk-{start:03d}"
        pages = ",".join(str(i) for i in range(start, end + 1))
        proc = subprocess.run(
            [str(NODE), str(CLI), "render", "--input", str(PDF),
             "--output-dir", str(out), "--pages", pages, "--dpi", "96"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if proc.returncode != 0:
            print(f"chunk {start}-{end} FAILED: render exit {proc.returncode}")
            continue
        files = sorted(out.glob("page-*.png"))
        for i, f in enumerate(files):
            rows.append((start + i, ink_ratio(f)))
        print(f"chunk {start}-{end}: {len(files)} pages")

    rows.sort()
    low = sorted(rows, key=lambda r: r[1])[:15]
    print("lowest ink:")
    for n, r in low:
        print(f"  p{n:03d} {r*100:5.2f}%")
    sparse = [(n, r) for n, r in rows if r < 0.02 and n > 1]
    print("under 2% ink:", len(sparse), " ".join(f"p{n}" for n, _ in sparse))
    dense = [(n, r) for n, r in rows if r > 0.55]
    print("over 55% ink:", len(dense), " ".join(f"p{n}" for n, _ in dense))
    (ROOT / "build" / "_ink_report.json").write_text(
        json.dumps(rows), encoding="utf-8")


if __name__ == "__main__":
    main()
