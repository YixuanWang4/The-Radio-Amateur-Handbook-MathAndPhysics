#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v0.2 结构一致性校验：公式/图/表编号顺序与引用、交叉章节、附录、习题。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CH_FILES = sorted(
    p for p in ROOT.glob("*.md") if re.match(r"^(0[1-9]|1[0-9]|2[0-5])-", p.name)
)

FIG_DEF = re.compile(r"!\[图 (\d+)-(\d+)[^\]]*\]\(figures/fig-(\d+)-(\d+)\.png\)")
FIG_REF = re.compile(r"图 (\d+)-(\d+)")
TAB_DEF = re.compile(r"\*\*表 (\d+)-(\d+)")
TAB_REF = re.compile(r"表 (\d+)-(\d+)")
F_DEF = re.compile(r"（F(\d+)-(\d+)）")
F_REF = re.compile(r"F(\d+)-(\d+)")
H2 = re.compile(r"^## (.+)$", re.M)
H1 = re.compile(r"^# (.+)$", re.M)


def main() -> int:
    problems: list[str] = []
    fig_defs: dict[int, set[int]] = {}
    tab_defs: dict[int, set[int]] = {}
    f_defs: dict[int, list[int]] = {}
    chapter_no: dict[str, int] = {}

    for p in CH_FILES:
        text = p.read_text(encoding="utf-8")
        key = int(p.name[:2])
        # 章节号：01 序章=0, 02..18 => 1..17, 19 结语, 20..25 附录
        if key == 1:
            ch = 0
        elif 2 <= key <= 18:
            ch = key - 1
        elif key == 19:
            ch = None
        else:
            ch = None
        chapter_no[p.name] = key

        if ch is not None:
            figs = [(int(a), int(b)) for a, b, c, d in FIG_DEF.findall(text)]
            if figs:
                nums = [b for a, b in figs]
                fig_defs[ch] = set(nums)
                if nums != list(range(1, len(nums) + 1)):
                    problems.append(f"{p.name}: 图编号不连续 {nums}")
                for a, b in figs:
                    if a != ch:
                        problems.append(f"{p.name}: 图 {a}-{b} 章号不符")
            tabs = [(int(a), int(b)) for a, b in TAB_DEF.findall(text)]
            if tabs:
                nums = [b for a, b in tabs]
                tab_defs[ch] = set(nums)
                if nums != sorted(nums):
                    problems.append(f"{p.name}: 表定义顺序错 {nums}")
        # 公式编号首次出现顺序
        seen: list[int] = []
        for a, b in F_DEF.findall(text):
            n = int(b)
            if n not in seen:
                seen.append(n)
        if seen and seen != sorted(seen):
            problems.append(f"{p.name}: 公式编号首次出现顺序错 {seen}")
            f_defs[ch if ch is not None else -1] = seen

        # 章节交叉引用
        for ref in re.findall(r"第\s*(\d+)\s*章", text):
            n = int(ref)
            if not (1 <= n <= 17):
                problems.append(f"{p.name}: 引用第 {n} 章超范围")

        # 习题数量
        if ch is not None and ch >= 1 and not p.name.startswith(("19", "20", "21", "22", "23", "24", "25")):
            ex = re.findall(r"(?m)^\d+\.\s", text)
            if len(ex) < 3:
                problems.append(f"{p.name}: 编号条目仅 {len(ex)} 条（查习题/自检）")

    # 图/表引用完整性
    for p in CH_FILES:
        text = p.read_text(encoding="utf-8")
        for a, b in FIG_REF.findall(text):
            a, b = int(a), int(b)
            if a in fig_defs and b not in fig_defs[a]:
                problems.append(f"{p.name}: 引用了不存在的图 {a}-{b}")
        for a, b in TAB_REF.findall(text):
            a, b = int(a), int(b)
            if a in tab_defs and b not in tab_defs[a]:
                problems.append(f"{p.name}: 引用了不存在的表 {a}-{b}")

    # 附录 D 章数
    d = (ROOT / "23-附录D-习题答案.md").read_text(encoding="utf-8")
    heads = re.findall(r"(?m)^## (第 \d+ 章|★ 第 \d+ 章|跨章)", d)
    if len(heads) != 18:
        problems.append(f"附录D：章目 {len(heads)} 个（应为 17 章 + 跨章）")
    for i in range(1, 18):
        if not any(str(i) in h for h in heads):
            problems.append(f"附录D：缺第 {i} 章")

    # 前作残留
    for p in CH_FILES:
        text = p.read_text(encoding="utf-8")
        if "前作" in text:
            problems.append(f"{p.name}: 前作×{text.count('前作')}")

    print("图定义:", {k: sorted(v) for k, v in sorted(fig_defs.items())})
    print("表定义:", {k: sorted(v) for k, v in sorted(tab_defs.items())})
    print(f"附录D 章目数: {len(heads)}")
    print()
    if problems:
        print("发现问题：")
        for x in problems:
            print(" -", x)
        return 1
    print("结构一致性：全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
