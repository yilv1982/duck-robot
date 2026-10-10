# -*- coding: utf-8 -*-
"""给微雪 Bus Servo Adapter (A) 照片做元件标注，输出到 docs/photos/。"""
from PIL import Image, ImageDraw, ImageFont

SRC = r"C:\Projects\duck-robot\docs\photos\waveshare-bus-servo-adapter-a.jpg"
DST = r"C:\Projects\duck-robot\docs\photos\waveshare-bus-servo-adapter-a-annotated.jpg"

FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"
RED = (200, 30, 30)

f_title = ImageFont.truetype(FONT_PATH, 40)
f_note = ImageFont.truetype(FONT_PATH, 26)
f_box = ImageFont.truetype(FONT_PATH, 27)
f_tbl = ImageFont.truetype(FONT_PATH, 23)

img = Image.open(SRC).convert("RGB")
W, H = img.size                      # 1080 x 1440
STRIP = 500                          # 底部扩展区高度
canvas = Image.new("RGB", (W, H + STRIP), (255, 255, 255))
canvas.paste(img, (0, 0))
d = ImageDraw.Draw(canvas)


def box(x, y, lines, font=f_box, pad=12):
    """画白底红框圆角标注框，返回框矩形。"""
    widths = [d.textbbox((0, 0), t, font=font)[2] for t in lines]
    bw = max(widths) + pad * 2
    bh = len(lines) * (font.size + 8) + pad * 2 - 8
    d.rounded_rectangle([x, y, x + bw, y + bh], radius=10,
                        fill=(255, 255, 255), outline=RED, width=4)
    for i, t in enumerate(lines):
        d.text((x + pad, y + pad + i * (font.size + 8)), t, font=font, fill=RED)
    return (x, y, x + bw, y + bh)


def leader(rect, dot, side="bottom"):
    """从框的边缘中点引线到目标红点。"""
    x0, y0, x1, y1 = rect
    anchors = {
        "bottom": ((x0 + x1) // 2, y1),
        "top": ((x0 + x1) // 2, y0),
        "left": (x0, (y0 + y1) // 2),
        "right": (x1, (y0 + y1) // 2),
    }
    ax, ay = anchors[side]
    d.line([ax, ay, dot[0], dot[1]], fill=RED, width=4)
    r = 9
    d.ellipse([dot[0] - r, dot[1] - r, dot[0] + r, dot[1] + r],
              fill=RED, outline=(255, 255, 255), width=3)


# ---------- 顶部标题 ----------
d.text((28, 28), "Waveshare Bus Servo Adapter (A) v1.1 — 元件标注", font=f_title, fill=RED)
d.text((28, 86), "2026-10-10 实物照片归档标注（duck-robot）", font=f_note, fill=(90, 90, 90))

# ---------- 顶部区标注框 ----------
r1 = box(40, 170, ["舵机口 ×2（5264-3P）", "D=数据  V=电源(输入直通)  G=地"])
leader(r1, (310, 585))
leader(r1, (570, 585))

r2 = box(580, 140, ["UART 排针 TX/RX/GND", "A 模式接 MCU", "（注意 RX-RX、TX-TX 直连）"])
leader(r2, (795, 560))

r3 = box(700, 330, ["模式跳线帽 ×2", "A=UART 控制 / B=USB 控制"])
leader(r3, (880, 850))

r4 = box(40, 350, ["板载降压（SOIC-8 + 47µH 电感）", "仅供板内逻辑，不给舵机稳压"])
leader(r4, (520, 975))

# ---------- 底部分隔线 ----------
d.line([0, H + 8, W, H + 8], fill=RED, width=4)

# ---------- 底部扩展区：剩余接口标注 ----------
y0 = H + 30
r5 = box(28, y0, ["电源输入：DC 母座 5.5/2.1", "∥ DC+/DC- 螺丝端子", "直通舵机口 V 脚（不稳压）"])
leader(r5, (290, 1060), side="top")
leader(r5, (555, 1175), side="top")

r6 = box(480, y0, ["USB-C：B 模式接电脑（CH343）", "PWR 电源指示灯"])
leader(r6, (780, 1165), side="top")
leader(r6, (945, 1095), side="top")

r7 = box(28, y0 + 125, ["版本丝印：Bus Servo Adapter (A) v1.1", "安装孔 φ2.5 ×4，孔距 37×28mm，板 42×33mm"])
leader(r7, (135, 795), side="top")

# ---------- 底部扩展区：用法要点 ----------
ty = y0 + 270
d.text((28, ty), "在本机的用法要点", font=f_note, fill=RED)
notes = [
    "注意：输入直通舵机口（不稳压），电压须=舵机额定。HD-1910 用 2S（6.6-8.4V），严禁 12V",
    "丝印 DC 9-12.6V 对应 ST 系 12V 舵机；微雪 wiki 注明 5-8.4V 亦可输入，2S 台架可用",
    "角色：台架总线调试（改 ID / 零位 / imu200 验收），不进整机供电链",
]
for i, t in enumerate(notes):
    d.text((28, ty + 42 + i * 36), t, font=f_tbl, fill=(30, 30, 30))

canvas.save(DST, quality=90)
print("saved:", DST, canvas.size)
