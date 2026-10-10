# -*- coding: utf-8 -*-
"""HAT 板正反面照片元件标注，输出到 docs/photos/。"""
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"
RED = (200, 30, 30)
GRAY = (90, 90, 90)
BLACK = (30, 30, 30)

f_title = ImageFont.truetype(FONT_PATH, 40)
f_note = ImageFont.truetype(FONT_PATH, 26)
f_box = ImageFont.truetype(FONT_PATH, 26)
f_box_s = ImageFont.truetype(FONT_PATH, 23)
f_tbl = ImageFont.truetype(FONT_PATH, 23)


def make(src, dst, strip_h, draw_fn):
    img = Image.open(src).convert("RGB")
    W, H = img.size
    canvas = Image.new("RGB", (W, H + strip_h), (255, 255, 255))
    canvas.paste(img, (0, 0))
    d = ImageDraw.Draw(canvas)

    def box(x, y, lines, font=f_box, pad=10):
        widths = [d.textbbox((0, 0), t, font=font)[2] for t in lines]
        bw = max(widths) + pad * 2
        bh = len(lines) * (font.size + 7) + pad * 2 - 7
        d.rounded_rectangle([x, y, x + bw, y + bh], radius=10,
                            fill=(255, 255, 255), outline=RED, width=4)
        for i, t in enumerate(lines):
            d.text((x + pad, y + pad + i * (font.size + 7)), t, font=font, fill=RED)
        return (x, y, x + bw, y + bh)

    def leader(rect, dot, side="bottom"):
        x0, y0, x1, y1 = rect
        anchors = {"bottom": ((x0 + x1) // 2, y1), "top": ((x0 + x1) // 2, y0),
                   "left": (x0, (y0 + y1) // 2), "right": (x1, (y0 + y1) // 2)}
        ax, ay = anchors[side]
        d.line([ax, ay, dot[0], dot[1]], fill=RED, width=4)
        r = 9
        d.ellipse([dot[0] - r, dot[1] - r, dot[0] + r, dot[1] + r],
                  fill=RED, outline=(255, 255, 255), width=3)

    draw_fn(d, box, leader, W, H)
    canvas.save(dst, quality=90)
    print("saved:", dst, canvas.size)


# ================= 正面（1440×1080，扩展底部 260） =================
def front(d, box, leader, W, H):
    d.text((28, 20), "Microduck Controller Hat for Radxa Zero 3W — 正面标注", font=f_title, fill=RED)
    d.text((28, 76), "2026-10-10 归档（duck-robot）。实物丝印 V1.2；存档原理图为 V1.0，图物有差异", font=f_note, fill=GRAY)

    b1 = box(30, 130, ["40P 排母焊盘（接 Radxa Zero 3W）", "排母本体装在背面"])
    leader(b1, (700, 400))

    b2 = box(600, 130, ["Qwiic/I2C 座 ×4（SH 1.0 4P）", "丝印 I2C3 / I2C4 / I2C5 等"])
    for dot in [(165, 555), (320, 545), (685, 565), (820, 560)]:
        leader(b2, dot)

    b3 = box(1080, 130, ["舵机口 ×2（JST EH 3P）", "丝印 SERVOS", "1=GND 2=+BATT 3=DATA"])
    leader(b3, (130, 690), side="left")
    leader(b3, (230, 690), side="left")

    b4 = box(1080, 290, ["RS485 座焊盘（EH 4P）", "未焊（空焊盘）"])
    leader(b4, (315, 770), side="left")
    leader(b4, (420, 770), side="left")

    y0 = H + 24
    d.line([0, H + 8, W, H + 8], fill=RED, width=4)
    b5 = box(28, y0, ["AP63205 5V 降压区", "（电感 CK 6R8 = 6.8µH）"])
    leader(b5, (640, 790), side="top")
    leader(b5, (745, 800), side="top")

    b6 = box(430, y0, ["超级电容（疑 1.0F 5.5V）", "疑 RTC 备份，V1.0 图无，待核"])
    leader(b6, (530, 810), side="top")

    b7 = box(850, y0, ["扬声器/麦克风座群", "SPEAKERS L/R、Mic、MICS"])
    leader(b7, (900, 845), side="top")
    leader(b7, (1150, 830), side="top")
    leader(b7, (1290, 640), side="top")

    b8 = box(28, y0 + 130, ["实物版本丝印 V1.2；安装孔 ×4", "（此前档案误记 V1.1，以此为准）"])
    leader(b8, (1120, 650), side="top")
    leader(b8, (140, 860), side="top")


# ================= 背面（1080×1440，扩展底部 240） =================
def back(d, box, leader, W, H):
    d.text((28, 16), "HAT 背面标注 — 实物丝印 v1.2", font=f_title, fill=RED)
    d.text((28, 72), "2026-10-10 归档（duck-robot）", font=f_note, fill=GRAY)

    b1 = box(700, 120, ["F303 类 MCU", "LQFP48，丝印 ?32F303CET6", "V1.0 原理图中无此件！"], font=f_box_s)
    leader(b1, (320, 190), side="left")

    b2 = box(740, 330, ["MCU 晶振（金属壳）"], font=f_box_s)
    leader(b2, (410, 290), side="left")

    b3 = box(700, 470, ["PAM8406 音频功放", "SOP-16（V1.0 图 U12）"], font=f_box_s)
    leader(b3, (290, 480), side="left")

    b4 = box(740, 640, ["40P 排母 ×1", "插 Radxa Zero 3W"], font=f_box_s)
    leader(b4, (640, 700), side="left")

    b5 = box(700, 800, ["小信号芯片区", "LDO / 74LVC / LM5050 等", "待 V1.2 图对照"], font=f_box_s)
    leader(b5, (250, 860), side="left")

    b6 = box(700, 990, ["圆形焊盘 ×8", "疑电源/总线输入焊盘，待核"], font=f_box_s)
    leader(b6, (200, 1010), side="left")
    leader(b6, (185, 1075), side="left")

    b7 = box(60, 1240, ["版本丝印 v1.2"], font=f_box_s)
    leader(b7, (140, 320), side="top")

    y0 = H + 24
    d.line([0, H + 8, W, H + 8], fill=RED, width=4)
    d.text((28, y0), "关键发现", font=f_note, fill=RED)
    notes = [
        "1. 实物丝印 V1.2（此前档案记为 V1.1，以实物为准）；存档原理图仅 V1.0",
        "2. 背面 F303 类 MCU + 正面超级电容在 V1.0 图中均不存在，图物差异大",
        "3. 接线/上电前必须向板卡来源索取 V1.2 原理图或改动说明",
    ]
    for i, t in enumerate(notes):
        d.text((28, y0 + 42 + i * 36), t, font=f_tbl, fill=BLACK)


make(r"C:\Projects\duck-robot\docs\photos\hat-v1.2-front.jpg",
     r"C:\Projects\duck-robot\docs\photos\hat-v1.2-front-annotated.jpg", 260, front)
make(r"C:\Projects\duck-robot\docs\photos\hat-v1.2-back.jpg",
     r"C:\Projects\duck-robot\docs\photos\hat-v1.2-back-annotated.jpg", 240, back)
