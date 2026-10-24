#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v0.2 修订验收：风格违规、前作引用、字数、图引用、章首框。

用法：python tools/style_check.py [--strict]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CH_RE = re.compile(r"^(0[1-9]|1[0-9]|2[0-5])-")

BANNED = [
    "算账", "账本", "账面", "一笔账", "三笔账", "买单", "划算", "白捡", "白干",
    "吃掉", "露馅", "砍半", "威力", "魔法", "漂亮", "坑", "心里没底", "别急",
    "便宜", "藏不住", "吞", "兜住", "撑",
    "说白了", "一目了然", "硬算", "硬套", "撑起", "闭环", "抓手", "颗粒度", "赋能",
]
SOFT = ["这就", "其实", "正好", "恰好", "反而", "当然", "显然", "值得", "地图", "钥匙", "武器"]
SOFT_LIMIT = 2
DASH_LIMIT = 4
NOT_BUT_LIMIT = 2
REMEMBER_LIMIT = 1
THIS_IS_LIMIT = 1

# 每章目标字数 (文件序号 -> 范围)
WORD_TARGET = {
    "02": (2600, 2900), "03": (4400, 4600), "04": (3950, 4050),
    "05": (4000, 4250), "06": (4200, 4450), "07": (4250, 4500),
    "08": (4700, 5050),  # v0.7 连贯性重写后放宽
    "09": (4150, 4400), "10": (4450, 4700),
    "11": (4780, 4950), "12": (4550, 4700), "13": (4450, 4650),
    "14": (4850, 5100), "15": (4200, 4450), "16": (4500, 4750),
    "17": (4150, 4350), "18": (4150, 4400),
}

FIG_RE = re.compile(r"!\[[^\]]*\]\((figures/fig-[0-9]+-[0-9]+\.png)\)")


def cn_count(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def check_file(p: Path, strict: bool) -> tuple[list[str], list[str]]:
    text = p.read_text(encoding="utf-8")
    name = p.name
    issues: list[str] = []
    warns: list[str] = []
    appendix = name.startswith(("20-", "21-", "22-", "23-", "24-", "25-"))

    pre = text.count("前作")
    if pre:
        issues.append(f"前作×{pre}")
    ant = text.count("天线概述")
    if ant and name != "01-序章.md":
        issues.append(f"天线概述×{ant}")

    if "业余无线电数学物理方法" in text:
        issues.append("旧书名残留")
    if "业余无线电实用数学物理" in text:
        issues.append("正文出现书名")

    dash = text.count("——")
    if dash > DASH_LIMIT:
        (warns if appendix else issues).append(f"破折号×{dash}")

    if "！" in text:
        (warns if appendix else issues).append(f"感叹号×{text.count('！')}")

    for w in BANNED:
        n = text.count(w)
        if n:
            issues.append(f"禁用词「{w}」×{n}")

    for w in SOFT:
        n = text.count(w)
        if n > SOFT_LIMIT:
            (warns if appendix else issues).append(f"慎用「{w}」×{n}")

    for w, limit in (("记住", REMEMBER_LIMIT), ("这就是", THIS_IS_LIMIT)):
        n = text.count(w)
        if n > limit:
            issues.append(f"「{w}」×{n}")

    for pat in ("搬到", "搬进"):
        n = text.count(pat)
        if n:
            issues.append(f"「{pat}」×{n}")

    nb = len(re.findall(r"不是[^，。；]{1,20}而是", text))
    if nb > NOT_BUT_LIMIT:
        issues.append(f"不是…而是×{nb}")

    if "这一节落到" in text:
        issues.append(f"「这一节落到」×{text.count('这一节落到')}")

    if name.startswith("00"):
        return issues, warns

    # 图引用
    for m in FIG_RE.finditer(text):
        if not (ROOT / m.group(1)).exists():
            issues.append(f"缺图 {m.group(1)}")

    # 字数
    key = name[:2]
    cn = cn_count(text)
    if key in WORD_TARGET:
        lo, hi = WORD_TARGET[key]
        if not (lo <= cn <= hi):
            issues.append(f"字数 {cn}（目标 {lo}–{hi}）")

    # 章首框行数
    box = re.search(r"> \*\*这一章会用到\*\*[^\n]*(?:\n>[^\n]*)*", text)
    if box and box.group(0).count("\n") > 1:
        issues.append("章首框超过 1 行")
    return issues, warns


def main() -> int:
    strict = "--strict" in sys.argv
    files = sorted(p for p in ROOT.glob("*.md") if CH_RE.match(p.name))
    bad = 0
    total_cn = 0
    print(f"{'file':<34}{'汉字':>6}  问题")
    for p in files:
        cn = cn_count(p.read_text(encoding="utf-8"))
        if not p.name.startswith("00"):
            total_cn += cn
        issues, warns = check_file(p, strict)
        mark = "OK" if not issues else "FAIL"
        if issues:
            bad += 1
        text = "; ".join(issues) if issues else ""
        if warns:
            text += ("  " if text else "") + "警告: " + "; ".join(warns)
        print(f"{p.name:<34}{cn:>6}  {mark}  {text}")
    print(f"\n正文汉字合计（01–25）: {total_cn}")
    print(f"有问题的文件: {bad}")
    if strict and bad:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
