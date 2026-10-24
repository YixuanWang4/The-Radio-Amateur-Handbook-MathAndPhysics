#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report near-empty pages from a rendered page directory."""

from pathlib import Path
import sys

from PIL import Image


def ink_ratio(path: Path):
    image = Image.open(path).convert("L")
    w, h = image.size
    pixels = image.load()
    dark = 0
    total = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            total += 1
            if pixels[x, y] < 245:
                dark += 1
    return dark / total


def main():
    folder = Path(sys.argv[1])
    files = sorted(folder.glob("page-*.png"))
    rows = []
    for f in files:
        number = int(f.stem.split("-")[-1])
        rows.append((number, ink_ratio(f)))
    print("pages:", len(rows))
    low = sorted(rows, key=lambda r: r[1])[:20]
    print("lowest ink ratio:")
    for number, ratio in low:
        print(f"  p{number:02d}  {ratio*100:.2f}%")
    sparse = [(n, r) for n, r in rows if r < 0.03 and n != 1]
    print("pages under 3% ink (excluding cover):", len(sparse))
    print(" ".join(f"p{n}" for n, _ in sparse))


if __name__ == "__main__":
    main()
