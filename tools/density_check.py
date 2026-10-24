#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v0.3 正文数字密度检查。

按 H2 分节统计"非算例正文"的数字密度（个/千汉字）：
排除 算例与误区、小结 两节，以及表格行、公式块、图片、引用框。
用法：python tools/density_check.py [--strict]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CH_FILES = sorted(
    p for p in ROOT.glob("*.md") if re.match(r"^(0[1-9]|1[0-8])-", p.name)
)
# 第 2/13/16 章（文件号 03/14/17）允许 200，其余 150
LIMITS = {3: 200, 14: 200, 17: 200}
DEFAULT_LIMIT = 150


def section_stats(body: str) -> tuple[int, int, int]:
    b = re.sub(r"\$\$.*?\$\$", "", body, flags=re.S)
    b = re.sub(r"(?m)^\|.*$", "", b)
    b = re.sub(r"!\[.*?\)", "", b)
    b = re.sub(r"(?m)^>.*$", "", b)
    cn = len(re.findall(r"[\u4e00-\u9fff]", b))
    dg = len(re.findall(r"[0-9]", b))
    runs = len(re.findall(r"(?:\d+[^\u4e00-\u9fff\n]{0,6}){3,}", b))
    return cn, dg, runs


def main() -> int:
    strict = "--strict" in sys.argv
    bad = 0
    total_cn = 0
    print(f"{'file':<30}{'汉字':>6}{'密度':>8}  说明")
    for p in CH_FILES:
        no = int(p.name[:2])
        limit = LIMITS.get(no, DEFAULT_LIMIT)
        text = p.read_text(encoding="utf-8")
        parts = re.split(r"(?m)^## ", text)
        cn_sum = dg_sum = runs_sum = 0
        worst = (0.0, "")
        for sec in parts[1:]:
            title = sec.split("\n", 1)[0].strip()
            body = sec.split("\n", 1)[1] if "\n" in sec else ""
            if re.match(r"[一二三四五六七八九十]+、(算例与误区|小结)", title):
                continue
            cn, dg, runs = section_stats(body)
            if cn < 80:
                continue
            density = dg / cn * 1000
            cn_sum += cn
            dg_sum += dg
            runs_sum += runs
            if density > worst[0]:
                worst = (density, title)
        total_cn += cn_sum
        density = dg_sum / cn_sum * 1000 if cn_sum else 0
        flags = []
        if density > limit:
            flags.append(f"超标(>{limit})")
            bad += 1
        if runs_sum:
            flags.append(f"数字串×{runs_sum}")
        print(f"{p.name:<30}{cn_sum:>6}{density:>8.0f}  {'; '.join(flags)}  最密节：{worst[1][:18]} {worst[0]:.0f}")
    print(f"\n非算例正文合计：{total_cn} 汉字")
    print(f"超标文件：{bad}")
    return 1 if (strict and bad) else 0


if __name__ == "__main__":
    raise SystemExit(main())
