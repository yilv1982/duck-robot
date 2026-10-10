"""Annotate the user's HAT V1.2 review image; does not infer pin orientation.

Run: python scripts/annotate-hat-wiring.py
Input stays unchanged; output is a conditional topology, not electrical approval.
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/photos/hat-v1.2-port-review.png"
OUTPUT = ROOT / "docs/photos/hat-v1.2-wiring-plan.png"
REGULAR = Path("C:/Windows/Fonts/msyh.ttc")
BOLD = Path("C:/Windows/Fonts/msyhbd.ttc")
NAVY, MUTED = "#153348", "#4F6373"
RED, GREEN, BLUE, AMBER = "#C93632", "#137B58", "#116DAC", "#9B5700"


def main():
    source = Image.open(SOURCE).convert("RGB")
    if source.size != (1390, 1140):
        raise ValueError("Source size changed; recheck crop and annotation coordinates")
    canvas = Image.new("RGB", (1800, 1740), "#F4F7FA")
    d = ImageDraw.Draw(canvas)

    def font(size, bold=False):
        return ImageFont.truetype(str(BOLD if bold else REGULAR), size)

    def text(x, y, value, size=29, color=NAVY, bold=False, max_width=None):
        ft = font(size, bold)
        bbox = d.textbbox((0, 0), value, font=ft)
        if max_width is not None and bbox[2] - bbox[0] > max_width:
            raise ValueError(f"Text exceeds allotted width: {value}")
        d.text((x, y), value, font=ft, fill=color)

    def box(rect, color, fill="white", width=3):
        d.rounded_rectangle(rect, radius=15, fill=fill, outline=color, width=width)

    def arrow(points, color, width=6, double=False):
        d.line(points, fill=color, width=width, joint="curve")
        def tip(a, b):
            angle = math.atan2(b[1]-a[1], b[0]-a[0])
            length, spread = 18, 0.48
            d.polygon([b, (b[0]-length*math.cos(angle-spread), b[1]-length*math.sin(angle-spread)),
                       (b[0]-length*math.cos(angle+spread), b[1]-length*math.sin(angle+spread))], fill=color)
        tip(points[-2], points[-1])
        if double:
            tip(points[1], points[0])

    def badge(x, y, label, color):
        box((x, y, x+49, y+47), color, color)
        text(x+11, y+2, label, 31, "white", True)

    text(55, 27, "HAT V1.2：电从哪进，舵机与主控怎么接", 46, bold=True)
    box((55, 104, 1745, 170), AMBER, "#FFF3DD", 2)
    text(76, 118, "接线意向图 · 需核实 V1.2 针脚、供电路径与载流后才能上电；不是已验证的施工图。", 29, AMBER, True, 1645)
    text(55, 190, "01  正面｜两个 SERVOS 口：一个进电，一个接舵机链", 32, bold=True)

    # Crop only the two photo panels from the exact user-supplied marked base.
    # Original photograph geometry and contact positions are not altered.
    front = source.crop((20, 116, 920, 559)).resize((1000, 492), Image.Resampling.LANCZOS)
    canvas.paste(front, (75, 266))
    d.rounded_rectangle((89, 484, 159, 641), radius=8, outline=RED, width=6)
    d.rounded_rectangle((162, 484, 239, 641), radius=8, outline=GREEN, width=6)
    badge(99, 431, "A", RED)
    badge(177, 431, "B", GREEN)

    box((1135, 267, 1745, 454), RED)
    text(1160, 281, "A  电池输入（候选口）", 33, RED, True)
    text(1160, 334, "2S → banana_pcb → 保护 → A", 28, max_width=555)
    text(1160, 376, "只接 +BATT、GND；DATA 不接。", 28, max_width=555)
    text(1160, 416, "正负针位置必须核实，不按照片猜。", 27, RED, max_width=555)
    arrow([(1135, 285), (1110, 285), (1110, 246), (126, 246), (126, 420)], RED)

    box((1135, 492, 1745, 711), GREEN)
    text(1160, 505, "B  舵机 + IMU 链", 33, GREEN, True)
    text(1160, 560, "B → 舵机 1 → … → 舵机 15", 29, max_width=555)
    text(1160, 603, "     → IMU 的 J1（放链末端）", 29, max_width=555)
    text(1160, 651, "三线连接；IMU 的 J3 留空即可。", 28, max_width=555)
    arrow([(202, 647), (202, 779), (1097, 779), (1097, 591), (1135, 591)], GREEN)
    text(270, 742, "电源 + 地 + DATA（三根线）", 26, GREEN)
    text(55, 801, "A/B 是本图分配，不是板上输入/输出标号；只有核验两口同网后，才可交换角色。", 27, MUTED)

    text(55, 855, "02  背面｜黑色 40P 排母对插 Radxa Zero 3W", 32, bold=True)
    back = source.crop((20, 652, 920, 1116)).resize((770, 397), Image.Resampling.LANCZOS)
    canvas.paste(back, (60, 912))
    d.rounded_rectangle((132, 929, 753, 1014), radius=10, outline=BLUE, width=6)
    badge(69, 942, "C", BLUE)
    box((925, 923, 1745, 1138), BLUE)
    text(952, 938, "C  主控从 HAT 获取 5V，并连接 UART", 32, BLUE, True, 770)
    text(952, 993, "关电后对齐 40P，确认方向与 pin1，禁止错位。", 28, max_width=765)
    text(952, 1035, "舵机仍吃电池原电压，不是这一路 5V。", 28, max_width=765)
    text(952, 1077, "未核实防倒灌前，不同时接主控 USB 供电。", 28, max_width=765)
    arrow([(762, 970), (900, 970), (925, 970)], BLUE, double=True)
    box((925, 1165, 1745, 1304), AMBER, "#FFF3DD", 2)
    text(952, 1180, "此接法的瓶颈：A 口承受整机电流", 31, AMBER, True)
    text(952, 1230, "EH 口按现有资料约 3A；15 舵机不能直接放行。", 28, AMBER, max_width=765)
    text(55, 1325, "本方案不使用 4Pin 空焊位及 I²C / 音频口供电；严禁把电池原电压接到 40P 的 5V 脚。", 27, RED)

    text(55, 1380, "03  你的简化流程：功能上成立，仍需通过上电前核验", 32, bold=True)
    items = [((55, 1441, 360, 1533), "电池 + 取电/保护", RED),
             ((417, 1441, 690, 1533), "HAT（A → B）", NAVY),
             ((747, 1441, 1110, 1533), "舵机 1 → … → 15", GREEN),
             ((1167, 1441, 1450, 1533), "IMU（末端）", GREEN)]
    for rect, label, color in items:
        box(rect, color)
        ft = font(28, True)
        width = d.textbbox((0, 0), label, font=ft)[2]
        text((rect[0]+rect[2]-width)/2, rect[1]+27, label, 28, color, True)
    for a, b in [(360, 417), (690, 747), (1110, 1167)]:
        arrow([(a+7, 1487), (b-7, 1487)], GREEN if a >= 690 else RED)
    text(1480, 1452, "主控走 C 口", 28, BLUE, True)
    text(1480, 1497, "不另接电池", 28, BLUE)
    text(55, 1572, "可不装进整机：微雪总线转接板、独立稳压板（前提：HAT 电源与通信验证通过）。", 28, bold=True)
    text(55, 1620, "仍要保留：取电连接、合适的线材/接头、过流保护、匹配充电器；微雪板可留作台架调试。", 27)
    text(55, 1686, "底图：hat-v1.2-port-review.png（本轮用户指定）；派生图，未改原件。2026-10-10 · 仅静态分析，未实测。", 22, MUTED)
    canvas.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
