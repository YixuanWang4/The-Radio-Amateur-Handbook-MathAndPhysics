#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图组 1：第 0–9 章配图（25 张）。

运行：python tools/figs_part1.py
输出：figures/fig-0-1.png … figures/fig-9-3.png 与 figures/_contact_part1.png
风格沿用前作《天线概述》tools/make_figures.py：Pillow、SimHei、深蓝 #1F3A5F、
白底、S=2 超采样、自动裁白边、1600×1000。
"""

from __future__ import annotations

import math
import os
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)

W, H = 1600, 1000
S = 2
ACCENT = (31, 58, 95)
LIGHT = (232, 238, 245)
GRAY = (70, 70, 70)
MID = (130, 130, 130)
RED = (150, 70, 70)
FAINT = (205, 205, 205)
WHITE = (255, 255, 255)
def _find_font():
    candidates = [
        os.environ.get("FIG_FONT"),
        r"C:\Windows\Fonts\simhei.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for item in candidates:
        if item and Path(item).exists():
            return item
    raise FileNotFoundError(
        "找不到中文字体，请设置环境变量 FIG_FONT 指向一个中文字体文件"
    )


FONT_PATH = _find_font()

TITLE = 40
SUB = 27
LAB = 28
SMALL = 24
TINY = 21


def fnt(size):
    return ImageFont.truetype(FONT_PATH, int(size * S))


def canvas():
    img = Image.new("RGB", (W * S, H * S), "white")
    return img, ImageDraw.Draw(img)


def pt(x, y):
    return (float(x) * S, float(y) * S)


def line(d, points, fill=ACCENT, width=3):
    if len(points) < 2:
        return
    d.line([pt(x, y) for x, y in points], fill=fill, width=max(1, int(width * S)),
           joint="curve")


def arrow(d, p1, p2, fill=ACCENT, width=3, head=14):
    x1, y1 = p1
    x2, y2 = p2
    line(d, [p1, p2], fill, width)
    ang = math.atan2(y2 - y1, x2 - x1)
    h = head
    for sign in (-1, 1):
        ax = x2 - h * math.cos(ang + sign * 0.45)
        ay = y2 - h * math.sin(ang + sign * 0.45)
        line(d, [(x2, y2), (ax, ay)], fill, width)
    d.polygon([pt(x2, y2),
               pt(x2 - h * math.cos(ang + 0.45), y2 - h * math.sin(ang + 0.45)),
               pt(x2 - h * math.cos(ang - 0.45), y2 - h * math.sin(ang - 0.45))],
              fill=fill)



SCRIPT_SCALE = 0.68


def _parse_rich(s):
    """把 V_rms / 10^-6 / e^(-t/tau) 解析为 [(kind, text)]，kind: 0 正常, 1 上标, -1 下标。"""
    segs = []
    buf = []
    i, n = 0, len(s)

    def flush():
        if buf:
            segs.append((0, "".join(buf)))
            buf.clear()

    while i < n:
        ch = s[i]
        if ch in "_^":
            j = i + 1
            content = None
            end = j
            if j < n and s[j] == "{":
                k = s.find("}", j + 1)
                if k != -1:
                    content, end = s[j + 1:k], k + 1
            elif j < n and s[j] == "(":
                depth = 0
                k = j
                while k < n:
                    if s[k] == "(":
                        depth += 1
                    elif s[k] == ")":
                        depth -= 1
                        if depth == 0:
                            content, end = s[j + 1:k], k + 1
                            break
                    k += 1
            if content is None:
                m = re.match(r"[+\-]?[A-Za-z0-9Α-ω]+", s[j:])
                if m:
                    content, end = m.group(0), j + m.end()
            if content is not None:
                flush()
                segs.append((1 if ch == "^" else -1, content))
                i = end
                continue
        buf.append(ch)
        i += 1
    flush()
    return segs


def text(d, xy, s, size=28, fill=GRAY, anchor="mm"):
    if not any(c in s for c in "_^"):
        d.text(pt(*xy), s, font=fnt(size), fill=fill, anchor=anchor)
        return
    segs = _parse_rich(s)
    if all(k == 0 for k, _ in segs):
        d.text(pt(*xy), s, font=fnt(size), fill=fill, anchor=anchor)
        return
    # 含上下标：逐段绘制
    lines = [[]]
    for kind, txt in segs:
        for pi, part in enumerate(txt.split("\n")):
            if pi:
                lines.append([])
            if part:
                lines[-1].append((kind, part))
    asc, desc = fnt(size).getmetrics()
    line_h = size * S * 1.32
    total_h = line_h * len(lines)
    h_anchor = anchor[0] if anchor else "m"
    v_anchor = anchor[1] if len(anchor) > 1 else "m"
    x, y = pt(*xy)
    if v_anchor == "m":
        block_top = y - total_h / 2
    elif v_anchor == "t":
        block_top = y
    elif v_anchor == "b":
        block_top = y - total_h
    else:
        block_top = y - asc
    for li, line in enumerate(lines):
        widths = []
        for kind, txt in line:
            fs = size * (SCRIPT_SCALE if kind else 1.0)
            widths.append(fnt(fs).getlength(txt))
        tw = sum(widths)
        if h_anchor == "l":
            sx = x
        elif h_anchor == "r":
            sx = x - tw
        else:
            sx = x - tw / 2
        baseline = block_top + li * line_h + asc
        for (kind, txt), w in zip(line, widths):
            fs = size * (SCRIPT_SCALE if kind else 1.0)
            off = 0
            if kind == 1:
                off = -size * S * 0.26
            elif kind == -1:
                off = size * S * 0.16
            d.text((sx, baseline + off), txt, font=fnt(fs), fill=fill, anchor="ls")
            sx += w


def box(d, x1, y1, x2, y2, s, size=LAB, fill=LIGHT, outline=ACCENT,
        text_fill=ACCENT, width=3, radius=14):
    d.rounded_rectangle([pt(x1, y1), pt(x2, y2)], radius=radius * S,
                        fill=fill, outline=outline, width=max(1, int(width * S)))
    text(d, ((x1 + x2) / 2, (y1 + y2) / 2), s, size=size, fill=text_fill)


def dot(d, x, y, r=7, fill=ACCENT):
    d.ellipse([pt(x - r, y - r), pt(x + r, y + r)], fill=fill)


def dashed_path(d, points, fill=MID, width=2, dash=16, gap=10):
    if len(points) < 2:
        return
    on, left = True, dash
    for i in range(1, len(points)):
        p0, p1 = points[i - 1], points[i]
        seg = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        if seg < 1e-9:
            continue
        t0 = 0.0
        while seg - t0 > 1e-9:
            step = min(left, seg - t0)
            t1 = t0 + step
            a = (p0[0] + (p1[0] - p0[0]) * t0 / seg,
                 p0[1] + (p1[1] - p0[1]) * t0 / seg)
            b = (p0[0] + (p1[0] - p0[0]) * t1 / seg,
                 p0[1] + (p1[1] - p0[1]) * t1 / seg)
            if on:
                line(d, [a, b], fill, width)
            t0 = t1
            left -= step
            if left <= 1e-9:
                on = not on
                left = dash if on else gap


def dashed_line(d, p1, p2, fill=MID, width=2, dash=16, gap=10):
    dashed_path(d, [p1, p2], fill, width, dash, gap)


def axis(d, x0, y0, x1, y1, fill=MID, width=2, head=12):
    arrow(d, (x0, y0), (x1, y0), fill, width, head)
    arrow(d, (x0, y0), (x0, y1), fill, width, head)


def axes_labels(d, xlabel, ylabel, x0, y0, x1, y1, size=SMALL):
    text(d, (x1 - 10, y0 + 50), xlabel, size, GRAY, "ra")
    text(d, (x0, y1 - 16), ylabel, size, GRAY, "mb")


def title(d, s, y=78, size=TITLE):
    text(d, (800, y), s, size, ACCENT)


def sub(d, s, y=140, size=SUB):
    text(d, (800, y), s, size, MID)


def poly(d, xs, ys, fill=ACCENT, width=3):
    line(d, [(float(x), float(y)) for x, y in zip(xs, ys)], fill, width)


def save(img, name):
    img = img.resize((W, H), Image.LANCZOS)
    mask = img.convert("L").point(lambda p: 255 if p < 250 else 0)
    bbox = mask.getbbox()
    if bbox:
        pad = 26
        img = img.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                        min(W, bbox[2] + pad), min(H, bbox[3] + pad)))
    img.save(OUT / name)
    print("wrote", OUT / name)


# ---------------------------------------------------------------- 0-1 三种答案
def fig_0_1():
    img, d = canvas()
    title(d, "同一个信号的三种答案")
    sub(d, "40 m 波段 · 100 W · 20 m 偶极 · 1000 km 外")
    items = [
        (120, 500, "① 经验", "“一千公里，正常”", "快，但不知道为什么"),
        (610, 990, "② 公式", "链路预算 -70 dBm", "能算，但依赖假设"),
        (1100, 1480, "③ 场", "电流→辐射→接收", "最慢，但每步可查"),
    ]
    for x1, x2, head, mid, tail in items:
        box(d, x1, 230, x2, 420, head + "\n" + mid, 27)
        text(d, ((x1 + x2) / 2, 470), tail, TINY, MID)
    arrow(d, (310, 432), (640, 600), ACCENT, 3, 15)
    arrow(d, (800, 432), (800, 590), ACCENT, 3, 15)
    arrow(d, (1290, 432), (960, 600), ACCENT, 3, 15)
    box(d, 480, 620, 1120, 770, "同一件事：接收功率约 -70 dBm\n差别只在各自假设", 27)
    text(d, (800, 855), "先问：这三种答案，各自靠什么假设？", 26, ACCENT)
    save(img, "fig-0-1.png")


# ---------------------------------------------------------------- 1-1 量纲三步
def fig_1_1():
    img, d = canvas()
    title(d, "量纲检查三步法")
    sub(d, "代数字之前，先让单位走一遍")
    steps = [(110, 490, "① 写公式"), (610, 990, "② 走单位链"), (1110, 1490, "③ 反查量级")]
    for x1, x2, s in steps:
        box(d, x1, 250, x2, 390, s, 30)
    arrow(d, (500, 320), (598, 320), ACCENT, 3, 14)
    arrow(d, (1000, 320), (1098, 320), ACCENT, 3, 14)
    texts = [
        "λ = 300 / f\n300 的单位：m·MHz",
        "m·MHz ÷ MHz = m\n300/7.05 ≈ 42.6 m",
        "42.6 m 是 20 m 偶极的\n两倍：量级合理",
    ]
    for (x1, x2, _), s in zip(steps, texts):
        text(d, ((x1 + x2) / 2, 500), s, 23, GRAY)
    text(d, (800, 660), "错例：f 代成 Hz，300/f 得 4.3×10^-5 —— 差 10^6 倍", 26, RED)
    text(d, (800, 760), "单位对不上，先别算数：多半是公式的隐藏单位没抓出来", 24, MID)
    save(img, "fig-1-1.png")


# ---------------------------------------------------------------- 1-2 平方反比
def fig_1_2():
    img, d = canvas()
    title(d, "平方反比：功率翻倍，距离只增 1.41 倍")
    x0, y0, x1, y1 = 240, 820, 1460, 230
    axis(d, x0, y0, x1, y1)
    axes_labels(d, "距离 r（相对）", "功率密度 S（相对）", x0, y0, x1, y1)
    # 坐标映射
    def X(r):
        return x0 + (r - 0.8) / (4.2 - 0.8) * (x1 - x0 - 30)

    def Y(s):
        return y0 - s / 1.1 * (y0 - y1 - 20)

    for r in (1, 1.41, 2, 3, 4):
        x = X(r)
        line(d, [(x, y0), (x, y0 + 8)], MID, 2)
        text(d, (x, y0 + 30), f"{r:g}", TINY, GRAY)
    for s in (0.25, 0.5, 0.75, 1.0):
        y = Y(s)
        line(d, [(x0 - 8, y), (x0, y)], MID, 2)
        text(d, (x0 - 14, y), f"{s:g}", TINY, GRAY, "rm")
    rs = np.linspace(1.0, 4.2, 300)
    poly(d, [X(r) for r in rs], [Y(1 / r ** 2) for r in rs], ACCENT, 4)
    text(d, (1120, 300), "S = P / (4πr^2)", 28, ACCENT)
    # 固定接收功率的对照线
    y = Y(0.5)
    dashed_line(d, (X(1.0), y), (X(1.41), y), RED, 2)
    dashed_line(d, (X(1.0), y), (X(1.0), Y(1.0)), RED, 2)
    dot(d, X(1.0), y, 7, RED)
    dot(d, X(1.41), y, 7, RED)
    arrow(d, (X(1.0), y - 26), (X(1.41), y - 26), RED, 2, 12)
    text(d, ((X(1.0) + X(1.41)) / 2, y + 36), "距离 ×1.41", 23, RED)
    arrow(d, (X(1.0) + 30, Y(0.5)), (X(1.0) + 30, Y(1.0)), RED, 2, 12)
    text(d, (X(1.0) + 44, Y(0.88)), "功率 ×2", 23, RED, "lm")
    text(d, (800, 905), "固定接收功率：P 翻倍，r 只能增 √2 ≈ 1.41 倍", 24, MID)
    save(img, "fig-1-2.png")


# ---------------------------------------------------------------- 2-1 dB 刻度盘
def fig_2_1():
    img, d = canvas()
    title(d, "dB 与倍数：一张心算刻度盘")
    sub(d, "每 +3 dB ≈ ×2；每 +10 dB = ×10")
    cx, cy, r = 800, 790, 330
    d.arc([pt(cx - r, cy - r), pt(cx + r, cy + r)], start=180, end=360,
          fill=ACCENT, width=4 * S)
    marks = [(0, "0 dB\n×1"), (3, "3 dB\n×2"), (6, "6 dB\n×4"),
             (10, "10 dB\n×10"), (20, "20 dB\n×100")]
    for db, label in marks:
        a = math.radians(180 - db / 20 * 180)
        x1, y1 = cx + (r - 16) * math.cos(a), cy - (r - 16) * math.sin(a)
        x2, y2 = cx + (r + 8) * math.cos(a), cy - (r + 8) * math.sin(a)
        line(d, [(x1, y1), (x2, y2)], ACCENT, 4)
        lx, ly = cx + (r + 55) * math.cos(a), cy - (r + 55) * math.sin(a)
        text(d, (lx, ly), label, 25, GRAY)
    text(d, (800, 640), "功率比：10lg", 30, ACCENT)
    text(d, (800, 700), "幅度/场强比：20lg", 25, MID)
    text(d, (800, 885), "-3 dB = 功率减半；-10 dB = 只剩十分之一", 24, MID)
    text(d, (800, 930), "心算先记 3、6、10、20 四个点，其余用加法拼", 23, MID)
    save(img, "fig-2-1.png")


# ---------------------------------------------------------------- 2-2 链路瀑布
def fig_2_2():
    img, d = canvas()
    title(d, "链路预算是一条加法链（40 m / 1000 km）")
    top, bot = 200, 850
    y = lambda v: bot - (v + 80) / 140 * (bot - top)
    ax = 160
    arrow(d, (ax, bot), (ax, top), MID, 2, 12)
    line(d, [(ax, bot), (ax + 1200, bot)], MID, 2)
    for v in (40, 0, -40, -80):
        yy = y(v)
        line(d, [(ax - 8, yy), (ax, yy)], MID, 2)
        text(d, (ax - 14, yy), f"{v:+d}", TINY, GRAY, "rm")
    text(d, (ax - 14, top - 24), "电平（dBm）", TINY, GRAY, "lm")
    # 阶梯：50 → 52.15 → 50.65 → -58.85 → -56.7
    levels = [50, 52.15, 50.65, -58.85, -56.7]
    xs = [220, 400, 580, 760, 940, 1180]
    for i, v in enumerate(levels):
        yy = y(v)
        line(d, [(xs[i], yy), (xs[i + 1], yy)], ACCENT, 4)
        if i < len(levels) - 1:
            line(d, [(xs[i + 1], yy), (xs[i + 1], y(levels[i + 1]))], ACCENT, 3)
    # 标签
    text(d, ((xs[0] + xs[1]) / 2, y(50) + 38), "+50 dBm 发射", 23, GRAY)
    text(d, ((xs[1] + xs[2]) / 2, y(52.15) - 34), "＋2.15 天线增益", 23, GRAY)
    text(d, ((xs[2] + xs[3]) / 2, y(50.65) - 34), "-1.5 馈线", 23, GRAY)
    text(d, (600, y(-58.85) - 30), "-109.5 自由空间损耗", 23, GRAY)
    text(d, ((xs[4] + xs[5]) / 2, y(-56.7) + 40), "＋2.15 接收增益", 23, GRAY)
    # 终值
    dashed_line(d, (xs[5], y(-56.7)), (1360, y(-56.7)), RED, 2)
    dot(d, 1360, y(-56.7), 7, RED)
    text(d, (1300, y(-56.7) - 40), "-56.7 dBm", 28, RED)
    text(d, (800, 905), "这是自由空间上限；实际传播再加 10–25 dB 损耗", 24, MID)
    save(img, "fig-2-2.png")


# ---------------------------------------------------------------- 3-1 正弦三要素
def fig_3_1():
    img, d = canvas()
    title(d, "正弦量的三个要素")
    sub(d, "幅度、频率、相位：改一个旋钮，波形变一种样子")
    panels = [
        (70, 520, "幅度 A"),
        (575, 1025, "频率 f"),
        (1075, 1525, "相位 φ"),
    ]
    for x1, x2, s in panels:
        d.rounded_rectangle([pt(x1, 200), pt(x2, 720)], radius=14 * S,
                            fill=(250, 251, 253), outline=FAINT, width=2 * S)
        text(d, ((x1 + x2) / 2, 246), s, 31, ACCENT)
    # 幅度
    x1, x2 = panels[0][0], panels[0][1]
    base = 565
    xs = np.linspace(x1 + 40, x2 - 40, 300)
    amp_big = 90
    ys = base - amp_big * np.sin((xs - (x1 + 40)) / (x2 - x1 - 80) * 2 * math.pi * 2)
    poly(d, xs, ys, ACCENT, 4)
    ys2 = base - 55 * np.sin((xs - (x1 + 40)) / (x2 - x1 - 80) * 2 * math.pi * 2)
    poly(d, xs, ys2, MID, 2)
    # 振幅箭头移到波形左端之外，标签放到第一个波峰上方的空白处，避开曲线与箭头
    arrow(d, (x1 + 22, base), (x1 + 22, base - amp_big), MID, 2, 10)
    text(d, (x1 + 32, base - amp_big - 35), "峰值 A", 22, MID, "lm")
    text(d, ((x1 + x2) / 2, 695), "峰值大小", 23, GRAY)
    # 频率
    x1, x2 = panels[1][0], panels[1][1]
    xs = np.linspace(x1 + 40, x2 - 40, 300)
    ys = base - 85 * np.sin((xs - (x1 + 40)) / (x2 - x1 - 80) * 2 * math.pi * 2)
    poly(d, xs, ys, ACCENT, 4)
    ys2 = base - 85 * np.sin((xs - (x1 + 40)) / (x2 - x1 - 80) * 2 * math.pi * 3)
    dashed_path(d, [(float(a), float(b)) for a, b in zip(xs, ys2)], MID, 2, 12, 8)
    text(d, ((x1 + x2) / 2, 695), "疏密：周期 T，f = 1/T", 23, GRAY)
    # 相位
    x1, x2 = panels[2][0], panels[2][1]
    xs = np.linspace(x1 + 40, x2 - 40, 300)
    ph = (xs - (x1 + 40)) / (x2 - x1 - 80) * 2 * math.pi * 2
    ys = base - 85 * np.sin(ph)
    ys2 = base - 85 * np.sin(ph + math.pi / 4)
    poly(d, xs, ys, ACCENT, 4)
    dashed_path(d, [(float(a), float(b)) for a, b in zip(xs, ys2)], MID, 2, 12, 8)
    arrow(d, (x1 + 150, base - 120), (x1 + 205, base - 120), MID, 2, 10)
    text(d, (x1 + 180, base - 155), "相位差 φ", 22, MID)
    text(d, ((x1 + x2) / 2, 695), "左右平移", 23, GRAY)
    text(d, (800, 805), "v(t) = V_p · sin(ωt + φ)", 32, ACCENT)
    text(d, (800, 880), "ω = 2πf；相位 φ 的单位是弧度，也要会看度", 23, MID)
    save(img, "fig-3-1.png")


# ---------------------------------------------------------------- 3-2 复平面相量
def fig_3_2():
    img, d = canvas()
    title(d, "相量：复平面上的旋转箭头")
    sub(d, "θ = ωt + φ：相角随时间增加")
    cx, cy, r = 720, 600, 260
    arrow(d, (cx - 370, cy), (cx + 430, cy), MID, 2, 12)
    arrow(d, (cx, cy + 330), (cx, cy - 360), MID, 2, 12)
    text(d, (cx + 405, cy + 34), "实轴 Re", SMALL, GRAY)
    text(d, (cx + 54, cy - 340), "虚轴 Im", SMALL, GRAY)
    d.ellipse([pt(cx - r, cy - r), pt(cx + r, cy + r)], outline=FAINT, width=2 * S)
    ang = math.radians(40)
    px, py = cx + r * math.cos(ang), cy - r * math.sin(ang)
    arrow(d, (cx, cy), (px, py), ACCENT, 4, 16)
    dashed_line(d, (px, py), (px, cy), MID, 2)
    dashed_line(d, (px, py), (cx, py), MID, 2)
    text(d, ((cx + px) / 2, cy + 34), "cosθ", 24, MID)
    text(d, (cx - 55, (cy + py) / 2), "j sinθ", 24, MID)
    # 角度弧
    arc_pts = [(cx + 90 * math.cos(math.radians(a)), cy - 90 * math.sin(math.radians(a)))
               for a in np.linspace(0, 40, 30)]
    poly(d, [p[0] for p in arc_pts], [p[1] for p in arc_pts], ACCENT, 2)
    text(d, (cx + 112, cy - 58), "θ", 26, ACCENT)
    # 旋转箭头
    rot = [(cx + 300 * math.cos(math.radians(a)), cy - 300 * math.sin(math.radians(a)))
           for a in np.linspace(50, 115, 40)]
    poly(d, [p[0] for p in rot], [p[1] for p in rot], MID, 2)
    arrow(d, rot[-6], rot[-1], MID, 2, 12)
    text(d, (cx + 265, cy - 305), "逆时针旋转 ω", 24, MID)
    text(d, (1180, 250), "e^(jθ) = cosθ + j sinθ", 29, ACCENT)
    text(d, (800, 895), "相量不是瞬时波形：它把“幅度 + 相位”装进一个旋转箭头", 24, MID)
    save(img, "fig-3-2.png")


# ---------------------------------------------------------------- 3-3 阻抗轨迹
def fig_3_3():
    img, d = canvas()
    title(d, "阻抗轨迹：串联 RLC 沿一条竖线移动")
    sub(d, "Z = R + jX；改变频率主要改 X，R 基本不变")
    x0, y0, x1, y1 = 280, 600, 1440, 210
    arrow(d, (x0 - 120, y0), (x1, y0), MID, 2, 12)
    arrow(d, (x0, y0 + 320), (x0, y1), MID, 2, 12)
    text(d, (x1 - 10, y0 + 38), "电阻 R（Ω）", SMALL, GRAY, "ra")
    text(d, (x0 - 18, y1 + 8), "电抗 X（Ω）", SMALL, GRAY, "rb")
    X = lambda R: x0 + R / 80 * (x1 - x0 - 30)
    Y = lambda x: y0 - x / 160 * (y0 - y1 - 20)
    for R in (0, 20, 40, 60, 80):
        xx = X(R)
        line(d, [(xx, y0 - 8), (xx, y0 + 8)], MID, 2)
        text(d, (xx, y0 + 30), f"{R}", TINY, GRAY)
    for xv in (-120, -80, -40, 0, 40, 80, 120):
        yy = Y(xv)
        line(d, [(x0 - 8, yy), (x0, yy)], MID, 2)
        text(d, (x0 - 14, yy if xv else yy - 12), f"{xv:+d}" if xv else "0", TINY, GRAY, "rm")
    # 竖线 R=36
    xr = X(36)
    line(d, [(xr, Y(-160)), (xr, Y(160))], ACCENT, 5)
    arrow(d, (xr + 26, Y(-60)), (xr + 26, Y(120)), ACCENT, 3, 14)
    text(d, (xr + 40, Y(70)), "f 升高 →", 24, ACCENT, "lm")
    text(d, (xr - 14, Y(-120)), "容性区\nX < 0", 23, MID, "rm")
    text(d, (xr - 14, Y(120)), "感性区\nX > 0", 23, MID, "rm")
    dot(d, xr, Y(0), 8, RED)
    text(d, (xr + 20, Y(0) - 30), "f0：X = 0（谐振）", 25, RED, "lm")
    dot(d, xr, Y(-120), 8, RED)
    text(d, (xr + 30, Y(-120) + 34), "7.05 MHz：36 - j120 Ω", 24, RED, "lm")
    save(img, "fig-3-3.png")


# ---------------------------------------------------------------- 4-1 导数
def fig_4_1():
    img, d = canvas()
    title(d, "导数 = 切线斜率 = 变化率")
    x0, y0, x1, y1 = 250, 780, 1400, 220
    axis(d, x0, y0, x1, y1)
    axes_labels(d, "x", "y", x0, y0, x1, y1)
    X = lambda x: x0 + x / 4.3 * (x1 - x0 - 30)
    Y = lambda y: y0 - y / 4.5 * (y0 - y1 - 20)
    for xv in (1, 2, 3, 4):
        line(d, [(X(xv), y0 - 8), (X(xv), y0 + 8)], MID, 2)
        text(d, (X(xv), y0 + 28), f"{xv}", TINY, GRAY)
    for yv in (1, 2, 3, 4):
        line(d, [(x0 - 8, Y(yv)), (x0, Y(yv))], MID, 2)
        text(d, (x0 - 14, Y(yv)), f"{yv}", TINY, GRAY, "rm")
    xs = np.linspace(0, 4.1, 220)
    poly(d, [X(x) for x in xs], [Y(x * x / 4) for x in xs], ACCENT, 4)
    # 切线 y = x - 1（过 x=2, y=1）
    tangent = [(1.0, 0.0), (3.2, 2.2)]
    dashed_line(d, (X(tangent[0][0]), Y(tangent[0][1])),
                (X(tangent[1][0]), Y(tangent[1][1])), RED, 3, 18, 10)
    dot(d, X(2), Y(1), 8, ACCENT)
    text(d, (X(2) - 20, Y(1) - 34), "P", 26, ACCENT, "rm")
    # 三角形
    dashed_line(d, (X(2), Y(1)), (X(3), Y(1)), MID, 2)
    dashed_line(d, (X(3), Y(1)), (X(3), Y(2.25)), MID, 2)
    text(d, ((X(2) + X(3)) / 2, Y(1) + 30), "Δx", 23, MID)
    text(d, (X(3) + 18, (Y(1) + Y(2.25)) / 2), "Δy", 23, MID, "lm")
    text(d, (1080, 330), "切线斜率 = Δy/Δx", 27, RED)
    text(d, (1080, 380), "Δx→0 时就是导数", 23, MID)
    text(d, (800, 885), "单位：y 的单位 / x 的单位（变化率也带单位）", 24, MID)
    save(img, "fig-4-1.png")


# ---------------------------------------------------------------- 4-2 积分/RMS
def fig_4_2():
    img, d = canvas()
    title(d, "积分是累积；RMS 是均方根")
    # 左：正弦积分
    x1, x2 = 110, 740
    base = 620
    xs = np.linspace(0, 2 * math.pi, 300)
    px = x1 + (xs / (2 * math.pi)) * (x2 - x1)
    py = base - 120 * np.sin(xs)
    for i in range(len(xs) - 1):
        if math.sin(xs[i]) >= 0 and math.sin(xs[i + 1]) >= 0:
            d.polygon([pt(px[i], py[i]), pt(px[i + 1], py[i + 1]),
                       pt(px[i + 1], base), pt(px[i], base)], fill=LIGHT)
    line(d, [(x1, base), (x2, base)], MID, 2)
    poly(d, px, py, ACCENT, 4)
    text(d, (425, 320), "① 积分 = 曲线下的面积", 27, ACCENT)
    text(d, (425, 700), "把每一小段的贡献累加起来", 23, MID)
    # 右：sin² 的平均
    x1, x2 = 840, 1470
    xs = np.linspace(0, 2 * math.pi, 300)
    px = x1 + (xs / (2 * math.pi)) * (x2 - x1)
    py = base - 120 * np.sin(xs) ** 2
    line(d, [(x1, base), (x2, base)], MID, 2)
    poly(d, px, py, ACCENT, 4)
    dashed_line(d, (x1, base - 60), (x2, base - 60), RED, 2)
    text(d, (1155, 470), "平均值 = 1/2", 23, RED)
    text(d, (1155, 320), "② RMS = √(平均值)", 27, ACCENT)
    arrow(d, (1155, base - 60), (1155, base - 110), MID, 2, 10)
    text(d, (1175, base - 86), "均方根", 22, MID, "lm")
    text(d, (800, 800), "V_rms = V_p/√2 ≈ 0.707 V_p（只对正弦）", 30, ACCENT)
    text(d, (800, 870), "∫ sinθ dθ 从 0 到 π = 2；RMS 先平方、再平均、再开方", 23, MID)
    save(img, "fig-4-2.png")


# ---------------------------------------------------------------- 4-3 趋肤深度
def fig_4_3():
    img, d = canvas()
    title(d, "铜的趋肤深度随频率下降")
    x0, y0, x1, y1 = 250, 820, 1430, 240
    axis(d, x0, y0, x1, y1)
    axes_labels(d, "频率 f（MHz，对数）", "趋肤深度 δ（μm）", x0, y0, x1, y1)
    lf0, lf1 = math.log10(1.0), math.log10(30.0)
    X = lambda f: x0 + (math.log10(f) - lf0) / (lf1 - lf0) * (x1 - x0 - 30)
    Y = lambda dv: y0 - dv / 55 * (y0 - y1 - 20)
    for f in (1, 2, 3, 5, 7, 10, 20, 30):
        xx = X(f)
        line(d, [(xx, y0 - 8), (xx, y0 + 8)], MID, 2)
        text(d, (xx, y0 + 28), f"{f}", TINY, GRAY)
    for dv in (0, 10, 20, 30, 40, 50):
        yy = Y(dv)
        line(d, [(x0 - 8, yy), (x0, yy)], MID, 2)
        text(d, (x0 - 14, yy), f"{dv}", TINY, GRAY, "rm")
    fs = np.linspace(1.0, 30.0, 300)
    poly(d, [X(f) for f in fs], [Y(66 / math.sqrt(f)) for f in fs], ACCENT, 4)
    pts = [(1.8, 66 / math.sqrt(1.8)), (7, 66 / math.sqrt(7)),
           (28, 66 / math.sqrt(28))]
    labels = [("1.8 MHz：约 49 μm", 16, -46, "lm"),
              ("7 MHz：约 25 μm", 14, -32, "lm"),
              ("28 MHz：约 12.5 μm", -10, 36, "rm")]
    for (f, dv), (s, dx, dy, anchor) in zip(pts, labels):
        x, y = X(f), Y(dv)
        dot(d, x, y, 7, RED)
        text(d, (x + dx, y + dy), s, 23, RED, anchor)
    text(d, (1150, 300), "δ ≈ 66/√f（μm，f 以 MHz 计）", 27, ACCENT)
    text(d, (800, 900), "频率越高，电流越挤在导体表面，有效截面越小", 24, MID)
    save(img, "fig-4-3.png")


# ---------------------------------------------------------------- 5-1 一阶
def fig_5_1():
    img, d = canvas()
    title(d, "一阶电路：时间常数 τ 决定快慢")
    x0, y0, x1, y1 = 260, 780, 1410, 240
    axis(d, x0, y0, x1, y1)
    axes_labels(d, "时间 t（以 τ 为单位）", "电压 / 电流（归一化）", x0, y0, x1, y1)
    X = lambda t: x0 + t / 5 * (x1 - x0 - 30)
    Y = lambda v: y0 - v / 1.12 * (y0 - y1 - 20)
    for t in (1, 2, 3, 4, 5):
        line(d, [(X(t), y0 - 8), (X(t), y0 + 8)], MID, 2)
        text(d, (X(t), y0 + 30), f"{t}τ", TINY, GRAY)
    for v in (0.25, 0.5, 0.63, 0.95, 1.0):
        line(d, [(x0 - 8, Y(v)), (x0, Y(v))], MID, 2)
        text(d, (x0 - 14, Y(v)), f"{v:g}", TINY, GRAY, "rm")
    ts = np.linspace(0, 5, 300)
    poly(d, [X(t) for t in ts], [Y(1 - math.exp(-t)) for t in ts], ACCENT, 4)
    # 63% 与 95%
    for t, v, lab in ((1, 0.632, "1τ：63%"), (3, 0.950, "3τ：95%")):
        dashed_line(d, (X(t), y0), (X(t), Y(v)), RED, 2)
        dashed_line(d, (x0, Y(v)), (X(t), Y(v)), RED, 2)
        dot(d, X(t), Y(v), 7, RED)
        # 标签放到点右下方的空白区，避开充电曲线与 0.95 / 1.0 水平虚线
        text(d, (X(t) + 26, Y(v) + 46), lab, 23, RED, "lm")
    dashed_line(d, (x0, Y(1.0)), (x1 - 40, Y(1.0)), MID, 2)
    text(d, (1340, Y(1.0) - 26), "稳态", 22, MID, "rm")
    text(d, (800, 885), "v = 1 - e^(-t/τ)；τ = RC 或 L/R", 28, ACCENT)
    text(d, (800, 930), "工程上记两点：1τ 到 63%，3τ 到 95%", 23, MID)
    save(img, "fig-5-1.png")


# ---------------------------------------------------------------- 5-2 阻尼
def fig_5_2():
    img, d = canvas()
    title(d, "二阶系统的三种结局")
    x0, y0, x1, y1 = 260, 790, 1400, 250
    axis(d, x0, y0, x1, y1)
    axes_labels(d, "时间（归一化）", "输出（归一化）", x0, y0, x1, y1)
    X = lambda t: x0 + t / 15 * (x1 - x0 - 30)
    Y = lambda v: y0 - v / 1.9 * (y0 - y1 - 20)
    dashed_line(d, (x0, Y(1.0)), (x1 - 30, Y(1.0)), MID, 2)
    text(d, (1360, Y(1.0) - 24), "稳态 1", 22, MID, "rm")
    ts = np.linspace(0, 15, 600)
    # 欠阻尼 ζ=0.2
    z = 0.2
    wd = math.sqrt(1 - z * z)
    y_under = 1 - np.exp(-z * ts) / wd * np.sin(wd * ts + math.acos(z))
    # 临界
    y_crit = 1 - np.exp(-ts) * (1 + ts)
    # 过阻尼 ζ=2
    z2 = 2.0
    s1, s2 = -z2 + math.sqrt(z2 * z2 - 1), -z2 - math.sqrt(z2 * z2 - 1)
    y_over = 1 - (s2 * np.exp(s1 * ts) - s1 * np.exp(s2 * ts)) / (s2 - s1)
    poly(d, [X(t) for t in ts], [Y(v) for v in y_under], ACCENT, 4)
    poly(d, [X(t) for t in ts], [Y(v) for v in y_crit], RED, 3)
    poly(d, [X(t) for t in ts], [Y(v) for v in y_over], MID, 3)
    text(d, (X(5.8), Y(0.55)), "欠阻尼：振荡", 24, ACCENT, "lm")
    text(d, (X(1.5), Y(0.08)), "临界阻尼：最快不振荡", 23, RED, "lm")
    text(d, (X(8.2), Y(1.35)), "过阻尼：慢", 23, MID, "lm")
    text(d, (800, 885), "ζ = 1/(2Q)；临界电阻 R = 2√(L/C)", 28, ACCENT)
    text(d, (800, 930), "R 小 → 振荡；R 大 → 爬得慢；临界只出现一次", 23, MID)
    save(img, "fig-5-2.png")


# ---------------------------------------------------------------- 5-3 谐振曲线
def fig_5_3():
    img, d = canvas()
    title(d, "Q 越高，谐振峰越尖、带宽越窄")
    x0, y0, x1, y1 = 260, 790, 1250, 250
    axis(d, x0, y0, x1, y1)
    axes_labels(d, "频率 f / f0", "相对幅度 |H|", x0, y0, x1, y1)
    X = lambda r: x0 + (r - 0.9) / 0.2 * (x1 - x0 - 20)
    Y = lambda v: y0 - v / 1.12 * (y0 - y1 - 20)
    for r in (0.90, 0.95, 1.00, 1.05, 1.10):
        line(d, [(X(r), y0 - 8), (X(r), y0 + 8)], MID, 2)
        text(d, (X(r), y0 + 30), f"{r:.2f}", TINY, GRAY)
    rs = np.linspace(0.9, 1.1, 500)
    info = []
    for Q in (10, 50, 100):
        h = 1 / np.sqrt(1 + Q * Q * (rs - 1 / rs) ** 2)
        poly(d, [X(r) for r in rs], [Y(v) for v in h], ACCENT if Q == 10 else MID, 4 if Q == 10 else 3)
        info.append((Q, h[-1]))
    dashed_line(d, (x0, Y(1 / math.sqrt(2))), (x1 - 30, Y(1 / math.sqrt(2))), RED, 2)
    text(d, (x0 + 20, Y(1 / math.sqrt(2)) - 22), "-3 dB（0.707）", 22, RED, "lm")
    # Q 标签
    for i, (Q, hv) in enumerate(info):
        ly = Y(hv) + (i - 1) * 34
        dashed_line(d, (X(1.099), ly), (X(1.1), Y(hv)), MID, 1)
        text(d, (1290, ly), f"Q={Q}", 23, ACCENT if Q == 10 else GRAY, "lm")
    # 带宽标注（Q=10）
    yb = Y(0.78)
    arrow(d, (X(0.95), yb), (X(1.05), yb), RED, 2, 10)
    arrow(d, (X(1.05), yb), (X(0.95), yb), RED, 2, 10)
    text(d, (X(0.918), yb - 40), "B = f0 / Q", 23, RED, "lm")
    text(d, (800, 890), "Q≥10 时 B = f0/Q；Q 越高，峰越尖、带宽越窄", 24, MID)
    text(d, (800, 930), "Q 是储能与损耗之比：损耗小，Q 高", 23, MID)
    save(img, "fig-5-3.png")


# ---------------------------------------------------------------- 6-1 四条定律
def fig_6_1():
    img, d = canvas()
    title(d, "麦克斯韦的四句话与电台器件")
    sub(d, "每条定律都对应电台里的一件东西")
    cells = [
        (110, 220, 730, 500, "① 高斯定律\n∮E·dA = Q/ε0\n对应：电容极板、静电场"),
        (870, 220, 1490, 500, "② 磁通连续\n∮B·dA = 0\n对应：磁环、同轴屏蔽"),
        (110, 570, 730, 850, "③ 法拉第定律\n∮E·dl = -dΦ_B/dt\n对应：变压器、加感线圈"),
        (870, 570, 1490, 850, "④ 安培—麦克斯韦\n∮B·dl = μ0I\n+ μ0ε0 dΦ_E/dt\n对应：馈线、位移电流"),
    ]
    for x1, y1, x2, y2, s in cells:
        box(d, x1, y1, x2, y2, s, 29)
    text(d, (800, 920), "四个积分号只是“把一圈或一面加起来”，不做推导", 23, MID)
    save(img, "fig-6-1.png")


# ---------------------------------------------------------------- 6-2 近场三区
def fig_6_2():
    img, d = canvas()
    title(d, "近场与远场：两个判据一起用")
    # 分区底色
    d.rectangle([pt(260, 280), pt(520, 790)], fill=(240, 244, 249))
    d.rectangle([pt(1030, 280), pt(1490, 790)], fill=(232, 238, 245))
    line(d, [(260, 790), (1490, 790)], MID, 3)
    for xb in (520, 1030):
        dashed_line(d, (xb, 280), (xb, 790), MID, 2)
    text(d, (390, 320), "反应近场", 26, ACCENT)
    text(d, (390, 362), "r < λ/2π", 24, ACCENT)
    text(d, (770, 320), "辐射近场（过渡）", 25, GRAY)
    text(d, (1260, 320), "远场", 26, ACCENT)
    text(d, (1260, 362), "r > 2D^2/λ\nr >> λ、r >> D", 22, ACCENT)
    # 天线
    line(d, [(260, 430), (260, 650)], ACCENT, 6)
    text(d, (260, 690), "天线", 23, GRAY)
    # 近场弧
    for rr in (80, 140, 200):
        d.arc([pt(260 - rr, 540 - rr), pt(260 + rr, 540 + rr)],
              start=180, end=360, fill=MID, width=2 * S)
    # 远场射线
    for dy in (-120, 0, 120):
        arrow(d, (260, 540), (1450, 540 + dy), ACCENT, 2, 12)
    text(d, (1200, 700), "E/H ≈ 377 Ω", 25, ACCENT)
    text(d, (420, 750), "近场 E/H ≠ 377 Ω", 22, MID)
    text(d, (800, 890), "方向图、增益、极化只在远场定义；HF 的近场可以延伸到几米", 24, MID)
    text(d, (800, 935), "反应近场看 r<λ/2π；远场要同时满足 r>2D^2/λ、r>>λ、r>>D", 23, MID)
    save(img, "fig-6-2.png")


# ---------------------------------------------------------------- 7-1 行波/驻波
def fig_7_1():
    img, d = canvas()
    title(d, "行波、反射波与驻波包络")
    left, right = 150, 1450
    # 入射波
    base1 = 290
    xs = np.linspace(0, 1, 600)
    yy = base1 - 80 * np.sin(xs * 2 * math.pi * 3)
    px = left + xs * (right - left)
    poly(d, px, yy, ACCENT, 4)
    arrow(d, (1060, 180), (1300, 180), ACCENT, 3, 14)
    text(d, (1180, 148), "入射波 →", 24, ACCENT)
    text(d, (left, 184), "① 行波", 26, ACCENT, "lm")
    # 反射波
    base2 = 540
    yy = base2 - 70 * np.sin(xs * 2 * math.pi * 3)
    poly(d, px, yy, MID, 4)
    arrow(d, (1300, 430), (1060, 430), MID, 3, 14)
    text(d, (1180, 402), "← 反射波", 24, MID)
    text(d, (left, 436), "② 反射波", 26, MID, "lm")
    # 驻波
    base3 = 790
    k = 3
    env = 105 * np.abs(np.cos(xs * 2 * math.pi * k / 2))
    poly(d, px, base3 - env, ACCENT, 3)
    poly(d, px, base3 + env, ACCENT, 3)
    yy = base3 - 105 * np.cos(xs * 2 * math.pi * k / 2) * np.sin(xs * 2 * math.pi * 14)
    dashed_path(d, [(float(a), float(b)) for a, b in zip(px, yy)], MID, 2, 10, 8)
    text(d, (left, 648), "③ 驻波：入射 + 反射", 26, ACCENT, "lm")
    text(d, (left + 286, 649), "实线：包络　虚线：瞬时电压", 21, MID, "lm")
    # 波节：包络在基线上捏合处（|V| 最小）；波腹：包络顶点（|V| 最大）
    for i in range(k):
        xx = left + (right - left) * (i + 0.5) / k
        d.ellipse([pt(xx - 6, base3 - 6), pt(xx + 6, base3 + 6)],
                  fill=MID, outline=WHITE, width=2 * S)
    for i in range(k + 1):
        xx = left + (right - left) * i / k
        dot(d, xx, base3 - 105, 6, RED)
    # 直接在节点/腹点位置标注
    line(d, [(800, base3 + 72), (800, base3 + 8)], MID, 2)
    text(d, (800, base3 + 88), "波节：电压最小", 22, MID)
    text(d, (left + (right - left) * 2 / k, base3 - 138), "波腹：电压最大", 22, RED)
    text(d, (800, 930), "SWR = Vmax / Vmin；反射越大，驻波越深", 26, ACCENT)
    save(img, "fig-7-1.png")


# ---------------------------------------------------------------- 7-2 Zin 随电长度
def fig_7_2():
    img, d = canvas()
    title(d, "输入阻抗随电长度旋转（ZL = 2Z0）")
    x0, y0, x1, y1 = 260, 790, 1250, 250
    axis(d, x0, y0, x1, y1)
    axes_labels(d, "电长度 βl", "|Zin| / Z0", x0, y0, x1, y1)
    X = lambda b: x0 + b / math.pi * (x1 - x0 - 20)
    Y = lambda v: y0 - v / 3.2 * (y0 - y1 - 20)
    ticks = [(0, "0"), (math.pi / 4, "λ/8"), (math.pi / 2, "λ/4"),
             (3 * math.pi / 4, "3λ/8"), (math.pi, "λ/2")]
    for b, s in ticks:
        line(d, [(X(b), y0 - 8), (X(b), y0 + 8)], MID, 2)
        text(d, (X(b), y0 + 30), s, TINY, GRAY)
    for v in (0.5, 1, 2, 3):
        line(d, [(x0 - 8, Y(v)), (x0, Y(v))], MID, 2)
        text(d, (x0 - 14, Y(v)), f"{v:g}", TINY, GRAY, "rm")
    bs = np.linspace(0, math.pi, 500)
    zl = 2.0
    vals = []
    for b in bs:
        t = math.tan(b)
        num = complex(zl, t)
        den = complex(1, zl * t)
        vals.append(abs(num / den))
    poly(d, [X(b) for b in bs], [Y(v) for v in vals], ACCENT, 4)
    # 两点
    dot(d, X(math.pi / 2), Y(0.5), 8, RED)
    dot(d, X(math.pi), Y(2.0), 8, RED)
    dashed_line(d, (X(math.pi / 2), y0), (X(math.pi / 2), Y(0.5)), RED, 2)
    text(d, (X(math.pi / 2) - 16, Y(0.5) + 44), "λ/4：Zin = Z0^2/ZL", 22, RED, "lm")
    dashed_line(d, (X(math.pi), y0), (X(math.pi), Y(2.0)), RED, 2)
    text(d, (X(math.pi) - 16, Y(2.0) + 40), "λ/2：Zin = ZL", 22, RED, "lm")
    text(d, (900, 360), "Zin = Z0 (ZL + jZ0 tanβl) / (Z0 + jZL tanβl)", 23, ACCENT)
    text(d, (800, 890), "λ/4 把阻抗倒过来；λ/2 原样搬回去；其余长度在两者之间", 24, MID)
    save(img, "fig-7-2.png")


# ---------------------------------------------------------------- 7-3 TDR
def fig_7_3():
    img, d = canvas()
    title(d, "TDR：反射时差换算故障距离")
    x0, y0, x1, y1 = 260, 760, 1400, 260
    axis(d, x0, y0, x1, y1)
    axes_labels(d, "时间（ns）", "反射电压（相对）", x0, y0, x1, y1)
    X = lambda t: x0 + t / 30 * (x1 - x0 - 30)
    Y = lambda v: y0 - v / 1.35 * (y0 - y1 - 20)
    for t in (0, 10, 20, 30):
        line(d, [(X(t), y0 - 8), (X(t), y0 + 8)], MID, 2)
        text(d, (X(t), y0 + 28), f"{t}", TINY, GRAY)
    # 入射阶跃与反射阶跃
    line(d, [(x0, Y(0)), (X(0), Y(0))], ACCENT, 3)
    line(d, [(X(0), Y(0)), (X(0), Y(0.5))], ACCENT, 4)
    line(d, [(X(0), Y(0.5)), (X(10), Y(0.5))], ACCENT, 4)
    line(d, [(X(10), Y(0.5)), (X(10), Y(0.85))], ACCENT, 4)
    line(d, [(X(10), Y(0.85)), (X(30), Y(0.85))], ACCENT, 4)
    dashed_line(d, (X(10), Y(0)), (X(10), Y(0.85)), RED, 2)
    dot(d, X(0), Y(0.5), 7, RED)
    dot(d, X(10), Y(0.85), 7, RED)
    # Δt 标尺
    yb = Y(1.18)
    arrow(d, (X(0), yb), (X(10), yb), RED, 2, 10)
    arrow(d, (X(10), yb), (X(0), yb), RED, 2, 10)
    text(d, ((X(0) + X(10)) / 2, yb - 30), "Δt = 10 ns", 24, RED)
    text(d, (800, 200), "d = VF · c · Δt / 2 = 0.66 × 3×10^8 × 10×10^-9 / 2 ≈ 0.99 m", 25, ACCENT)
    text(d, (800, 880), "反射来回走了两倍距离，所以时间差要除以 2", 24, MID)
    text(d, (800, 925), "换成 30 ns：d ≈ 3.0 m；先量时间，再谈剪线", 23, MID)
    save(img, "fig-7-3.png")


# ---------------------------------------------------------------- 8-1 失配损耗
def fig_8_1():
    img, d = canvas()
    title(d, "失配损耗 ML 随 SWR 的变化")
    x0, y0, x1, y1 = 260, 790, 1250, 250
    axis(d, x0, y0, x1, y1)
    axes_labels(d, "SWR（n:1）", "失配损耗 ML（dB）", x0, y0, x1, y1)
    X = lambda s: x0 + (s - 1) / 5 * (x1 - x0 - 20)
    Y = lambda v: y0 - v / 4.5 * (y0 - y1 - 20)
    for s in (1, 1.5, 2, 3, 4, 5, 6):
        line(d, [(X(s), y0 - 8), (X(s), y0 + 8)], MID, 2)
        text(d, (X(s), y0 + 30), f"{s:g}", TINY, GRAY)
    for v in (0, 1, 2, 3, 4):
        line(d, [(x0 - 8, Y(v)), (x0, Y(v))], MID, 2)
        text(d, (x0 - 14, Y(v)), f"{v}", TINY, GRAY, "rm")
    ss = np.linspace(1.0, 6.0, 400)
    ml = -10 * np.log10(1 - ((ss - 1) / (ss + 1)) ** 2)
    poly(d, [X(s) for s in ss], [Y(v) for v in ml], ACCENT, 4)
    marks = [(1.5, 0.177, "1.5：0.18 dB", 695),
             (2.0, 0.512, "2.0：0.51 dB", 660),
             (3.0, 1.249, "3.0：1.25 dB", 576),
             (5.0, 2.553, "5.0：2.55 dB", 432)]
    for s, v, lab, ly in marks:
        x, y = X(s), Y(v)
        dot(d, x, y, 7, RED)
        # 读数统一放在曲线上方的空白处，再用短虚线引到数据点
        dashed_line(d, (x, ly + 10), (x, y - 12), RED, 2, 8, 6)
        text(d, (x, ly), lab, 23, RED)
    text(d, (1260, 340), "ML = -10lg(1 - |Γ|^2)", 24, ACCENT)
    text(d, (1260, 388), "|Γ| = (SWR-1)/(SWR+1)", 22, MID)
    text(d, (800, 890), "SWR 1.5 只有 0.18 dB；回波损耗 RL 是另一个口径", 24, MID)
    save(img, "fig-8-1.png")


# ---------------------------------------------------------------- 8-2 Smith 圆图
def fig_8_2():
    img, d = canvas()
    title(d, "Smith 圆图：先记住三个端点")
    text(d, (800, 140), "圆心 Γ=0 表示匹配；圆周 |Γ|=1 表示全反射", 24, MID)
    cx, cy, r = 800, 520, 290
    line(d, [(cx - r - 80, cy), (cx + r + 80, cy)], MID, 2)
    line(d, [(cx, cy - r - 70), (cx, cy + r + 70)], MID, 2)
    d.ellipse([pt(cx - r, cy - r), pt(cx + r, cy + r)], outline=ACCENT, width=3 * S)
    for ang in (30, 60, 120, 150):
        a = math.radians(ang)
        line(d, [(cx, cy), (cx + r * math.cos(a), cy - r * math.sin(a))], FAINT, 1)
    dot(d, cx, cy, 8, ACCENT)
    text(d, (cx + 24, cy - 26), "50 Ω（匹配）", 25, ACCENT, "lm")
    dot(d, cx - r, cy, 8, RED)
    text(d, (cx - r - 16, cy + 34), "短路\nΓ = -1", 24, RED, "rm")
    dot(d, cx + r, cy, 8, RED)
    text(d, (cx + r + 16, cy + 34), "开路\nΓ = +1", 24, RED, "lm")
    text(d, (cx + 34, cy - r - 30), "感性 +jX", 25, GRAY, "lm")
    text(d, (cx + 34, cy + r + 34), "容性 -jX", 25, GRAY, "lm")
    text(d, (800, 905), "阻抗 → 反射系数 Γ → 图上一点", 23, MID)
    save(img, "fig-8-2.png")


# ---------------------------------------------------------------- 8-3 差模/共模
def fig_8_3():
    img, d = canvas()
    title(d, "差模与共模：扼流圈挡的是共模")
    # 天线
    line(d, [(520, 210), (800, 210)], ACCENT, 6)
    line(d, [(800, 210), (1080, 210)], ACCENT, 6)
    line(d, [(800, 210), (800, 250)], ACCENT, 4)
    text(d, (800, 185), "偶极两臂", 23, GRAY)
    # 同轴双线
    line(d, [(780, 250), (780, 800)], ACCENT, 4)
    line(d, [(820, 250), (820, 800)], ACCENT, 4)
    text(d, (740, 520), "同轴", 22, MID, "rm")
    # 差模箭头
    arrow(d, (780, 470), (780, 530), RED, 3, 12)
    arrow(d, (820, 530), (820, 470), RED, 3, 12)
    text(d, (850, 500), "差模：反向", 24, RED, "lm")
    # 共模箭头
    arrow(d, (780, 590), (780, 660), (120, 90, 40), 3, 12)
    arrow(d, (820, 590), (820, 660), (120, 90, 40), 3, 12)
    text(d, (850, 630), "共模：同向（外皮）", 24, (120, 90, 40), "lm")
    # 扼流圈
    for yy in (300, 336, 372):
        d.ellipse([pt(748, yy), pt(852, yy + 26)], outline=ACCENT, width=3 * S)
    text(d, (880, 340), "扼流圈（靠近天线端）", 24, ACCENT, "lm")
    # 电台
    box(d, 620, 800, 980, 880, "电台", 27)
    text(d, (800, 930), "差模电流在内外导体之间反向流；共模电流同向流在外皮上", 23, MID)
    save(img, "fig-8-3.png")


# ---------------------------------------------------------------- 9-1 电流/方向图
def fig_9_1():
    img, d = canvas()
    title(d, "半波偶极：电流分布与 E 面方向图")
    # 左：电流分布
    x1, x2, y0 = 120, 680, 470
    line(d, [(x1, y0), (x2, y0)], ACCENT, 5)
    line(d, [(400, y0), (400, y0 + 130)], ACCENT, 3)
    text(d, (400, y0 + 160), "馈电点（中心）", 23, MID)
    xs = np.linspace(x1, x2, 600)
    # 半波偶极、中心馈电：电流在中心（馈电点）最大，两端为零
    env = np.cos(np.pi * (xs - (x1 + x2) / 2) / (x2 - x1))
    poly(d, xs, y0 - 120 * env, RED, 4)
    dot(d, 400, y0 - 120, 7, RED)
    arrow(d, (400, y0 - 168), (400, y0 - 134), RED, 2, 10)
    text(d, (400, y0 - 188), "电流波腹（中心最大）", 23, RED)
    text(d, (x1, y0 + 42), "电流波节（两端为零）", 23, RED, "lm")
    text(d, (400, 225), "① 电流分布（驻波）", 27, ACCENT)
    # 右：E 面方向图
    cx, cy, sc = 1130, 500, 225
    line(d, [(cx - sc - 40, cy), (cx + sc + 120, cy)], FAINT, 2)
    th = np.linspace(0.001, 2 * math.pi - 0.001, 720)
    rr = np.abs(np.cos((math.pi / 2) * np.cos(th)) / np.sin(th))
    rr = rr / rr.max()
    px = cx + sc * rr * np.cos(th)
    py = cy - sc * rr * np.sin(th)
    poly(d, px, py, ACCENT, 4)
    text(d, (cx - sc - 50, cy - 18), "振子轴线", 21, MID, "rm")
    text(d, (cx + sc + 28, cy - 22), "零点", 23, MID, "lm")
    text(d, (cx, cy - sc + 84), "最大", 23, ACCENT)
    text(d, (1150, 225), "② E 面方向图（8 字形）", 27, ACCENT)
    text(d, (800, 890), "电流在两端为零、中心最大；远场方向图在导线方向为零点", 24, MID)
    text(d, (800, 935), "73 Ω 与 2.15 dBi 都来自同一组电流分布的积分", 23, MID)
    save(img, "fig-9-1.png")


# ---------------------------------------------------------------- 9-2 镜像
def fig_9_2():
    img, d = canvas()
    title(d, "极化：E 矢量端点的轨迹")
    panels = [(280, 500, "线极化"), (800, 500, "圆极化"), (1320, 500, "椭圆极化")]
    for cx, cy, s in panels:
        arrow(d, (cx - 210, cy), (cx + 210, cy), MID, 2, 10)
        arrow(d, (cx, cy + 190), (cx, cy - 190), MID, 2, 10)
        text(d, (cx + 200, cy + 30), "Ex", TINY, GRAY, "ra")
        text(d, (cx + 16, cy - 196), "Ey", TINY, GRAY, "lb")
        text(d, (cx, 250), s, 28, ACCENT)
    # 线
    cx, cy = panels[0][0], panels[0][1]
    line(d, [(cx - 150, cy + 150), (cx + 150, cy - 150)], ACCENT, 4)
    arrow(d, (cx + 60, cy - 60), (cx + 150, cy - 150), ACCENT, 3, 12)
    text(d, (cx + 42, cy + 205), "E 方向固定", 22, MID, "lm")
    # 圆
    cx, cy = panels[1][0], panels[1][1]
    d.ellipse([pt(cx - 160, cy - 160), pt(cx + 160, cy + 160)], outline=ACCENT, width=3 * S)
    arrow(d, (cx + 114, cy - 114), (cx + 155, cy - 60), ACCENT, 2, 10)
    text(d, (cx, cy + 205), "幅度相等、相位差 90°", 21, MID)
    # 椭圆
    cx, cy = panels[2][0], panels[2][1]
    d.ellipse([pt(cx - 175, cy - 100), pt(cx + 175, cy + 100)], outline=ACCENT, width=3 * S)
    arrow(d, (cx + 124, cy - 71), (cx + 170, cy - 30), ACCENT, 2, 10)
    text(d, (cx, cy + 205), "幅度不等或相位差不是 90°", 21, MID)
    text(d, (800, 890), "线/圆固定失配 3 dB；正交极化理论上为 0", 24, ACCENT)
    text(d, (800, 935), "短波经电离层后极化会旋转，本地与卫星链路才需严格对齐", 23, MID)
    save(img, "fig-9-2.png")


def fig_9_3():
    img, d = canvas()
    title(d, "地面镜像：符号规则决定仰角")
    ground = 620
    line(d, [(80, ground), (1520, ground)], ACCENT, 4)
    text(d, (1280, ground + 34), "地面", 22, MID)
    # 左：垂直
    xv = 400
    line(d, [(xv, ground), (xv, 340)], ACCENT, 6)
    line(d, [(xv, ground), (xv, 900)], (190, 200, 215), 4)
    arrow(d, (xv, 520), (xv, 440), RED, 3, 12)
    arrow(d, (xv + 24, 800), (xv + 24, 720), RED, 3, 12)
    text(d, (xv - 16, 470), "真实电流 ↑", 22, RED, "rm")
    text(d, (xv + 34, 770), "镜像同向 ↑", 22, RED, "lm")
    text(d, (xv, 300), "垂直天线", 26, ACCENT)
    text(d, (xv + 30, 870), "低仰角增强", 23, ACCENT, "lm")
    # 右：水平
    xh1, xh2 = 930, 1390
    yh = 360
    gimg = 2 * ground - yh
    line(d, [(xh1, yh), (xh2, yh)], ACCENT, 6)
    line(d, [(xh1, gimg), (xh2, gimg)], (190, 200, 215), 4)
    line(d, [(1250, yh), (1250, ground)], FAINT, 2)
    line(d, [(1250, ground), (1250, gimg)], FAINT, 2)
    text(d, (1266, (yh + ground) / 2), "h", 22, GRAY, "lm")
    text(d, (1266, (ground + gimg) / 2), "2h", 22, GRAY, "lm")
    arrow(d, (1030, yh), (1140, yh), RED, 3, 12)
    arrow(d, (1140, gimg), (1030, gimg), MID, 3, 12)
    text(d, (1010, yh - 34), "真实电流 →", 22, RED, "rm")
    text(d, (1010, gimg - 34), "← 镜像反向", 22, MID, "rm")
    text(d, (1200, 290), "水平天线", 26, ACCENT)
    text(d, (1330, 500), "沿地面相消\n能量上抬：高仰角", 22, ACCENT, "lm")
    text(d, (800, 925), "垂直镜像同向 → 低仰角；水平镜像反向 → 高仰角", 24, MID)
    text(d, (800, 965), "sinθ = λ/(4h) 只在水平极化、理想地面时作估算", 23, MID)
    save(img, "fig-9-3.png")


# ---------------------------------------------------------------- 9-3 极化


FIGURES = [
    ("fig-0-1.png", fig_0_1), ("fig-1-1.png", fig_1_1), ("fig-1-2.png", fig_1_2),
    ("fig-2-1.png", fig_2_1), ("fig-2-2.png", fig_2_2),
    ("fig-3-1.png", fig_3_1), ("fig-3-2.png", fig_3_2), ("fig-3-3.png", fig_3_3),
    ("fig-4-1.png", fig_4_1), ("fig-4-2.png", fig_4_2), ("fig-4-3.png", fig_4_3),
    ("fig-5-1.png", fig_5_1), ("fig-5-2.png", fig_5_2), ("fig-5-3.png", fig_5_3),
    ("fig-6-1.png", fig_6_1), ("fig-6-2.png", fig_6_2),
    ("fig-7-1.png", fig_7_1), ("fig-7-2.png", fig_7_2), ("fig-7-3.png", fig_7_3),
    ("fig-8-1.png", fig_8_1), ("fig-8-2.png", fig_8_2), ("fig-8-3.png", fig_8_3),
    ("fig-9-1.png", fig_9_1), ("fig-9-2.png", fig_9_2), ("fig-9-3.png", fig_9_3),
]


def contact_sheet(names):
    cols, rows = 5, 5
    cw, ch = 300, 188
    pad = 10
    label_h = 28
    header = 56
    cellw, cellh = cw + pad * 2, ch + label_h + pad * 2
    sheet = Image.new("RGB", (cols * cellw + pad, rows * cellh + pad + header), "white")
    dr = ImageDraw.Draw(sheet)
    dr.text((pad * 2, header // 2), "图组 1（第 0–9 章，25 张）contact sheet",
            font=fnt(22), fill=ACCENT, anchor="lm")
    for i, name in enumerate(names):
        c, r = i % cols, i // cols
        x0 = pad + c * cellw
        y0 = header + pad + r * cellh
        p = OUT / name
        if p.exists():
            im = Image.open(p).convert("RGB")
            im.thumbnail((cw, ch), Image.LANCZOS)
            ox = x0 + pad + (cw - im.width) // 2
            oy = y0 + pad + (ch - im.height) // 2
            sheet.paste(im, (ox, oy))
        dr.rectangle([x0 + pad, y0 + pad, x0 + pad + cw, y0 + pad + ch],
                     outline=FAINT, width=2)
        label = name.replace("fig-", "").replace(".png", "")
        dr.text((x0 + pad + cw // 2, y0 + pad + ch + label_h // 2), label,
                font=fnt(17), fill=GRAY, anchor="mm")
    out = OUT / "_contact_part1.png"
    sheet.save(out)
    print("wrote", out)


def main():
    for name, fn in FIGURES:
        fn()
    names = [n for n, _ in FIGURES]
    missing = [n for n in names if not (OUT / n).exists()]
    small = [n for n in names if (OUT / n).exists() and (OUT / n).stat().st_size < 5120]
    print(f"figures: {len(names) - len(missing)}/{len(names)}")
    if missing:
        print("MISSING:", missing)
    if small:
        print("SMALL(<5KB):", small)
    contact_sheet(names)
    print("done")


if __name__ == "__main__":
    main()
