# -*- coding: utf-8 -*-
"""A1 量点标注：舵机口 pin1 与排母 pin6 的定位方法，输出到 docs/photos/。"""
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"
RED = (200, 30, 30)
BLUE = (30, 90, 200)
GRAY = (90, 90, 90)
BLACK = (30, 30, 30)

f_title = ImageFont.truetype(FONT_PATH, 40)
f_note = ImageFont.truetype(FONT_PATH, 26)
f_box = ImageFont.truetype(FONT_PATH, 26)
f_tbl = ImageFont.truetype(FONT_PATH, 25)

SRC = r"C:\Projects\duck-robot\docs\photos\hat-v1.2-front.jpg"
DST = r"C:\Projects\duck-robot\docs\photos\hat-v1.2-a1-pinout.jpg"

img = Image.open(SRC).convert("RGB")
W, H = img.size
STRIP = 400
canvas = Image.new("RGB", (W, H + STRIP), (255, 255, 255))
canvas.paste(img, (0, 0))
d = ImageDraw.Draw(canvas)


def box(x, y, lines, font=f_box, color=RED, pad=10):
    widths = [d.textbbox((0, 0), t, font=font)[2] for t in lines]
    bw = max(widths) + pad * 2
    bh = len(lines) * (font.size + 7) + pad * 2 - 7
    d.rounded_rectangle([x, y, x + bw, y + bh], radius=10,
                        fill=(255, 255, 255), outline=color, width=4)
    for i, t in enumerate(lines):
        d.text((x + pad, y + pad + i * (font.size + 7)), t, font=font, fill=color)
    return (x, y, x + bw, y + bh)


def leader(rect, dot, side="bottom", color=RED):
    x0, y0, x1, y1 = rect
    anchors = {"bottom": ((x0 + x1) // 2, y1), "top": ((x0 + x1) // 2, y0),
               "left": (x0, (y0 + y1) // 2), "right": (x1, (y0 + y1) // 2)}
    ax, ay = anchors[side]
    d.line([ax, ay, dot[0], dot[1]], fill=color, width=4)
    r = 10
    d.ellipse([dot[0] - r, dot[1] - r, dot[0] + r, dot[1] + r],
              fill=color, outline=(255, 255, 255), width=3)


d.text((28, 20), "A1 量点标注 — 舵机口 pin1 与排母 pin6 怎么找", font=f_title, fill=RED)
d.text((28, 76), "2026-10-11（duck-robot）。pin1/pin6 丝印被座子与排母孔挡住，用蜂鸣档按底部步骤定位",
       font=f_note, fill=GRAY)

# 舵机口两座各 3 触点（上/中/下）
b1 = box(330, 560, ["舵机口 3 触点（两座相同）", "1=GND 2=+BATT 3=DATA", "pin1 是哪根？→ 步骤①"])
for x in (112, 207):
    for y in (648, 700, 750):
        leader(b1, (x, y), side="left")

# 安装孔 = GND 参考点
b2 = box(330, 760, ["安装孔金环 = GND 参考点", "（蜂鸣对照的基准）"], color=BLUE)
leader(b2, (155, 852), side="left", color=BLUE)
leader(b2, (140, 398), side="left", color=BLUE)

# 40P 排母两排孔
b3 = box(560, 200, ["40P 排母孔（2×20）", "pin2/4=5V、pin6=GND 在哪？→ 步骤②③"])
leader(b3, (250, 392))
leader(b3, (250, 440))
leader(b3, (1160, 392), side="right")
leader(b3, (1160, 440), side="right")

# 底部步骤条
y0 = H + 24
d.line([0, H + 8, W, H + 8], fill=RED, width=4)
d.text((28, y0), "定位步骤（万用表蜂鸣档，板子不上电）", font=f_note, fill=RED)
steps = [
    ("① 舵机口 pin1：一笔碰安装孔金环（GND），另一笔逐个碰插座 3 个触点 —— 响的那根 = pin1（GND）。",
     BLACK),
    ("    剩余两根：与 AP63205 输入电容正极（正面 CK 6R8 电感旁）通的 = pin2（+BATT）；最后那根 = pin3（DATA）。",
     BLACK),
    ("② 排母 pin2/4：一笔碰 CK 6R8 电感（5V 输出），另一笔沿两排孔扫 —— 同排相邻两孔都响 = pin2、pin4（5V 排）。",
     BLUE),
    ("③ 排母 pin6：从 pin2、pin4 沿同一排往同方向数第 3 个孔 = pin6（GND），应与安装孔金环相通；",
     BLUE),
    ("    不通说明从错的端头数起，换另一端重新数。两座舵机口同样各量一遍。",
     BLUE),
]
for i, (t, c) in enumerate(steps):
    d.text((28, y0 + 44 + i * 40), t, font=f_tbl, fill=c)

canvas.save(DST, quality=90)
print("saved:", DST, canvas.size)
