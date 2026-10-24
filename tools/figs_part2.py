#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二组配图（第 10-17 章，26 张）：fig-10-1 … fig-17-3。

风格与前作 tools/make_figures.py 一致：Pillow 自绘、SimHei、白底、
深蓝 #1F3A5F + 少量红/灰、S=2 超采样后缩回 1600x1000、保存前裁白边。
只输出到本工作区 figures/ 目录。
"""

from __future__ import annotations

import math
import os
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)

W, H = 1600, 1000
S = 2
ACCENT = (31, 58, 95)
LIGHT = (232, 238, 245)
GRAY = (70, 70, 70)
MID = (138, 138, 138)
FAINT = (205, 210, 218)
RED = (150, 70, 70)
BROWN = (140, 105, 60)
TEAL = (55, 105, 120)
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

NAMES = [
    "fig-10-1.png", "fig-10-2.png",
    "fig-11-1.png", "fig-11-2.png", "fig-11-3.png",
    "fig-12-1.png", "fig-12-2.png",
    "fig-13-1.png", "fig-13-2.png", "fig-13-3.png", "fig-13-4.png",
    "fig-14-1.png", "fig-14-2.png", "fig-14-3.png", "fig-14-4.png",
    "fig-15-1.png", "fig-15-2.png", "fig-15-3.png", "fig-15-4.png",
    "fig-15-5.png",
    "fig-16-1.png", "fig-16-2.png", "fig-16-3.png",
    "fig-17-1.png", "fig-17-2.png", "fig-17-3.png",
]


# ---------------------------------------------------------------- 基础函数
def fnt(size):
    return ImageFont.truetype(FONT_PATH, int(size * S))


def canvas():
    img = Image.new("RGB", (W * S, H * S), "white")
    return img, ImageDraw.Draw(img)


def pt(x, y):
    return (x * S, y * S)


def line(d, points, fill=ACCENT, width=3):
    d.line([pt(x, y) for x, y in points], fill=fill, width=int(width * S),
           joint="curve")


def dashed(d, p1, p2, fill=MID, width=2, dash=16, gap=11):
    x1, y1 = p1
    x2, y2 = p2
    length = math.hypot(x2 - x1, y2 - y1)
    if length <= 0:
        return
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        line(d, [(x1 + ux * pos, y1 + uy * pos),
                 (x1 + ux * end, y1 + uy * end)], fill, width)
        pos = end + gap


def arrow(d, p1, p2, fill=ACCENT, width=3, head=15):
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


def box(d, x1, y1, x2, y2, s="", size=28, fill=LIGHT, outline=ACCENT,
        width=3, txt=ACCENT):
    d.rounded_rectangle([pt(x1, y1), pt(x2, y2)], radius=9 * S, fill=fill,
                        outline=outline, width=int(width * S))
    if s:
        text(d, ((x1 + x2) / 2, (y1 + y2) / 2), s, size, txt)


def ellipse(d, cx, cy, rx, ry, fill=None, outline=ACCENT, width=3):
    d.ellipse([pt(cx - rx, cy - ry), pt(cx + rx, cy + ry)], fill=fill,
              outline=outline, width=int(width * S))


def dot(d, cx, cy, r=8, fill=ACCENT):
    d.ellipse([pt(cx - r, cy - r), pt(cx + r, cy + r)], fill=fill)


def title(d, s):
    text(d, (800, 76), s, 36, ACCENT)


def note(d, s, y=936):
    text(d, (800, y), s, 23, MID)


def save(img, name):
    img = img.resize((W, H), Image.LANCZOS)
    mask = img.convert("L").point(lambda p: 255 if p < 250 else 0)
    bbox = mask.getbbox()
    if bbox:
        pad = 26
        img = img.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                        min(W, bbox[2] + pad), min(H, bbox[3] + pad)))
    img.save(OUT / name)
    print("wrote", name, img.size)


def mx(v, v0, v1, x0, x1):
    return x0 + (v - v0) / (v1 - v0) * (x1 - x0)


def my(v, v0, v1, y0, y1):
    """v0 -> y0（下）, v1 -> y1（上）."""
    return y0 + (v - v0) / (v1 - v0) * (y1 - y0)


def polyline(d, pts, fill=ACCENT, width=3):
    line(d, pts, fill, width)


# ---------------------------------------------------------------- 第 10 章
def fig_10_1():
    img, d = canvas()
    title(d, "二元阵：路程差变成相位差")
    # 左：几何
    s1 = (350, 340)
    s2 = (350, 660)
    d_ax = s2[1] - s1[1]
    theta = math.radians(50)
    u = (math.sin(theta), -math.cos(theta))
    n = (math.cos(theta), math.sin(theta))
    ray_len = 360
    e1 = (s1[0] + ray_len * u[0], s1[1] + ray_len * u[1])
    e2 = (s2[0] + ray_len * u[0], s2[1] + ray_len * u[1])
    line(d, [s1, e1], ACCENT, 2)
    line(d, [s2, e2], ACCENT, 2)
    # 阵轴与元
    dashed(d, (350, 250), (350, 750), MID, 2, 10, 8)
    for sx, sy, lab in ((s1[0], s1[1], "源 1"), (s2[0], s2[1], "源 2")):
        line(d, [(sx - 90, sy), (sx + 90, sy)], ACCENT, 5)
        text(d, (sx + 130, sy), lab, 27, ACCENT, "lm")
    # 间距 d
    arrow(d, (300, s1[1]), (300, s2[1]), RED, 2, 11)
    arrow(d, (300, s2[1]), (300, s1[1]), RED, 2, 11)
    text(d, (268, (s1[1] + s2[1]) / 2), "d", 30, RED, "rm")
    # 角 theta
    arc_pts = []
    for i in range(0, 26):
        a = math.radians(270 + 50 * i / 25)
        arc_pts.append((s2[0] + 105 * math.cos(a), s2[1] + 105 * math.sin(a)))
    line(d, arc_pts, GRAY, 2)
    text(d, (420, 572), "θ", 28, GRAY)
    # Δr：从 s1 到射线 2 的垂足
    proj = (s1[0] - s2[0]) * u[0] + (s1[1] - s2[1]) * u[1]
    q = (s2[0] + proj * u[0], s2[1] + proj * u[1])
    dashed(d, s1, q, RED, 3, 12, 8)
    dot(d, q[0], q[1], 6, RED)
    text(d, (452, 470), "Δr = d·cosθ", 27, RED, "lm")
    text(d, (760, 180), "远场方向\n（两条射线近似平行）", 24, MID)
    # 右：极坐标阵因子
    cx, cy, R = 1170, 540, 225
    ellipse(d, cx, cy, R, R, None, FAINT, 2)
    ellipse(d, cx, cy, R / 2, R / 2, None, FAINT, 2)
    dashed(d, (cx - R, cy), (cx + R, cy), FAINT, 1, 8, 8)
    dashed(d, (cx, cy - R), (cx, cy + R), FAINT, 1, 8, 8)
    pts = []
    for i in range(0, 361):
        th = math.radians(i)
        af = abs(math.cos(math.pi / 2 * math.cos(th)))
        pts.append((cx + R * af * math.sin(th), cy - R * af * math.cos(th)))
    polyline(d, pts, ACCENT, 4)
    # −3 dB 方向与波束宽度
    for th in (60, 120):
        a = math.radians(th)
        dashed(d, (cx, cy), (cx + R * math.sin(a), cy - R * math.cos(a)),
               RED, 2, 8, 7)
    arc = []
    for i in range(0, 21):
        a = math.radians(60 + 60 * i / 20)
        arc.append((cx + 120 * math.sin(a), cy - 120 * math.cos(a)))
    line(d, arc, RED, 2)
    text(d, (cx + 150, cy + 40), "60°", 26, RED, "lm")
    text(d, (cx + R + 22, cy), "边射\n+3 dB", 24, ACCENT, "lm")
    text(d, (cx, cy - R - 32), "端射零点", 24, RED)
    text(d, (cx, cy + R + 34), "端射零点", 24, RED)
    text(d, (cx, 880), "阵因子：d=λ/2、同相馈电", 24, MID)
    note(d, "路程差 Δr 除以波长得到相位差，各方向叠加结果不同")
    save(img, "fig-10-1.png")


def fig_10_2():
    img, d = canvas()
    title(d, "八木：寄生单元让前方相加、后方相消")
    y = 520
    line(d, [(170, y), (1430, y)], MID, 6)
    text(d, (270, y + 46), "横梁", 24, MID)
    items = [
        (400, 430, "反射器\n（约长 5%）"),
        (760, 380, "激励器\n（半波）"),
        (1120, 320, "引向器\n（约短 5%–10%）"),
    ]
    for x, length, lab in items:
        line(d, [(x, y - length / 2), (x, y + length / 2)], ACCENT, 6)
        if x == 760:
            # 馈线从激励器中心向下引出，标签放到馈线左侧，避免竖线穿字
            text(d, (735, 776), lab, 25, GRAY, "rm")
        else:
            text(d, (x, y + length / 2 + 52), lab, 25, GRAY)
    # 馈线
    line(d, [(760, y), (760, y + 250)], ACCENT, 3)
    text(d, (800, y + 280), "馈线", 24, MID, "lm")
    # 相位小箭头
    for x, lab, cy, col in ((400, "电流滞后", y - 250, RED),
                            (760, "激励电流", y - 250, ACCENT),
                            (1120, "电流超前", y - 250, RED)):
        arrow(d, (x, cy + 60), (x, cy - 20), col, 2, 10)
        text(d, (x, cy - 45), lab, 23, col)
    # 前后抵消/叠加
    arrow(d, (300, 250), (120, 250), RED, 3, 14)
    text(d, (120, 210), "后方抵消", 25, RED, "lm")
    arrow(d, (1300, 250), (1480, 250), ACCENT, 3, 14)
    text(d, (1300, 210), "前方叠加", 25, ACCENT, "rm")
    arrow(d, (1200, 800), (1480, 800), ACCENT, 3, 14)
    text(d, (1200, 840), "最大辐射方向", 25, ACCENT, "rm")
    # 相位关系说明
    text(d, (800, 890), "无源单元靠感应电流再辐射：尺寸决定相位，间距决定叠加", 24, MID)
    note(d, "反射器再辐射场在后方相消、在前方相加，引向器把能量继续往前引")
    save(img, "fig-10-2.png")


# ---------------------------------------------------------------- 第 11 章
def fig_11_1():
    img, d = canvas()
    title(d, "方波 = 基波 + 三次 + 五次谐波")
    # 上：方波与三项和
    x0, x1 = 190, 1410
    yc, amp = 360, 130
    pts_sq, pts_sum = [], []
    for i in range(0, 1201):
        t = 2 * math.pi * 2 * i / 1200  # 两个周期
        x = x0 + (x1 - x0) * i / 1200
        sq = 1.0 if math.sin(t) >= 0 else -1.0
        pts_sq.append((x, yc - amp * sq))
        s = math.sin(t) + math.sin(3 * t) / 3 + math.sin(5 * t) / 5
        pts_sum.append((x, yc - amp * 4 / math.pi * s))
    dashed(d, (x0, yc), (x1 + 6, yc), FAINT, 2, 10, 8)
    polyline(d, pts_sq, FAINT, 3)
    polyline(d, pts_sum, ACCENT, 4)
    text(d, (200, 150), "理想方波（灰）", 23, MID, "lm")
    text(d, (200, 186), "前三次谐波之和（深蓝）", 23, ACCENT, "lm")
    # Gibbs 过冲
    arrow(d, (1230, 255), (1160, 222), RED, 2, 11)
    text(d, (1245, 215), "过冲约 9%", 23, RED, "lm")
    # 下：三条谐波
    yb = 720
    for n, a, yoff, lab in ((1, 4 / math.pi, 0, "基波 1.27"),
                            (3, 4 / math.pi / 3, 0, "三次 0.42"),
                            (5, 4 / math.pi / 5, 0, "五次 0.25")):
        col = ACCENT if n == 1 else (TEAL if n == 3 else BROWN)
        pts = []
        for i in range(0, 801):
            t = 2 * math.pi * 2 * i / 800
            x = x0 + (x1 - x0) * i / 800
            pts.append((x, yb - amp * a * math.sin(n * t) * 0.92))
        polyline(d, pts, col, 2)
    text(d, (x1 - 10, yb - 155), "基波 1.27（相对值）", 23, ACCENT, "rm")
    text(d, (x1 - 10, yb - 108), "三次谐波 0.42", 23, TEAL, "rm")
    text(d, (x1 - 10, yb - 70), "五次谐波 0.25", 23, BROWN, "rm")
    text(d, (330, yb - 160), "振幅", 24, GRAY)
    text(d, (x1 - 10, 876), "时间 →", 24, GRAY, "rm")
    note(d, "项数越多边沿越陡；过冲不会消失，只会变窄（Gibbs 现象）")
    save(img, "fig-11-1.png")


def fig_11_2():
    img, d = canvas()
    title(d, "占用带宽：同样一段频率，差几十倍")
    fc, scale = 790, 78  # 每 kHz 像素
    rows = [
        (265, "CW", "约 0.5 kHz", [(-0.25, 0.25, 78)], []),
        (430, "SSB", "约 2.4 kHz", [(0.3, 2.7, 90)], []),
        (595, "AM", "约 6 kHz", [(-3.0, -0.35, 55), (0.35, 3.0, 55)], [(0, 110)]),
        (760, "FM", "约 10 kHz", [(-5.0, 5.0, 62)], []),
    ]
    for y, name, lab, spans, carriers in rows:
        line(d, [(240, y + 80), (1400, y + 80)], FAINT, 2)
        for a, b, h in spans:
            xa, xb = fc + a * scale, fc + b * scale
            d.rounded_rectangle([pt(xa, y + 80 - h), pt(xb, y + 80)],
                                radius=6 * S, fill=LIGHT, outline=ACCENT,
                                width=2 * S)
            dashed(d, (xa, y + 80 - h), (xa, y + 80), ACCENT, 1, 6, 5)
            dashed(d, (xb, y + 80 - h), (xb, y + 80), ACCENT, 1, 6, 5)
        for c, h in carriers:
            xc = fc + c * scale
            line(d, [(xc, y + 80), (xc, y + 80 - h)], ACCENT, 4)
        text(d, (225, y + 40), name, 27, ACCENT, "rm")
        text(d, (1410, y + 40), lab, 24, GRAY, "lm")
    # 载波轴
    for v in (-6, -3, 0, 3, 6):
        x = fc + v * scale
        line(d, [(x, 848), (x, 862)], MID, 2)
        text(d, (x, 884), f"{v:+d}" if v else "0", 23, MID)
    text(d, (fc, 918), "离开载波的频率偏移（kHz）", 24, GRAY)
    text(d, (250, 918), "各行的中心载波对齐", 21, MID, "lm")
    note(d, "SSB 为单边带、AM 为双边带；同一段话音，占用带宽由调制方式决定", y=952)
    save(img, "fig-11-2.png")


def fig_11_3():
    img, d = canvas()
    title(d, "滤波器：幅度、相位、群时延三条曲线")
    x0, x1 = 300, 1420
    # 幅频面板
    yb1 = 378
    line(d, [(x0, yb1), (x1 + 10, yb1)], FAINT, 2)
    line(d, [(x0, yb1), (x0, 215)], GRAY, 2)
    pts = [(x0, 252), (1020, 252), (1080, 258), (1140, 276), (1200, 312),
           (1250, 352), (1300, 372), (x1, yb1)]
    polyline(d, pts, ACCENT, 4)
    text(d, (x0 - 16, 245), "幅度", 24, GRAY, "rm")
    text(d, (x0 + 20, 232), "通带", 23, GRAY, "lm")
    text(d, (1000, 330), "边沿滚降", 22, MID, "lm")
    text(d, (x0 + 20, 340), "-6 dB / -60 dB 处量带宽", 21, MID, "lm")
    # 相频面板
    yb2 = 590
    line(d, [(x0, yb2), (x1 + 10, yb2)], FAINT, 2)
    line(d, [(x0, yb2), (x0, 430)], GRAY, 2)
    pts = []
    for i in range(0, 201):
        t = i / 200
        xx = x0 + (x1 - x0) * t
        yy = 555 - 95 * t + 9 * math.sin((t - 0.5) * 9)
        pts.append((xx, yy))
    polyline(d, pts, ACCENT, 3)
    text(d, (x0 - 16, 445), "相位", 24, GRAY, "rm")
    text(d, (x0 + 10, 408), "通带内接近直线，边沿弯折", 23, GRAY, "lm")
    # 群时延面板
    yb3 = 800
    line(d, [(x0, yb3), (x1 + 10, yb3)], FAINT, 2)
    line(d, [(x0, yb3), (x0, 645)], GRAY, 2)
    pts = []
    for i in range(0, 201):
        t = i / 200
        xx = x0 + (x1 - x0) * t
        bump = 0.55 * math.exp(-((t - 0.44) ** 2) / 0.004) + \
               0.7 * math.exp(-((t - 0.62) ** 2) / 0.004)
        pts.append((xx, 762 - 95 * bump))
    polyline(d, pts, ACCENT, 3)
    text(d, (x0 - 16, 660), "群时延", 24, GRAY, "rm")
    text(d, (x0 + 10, 682), "τg = -dφ/dω；边沿凸起 → 振铃", 23, GRAY, "lm")
    text(d, (860, 850), "频率 →", 24, GRAY)
    text(d, (800, 895), "BW6 在 -6 dB 处量，BW60 在 -60 dB 处量；矩形系数 = BW60 / BW6",
         22, MID)
    note(d, "幅频决定选谁，相频与群时延决定波形会不会被拖尾")
    save(img, "fig-11-3.png")


# ---------------------------------------------------------------- 第 12 章
def fig_12_1():
    img, d = canvas()
    title(d, "用百分位读衰落：中值与两个尾巴")
    x0, x1, y0, y1 = 190, 850, 790, 250
    sigma = 1.0
    rmax = 3.4
    pdf = lambda r: (r / sigma ** 2) * math.exp(-r * r / (2 * sigma ** 2))
    pmax = pdf(sigma)
    pts = []
    for i in range(0, 341):
        r = rmax * i / 340
        pts.append((mx(r, 0, rmax, x0, x1), my(pdf(r), 0, pmax * 1.05, y0, y1)))
    # 左侧 10% 尾巴
    r10 = sigma * math.sqrt(-2 * math.log(0.9))
    r50 = sigma * math.sqrt(-2 * math.log(0.5))
    r90 = sigma * math.sqrt(-2 * math.log(0.1))
    for lo, hi, col in ((0, r10, (250, 225, 225)), (r90, rmax, (225, 232, 242))):
        seg = [(mx(lo, 0, rmax, x0, x1), y0)]
        for i in range(0, 61):
            r = lo + (hi - lo) * i / 60
            seg.append((mx(r, 0, rmax, x0, x1), my(pdf(r), 0, pmax * 1.05, y0, y1)))
        seg.append((mx(hi, 0, rmax, x0, x1), y0))
        d.polygon([pt(px, py) for px, py in seg], fill=col)
    polyline(d, pts, ACCENT, 4)
    line(d, [(x0, y0), (x1, y0)], GRAY, 2)
    line(d, [(x0, y0), (x0, y1 - 20)], GRAY, 2)
    for r, lab, yl in ((r10, "10% 分位", 842), (r50, "中值", 872),
                       (r90, "90% 分位", 842)):
        xx = mx(r, 0, rmax, x0, x1)
        dashed(d, (xx, y0), (xx, y1), RED if lab != "中值" else MID, 2, 9, 7)
        text(d, (xx, yl), lab, 23, GRAY)
    text(d, (x0 + 8, 238), "概率密度", 23, GRAY, "lm")
    text(d, (860, 812), "幅度 →", 23, GRAY, "lm")
    # 右侧解释
    text(d, (960, 300), "中值：一半时间低于它", 25, GRAY, "lm")
    text(d, (960, 370), "10% 分位：10% 时间低于它", 25, GRAY, "lm")
    text(d, (960, 440), "可当“门限”：低于它算中断", 23, MID, "lm")
    text(d, (960, 530), "90% 分位：只有 10% 时间超过", 25, GRAY, "lm")
    text(d, (960, 620), "衰落余量就从这两个数来", 24, MID, "lm")
    note(d, "把“某电平出现多少时间”变成百分位，才能比较两种方案")
    save(img, "fig-12-1.png")


def fig_12_2():
    img, d = canvas()
    title(d, "高斯与瑞利：一个对称，一个单边")
    # 左：高斯
    x0, x1, y0, y1 = 150, 700, 780, 270
    cx = (x0 + x1) / 2
    sx = 115
    g = lambda u: math.exp(-u * u / 2)
    pts = [(mx(-3.4, -3.4, 3.4, x0, x1), my(0, 0, 1.05, y0, y1))]
    for i in range(0, 341):
        u = -3.4 + 6.8 * i / 340
        pts.append((cx + u * sx, my(g(u), 0, 1.05, y0, y1)))
    pts.append((mx(3.4, -3.4, 3.4, x0, x1), my(0, 0, 1.05, y0, y1)))
    d.polygon([pt(px, py) for px, py in pts], fill=LIGHT)
    polyline(d, pts[1:-1], ACCENT, 4)
    line(d, [(x0, y0), (x1, y0)], GRAY, 2)
    dashed(d, (cx, y0), (cx, y1), MID, 2, 9, 7)
    text(d, (cx, 856), "均值", 23, GRAY)
    text(d, (416, 236), "高斯分布：误差、噪声电压", 24, ACCENT)
    text(d, (200, 824), "对称：两侧都有尾巴", 23, MID, "lm")
    # 右：瑞利
    x0r, x1r, y0r, y1r = 900, 1450, 780, 270
    ox = 930
    s = 120
    pdf = lambda r: (r / s ** 2) * math.exp(-r * r / (2 * s ** 2))
    pmax = pdf(s)
    pts = [(ox, y0r)]
    for i in range(0, 341):
        r = 3.4 * i / 340 * s
        pts.append((ox + r, my(pdf(r), 0, pmax * 1.05, y0r, y1r)))
    pts.append((ox + 3.4 * s, y0r))
    d.polygon([pt(px, py) for px, py in pts], fill=LIGHT)
    polyline(d, pts[1:-1], ACCENT, 4)
    line(d, [(x0r, y0r), (x1r, y0r)], GRAY, 2)
    rmed = s * 1.177
    dashed(d, (ox + rmed, y0r), (ox + rmed, y1r), RED, 2, 9, 7)
    text(d, (ox + rmed + 8, y0r - 60), "中值 1.177σ", 23, RED, "lm")
    text(d, (1180, 236), "瑞利分布：衰落包络", 24, ACCENT)
    text(d, (950, 824), "单边、右偏：深衰落尾巴长", 23, MID, "lm")
    note(d, "高斯适合“围绕均值抖动”的噪声；瑞利适合“没有直射路径”的衰落")
    save(img, "fig-12-2.png")


# ---------------------------------------------------------------- 第 13 章
def fig_13_1():
    img, d = canvas()
    title(d, "噪声底：-174 dBm/Hz 是起点")
    x0, x1, y0, y1 = 260, 1400, 790, 240
    lo, hi = 2.0, 5.0  # log10(Hz)

    def xb(b):
        return mx(math.log10(b), lo, hi, x0, x1)

    def yp(p):
        return my(p, -205, -115, y0, y1)

    # 网格与刻度
    for b in (100, 1000, 10000, 100000):
        line(d, [(xb(b), y0), (xb(b), y1)], FAINT, 1)
        text(d, (xb(b), y0 + 34), f"{b:,}".replace(",", " "), 22, MID)
    for p in (-200, -180, -160, -140, -120):
        line(d, [(x0, yp(p)), (x1, yp(p))], FAINT, 1)
        text(d, (x0 - 16, yp(p)), str(p), 22, MID, "rm")
    # 曲线
    pts = []
    for i in range(0, 201):
        lg = lo + (hi - lo) * i / 200
        pts.append((mx(lg, lo, hi, x0, x1), yp(-174 + 10 * lg)))
    polyline(d, pts, ACCENT, 4)
    pts2 = []
    for i in range(0, 201):
        lg = lo + (hi - lo) * i / 200
        pts2.append((mx(lg, lo, hi, x0, x1), yp(-166 + 10 * lg)))
    polyline(d, pts2, RED, 3)
    # 标点
    for b, lab in ((500, "500 Hz\n-147 dBm"), (2400, "2.4 kHz\n-140.2 dBm"),
                   (20000, "20 kHz\n-131 dBm")):
        px, py = xb(b), yp(-174 + 10 * math.log10(b))
        dot(d, px, py, 8, ACCENT)
        text(d, (px + 14, py + 34), lab, 22, ACCENT, "lm")
    text(d, (x0 + 40, y1 + 26), "热噪声底（290 K）", 24, ACCENT, "lm")
    text(d, (x0 + 40, y1 + 66), "加 NF=8 dB 后（红线）", 24, RED, "lm")
    text(d, (x1 - 6, y0 - 150), "每 10 倍带宽 +10 dB", 23, MID, "rm")
    text(d, (250, y1 - 6), "噪声功率\n（dBm）", 22, GRAY, "rm")
    note(d, "先算自己的带宽，再谈灵敏度；离开带宽说噪声底没有意义")
    save(img, "fig-13-1.png")


def fig_13_2():
    img, d = canvas()
    title(d, "Friis：第一级的噪声决定总 NF")
    rows = [
        (285, "LNA 在馈线之前（最好）", ["天线", "低噪放\n1 dB / 20 dB", "馈线\n损耗 3 dB", "接收机\n10 dB"], "总 NF ≈ 1.6 dB"),
        (545, "LNA 在馈线之后", ["天线", "馈线\n损耗 3 dB", "低噪放\n1 dB / 20 dB", "接收机\n10 dB"], "总 NF ≈ 4.3 dB"),
        (805, "不加低噪放", ["天线", "馈线\n损耗 3 dB", "接收机\n10 dB"], "总 NF ≈ 13 dB"),
    ]
    for y, lab, blocks, res in rows:
        text(d, (150, y - 92), lab, 25, ACCENT, "lm")
        n = len(blocks)
        widths = [180, 250, 250, 230][:n]
        gap = 58
        total = sum(widths) + gap * (n - 1)
        sx = 220
        ends = []
        for i, (w, s) in enumerate(zip(widths, blocks)):
            x1 = sx
            x2 = sx + w
            box(d, x1, y - 48, x2, y + 48, s, 23)
            ends.append((x1, x2))
            if i < n - 1:
                arrow(d, (x2 + 4, y), (x2 + gap - 4, y), MID, 2, 12)
            sx = x2 + gap
        text(d, (min(ends[-1][1] + 40, 1320), y), res, 24, RED, "lm")
    note(d, "级联：F = F1 + (F2-1)/G1 + (F3-1)/(G1G2)；第一级增益越高，后面的噪声越不重要")
    save(img, "fig-13-2.png")


def fig_13_3():
    img, d = canvas()
    title(d, "S 表：一格 6 dB，三种写法")
    xc = 620
    cols = [(400, "信号强度"), (760, "功率 dBm"), (1090, "电压 μV（50 Ω）")]
    for x, s in cols:
        box(d, x - 140, 180, x + 140, 240, s, 24)
    vals = [
        ("S9", "-73", "50.0"), ("S8", "-79", "25.1"), ("S7", "-85", "12.6"),
        ("S6", "-91", "6.3"), ("S5", "-97", "3.16"), ("S4", "-103", "1.58"),
        ("S3", "-109", "0.79"), ("S2", "-115", "0.40"), ("S1", "-121", "0.20"),
    ]
    y = 290
    for i, (s, dbm, uv) in enumerate(vals):
        if i % 2 == 0:
            d.rectangle([pt(230, y - 28), pt(1290, y + 28)], fill=(246, 248, 251))
        text(d, (400, y), s, 28, ACCENT)
        text(d, (760, y), dbm, 26, GRAY)
        text(d, (1090, y), uv, 26, GRAY)
        y += 62
    line(d, [(220, 258), (1300, 258)], ACCENT, 2)
    text(d, (620, 870), "S9 = -73 dBm = 50 μV；每差一格 6 dB，电压差 2 倍", 24, MID)
    note(d, "读 S 表先问“哪一档、什么带宽、什么阻抗”，单位不能混")
    save(img, "fig-13-3.png")


def fig_13_4():
    img, d = canvas()
    title(d, "低波段听环境，高波段听机器")
    x0, x1, y0, y1 = 260, 1380, 780, 250
    freqs = [1.8, 3.5, 7, 14, 28]
    ext = [-91, -97, -103, -113, -126]
    xs = [mx(i, 0, 4, x0, x1) for i in range(5)]

    def yp(p):
        return my(p, -140, -85, y0, y1)

    for i, f in enumerate(freqs):
        line(d, [(xs[i], y0), (xs[i], y1)], FAINT, 1)
        text(d, (xs[i], y0 + 36), f"{f:g} MHz", 23, MID)
    for p in (-135, -125, -115, -105, -95):
        line(d, [(x0, yp(p)), (x1, yp(p))], FAINT, 1)
        text(d, (x0 - 16, yp(p)), str(p), 22, MID, "rm")
    # 外部噪声
    pts = [(xs[0], yp(ext[0]))]
    for i in range(1, 5):
        pts += [(xs[i], yp(ext[i - 1]))] if False else []
        pts.append((xs[i], yp(ext[i])))
    polyline(d, pts, RED, 4)
    for i in range(5):
        dot(d, xs[i], yp(ext[i]), 7, RED)
        text(d, (xs[i] + 10, yp(ext[i]) - 24), str(ext[i]), 21, RED, "lm")
    # 内部噪声底 / MDS
    mds = -122
    dashed(d, (x0, yp(mds)), (x1, yp(mds)), ACCENT, 3, 14, 9)
    text(d, (280, 575), "内部噪声底 + 所需信噪比 ≈ -122 dBm", 22, ACCENT, "lm")
    text(d, (460, 268), "外部噪声（夏季/城市典型）", 23, RED, "lm")
    # 交叉区说明
    text(d, (430, 505), "低波段：外部噪声\n高出内部底 20 dB 以上", 23,
         GRAY, "lm")
    text(d, (xs[4] - 10, yp(-135)), "高波段：差距缩小，\n内部噪声重新重要", 23,
         GRAY, "rm")
    text(d, (250, y1 - 6), "噪声功率\n（dBm）", 22, GRAY, "rm")
    note(d, "外部噪声远高于内部噪声时，加前置放大器只会把噪声一起放大")
    save(img, "fig-13-4.png")


# ---------------------------------------------------------------- 第 14 章
def fig_14_1():
    img, d = canvas()
    title(d, "采样率 48 kHz：30 kHz 的信号出现在 18 kHz")
    x0, x1, yax = 240, 1400, 560
    fs = 48.0
    f_hi = 36.0

    def xf(f):
        return mx(f, 0, f_hi, x0, x1)

    # 基带区
    d.rectangle([pt(x0, yax - 190), pt(xf(24), yax + 190)],
                fill=(243, 246, 250), outline=None)
    text(d, (x0 + 20, yax - 160), "奈奎斯特区：0 - 24 kHz", 23, MID, "lm")
    dashed(d, (xf(24), yax - 240), (xf(24), yax + 240), ACCENT, 2, 10, 8)
    text(d, (xf(24), yax - 268), "fs/2 = 24 kHz", 24, ACCENT)
    line(d, [(x0 - 20, yax), (x1 + 20, yax)], GRAY, 2)
    for f in (0, 12, 24, 36):
        line(d, [(xf(f), yax), (xf(f), yax + 16)], GRAY, 1)
        text(d, (xf(f), yax + 40), str(f), 21, MID)
    text(d, (x1 + 10, yax + 40), "kHz", 21, MID, "lm")
    # 真实信号
    arrow(d, (xf(30), yax), (xf(30), yax - 150), RED, 4, 15)
    text(d, (xf(30), yax - 190), "真实信号 30 kHz", 24, RED)
    # 混叠信号
    arrow(d, (xf(18), yax + 6), (xf(18), yax + 150), RED, 3, 13)
    dashed(d, (xf(18), yax + 150), (xf(18), yax + 160), RED, 2, 8, 6)
    text(d, (xf(18), yax + 200), "混叠到 18 kHz", 24, RED)
    # 折叠箭头
    arc = []
    for i in range(0, 41):
        t = i / 40
        xx = xf(30) + (xf(18) - xf(30)) * t
        yy = yax - 110 * math.sin(math.pi * t)
        arc.append((xx, yy))
    polyline(d, arc, MID, 2)
    text(d, (400, 470), "折叠：48 - 30 = 18 kHz", 22, MID, "lm")
    note(d, "超过 fs/2 的成分不会消失，它折回基带，成为假信号")
    save(img, "fig-14-1.png")


def fig_14_2():
    img, d = canvas()
    title(d, "量化：台阶、噪声与 6 dB/bit")
    # 左：台阶
    x0, x1, y0, y1 = 170, 760, 760, 270
    n = 8
    step = (y0 - y1) / (n + 1)
    for k in range(n + 1):
        yy = y0 - k * step
        line(d, [(x0 - 10, yy), (x1 + 10, yy)], FAINT, 1)
    ideal, quant = [], []
    for i in range(0, 241):
        t = 2 * math.pi * 2 * i / 240
        x = mx(i / 240, 0, 1, x0, x1)
        ideal.append((x, y0 - (math.sin(t) + 1) / 2 * (n * step)))
        q = round((math.sin(t) + 1) / 2 * n)
        quant.append((x, y0 - q * step))
    polyline(d, ideal, FAINT, 3)
    polyline(d, quant, ACCENT, 3)
    arrow(d, (x1 + 30, y0 - 2 * step), (x1 + 30, y0 - 3 * step), RED, 2, 9)
    text(d, (x1 + 44, y0 - 2.5 * step), "LSB", 21, RED, "lm")
    text(d, (x0, y1 - 30), "量化台阶（LSB）", 23, GRAY, "lm")
    text(d, (x0, y0 + 40), "量化误差 ≤ ±LSB/2", 22, MID, "lm")
    text(d, (400, 220), "连续值 → 离散台阶", 24, ACCENT)
    # 右：SNR vs bits
    x0b, x1b, y0b, y1b = 960, 1450, 760, 300

    def xp(nb):
        return mx(nb, 8, 16, x0b, x1b)

    def yp(db):
        return my(db, 40, 105, y0b, y1b)

    line(d, [(x0b, y0b), (x1b, y0b)], GRAY, 2)
    line(d, [(x0b, y0b), (x0b, y1b - 20)], GRAY, 2)
    pts = []
    for i in range(0, 101):
        nb = 8 + 8 * i / 100
        pts.append((xp(nb), yp(6.02 * nb + 1.76)))
    polyline(d, pts, ACCENT, 3)
    for nb in (8, 10, 12, 14, 16):
        px = xp(nb)
        py = yp(6.02 * nb + 1.76)
        dot(d, px, py, 6, RED)
        line(d, [(px, y0b), (px, py)], FAINT, 1)
        text(d, (px, y0b + 32), str(nb), 21, MID)
    text(d, (xp(12), yp(6.02 * 12 + 1.76) - 34), "12 bit ≈ 74 dB", 22, ACCENT)
    text(d, (x0b, 250), "信噪比（dB）", 23, GRAY, "lm")
    text(d, ((x0b + x1b) / 2, y0b + 72), "位数", 22, GRAY)
    text(d, (x0b + 40, 360), "每多 1 bit ≈ +6 dB", 23, ACCENT, "lm")
    text(d, (1170, 900), "实测 SINAD 68 dB → ENOB ≈ 11", 24, MID)
    note(d, "位数和时钟决定动态范围；采样率只决定能看多宽")
    save(img, "fig-14-2.png")


def fig_14_3():
    img, d = canvas()
    title(d, "FFT：分辨率由观测时间决定")
    x0, x1, y0, y1 = 220, 1400, 760, 260
    line(d, [(x0, y0), (x1, y0)], GRAY, 2)
    line(d, [(x0, y0), (x0, y1 - 20)], GRAY, 2)
    # 噪声底
    floor = -82
    for i in range(0, 44):
        xx = x0 + 26 * i
        if 18 <= i <= 24:
            continue
        h = 12 + 6 * math.sin(i * 2.1) + 4 * math.cos(i * 1.3)
        line(d, [(xx, y0), (xx, my(floor + h, -100, 0, y0, y1))], FAINT, 2)
        dot(d, xx, my(floor + h, -100, 0, y0, y1), 3, MID)
    # 主瓣（矩形窗）
    main = [(-4, -12), (-3, -6), (-2, -1.5), (-1, 0), (0, 0), (1, -1.5),
            (2, -6), (3, -12), (4, -20), (5, -28), (6, -36)]
    for k, db in main:
        xx = x0 + 26 * 21 + 26 * k
        yy = my(max(db, -100), -100, 0, y0, y1)
        line(d, [(xx, y0), (xx, yy)], ACCENT, 2)
        dot(d, xx, yy, 4, ACCENT)
    # 汉宁窗主瓣（更宽、旁瓣更低）
    hann = [(-6, -55), (-5, -40), (-4, -20), (-3, -8), (-2, -2.5), (-1, 0),
            (0, 0), (1, 0), (2, -2.5), (3, -8), (4, -20), (5, -40), (6, -55)]
    pts = []
    for k, db in hann:
        pts.append((x0 + 26 * 21 + 26 * k, my(max(db, -100), -100, 0, y0, y1)))
    polyline(d, pts, RED, 3)
    dashed(d, (x0, my(-60, -100, 0, y0, y1)),
           (x1, my(-60, -100, 0, y0, y1)), FAINT, 1, 10, 8)
    # Δf 标注
    xa = x0 + 26 * 21 - 26
    xb = x0 + 26 * 21 + 26
    arrow(d, (xa, 238), (xb, 238), RED, 2, 10)
    arrow(d, (xb, 238), (xa, 238), RED, 2, 10)
    text(d, (766, 205), "Δf = fs/N = 1/T", 23, RED)
    text(d, (x0, y1 - 10), "幅度（dB）", 23, GRAY, "lm")
    text(d, (x1, y0 + 34), "频率 →", 23, GRAY, "rm")
    text(d, (x1 - 8, y1 + 6), "矩形窗（深蓝）\n汉宁窗（红）", 22, MID, "rm")
    text(d, (250, 820), "每 bin 噪声比总噪声低 10lg(N/2) ≈ 33 dB", 22, MID, "lm")
    note(d, "想分辨更近的两条谱线，只能观测更久：分辨率 = 1/T")
    save(img, "fig-14-3.png")


def fig_14_4():
    img, d = canvas()
    title(d, "I/Q：一路信号拆成两路")
    # 天线与前端
    text(d, (110, 468), "天线", 26, ACCENT, "lm")
    box(d, 175, 450, 315, 550, "带通\n滤波", 23)
    line(d, [(110, 500), (175, 500)], ACCENT, 3)
    line(d, [(315, 500), (330, 500)], ACCENT, 3)
    dot(d, 330, 500, 5, ACCENT)
    line(d, [(330, 500), (330, 355)], ACCENT, 3)
    line(d, [(330, 500), (330, 685)], ACCENT, 3)
    # I 路
    box(d, 430, 315, 590, 395, "混频\n× cos", 22)
    box(d, 640, 315, 780, 395, "低通", 23)
    box(d, 830, 315, 940, 395, "ADC", 23)
    line(d, [(330, 355), (430, 355)], ACCENT, 3)
    arrow(d, (590, 355), (640, 355), MID, 2, 12)
    arrow(d, (780, 355), (830, 355), MID, 2, 12)
    arrow(d, (940, 355), (1010, 355), ACCENT, 2, 12)
    text(d, (1030, 355), "同相 I", 25, ACCENT, "lm")
    # Q 路
    box(d, 430, 645, 590, 725, "混频\n× sin", 22)
    box(d, 640, 645, 780, 725, "低通", 23)
    box(d, 830, 645, 940, 725, "ADC", 23)
    line(d, [(330, 685), (430, 685)], ACCENT, 3)
    arrow(d, (590, 685), (640, 685), MID, 2, 12)
    arrow(d, (780, 685), (830, 685), MID, 2, 12)
    arrow(d, (940, 685), (1010, 685), ACCENT, 2, 12)
    text(d, (1030, 685), "正交 Q", 25, ACCENT, "lm")
    # 本振：两条支路，相差 90°
    box(d, 200, 790, 370, 880, "本振", 23)
    line(d, [(370, 850), (395, 850)], ACCENT, 2)
    line(d, [(395, 850), (395, 355)], ACCENT, 2)
    line(d, [(395, 355), (430, 355)], ACCENT, 2)
    dashed(d, (395, 850), (395, 685), MID, 2, 10, 8)
    line(d, [(395, 685), (430, 685)], ACCENT, 2)
    text(d, (385, 338), "0°", 21, MID, "rm")
    text(d, (385, 668), "90°", 21, MID, "rm")
    # 数字处理
    box(d, 1075, 420, 1440, 620, "数字下变频\n抽取\n→ 基带 I/Q", 26)
    arrow(d, (1010, 355), (1075, 470), ACCENT, 2, 12)
    arrow(d, (1010, 685), (1075, 570), ACCENT, 2, 12)
    text(d, (800, 895), "复采样覆盖 ±fs/2，共 fs 宽", 23, MID)
    note(d, "两路本振相差 90°：同一信号的两面被同时拿到，频谱不再折叠")
    save(img, "fig-14-4.png")


# ---------------------------------------------------------------- 第 15 章
def fig_15_1():
    img, d = canvas()
    title(d, "40 m、1000 km：50 dBm 出发，-71.2 dBm 到达")
    deltas = [("发射天线\n增益", 2.15, "+2.15"),
              ("馈线\n损耗", -3.0, "-3"),
              ("自由空间\n损耗", -109.5, "-109.5"),
              ("接收天线\n增益", 2.15, "+2.15"),
              ("电离层\n吸收", -10.0, "-10"),
              ("地面/极化\n损耗", -3.0, "-3")]
    x_l, x_r = 150, 1460
    n = 7
    seg = (x_r - x_l) / n

    def yp(db):
        return my(db, -110, 58, 800, 240)

    level = 50.0
    prev_y = yp(level)
    # 基线：100 W = +50 dBm
    line(d, [(x_l, prev_y), (x_l + seg, prev_y)], ACCENT, 4)
    text(d, (x_l + seg / 2, 832), "发射 100 W\n50 dBm", 21, GRAY)
    for i, (lab, delta, tag) in enumerate(deltas, start=1):
        level += delta
        y_new = yp(level)
        xb = x_l + seg * i
        line(d, [(xb, prev_y), (xb, y_new)], ACCENT, 4)
        line(d, [(xb, y_new), (min(xb + seg, x_r), y_new)], ACCENT, 4)
        text(d, (xb + seg / 2, 832), lab, 21, GRAY)
        if delta > 0:
            # 正增益的台阶很浅，标注放到台阶上方，避免横线穿字
            text(d, (xb + seg / 2, y_new - 12), tag, 20, ACCENT, "mb")
        else:
            text(d, (xb + 8, (prev_y + y_new) / 2 - 8), tag, 20, RED, "lm")
        prev_y = y_new
    text(d, (x_r + 6, prev_y), "-71.2 dBm", 25, ACCENT, "lm")
    # 外部噪声带
    ntop, nbot = yp(-91), yp(-103)
    d.rectangle([pt(x_l, ntop), pt(x_r, nbot)], fill=(250, 235, 235))
    text(d, (x_l + 12, (ntop + nbot) / 2), "外部噪声 -103 … -91 dBm", 23, RED, "lm")
    # 余量
    arrow(d, (x_r - 90, prev_y), (x_r - 90, ntop), MID, 2, 11)
    arrow(d, (x_r - 90, ntop), (x_r - 90, prev_y), MID, 2, 11)
    text(d, (x_r - 112, (prev_y + ntop) / 2), "余量\n约 20 dB", 22, MID, "rm")
    for db in (50, 25, 0, -25, -50, -75, -100):
        line(d, [(x_l - 8, yp(db)), (x_l, yp(db))], MID, 2)
        text(d, (x_l - 16, yp(db)), str(db), 21, MID, "rm")
    text(d, (100, 240), "dBm", 22, GRAY, "rm")
    note(d, "每个环节都是加减法；最后比的是“接收电平相对外部噪声还剩多少”")
    save(img, "fig-15-1.png")


def fig_15_2():
    img, d = canvas()
    title(d, "单跳几何：h、θ、d 的关系")
    def gy(x):
        return 720 + 42 * ((x - 800) / 680) ** 2
    ground = []
    for i in range(0, 201):
        x = 120 + 1360 * i / 200
        ground.append((x, gy(x)))
    polyline(d, ground, ACCENT, 4)
    text(d, (800, gy(800) + 70), "地面（球面近似）", 23, MID)
    iono = []
    for i in range(0, 201):
        x = 120 + 1360 * i / 200
        iono.append((x, 180 + 18 * ((x - 800) / 680) ** 2))
    polyline(d, iono, TEAL, 4)
    text(d, (800, 142), "电离层 F2 层（h ≈ 300 km）", 24, TEAL)
    tx = (260, gy(260))
    rx = (1340, gy(1340))
    rf = (800, 196)
    line(d, [tx, rf, rx], RED, 3)
    for p in (tx, rx):
        line(d, [(p[0] - 26, p[1]), (p[0] + 26, p[1])], ACCENT, 5)
        line(d, [(p[0], p[1]), (p[0], p[1] - 120)], ACCENT, 4)
    text(d, (tx[0] - 40, tx[1] - 150), "发射", 24, ACCENT, "rm")
    text(d, (rx[0] + 40, rx[1] - 150), "接收", 24, ACCENT, "lm")
    # θ 角
    a1 = math.atan2(rf[1] - tx[1], rf[0] - tx[0])
    arc = []
    for i in range(0, 21):
        a = a1 * i / 20
        arc.append((tx[0] + 150 * math.cos(a), tx[1] + 150 * math.sin(a)))
    line(d, arc, GRAY, 2)
    text(d, (tx[0] + 190, tx[1] - 66), "θ", 27, GRAY)
    # h 与 d
    arrow(d, (880, gy(800)), (880, 196), MID, 2, 11)
    arrow(d, (880, 196), (880, gy(800)), MID, 2, 11)
    text(d, (900, 470), "h", 27, MID, "lm")
    arrow(d, (260, 900), (1340, 900), MID, 2, 12)
    arrow(d, (1340, 900), (260, 900), MID, 2, 12)
    text(d, (295, 888), "d", 24, MID)
    text(d, (800, 868), "单跳距离 d ≈ 2h / tanθ", 25, MID)
    text(d, (850, 172), "反射点", 23, RED, "lm")
    note(d, "h 固定时，仰角越低，一跳越远；θ 与 d 一一对应")
    save(img, "fig-15-2.png")


def fig_15_3():
    img, d = canvas()
    title(d, "第一菲涅尔区：至少留出 60% 净空")
    ground = 830
    line(d, [(100, ground), (1500, ground)], ACCENT, 4)
    for x in (220, 1380):
        line(d, [(x, ground), (x, 560)], ACCENT, 5)
        line(d, [(x - 55, 560), (x + 55, 560)], ACCENT, 5)
        text(d, (x, ground + 40), "天线", 23, GRAY)
    ellipse(d, 800, 560, 560, 122, (240, 245, 250), ACCENT, 3)
    ellipse(d, 800, 560, 336, 73, None, MID, 2)
    dashed(d, (800, 560), (800, 438), MID, 2, 8, 6)
    # 障碍物
    d.rectangle([pt(730, 600), pt(830, ground)], fill=(235, 228, 220),
                outline=BROWN, width=3 * S)
    text(d, (780, ground + 40), "障碍物", 23, BROWN)
    text(d, (860, 520), "侵入第一区\n→ 额外损耗", 23, RED, "lm")
    arrow(d, (860, 560), (806, 600), RED, 2, 10)
    # 净空
    arrow(d, (690, 682), (690, 604), RED, 2, 9)
    text(d, (676, 640), "净空", 22, RED, "rm")
    text(d, (560, 420), "第一菲涅尔区", 25, ACCENT)
    text(d, (1030, 600), "虚线：60% 净空线", 22, MID, "lm")
    # d1 d2
    arrow(d, (220, 905), (780, 905), MID, 2, 10)
    arrow(d, (780, 905), (1380, 905), MID, 2, 10)
    text(d, (500, 878), "d1", 24, MID)
    text(d, (1080, 878), "d2", 24, MID)
    text(d, (800, 940), "r = √(λ·d1·d2/(d1+d2))", 24, ACCENT)
    save(img, "fig-15-3.png")


def fig_15_4():
    img, d = canvas()
    title(d, "MUF 跟着太阳走：同一个 7.1 MHz")
    x0, x1, y0, y1 = 260, 1400, 760, 250
    def xh(h):
        return mx(h, 0, 24, x0, x1)
    def ym(f):
        return my(f, 0, 16, y0, y1)
    fo = []
    muf = []
    for i in range(0, 241):
        h = 24 * i / 240
        if 6 <= h <= 18:
            f = 2.6 + 4.9 * math.sin(math.pi * (h - 6) / 12)
        else:
            f = 2.6
        fo.append((xh(h), ym(f)))
        muf.append((xh(h), ym(1.94 * f)))
    # 可通时段淡色
    for i in range(0, 240):
        h = 24 * (i + 0.5) / 240
        f = 2.6 + 4.9 * math.sin(math.pi * (h - 6) / 12) if 6 <= h <= 18 else 2.6
        if 1.94 * f >= 7.1:
            d.rectangle([pt(xh(24 * i / 240), ym(16)), pt(xh(24 * (i + 1) / 240), y0)],
                        fill=(243, 247, 251))
    polyline(d, fo, RED, 3)
    polyline(d, muf, ACCENT, 4)
    line(d, [(x0, ym(7.1)), (x1, ym(7.1))], BROWN, 3)
    text(d, (x0 + 14, ym(7.1) - 22), "40 m：7.1 MHz", 23, BROWN, "lm")
    text(d, (x0 + 760, ym(15.3)), "MUF（1000 km，约 1.94 × foF2）", 23, ACCENT, "lm")
    text(d, (x0 + 120, ym(6.2)), "foF2", 24, RED, "lm")
    for h in (0, 6, 12, 18, 24):
        text(d, (xh(h), y0 + 36), str(h), 22, MID)
        line(d, [(xh(h), y0), (xh(h), y0 + 10)], MID, 1)
    for f in (0, 4, 8, 12, 16):
        line(d, [(x0, ym(f)), (x0 - 8, ym(f))], MID, 1)
        text(d, (x0 - 16, ym(f)), str(f), 21, MID, "rm")
    text(d, ((x0 + x1) / 2, y0 + 76), "地方时（小时）", 23, GRAY)
    text(d, (230, 200), "频率\n（MHz）", 22, GRAY, "rm")
    text(d, (xh(9), ym(10.4)), "可通时段", 23, MID)
    text(d, (1330, 718), "夜间 MUF 低于 7.1\n40 m 单跳关闭", 22, RED, "rm")
    note(d, "同一个频率，白天在 MUF 之下能通，夜里 MUF 降下来就不通")
    save(img, "fig-15-4.png")


def fig_15_5():
    img, d = canvas()
    title(d, "衰落余量买的是可靠度")
    x0, x1, y0, y1 = 230, 1400, 780, 250
    def xm(m):
        return mx(m, 0, 20, x0, x1)
    def yr(r):
        return my(r, 50, 100, y0, y1)
    pts = []
    for i in range(0, 201):
        m = 20 * i / 200
        p_out = 1 - math.exp(-math.log(2) * 10 ** (-m / 10))
        pts.append((xm(m), yr(100 * (1 - p_out))))
    line(d, [(x0, y0), (x1, y0)], GRAY, 2)
    line(d, [(x0, y0), (x0, y1 - 20)], GRAY, 2)
    for p in (50, 60, 70, 80, 90, 100):
        line(d, [(x0, yr(p)), (x1, yr(p))], FAINT, 1)
        text(d, (x0 - 16, yr(p)), str(p), 21, MID, "rm")
    polyline(d, pts, ACCENT, 4)
    marks = [(10, "10 dB：约 93%\n（7% 时间中断）"),
             (20, "20 dB：约 99.3%\n（0.7% 时间中断）")]
    for m, lab in marks:
        px = xm(m)
        p_out = 1 - math.exp(-math.log(2) * 10 ** (-m / 10))
        py = yr(100 * (1 - p_out))
        dot(d, px, py, 8, RED)
        dashed(d, (px, y0), (px, py), RED, 2, 8, 6)
        text(d, (px - 16, py - 70), lab, 22, RED, "rm")
    for m in (0, 5, 10, 15, 20):
        text(d, (xm(m), y0 + 36), str(m), 22, MID)
    text(d, ((x0 + x1) / 2, y0 + 76), "低于中值的余量（dB）", 23, GRAY)
    text(d, (215, 195), "可靠度\n（%）", 22, GRAY, "rm")
    text(d, (300, 285), "瑞利衰落：余量每加 10 dB，中断概率约降一个数量级",
         22, MID, "lm")
    note(d, "先定能容忍多少中断时间，再决定花多少钱买余量")
    save(img, "fig-15-5.png".replace("15-5", "15-5"))


# ---------------------------------------------------------------- 第 16 章
def fig_16_1():
    img, d = canvas()
    title(d, "准确 ≠ 精密：一个看偏差，一个看散布")
    panels = [
        ((120, 200, 760, 500), "准确，不精密", (440, 350), 0,
         [(-90, -55), (70, -75), (-40, 85), (100, 55), (-105, 30), (30, 105),
          (80, -20), (-60, -95)]),
        ((840, 200, 1480, 500), "精密，不准确", (1160, 300), 0,
         [(28, -40), (50, -46), (34, -22), (54, -26), (40, -32), (24, -28),
          (48, -34), (42, -20)]),
        ((120, 560, 760, 860), "又准确又精密", (440, 710), 0,
         [(-10, -6), (8, -10), (-5, 8), (10, 5), (0, 0), (-12, 3), (6, -3),
          (2, 9)]),
        ((840, 560, 1480, 860), "既不准确也不精密", (1170, 710), 0,
         [(-45, -30), (140, -50), (5, 110), (160, 80), (-60, 50), (75, 130)]),
    ]
    for (x1, y1, x2, y2), lab, c, _, offs in panels:
        d.rounded_rectangle([pt(x1, y1), pt(x2, y2)], radius=8 * S,
                            fill=(249, 250, 252), outline=FAINT,
                            width=2 * S)
        cx, cy = c
        line(d, [(cx - 55, cy), (cx + 55, cy)], FAINT, 2)
        line(d, [(cx, cy - 55), (cx, cy + 55)], FAINT, 2)
        ellipse(d, cx, cy, 10, 10, RED, RED, 1)
        for ox, oy in offs:
            dot(d, cx + ox, cy + oy, 7, ACCENT)
        text(d, ((x1 + x2) / 2, y2 + 34), lab, 25, GRAY)
    text(d, (800, 528), "靶心 = 真值，蓝点 = 测量值", 23, MID)
    note(d, "准不准看系统误差，稳不稳看随机误差；两件事要分开报告")
    save(img, "fig-16-1.png")


def fig_16_2():
    img, d = canvas()
    title(d, "驻波表读 1.5±0.1，误差传到三个量")
    x0, x1, y0, y1 = 250, 800, 790, 250
    def xs(s):
        return mx(s, 1.0, 3.0, x0, x1)
    def yg(g):
        return my(g, 0, 0.6, y0, y1)
    line(d, [(x0, y0), (x1, y0)], GRAY, 2)
    line(d, [(x0, y0), (x0, y1 - 20)], GRAY, 2)
    for s in (1.0, 1.5, 2.0, 2.5, 3.0):
        line(d, [(xs(s), y0), (xs(s), y0 + 10)], MID, 1)
        text(d, (xs(s), y0 + 36), f"{s:g}", 22, MID)
    for g in (0, 0.2, 0.4, 0.6):
        line(d, [(x0, yg(g)), (x0 - 8, yg(g))], MID, 1)
        text(d, (x0 - 16, yg(g)), f"{g:g}", 22, MID, "rm")
    pts = []
    for i in range(0, 201):
        s = 1.0 + 2.0 * i / 200
        pts.append((xs(s), yg((s - 1) / (s + 1))))
    polyline(d, pts, ACCENT, 4)
    # 不确定带
    d.rectangle([pt(xs(1.4), y1), pt(xs(1.6), y0)], fill=(250, 238, 238))
    polyline(d, pts, ACCENT, 4)
    dot(d, xs(1.5), yg(0.2), 8, RED)
    dashed(d, (xs(1.5), y0), (xs(1.5), yg(0.2)), RED, 2, 8, 6)
    text(d, (xs(1.7), yg(0.05)), "S=1.5±0.1", 23, RED, "lm")
    text(d, (280, 205), "|Γ|", 24, GRAY, "lm")
    text(d, (700, y0 + 76), "SWR", 23, GRAY)
    # 右：三个结果
    res = [("|Γ| = 0.20 ± 0.03", ACCENT, 300),
           ("回波损耗 RL = 14.0 dB\n（12.7 - 15.5 dB）", GRAY, 430),
           ("失配损耗 ML = 0.18 dB\n（远小于 1 dB，不必追）", GRAY, 570)]
    for s, col, y in res:
        box(d, 930, y - 60, 1450, y + 60, s, 25, LIGHT, ACCENT, 3, col)
    arrow(d, (xs(1.5) + 8, yg(0.2)), (925, 300), MID, 2, 12)
    text(d, (930, 690), "同一条 Γ 的三种说法", 23, MID, "lm")
    text(d, (930, 740), "读数的 ±0.1 传到 RL 约 ±1.4 dB", 23, MID, "lm")
    note(d, "先算不确定度，再判断“两副天线差 1 dB”是否真的分得开")
    save(img, "fig-16-2.png")


def fig_16_3():
    img, d = canvas()
    title(d, "找谐振点：看 X=0，不看 SWR 最低")
    x0, x1, y0, y1 = 240, 1320, 790, 250
    def xf(f):
        return mx(f, 7.00, 7.10, x0, x1)
    def yx(v):
        return my(v, -40, 40, y0, y1)
    line(d, [(x0, yx(0)), (x1, yx(0))], FAINT, 2)
    line(d, [(x0, y0), (x0, y1 - 20)], GRAY, 2)
    for f in (7.00, 7.02, 7.04, 7.06, 7.08, 7.10):
        line(d, [(xf(f), yx(0)), (xf(f), yx(0) + 10)], MID, 1)
        text(d, (xf(f), y0 + 36), f"{f:.2f}", 22, MID)
    for v in (-40, -20, 0, 20, 40):
        line(d, [(x0, yx(v)), (x0 - 8, yx(v))], MID, 1)
        text(d, (x0 - 16, yx(v)), str(v), 22, MID, "rm")
    points = [(7.00, -30), (7.05, -5), (7.10, 25)]
    # 最小二乘线
    m = 550.0
    b = -3.333 - m * 7.05
    line_pts = [(xf(7.00), yx(m * 7.00 + b)), (xf(7.10), yx(m * 7.10 + b))]
    polyline(d, line_pts, ACCENT, 3)
    for f, v in points:
        dot(d, xf(f), yx(v), 9, RED)
        dy = 26 if v == -5 else -22
        text(d, (xf(f) + 12, yx(v) + dy), f"{v:+d} Ω", 22, RED, "lm")
    f0 = (0 - b) / m
    dashed(d, (xf(f0), y0), (xf(f0), y1), ACCENT, 2, 10, 7)
    text(d, (xf(f0) + 12, y1 + 18), "f0 ≈ 7.056 MHz", 24, ACCENT, "lm")
    text(d, (x0 + 10, y1 - 6), "电抗 X（Ω）", 23, GRAY, "lm")
    text(d, (1200, y0 + 72), "频率（MHz）", 23, GRAY, "rm")
    text(d, (xf(7.015), yx(30)), "三点法：f0 ≈ 7.059 MHz\n最小二乘：≈ 7.056 MHz\n取 7.06 MHz", 23, MID, "lm")
    note(d, "SWR 最低只说明匹配最好；谐振要 X=0，两者不一定重合")
    save(img, "fig-16-3.png")


# ---------------------------------------------------------------- 第 17 章
def fig_17_1():
    img, d = canvas()
    title(d, "梯形法：积分面积与步长")
    f = lambda t: abs(math.sin(t)) ** 3
    for k, (x0, x1, N, lab) in enumerate([
            (150, 730, 4, "N=4：I ≈ 1.341，误差 0.6%"),
            (870, 1450, 8, "N=8：误差 < 0.1%")]):
        y0, y1 = 780, 260
        line(d, [(x0, y0), (x1, y0)], GRAY, 2)
        line(d, [(x0, y0), (x0, y1 - 20)], GRAY, 2)
        pts = []
        for i in range(0, 201):
            t = math.pi * i / 200
            pts.append((mx(t, 0, math.pi, x0, x1), my(f(t), 0, 1.05, y0, y1)))
        # 梯形
        for i in range(N):
            a = math.pi * i / N
            b = math.pi * (i + 1) / N
            xa = mx(a, 0, math.pi, x0, x1)
            xb = mx(b, 0, math.pi, x0, x1)
            ya = my(f(a), 0, 1.05, y0, y1)
            yb = my(f(b), 0, 1.05, y0, y1)
            d.polygon([pt(xa, y0), pt(xa, ya), pt(xb, yb), pt(xb, y0)],
                      fill=LIGHT, outline=ACCENT, width=1 * S)
            line(d, [(xa, ya), (xb, yb)], RED, 2)
        polyline(d, pts, ACCENT, 4)
        text(d, ((x0 + x1) / 2, 828), lab, 23, GRAY)
        text(d, (x0 + 8, y1 - 8), "F(θ)=sinθ^3", 22, GRAY, "lm")
    text(d, (800, 905), "步长减半，误差约按 1/4 下降（二阶收敛）", 24, MID)
    note(d, "四段梯形已经能把方向性积分算到 1% 以内；加密要看误差怎么降")
    save(img, "fig-17-1.png")


def fig_17_2():
    img, d = canvas()
    title(d, "网格收敛：什么时候可以停")
    xs = [300, 550, 800, 1050, 1300]
    labels = ["5", "11", "21", "41", "81"]
    y0, y1 = 780, 280
    # 左轴 Rin
    rin = [48.6, 50.1, 50.35, 50.30, 50.30]
    gain = [2.06, 2.12, 2.14, 2.15, 2.15]
    line(d, [(220, y0), (1460, y0)], GRAY, 2)
    line(d, [(220, y0), (220, y1 - 20)], GRAY, 2)
    for i, lab in enumerate(labels):
        line(d, [(xs[i], y0), (xs[i], y0 + 10)], MID, 1)
        text(d, (xs[i], y0 + 36), lab, 22, MID)
    for v in (47, 49, 51):
        yy = my(v, 47, 51, y0, y1)
        line(d, [(220, yy), (1460, yy)], FAINT, 1)
        text(d, (206, yy), str(v), 21, MID, "rm")
    dashed(d, (220, my(50.3, 47, 51, y0, y1)), (1460, my(50.3, 47, 51, y0, y1)),
           ACCENT, 2, 10, 8)
    pts = [(xs[i], my(rin[i], 47, 51, y0, y1)) for i in range(5)]
    polyline(d, pts, ACCENT, 3)
    for x, y in pts:
        dot(d, x, y, 7, ACCENT)
    text(d, (235, 218), "输入电阻 Rin（Ω）", 23, ACCENT, "lm")
    # 右轴增益
    for v in (2.00, 2.10, 2.20):
        yy = my(v, 2.00, 2.20, y0, y1)
        text(d, (1474, yy), f"{v:.2f}", 21, MID, "lm")
    pts2 = [(xs[i], my(gain[i], 2.00, 2.20, y0, y1)) for i in range(5)]
    polyline(d, pts2, RED, 3)
    for x, y in pts2:
        dot(d, x, y, 7, RED)
    text(d, (1445, 218), "增益（dBi）", 23, RED, "rm")
    text(d, (800, 690), "21 段以后，相邻两次结果差 < 0.1 dB\n再加密只是浪费机时", 23, MID)
    text(d, (800, 852), "段数（每臂）", 23, GRAY)
    note(d, "收敛判据写进流程：相邻两次网格结果之差小于目标（约 0.1 dB）")
    save(img, "fig-17-2.png")


def fig_17_3():
    img, d = canvas()
    title(d, "公差变成分布：±1 cm 对应多少 kHz")
    x0, x1, y0, y1 = 260, 1360, 780, 280
    mu, sig = 7.100, 0.004
    lo, hi = 7.070, 7.130
    nbin = 31
    bw = (hi - lo) / nbin
    def xf(f):
        return mx(f, lo, hi, x0, x1)
    def yn(c):
        return my(c, 0, 220, y0, y1)
    line(d, [(x0, y0), (x1, y0)], GRAY, 2)
    line(d, [(x0, y0), (x0, y1 - 20)], GRAY, 2)
    counts = []
    for i in range(nbin):
        f = lo + (i + 0.5) * bw
        c = 1000 * bw * math.exp(-((f - mu) ** 2) / (2 * sig ** 2)) / (sig * math.sqrt(2 * math.pi))
        counts.append(c)
    peak = max(counts) * 1.08
    for i, c in enumerate(counts):
        xa = xf(lo + i * bw)
        xb = xf(lo + (i + 1) * bw)
        yy = my(c, 0, peak, y0, y1)
        d.rectangle([pt(xa + 1, yy), pt(xb - 1, y0)], fill=LIGHT, outline=ACCENT,
                    width=1 * S)
    # 包络
    pts = []
    for i in range(0, 241):
        f = lo + (hi - lo) * i / 240
        c = 1000 * bw * math.exp(-((f - mu) ** 2) / (2 * sig ** 2)) / (sig * math.sqrt(2 * math.pi))
        pts.append((xf(f), my(c, 0, peak, y0, y1)))
    polyline(d, pts, RED, 3)
    dashed(d, (xf(mu), y0), (xf(mu), y1), ACCENT, 2, 9, 7)
    text(d, (xf(mu), y1 + 16), "7.100 MHz", 24, ACCENT)
    for f in (7.07, 7.09, 7.11, 7.13):
        line(d, [(xf(f), y0), (xf(f), y0 + 10)], MID, 1)
        text(d, (xf(f), y0 + 38), f"{f:.2f}", 21, MID)
    text(d, (240, y1 - 6), "次数\n（1000 次）", 22, GRAY, "rm")
    text(d, (1300, y0 + 76), "谐振频率（MHz）", 23, GRAY, "rm")
    text(d, (300, 330), "每臂 ±1 cm → 谐振频率约 ±7 kHz", 23, MID, "lm")
    text(d, (300, 390), "1000 次抽样：σ ≈ 4 kHz", 23, MID, "lm")
    text(d, (300, 450), "远小于 40 m 可用带宽（约 100 kHz）", 23, MID, "lm")
    note(d, "按 143/f 裁、留 2 cm 余量，比算到毫米更实际")
    save(img, "fig-17-3.png")


# ---------------------------------------------------------------- 拼图与验收
def contact_sheet(names, out_name="_contact_part2.png"):
    cols, cell_w, cell_h = 4, 470, 340
    rows = math.ceil(len(names) / cols)
    sheet = Image.new("RGB", (cols * cell_w + 20, rows * cell_h + 20),
                      (248, 249, 251))
    dd = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(FONT_PATH, 26)
    for i, name in enumerate(names):
        r, c = divmod(i, cols)
        x0 = 10 + c * cell_w
        y0 = 10 + r * cell_h
        dd.rectangle([x0, y0, x0 + cell_w - 10, y0 + cell_h - 10],
                     fill="white", outline=(200, 205, 212), width=2)
        dd.text((x0 + 12, y0 + 8), "图 " + name.replace("fig-", "").replace(".png", ""),
                font=f, fill=ACCENT)
        p = OUT / name
        if not p.exists():
            dd.text((x0 + 150, y0 + 160), "缺图", font=f, fill=(180, 40, 40))
            continue
        im = Image.open(p).convert("RGB")
        im.thumbnail((cell_w - 30, cell_h - 72), Image.LANCZOS)
        px = x0 + (cell_w - 10 - im.width) // 2
        py = y0 + 44 + (cell_h - 60 - im.height) // 2
        sheet.paste(im, (px, py))
    sheet.save(OUT / out_name)
    print("wrote", out_name, sheet.size)


FUNCS = [fig_10_1, fig_10_2, fig_11_1, fig_11_2, fig_11_3, fig_12_1,
         fig_12_2, fig_13_1, fig_13_2, fig_13_3, fig_13_4, fig_14_1,
         fig_14_2, fig_14_3, fig_14_4, fig_15_1, fig_15_2, fig_15_3,
         fig_15_4, fig_15_5, fig_16_1, fig_16_2, fig_16_3, fig_17_1,
         fig_17_2, fig_17_3]


def main():
    for fn in FUNCS:
        fn()
    contact_sheet(NAMES)
    print("\n== 验收 ==")
    ok = 0
    for name in NAMES:
        p = OUT / name
        size = p.stat().st_size if p.exists() else 0
        good = p.exists() and size > 5000
        print(("OK  " if good else "FAIL") + f" {name} {size} B")
        ok += good
    print(f"{ok}/{len(NAMES)} 张通过")


if __name__ == "__main__":
    main()
