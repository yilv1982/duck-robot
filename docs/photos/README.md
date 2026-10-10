# 硬件照片存档

用户实拍硬件照片及派生标注图的统一索引。附件或缓存可能被清理，取得原文件后应及时归档；已在其他专题保存的原件直接链接。**原图与标注图分别保存，每次新增都登记来源、日期及用途。** 全部规则见 [AGENTS.md](../../AGENTS.md)。

## 登记表

| 文件 | 拍摄对象 | 收到日期 | 一句话说明 | 关联待办 |
|---|---|---|---|---|
| [multimeter-delixi-6000counts.jpg](./multimeter-delixi-6000counts.jpg) | 万用表（德力西） | 2026-10-09 | 6000 位手动量程数字万用表，本项目的电测工具 | 降压模块实测、banana_pcb 核极性 |
| [dc-power-supply-delixi-dlx-30v10amf.jpg](./dc-power-supply-delixi-dlx-30v10amf.jpg) | 直流稳压电源（德力西） | 2026-10-10 | DLX-30V10AMF 可调电源，30V/10A 上限 | 降压模块输入下限扫描、首次上电限流保护 |
| [buck-module-xt60.jpg](./buck-module-xt60.jpg) | 黑色降压模块原件 | 2026-10-10 | XT60 输入、选压焊盘 5/6/7V（无电位器） | 输入下限扫描、输出档位确认 |
| [buck-module-xt60-annotated.jpg](./buck-module-xt60-annotated.jpg) | ↑ 的元件标注版 | 2026-10-10 | v2（实测后勘误）：10 处元件编号 + 图例，⑧=3P 排针⑨=PWR OUT 红塑 2P；脚本 `scripts/annotate_buck_module.py` | 对照实物讲解/测试接线 |
| [buck-module-xt60-back.jpg](./buck-module-xt60-back.jpg) | 降压模块背面 | 2026-10-10 | 板名 BUS SERVO POWER SUPPLY V1.3（By 造物の乐趣），背面有 VOLT_SEL 选压焊盘/排针焊点/二维码 | 确认板子身份与接口定义 |
| [buck-module-xt60-back-annotated.jpg](./buck-module-xt60-back-annotated.jpg) | ↑ 的接口标注版 | 2026-10-10 | v4（勘误无 DC 母座）：① 金色圆孔（疑安装孔）② 二维码 ③ XT60 焊点 ④ VOLT_SEL 焊盘（改焊处）⑤ PWR OUT 焊点 ⑥ 3P 排针焊点 ⑦ 安装孔 | 实测/改焊时对照 |
| [waveshare-bus-servo-adapter-a.jpg](./waveshare-bus-servo-adapter-a.jpg) | 微雪总线转接板正面 | 2026-10-10 | Bus Servo Adapter (A) v1.1，双舵机口 + UART 排针 + USB-C + DC 母座/端子 | 台架总线调试接线对照 |
| [waveshare-bus-servo-adapter-a-annotated.jpg](./waveshare-bus-servo-adapter-a-annotated.jpg) | ↑ 的元件标注版 | 2026-10-10 | 7 处标注 + 用法要点；脚本 `scripts/annotate-waveshare-adapter.py` | 台架接线/模式跳线对照 |
| [hat-v1.2-front.jpg](./hat-v1.2-front.jpg) | HAT 正面 | 2026-10-10 | 实物丝印 **V1.2**（此前档案误记 V1.1）；舵机口×2、Qwiic×4、扬声器/麦克风座群、圆柱电容（标记 10 / 50V） | 图物差异核对 |
| [hat-v1.2-back.jpg](./hat-v1.2-back.jpg) | HAT 背面 | 2026-10-10 | **F303 类 MCU（V1.0 原理图无此件）**、PAM8406、40P 排母、圆形焊盘×8 | 索取 V1.2 原理图 |
| [hat-v1.2-front-annotated.jpg](./hat-v1.2-front-annotated.jpg) | 历史正面标注 | 2026-10-10 | **过期，不用于接线**：含“超级电容”等错误；旧脚本 `scripts/annotate-hat.py` 亦需修订后再用 | 现行接口识别见下方复核图 |
| [hat-v1.2-back-annotated.jpg](./hat-v1.2-back-annotated.jpg) | 历史背面标注 | 2026-10-10 | **过期，不用于接线**：八焊盘不能认作独立电池入口 | 现行接口识别见下方复核图 |
| [imu-ldo-location.png](./imu-ldo-location.png) | IMU 板 U3 定位及放大图 | 2026-10-10（制作） | 本会话生成，源图为下行的用户实物标注原件；去掉错误的 5.5V 上限说明，按设计识别 AP2210K-3.3 | [供电复核](../references/power-review-20261010/research.md) |
| [IMU 旧实物标注原件](../schematics/imu-to-dxl-scrapmeta-v0.3/实物板元件标注.jpg) | IMU 板历史总览 | 2026-10-09（原登记） | 原件已在原理图专题保存；**电压说明过期，不用于接线**，仅保留来源追溯 | U3 位置说明使用上行新版 |
| [hat-v1.2-port-review.png](./hat-v1.2-port-review.png) | HAT V1.2 接口复核 | 2026-10-10（制作） | 本会话生成；源图为本表正反面原图，标出两个 3Pin 口、两组 4Pin 空位及圆柱电容；背面旋转 90° | [供电复核](../references/power-review-20261010/research.md)，入口仍待电气核验 |
| [hat-v1.2-wiring-plan.png](./hat-v1.2-wiring-plan.png) | HAT 单链供电意向图 | 2026-10-10（制作） | 本轮用户指定本表 `hat-v1.2-port-review.png` 为底图（已有原件，不重复拷贝）；裁出正背面面板，加 A/B/C 和功能箭头。脚本 `scripts/annotate-hat-wiring.py`；**不标照片上下针极性，非上电放行** | [验证单](../hat-v1.2-test.md)、[供电记录](../references/power-review-20261010/research.md) |

## 降压模块（黑色，XT60 输入）— 2026-10-10 照片识别（正面+背面）

正反面共三次视觉识别 + 像素色块校验（红端子质心与标记完全吻合）。**照片识别、实物未复测**，丝印文字以手上实物为准。

**板子身份（背面丝印）**：**BUS SERVO POWER SUPPLY V1.3**，By **造物の乐趣**（@Make & Share），带二维码（微信压缩图码点损坏，OpenCV 无法解码，**待手机扫描取作者文档**）。网检（2026-10-10）：本地三个参考库与公开网络均无此板资料——社区文章[证实电源板是 microduck 复刻需自研的关键件](https://post.m.smzdm.com/p/a70nxnqg)，此板应为某位社区作者的自研件。丝印 **OUT PWR: 5V or 7.4V MAX 6A**——"5V 或 7.4V"疑似"稳压 5V / 直通电池 7.4V"两种输出模式，待二维码文档或实测确认。

**正面元件（编号对应标注图）：**

| # | 元件 | 识别要点 |
|---|---|---|
| 1 | XT60 输入插座（母头） | Amass，丝印 PWR IN 7.2-18V +/− |
| 2 | 选压焊盘 7V/6V/5V（VOLT_SEL） | 三对焊盘焊锡桥选定输出电压，**当前桥哪档照片不可辨** |
| 3 | 功率电感 | 屏蔽方型，丝印 4R7 = 4.7µH |
| 4 | 降压主控 IC | SOIC 无散热罩，旁有 MAX: 6A 丝印，型号待实物近拍 |
| 5 | 贴片功率器件区 | MOSFET/二极管/电阻小件 |
| 6 | 输入电解电容 ×2 | 丝印 22 16V |
| 7 | 输出电解电容 | 丝印 100µF 16V（CK） |
| 8 | 3P 输出排针（白座） | 丝印 GND/VCC/NC，实测 VCC=6.00V 稳压输出 |
| 9 | PWR OUT 输出端子（红塑 2P） | 实测跟随输入=电池直通，舵机总线走它 |
| 10 | 安装孔 ×4 | 四角 |

**背面另见**：金色圆孔一颗（**2026-10-10 勘误：曾据照片误判为 DC 母座，用户实物核对板上无此件**，疑为镀铜安装孔/过孔，实物待认）、VOLT_SEL 选压焊盘（改焊处）、XT60 大焊点 ×2、3P 排针焊点（左边缘竖排）。

**现行使用边界**：空载已测 VCC 为 6V、约 6.3V 开始跌落；当前方案仅用 PWR OUT 直通口，VCC 闲置，取消为 IMU 改焊 5V 的要求。空载结果不证明整机载流合格，见[供电复核](../references/power-review-20261010/research.md)。

**实测手顺（2026-10-10 已完成空载扫描，结论见 [buck-module-test.md](../buck-module-test.md)）：** 剩余：台架带载复测。~~核 DC 母座~~（勘误：板上无此件）。~~改焊 5V 档~~（2026-10-10 v2 评审取消：AP2210K-3.3 输入上限实为 13.2V，IMU 直挂总线，本板稳压支路无负载）。**该板在整机中的角色与接线见 [power-architecture-v2.md](../power-architecture-v2.md)（历史版本 v1 同目录存档）。**

## 微雪总线转接板 — Bus Servo Adapter (A) v1.1 — 2026-10-10 照片识别

板子身份（左缘竖排丝印）：**Bus Servo Adapter (A) v1.1**，Waveshare，板 42×33mm、安装孔 φ2.5×4（孔距 37×28mm）。成品模块无公开原理图；规格以[微雪官方 wiki](https://www.waveshare.com/wiki/Bus_Servo_Adapter_(A)) 为准。**照片识别、实物未复测**；板载降压 IC 与 USB 串口芯片型号丝印照片上不可辨（USB 串口按微雪资料为 CH343）。

**正面元件（对应标注图 [waveshare-bus-servo-adapter-a-annotated.jpg](./waveshare-bus-servo-adapter-a-annotated.jpg)）：**

| 元件 | 识别要点 |
|---|---|
| 舵机口 ×2（白座 5264-3P） | 丝印 D/V/G = 数据/电源/地；两口并联，菊链最多 253 颗 |
| UART 排针 TX/RX/GND | A 模式接 MCU；微雪 wiki 提醒 **RX-RX、TX-TX 直连**（丝印已按对端标注，勿交叉） |
| 模式跳线帽 ×2（黄色） | **A = UART 控制 / B = USB 控制**，对照板面 A/B 表格丝印 |
| USB-C 座 | B 模式接电脑（CH343 串口，微雪总线工具/LeRobot 可用） |
| DC 母座 5.5/2.1 ∥ DC+/DC- 螺丝端子（绿 2P） | 电源输入，两路并联；丝印 DC 9-12.6V |
| 板载降压（SOIC-8 + 47µH 电感） | 仅供板内逻辑；**不给舵机稳压** |
| PWR 电源指示灯 | 右下角 |
| 半双工转换与阻容区 | UART↔单线总线收发切换电路（芯片丝印未读清） |

**关键事实（官方资料 + 第三方实测一致）**：**输入电压直通舵机口 V 脚，板上不给舵机稳压**——输入必须等于舵机额定电压。丝印 9-12.6V 是针对 ST 系 12V 舵机的标称；微雪 wiki 注明 5-8.4V 亦可输入。

**本项目用法**：HD-1910 是 7.4V 舵机 → 台架喂 **2S（6.6-8.4V）正确，严禁 12V**。角色 = 台架总线调试（舵机改 ID/零位、imu200 验收、对比飞线/FE-URT-2 方案），**不进整机供电链**（整机架构见 [power-architecture-v2.md](../power-architecture-v2.md)）。

## HAT — Microduck Controller Hat for Radxa Zero 3W（实物 V1.2）— 2026-10-10 照片识别

板子身份（正面丝印）：**Microduck Controller Hat for Radxa Zero 3W**，实物版本丝印 **V1.2**（正背面均有）。**⚠️ 此前档案记为 V1.1，以实物为准更正为 V1.2**；存档原理图（[SCH PDF](../references/microduck-hat-20261006/SCH_Microduck-Hat-for-Radxa-Zero_2026-10-06.pdf)）仅为 **V1.0**。照片识别、未上电未复测。

**关键发现（图物差异）**：

1. **背面有一颗 F303 类 MCU**（LQFP48，丝印 ?32F303CET6，品牌前缀不可辨）+ 金属壳晶振——V1.0 原理图 5 页中**没有任何 MCU**，属 V1.1/V1.2 新增，用途未知（总线卸载/电源管理/RTC 皆有可能）。
2. **正面圆柱电容可见“10 / 50V / RVT”标记**，更符合普通电解电容；撤回此前“1.0F 5.5V 超级电容/RTC 备份”的推断。
3. 背面**焊盘 ×8**的位置与排列对应正面两组 4Pin 空接口，不能作为另有独立电池入口的证据；具体网络待 V1.2 图纸或断电测量确认。
4. RS485 座（EH 4P ×2）位置为**空焊盘未焊**；本项目用 TTL 总线，不影响。

**正面元件（现行位置复核见 [hat-v1.2-port-review.png](./hat-v1.2-port-review.png)，旧综合标注不用于接线）：**

| 元件 | 识别要点 |
|---|---|
| 舵机口 ×2（JST EH 3P，左缘大白座） | 丝印 SERVOS；按 V1.0 图：1=GND 2=+BATT 直通 3=DATA（V1.2 待复核） |
| Qwiic/I2C 座 ×4（SH 1.0 4P） | 丝印 I2C3 / I2C4 / I2C5 等 |
| RS485 座焊盘 ×2（EH 4P） | 空焊盘未焊 |
| AP63205 5V 降压区 | 电感丝印 CK 6R8 = 6.8µH，与 V1.0 图 L1 一致 |
| 圆柱电容 | 标记可见 10 / 50V / RVT；无证据称其为超级电容 |
| 扬声器/麦克风座群 | 丝印 SPEAKERS、LEFT/RIGHT、Mic、MICS |
| 40P 排母焊盘（正面） | 排母本体焊在背面，插 Radxa Zero 3W |

**背面元件（位置对应关系见现行接口复核图）：**

| 元件 | 识别要点 |
|---|---|
| F303 类 MCU（LQFP48） | 丝印 ?32F303CET6；**V1.0 图无此件** |
| MCU 晶振 | 金属壳贴片 |
| PAM8406 音频功放（SOP-16） | 与 V1.0 图 U12 一致 |
| 40P 排母 | 2×20，插 Radxa Zero 3W |
| 小信号芯片区 | SOT-23-5/6 多颗（LDO/74LVC/LM5050 等，待 V1.2 图对照） |
| 焊盘 ×8 | 对应正面两组 4Pin 空接口，不是已确认的独立电池输入 |

**接口结论**：照片中只明确看到两个已焊接 SERVOS 3Pin 口，未识别出标注 BAT/VIN 的独立电池入口。现将用户提出的流程画为[接线意向图](./hat-v1.2-wiring-plan.png)：A 两线进电、B 接单条舵机链与末端 IMU、C 对插主控。这与“两口各接一条舵机链”不同；实物针序/路径/载流未核准，不能凭图上电。详见[复核记录](../references/power-review-20261010/research.md)。

**行动项**：接线/上电前向板卡来源索取 **V1.2 原理图或改动说明**（重点：MCU 功能与固件、+BATT 入口形式、舵机口供电路径是否与 V1.0 一致）。供电架构分析（[power-architecture-v2.md](../power-architecture-v2.md)）基于 V1.0 图，舵机口 +BATT 直通等结论需按 V1.2 实物复核。

## 万用表 — 德力西 6000 位数字万用表

6000 Counts（最多显示 5999），手动量程。照片状态：显示 `000 mV` + DC，直流毫伏档空载。

**档位（旋钮）**

- `V⎓` 直流电压 ×4 档：600m / 6 / 60 / 600（V）。测 3.3V/5V 用 6V 档，7.4V 电池及以上用 60V 档
- `V~` 交流电压：600V~（配 Live 火线识别档）
- `Ω` 电阻 ×5 档：600 / 6k / 60k / 600k / 6M（断电测量）
- 蜂鸣/二极管档：响=通；二极管正向约 0.5~0.7V
- `A⎓` 直流电流：60μ / 600μ / 6m / 60m / 600m（红笔在 VΩmA 孔）+ 10A 专用档（红笔换 10A 孔）
- `NCV` 非接触验电、`OFF` 关机

**插孔**

- `COM`：黑表笔，公共端，任何测量都在这
- `VΩmA`：红表笔，测电压/电阻/通断/≤600mA 电流；内部 **600mA 保险丝**
- `10ADC`：仅 10A 档用，**无保险丝（UNFUSED）**，超 10A 直接烧表

**按钮**：左=背光，右=HOLD 读数锁定。

**红线**：禁止带电测电阻；禁止电流档测电压；测完电流红笔立刻插回 VΩmA。

## 直流稳压电源 — 德力西 DLX-30V10AMF

可调线性/开关直流电源，最大 **30V / 10A**。照片状态：3.00V、0A、C.V. 灯亮（恒压、空载）。

**面板**

- `VOLTAGE` 旋钮（带 SETOUT）：调输出电压
- `CURRENT` 旋钮（带 LOCK）：调**电流上限**（限流保护值，不是输出电流）
- `ON/OFF` 按键：输出通断（按键灯亮=输出开）
- 三行显示：绿=电压 V，红=电流 A，黄=功率 W
- `C.V.` 灯=恒压正常工作；电流顶到上限时跳 `C.C.`（恒流，电压自动压下来，起保护作用）

**本项目用法**

1. 降压模块实测（PROGRESS 待办）：电源接模块输入，万用表并输出，电压 12V→6V 扫描找掉出稳压点，判定 2S 电池（带载跌 6.6V）是否可用
2. 电路板首次上电：先限流 0.1~0.2A 排短路，正常后放宽到 0.5~1A
3. 电机单独测试可直接带，但与开发板同测时分两路供电、GND 共地，不共用同一路 5V

## 新增照片规则

- 文件名：`主题-型号.jpg`（英文小写连字符），收到日期写登记表
- 待收照片（拍后补入）：IMU 板 J2 焊盘面、舵机清点、打印件清点、降压模块主控 IC 近拍；**二维码用手机扫（结果发给助手即可），压缩照片解不了码**
- 说明写在对应小节，重点记"照片里当时的状态"和"后续要用它核对什么"
