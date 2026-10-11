"""Show community dxl_hub PCB evidence; not an electrical approval or HAT pin map."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'references/microduck-community-kit/hardware/dxl_hub/docs/1.jpg'
OUTPUT = ROOT / 'docs/photos/dxl-hub-power-distribution-explained.png'


def main():
    src = Image.open(SOURCE).convert('RGB')
    if src.size != (1242, 725):
        raise ValueError('Source dimensions changed: recheck crop and pointer coordinates')
    image = Image.new('RGB', (1440, 1140), '#F3F6FA')
    d = ImageDraw.Draw(image)
    navy, muted, red, green, amber = '#17354A', '#506575', '#C43632', '#12714F', '#955200'

    def font(size, bold=False):
        return ImageFont.truetype('C:/Windows/Fonts/' + ('msyhbd.ttc' if bold else 'msyh.ttc'), size)

    def text(x, y, value, size=25, color=navy, bold=False):
        d.text((x, y), value, font=font(size, bold), fill=color)

    def box(rect, color, fill='white'):
        d.rounded_rectangle(rect, radius=12, outline=color, fill=fill, width=3)

    def arrow(points, color):
        d.line(points, fill=color, width=5, joint='curve')
        a, b = points[-2:]
        theta = math.atan2(b[1]-a[1], b[0]-a[0])
        d.polygon([b, (b[0]-15*math.cos(theta-.5), b[1]-15*math.sin(theta-.5)),
                      (b[0]-15*math.cos(theta+.5), b[1]-15*math.sin(theta+.5))], fill=color)

    text(40, 25, '其他方案的关键：电池先到配电点，再分支', 42, bold=True)
    box((40, 95, 1400, 159), amber, '#FFF1D9')
    text(60, 109, '下图是社区 dxl_hub 的 PCB 设计图，不是你的 HAT V1.2，也不是本机已验证接法。', 27, amber, True)
    # Preserve source board layout, crop around relevant pads and connectors.
    crop = (390, 45, 750, 565)
    image.paste(src.crop(crop).resize((504, 728), Image.Resampling.LANCZOS), (48, 200))
    def xy(x, y):
        return (48+(x-crop[0])*1.4, 200+(y-crop[1])*1.4)
    d.rounded_rectangle((*xy(616, 427), *xy(705, 553)), radius=10, outline=red, width=5)
    d.rounded_rectangle((*xy(474, 77), *xy(716, 408)), radius=10, outline=green, width=5)
    text(43, 935, '红框：J3 电源焊盘；绿框：分支接口区', 22, muted)

    text(610, 195, '上游 README 所示的电力分配', 30, bold=True)
    box((610, 250, 1000, 322), red)
    text(630, 270, '电池 → banana_pcb 取电', 27, red, True)
    arrow([(810, 325), (810, 365)], red)
    box((610, 370, 1000, 485), red)
    text(632, 389, 'dxl_hub 的 J3 两线输入', 27, red, True)
    text(632, 435, 'PCB 网络：+BATT / GND', 25)
    arrow([xy(705, 490), (580, xy(705, 490)[1]), (580, 430), (605, 430)], red)

    for y, label in [(552, '头部链'), (642, '左腿链'), (732, '右腿链'), (822, 'IMU')]:
        box((900, y, 1310, y+65), green)
        text(935, y+14, label, 28, green, True)
        arrow([(810, 485), (810, y+32), (895, y+32)], green)
    text(610, 535, '板内分配', 25, green, True)
    text(610, 577, '共用电池母线', 24, green)
    text(610, 614, '仍是同一数据总线', 24, green)
    text(610, 662, '各支路承担', 24)
    text(610, 698, '各自的负载电流', 24)
    text(610, 755, '不是自动均流', 24, amber)
    text(610, 791, '也不是自动限流', 24, amber)

    box((40, 993, 1400, 1110), amber, '#FFF1D9')
    text(61, 1006, '解决一部分风险：总电流不必先经过一个舵机插头，再去驱动全部关节。', 28, amber, True)
    text(61, 1050, '仍需核验焊线、铜箔、各支路接头和温升；该 PCB 未见保险，1000µF 电容不是过流保护。', 25, amber)
    image.save(OUTPUT)
    print(OUTPUT)


if __name__ == '__main__':
    main()
