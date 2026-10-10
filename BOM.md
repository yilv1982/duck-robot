# BOM 采购清单（当前路线：C · 飞特）

> **2026-10-10 重写**：2026-10-09 路线定稿「主参考 = community-kit 飞特路线」（HD-1910-C001 + HAT + imu_to_dxl 总线从站，见 [PROGRESS](./PROGRESS.md)「方案方向」）。本文件替换原根目录 A 线清单（XL330 + OpenRB + Pi Zero，2026-09-28 编写），A 线清单原样存档于 [docs/bom-route-a-20260928.md](./docs/bom-route-a-20260928.md)——仅当回退 A 线时使用。
>
> 状态口径：`[x]` 到货并登记 · `[~]` 在途/已下单 · `[ ]` 未购或待定。供电口径按 [docs/power-architecture-v2.md](./docs/power-architecture-v2.md)：**电池直通是唯一动力母线，舵机/HAT/IMU 全部吃电池原电压，5V 只存在于 HAT 板内**。

## 核心件

| 状态 | 物料 | 数量 | 用途 | 状态说明 |
| :---: | :--- | :---: | :--- | :--- |
| [x] | 飞特舵机 HD-1910-C001（预期型号） | 15（含嘴） | 关节 | 在手**待清点**：型号/数量/出厂 ID（预期出厂全 ID 1，需逐个设 ID） |
| [x] | 白色鸭图案 HAT | 1 | 主控适配 + 总线物理层（74LVC 半双工 + UART2/ttyS2） | 实物丝印 **V1.2**（10-10 照片确认）；存档原理图为 V1.0，图物差异大（多 F303 类 MCU + 超级电容），**V1.2 图纸待向板卡来源索取**；电气功能按 [docs/hat-v1.2-test.md](./docs/hat-v1.2-test.md) 操作单验证 |
| [x] | IMU 板 imu_to_dxl | 1 | 姿态总线从站（DXL ID 200，双协议） | 确认 ScrapMeta microduck-diy **v0.3**（STM32G031，LDO=AP2210K-3.3 耐 13.2V，**直挂总线**）；待 J2 焊接 → DAPLink 刷机 → imu200 验收（[flash/README](./flash/README.md) 固件包已备），上台架做一次 8.4V 供电验证 |
| [x] | BUS SERVO POWER SUPPLY V1.3 降压板 | 1 | **可选**转接件：XT60 ↔ 螺丝端子 | 空载实测完成（6V 档/下限 ≈6.3V/直通可用）。架构 v2 后**降为可选**：VCC 稳压口闲置不动，拿掉它则自制线直连 HAT |
| [x] | 微雪 Bus Servo Adapter (A) | 1 | 半双工总线转接（台架调试） | 待上机验证，对比飞线方案 |
| [~] | banana_pcb ×5 | 5 | 电池触点取电转接 | 订单 85078132 已下单；到货后装配（焊 U6068 → locker 打印 → 核极性 → 主控支路验证） |
| [~] | DAPLink SWD 调试器 | 1 | IMU 刷机链路 | 在途 |
| [~] | U6068 插针 | 2 | banana_pcb 电池触点 | 在途 |
| [~] | 2S 电池（NP-F550，8.4V） | 1 | 动力 + 逻辑总电源 | 在途；到货登记触点形式，与 banana_pcb 装配一起定供电终案 |

## 供电与充电

| 状态 | 物料 | 说明 |
| :---: | :--- | :--- |
| [ ] | **匹配充电器** | 与 NP-F550 配套；无采购记录，**需确认是否已有** |
| [ ] | **保险丝 5A + 座** | ⚠️ 架构 v2 新增：全链（banana_pcb→电源板→HAT→总线）**目前无任何过流保护**，建议 banana_pcb 出线串 5A 保险 |
| [x] | 电池盒 | banana_pcb 取电方案配套；触点形式待登记 |
| [x] | 直流稳压电源 DLX-30V10AMF | 台架供电/实测（30V/10A，限流保护） |

## 线材与小件

| 状态 | 物料 | 说明 |
| :---: | :--- | :--- |
| [x] | 杜邦线 | IMU J2「直焊焊盘」路线材料；走此路线则无需另购座子+线 |
| [ ] | BM07B-SRSS-TB 座 + SH1.0 7P 线 | 仅当 J2 不走杜邦直焊路线时才需购 |
| [ ] | 飞特 5264 ↔ JST EH 3P 适配 | HAT 舵机座是 EH 3P，飞特原线是 5264 端子——**先试插再决定**（换 5264-3P 座或转接线），不预购 |
| [x] | 无头电子线 | banana_pcb 拆电池焊接出线备选；线径须按 3-5A 核对 |
| [x] | 电烙铁 + 焊锡/助焊剂 | IMU J2 焊接、banana_pcb 装配 |

## 工具（已到位）

万用表（10-09 到货）、直流电源、电烙铁——照片与用法存档见 [docs/photos/](./docs/photos/README.md)。

## 结构件

- [ ] 打印件清点：版本/材料/缺件登记。
- **C 线打印模型以上游独立仓库 [microduck-replica-cad](https://github.com/fanhao375/microduck-replica-cad) 为准**（本地未导入）；A 线的 `references/microduck-build-tutorial/microduck3D打印.3mf` 是 XL330 结构，**不适用 C 线**。
- C 线专属打印件：`banana_pcb_locker`（banana_pcb 到货后打）。

## 安全边界速记（C 线，按架构 v2）

- **全链吃电池直通电压**：舵机 ×15、IMU（板内 AP2210K-3.3 自降 3.3V，耐 13.2V）、HAT +BATT；5V 只在 HAT 板内（AP63205 2A，仅够主控）
- **全链无保险丝**：唯一兜底是电池自带保护板——banana_pcb 出线串 5A 保险（见供电表）
- **EH 座载流 3A** vs 整机常态 3-5A：总线**分两支**挂 CN11/CN12，单链 15 颗会让首座过全链电流
- **IMU 上电前台架验证一次**：限流 0.1A 从 J1-2 升到 8.4V，确认 J2-1 +3V3 稳定、U3 不烫（覆盖实物 LDO 与设计文件不符的残余风险）
- **HAT F1（21mA）在数据线上**，与舵机电源无关，不能当电源保护
- **电源板 MAX 6A** 天花板（若串入链路）；15 舵机同堵转远超，靠 robotd 力矩限幅兜底
- 2S 带载最低 6.6V：若电源板串入链路，其稳压口下限 ≈6.3V（实测）；直通口与拿掉电源板的直连方案无此限制

## A / B 线遗留资产（保留，不适用当前采购）

- A 训练基线与验收：[docs/a-training.md](./docs/a-training.md)；B 线训练（旧机环境）：[docs/b-training.md](./docs/b-training.md)、[.goal/PROJECT_KNOWLEDGE.md](./.goal/PROJECT_KNOWLEDGE.md)
- 回退 A 线时的采购清单：[docs/bom-route-a-20260928.md](./docs/bom-route-a-20260928.md)
