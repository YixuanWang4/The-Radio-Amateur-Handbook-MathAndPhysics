#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static checks before layout, adapted to this book's contract."""

from __future__ import annotations

import re
from pathlib import Path

CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
FIG_REF_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
FORWARD = ["下一章", "后面会讲", "后面将讲", "后续章节", "下一节将介绍"]
AI_FLAVOUR = [
    "让我们一起", "值得注意的是", "总而言之", "综上所述",
    "首先，其次", "一方面，另一方面", "不难看出", "显然，", "易证",
]
OVERLAP_BLACKLIST = [
    "一百瓦的账", "骗过天调", "端馈不需要地",
    "剪短容易", "驻波表不是成绩单",
]
TARGET = {
    "序章": (2400, 3400),
    "结语": (1000, 1800),
    "第01章": (4200, 5800),
    "第02章": (4600, 6000),
    "第03章": (4400, 5800),
    "第04章": (4400, 5800),
    "第05章": (4300, 5800),
    "第06章": (4200, 5600),
    "第07章": (4600, 6000),
    "第08章": (4600, 6000),
    "第09章": (4800, 6400),
    "第10章": (4300, 5800),
    "第11章": (4600, 6000),
    "第12章": (4300, 5800),
    "第13章": (5000, 6400),
    "第14章": (4500, 6000),
    "第15章": (5000, 6400),
    "第16章": (4400, 5800),
    "第17章": (4400, 5800),
}


def chapter_key(name: str):
    m = re.match(r"^\d+-第(\d+)章", name)
    if m:
        return f"第{int(m.group(1)):02d}章"
    if "序章" in name:
        return "序章"
    if "结语" in name:
        return "结语"
    return None


def check(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    problems: list[str] = []
    key = chapter_key(path.name)
    chars = len(CHINESE_RE.findall(text))

    if key in TARGET:
        lo, hi = TARGET[key]
        if not (lo <= chars <= hi):
            problems.append(f"字数 {chars} 不在 {lo}–{hi} 范围")

    if not lines or not lines[0].startswith("# "):
        problems.append("首行不是一级标题")
    heads = [ln for ln in lines if ln.startswith("## ")]
    if key and key.startswith("第"):
        content_heads = [h for h in heads if re.match(r"^## [一二三四五六七八九十]+、", h)]
        if len(content_heads) < 5:
            problems.append(f"二级内容节只有 {len(content_heads)} 个（应 4–6 内容节 + 算例与误区 + 小结）")
        if not any("小结" in h for h in heads):
            problems.append("缺少“小结”一节")
        if key.startswith("第") and not any("算例" in h for h in heads):
            problems.append("缺少“算例与误区”一节")
    if "自检三问" not in text:
        problems.append("缺少“自检三问”")
    if text.count("$$") % 2 != 0:
        problems.append("$$ 标记不成对")
    if "$$" not in text and key and key.startswith("第"):
        problems.append("没有行间公式")
    if "习题" not in text and key and key.startswith("第"):
        problems.append("缺少习题")
    for image in FIG_REF_RE.findall(text):
        rel = image.strip()
        if not (path.parent / rel).exists():
            problems.append(f"图片文件不存在：{rel}")
    for word in FORWARD:
        if word in text:
            problems.append(f"跨章预告词：{word}")
    for word in AI_FLAVOUR:
        if word in text:
            problems.append(f"AI 腔/教材腔：{word}")
    for word in OVERLAP_BLACKLIST:
        if word in text:
            problems.append(f"前作标志性语句（需确认是否只引用）：{word}")
    return [f"{path.name} 约 {chars} 汉字"] + [f"  ! {p}" for p in problems]


def main():
    root = Path(__file__).resolve().parent.parent
    files = [
        p for p in sorted(root.glob("*.md"))
        if re.match(r"^(0[1-9]|1[0-9])-", p.name)
    ]
    total = 0
    bad = 0
    for p in files:
        lines = check(p)
        for line in lines:
            print(line)
        if any(line.strip().startswith("!") for line in lines):
            bad += 1
        m = re.search(r"约 (\d+) 汉字", lines[0])
        if m:
            total += int(m.group(1))
    print(f"\n共 {len(files)} 个文件，{total} 汉字，{bad} 个文件有待修问题")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
