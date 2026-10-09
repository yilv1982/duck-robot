# -*- coding: utf-8 -*-
"""给 docs/photos/buck-module-xt60.jpg 画元件标注 → buck-module-xt60-annotated.jpg
坐标经色块质心校验；图例文字为 2026-10-10 空载实测后的勘误版（v2）。"""
from PIL import Image, ImageDraw, ImageFont

SRC = r"C:\Projects\duck-robot\docs\photos\buck-module-xt60.jpg"
DST = r"C:\Projects\duck-robot\docs\photos\buck-module-xt60-annotated.jpg"

def font(size, bold=True):
    for name in ("msyhbd.ttc" if bold else "msyh.ttc", "msyh.ttc", "simhei.ttf"):
        try:
            return ImageFont.truetype(r"C:\Windows\Fonts" + "\\" + name, size)
        except OSError:
            continue
    return ImageFont.load_default()

# (编号, x%, y%, 图例文字) —— 实测后勘误
ITEMS = [
    (1, 70, 56, "XT60 输入插座 · 丝印 PWR IN 7.2-18V（实测 5V 起就能工作）"),
    (2, 44, 48, "选压焊盘 7V/6V/5V —— 实测当前 6V 档（输出 6.00V），接 IMU 前改焊 5V"),
    (3, 29, 51, "功率电感（屏蔽方型，丝印 4R7 = 4.7µH）"),
    (4, 38, 61, "降压主控 IC（旁丝印 MAX: 6A；型号待近拍）"),
    (5, 30, 60, "贴片功率器件区（MOSFET / 二极管 / 电阻小件）"),
    (6, 14, 60, "输入电解电容 ×2（丝印 22 16V）"),
    (7, 46, 59, "输出电解电容（丝印 100µF 16V，CK）"),
    (8, 25, 71, "3P 输出排针（白座）· 丝印 GND/VCC/NC · 实测 VCC=6.00V 稳压"),
    (9, 47, 71, "PWR OUT 输出端子（红塑 2P）· 实测跟随输入 = 电池直通，舵机总线走它"),
    (10, 12, 50, "安装孔 ×4（四角）"),
]

img = Image.open(SRC).convert("RGB")
w, h = img.size
r = max(18, w // 72)
num_f = font(max(20, r))
leg_f = font(max(22, w // 46))
tit_f = font(max(26, w // 38))
pad = int(w * 0.025)

d = ImageDraw.Draw(img)
for n, xp, yp, _ in ITEMS:
    cx, cy = int(xp / 100 * w), int(yp / 100 * h)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(230, 30, 30),
              outline=(255, 255, 255), width=3)
    bb = d.textbbox((0, 0), str(n), font=num_f)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]),
           str(n), font=num_f, fill=(255, 255, 255))

line_h = int(leg_f.size * 1.75)
legend_h = pad * 3 + tit_f.size * 2 + line_h * len(ITEMS)
out = Image.new("RGB", (w, h + legend_h), (255, 255, 255))
out.paste(img, (0, 0))
d = ImageDraw.Draw(out)
y = h + pad
d.text((pad, y), "降压模块正面元件标注 v2（2026-10-10 实测后勘误；位置经色块校验）",
       font=tit_f, fill=(20, 20, 20))
y += tit_f.size + pad
for n, _, _, text in ITEMS:
    d.ellipse([pad, y + line_h // 2 - r // 1.6, pad + r * 1.25, y + line_h // 2 + r // 1.6],
              fill=(230, 30, 30))
    bb = d.textbbox((0, 0), str(n), font=leg_f)
    d.text((pad + r * 0.625 - (bb[2] - bb[0]) / 2 - bb[0],
            y + line_h // 2 - (bb[3] - bb[1]) / 2 - bb[1]), str(n),
           font=leg_f, fill=(255, 255, 255))
    d.text((pad + r * 2.2, y), text, font=leg_f, fill=(30, 30, 30))
    y += line_h

out.save(DST, quality=90)
print(f"saved {DST}  size={out.size}")
