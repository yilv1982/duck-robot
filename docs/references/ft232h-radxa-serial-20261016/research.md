# FT232H 转接板 ↔ Radxa Zero 3W 串口接线与使用（2026-10-16）

## 日期与问题

- 日期：2026-10-16
- 问题：用户已购得 FT232H 转接板（紫色 Adafruit 兼容板，照片见 [docs/photos/ft232h-breakout-20261016.jpg](../../photos/ft232h-breakout-20261016.jpg)），如何与 Radxa Zero 3W 调试串口连接使用。
- 目的：替代克隆 DAPLink 的串口通道。克隆 DAPLink 在 1.5M 波特下启动突发丢字节/乱码的根因是**其固件无硬件 FIFO/DMA、实时性不足**（勘误后的结论，150KB/s 仅占全速 USB 有效吞吐约 15%，带宽不是瓶颈——见 [daplink-connectivity-20261014](../daplink-connectivity-20261014/research.md)）；FT232H 有硬件缓冲与成熟 USB 栈，预期 1.5M 全程干净。
- 证据级别：照片识别 + Adafruit 官方文档 + 本项目既有实测（Radxa 针位 2026-10-13 已实测收到 DDR banner）的组合；**FT232H 侧接线与驱动流程尚未本机实测**。

## 来源

- Adafruit FT232H Breakout 官方指南 Serial UART 页（D0=TX / D1=RX、3.3V/5V 信号安全、出厂即 USB 串口 COM 口、UART 与 MPSSE 二选一）：<https://learn.adafruit.com/adafruit-ft232h-breakout/serial-uart>
- 本项目接线速查卡（锚定数法/交叉原则/供电参数，实测）：[emmc-flash-radxa-zero3w-20261013](../emmc-flash-radxa-zero3w-20261013/research.md)「接线」一节
- 板卡照片识别登记：[docs/photos/README.md](../../photos/README.md)「FT232H 转接板」小节

## 板卡要点（照片识别）

- Adafruit FT232H Breakout 兼容板：USB-C、两排孔 D0–D7（ADBUS）/ C0–C9（ACBUS）+ 3V/5V/Gnd。
- UART 模式引脚：**D0 = TX（板发出）、D1 = RX（板接收）**；D2/D3 = RTS/CTS（console 不用，不接）。丝印 TX/RX 相对转接板自己。
- 电平：3.3V 逻辑（VCCIO 由板载 LDO 供，Adafruit 原版明确 3.3V/5V 信号均可安全对接 3.3V 目标；兼容板按同设计推断，照片未见电平跳线）→ 与 Radxa GPIO 3.3V 匹配。
- **照片上排针未焊（只有通孔焊盘）→ 接线前先焊排针**，至少下排相邻三脚 Gnd / D0 / D1。
- I2C 拨码开关只影响专用 I2C 座的上拉，UART 场景不用管（任意位置/保持默认）。

## 接线速查（沿用 emmc 专题锚定法）

彩色功能座朝上、板左端**黄=pin1(3.3V)、红=pin2(5V)**，内排全奇数、外排全偶数，从锚点起数：

| FT232H 板 | 接 Radxa Zero 3W 40-pin | 位置锚定 | 作用 |
|---|---|---|---|
| **D1（RX）** | **pin 8**（板 TX） | 外排左起第 4 孔：红(2)→4→6→**8** | 抓日志必接 |
| **GND** | **pin 6 或 pin 9** | pin9=内排左起第 5 孔：黄(1)→3→5→7→**9** | 共地必须 |
| **D0（TX）** | **pin 10**（板 RX） | 外排左起第 5 孔（pin8 下一孔），与 pin8/9 成小三角 | 需向板发按键/登录命令时接 |
| 3V / 5V | **一律不接** | — | Radxa 由稳压电源排针直供，转接板只需 USB 取电 |

- **交叉原则**：D0(FT232H TX)→pin10、D1(FT232H RX)→pin8；**同名相连（TX 对 TX）必然无输出**。此板丝印是相对自己的约定，与微雪转接板"RX-RX 直连"丝印约定不同，别混。
- Radxa 供电沿用既定方案：稳压电源 **5.0V→pin2（或 pin4）、GND→pin6（或 pin9）**，限流 2A，**严禁调高电压、严禁接 pin1（3.3V 轨）**；FT232H 的 GND 接任一 GND 脚即自然共地。

## 软件与操作顺序

1. **数据线**（非充电线，优先台式机后置 USB-A——沿用既往故障①教训）插 FT232H 的 USB-C，设备管理器应出现 **"USB Serial Port (COMx)"**（FTDI VCP 驱动，Win10/11 一般自动装）。FT232H 真品 VID/PID = `0403:6014`。若不出现：换线换口 → 装 FTDI 官方 VCP 驱动 → 仍不行用 FT_Prog 查 EEPROM 接口模式是否 UART（克隆板偶有预配置差异）。
2. 打开 PuTTY（本机已装 v0.85）：Connection type=Serial，COMx，Speed **1500000**，Data bits 8 / Parity None / Stop bits 1，**Flow control 必须改 None**（默认 XON/XOFF 会被输出里的 0x13 字节误触发、显示"冻结"）。带时间戳落盘用 `tools/serial-log.py`，自动登录验证用 `tools/serial-login-test.py`。
3. 确认没有其他窗口/脚本占着该 COM 口（既往故障②：第二个窗口占口表现为打开失败或全静默）。
4. **断电接线**：先焊好排针 → 杜邦线按上表接三根（抓日志两根也行：D1→pin8 + GND）→ 稳压电源空载设定 5.0V/2A、关输出接好电源线、核对极性 → 开输出上电。
5. 预期输出：上电第 1 秒起 DDR banner → U-Boot → 内核全程；系统起来后 rsdk-b1 有 `radxa-zero3 login:`（1.5M 应答，登录流程此前已验证）。
6. 判读：FT232H 走硬件 FIFO，1.5M 启动突发**不应**再丢字节乱码；若仍乱码，先查波特率/流控设置，别先怀疑接线（针位已被 10-13 实测背书）。

## 验证状态与待回填

- 本页接线关系未上机验证；执行后回填：实际 COM 号、是否需补焊排针、1.5M 全程输出是否干净、VID/PID。
- 若 FT232H 通道验证通过：DAPLink 退役为纯 SWD 烧录器角色（IMU 板），串口第一通道改由 FT232H 承担——此变更确认后同步 PROGRESS.md 与相关入口。

## 关联

- [FT232H 与 FT232RL 区别调研（含 JTAG/SWD 概念速记与勘误）](../ft232h-ft232rl-20261014/research.md)
- [Radxa 接线速查卡与供电参数（emmc 专题）](../emmc-flash-radxa-zero3w-20261013/research.md)
- [DAPLink 排障与 1.5M 乱码机制勘误](../daplink-connectivity-20261014/research.md)
