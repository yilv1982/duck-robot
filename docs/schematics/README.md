# 已确认硬件原理图档案

存放**本项目实物在手、且已确认对应关系**的硬件原理图/设计源文件。每块板一个子目录，来源与版本钉死在上游提交。查证分析记录另见 `docs/references/`（那里保留研究过程，这里只放权威文件副本）。

| 子目录 | 硬件 | 确认依据 | 权威文件 | 上游来源与版本 |
|---|---|---|---|---|
| `imu-to-dxl-scrapmeta-v0.3/` | 绿色 IMU 板（imu_to_dxl v0.3，32×22mm，STM32G031F8P6 + LSM6DSV16X） | 2026-10-09 用户确认对应 [ScrapMeta/microduck-diy](https://github.com/ScrapMeta/microduck-diy/tree/main/imu_to_dxl) | `*.eprj2`（嘉立创EDA专业版工程，真源） | `main @ aa4c32d`（hardware/ 最后改动，2026-09-10）；MIT |
| `microduck-hat-v1.0-sch/` | 白色鸭图案 HAT（实物丝印 **V1.2**，2026-10-10 照片更正；Radxa Zero / Pi Zero 形态） | 2026-10-09 用户供图并确认 | `SCH_..._2026-10-06.pdf`（5 页原理图，图版本 **V1.0**） | 社区改绘版（嘉立创EDA，原理图 V1.0，2026-09-03~09-20）；派生自官方 pollen-robotics/elec_RPI_Robot_HAT（Apache-2.0）。⚠️ 图物差异大（实物多 F303 MCU + 超级电容）。查证：`docs/references/microduck-hat-20261006/` |

**没有原理图的两件到位硬件**（成品模块，无法开源存档，只留定位信息）：

| 硬件 | 说明 |
|---|---|
| 微雪 Waveshare Bus Servo Adapter (A) | 商品模块，USB/UART 转半双工总线舵机；官方产品页有规格书（waveshare.com），需要时下载存档 |
| 黑色降压模块（XT60，丝印 7.2-16V） | 通用商品模块，无公开原理图；用前实测输入下限/输出（见 PROGRESS 待办） |

> 同源参考：fanhao375 replica 的 imu_to_dxl 原理图 PDF（STM32G031 同引脚布局的另一块板）在参考库 `references/microduck-replica/hardware/imu_to_dxl/imu_to_dxl-原理图.pdf`，可作对照，但**不是本档案板的图**。
