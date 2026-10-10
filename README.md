# duck-robot

Microduck 小型双足机器人的个人复刻项目。**当前主线为方案 C（社区套件，飞特舵机路线，2026-10-09 定稿）**：选型采购、3D 打印、装配、系统部署与实机验证；强化学习训练在基础验证后再复现（方案 A 已存档，见下）。

进度流水、硬件到位记录与当前待办见 [PROGRESS.md](./PROGRESS.md)。

**项目规则与目录导航：[AGENTS.md](./AGENTS.md)**。协作前先读；调研/图片归档、中文沟通、过期信息清理及自动提交推送按此执行。

## 当前主线：方案 C（飞特路线）

- **执行机构**：飞特 HD-1910-C001 ×15（总线型，官方 robotd 有飞特补丁）
- **主控/总线**：microduck HAT（Radxa Zero 3W，板载 74LVC 半双工驱动接 UART2）+ imu_to_dxl v0.3 作总线从站（ID 200，双协议）
- **供电路线 v2（用户确认推进）**：电池原压经取电/保护进入 HAT 一口，另一口接舵机链+末端 IMU，40P 对插主控并供 5V；正常整机不装微雪板和独立稳压板，暂不增加配电板。先按[基础检查清单](./docs/hat-v1.2-test.md)逐步验证，发现实际问题再调整；**路线确认不等于实物已经验收**。见[接线图](./docs/photos/hat-v1.2-wiring-plan.png)与[架构说明](./docs/power-architecture-v2.md)
- **采购清单**：[BOM.md](./BOM.md)（已重写为 C 线；A 版存档于 [docs/bom-route-a-20260928.md](./docs/bom-route-a-20260928.md)）
- **PCB 打样**：[tools/jlc-order](./tools/jlc-order/README.md) —— 嘉立创开放平台全自动下单（计价→建单→审核→进度跟踪），2026-10-09 已实测下单并审核通过
- **IMU 刷机**：[flash/README.md](./flash/README.md)（DAPLink 接 J2 焊盘）
- 当前工作序列（IMU 刷机、banana_pcb 到板装配、舵机清点、HAT 验证）以 [PROGRESS](./PROGRESS.md) 待办为准；路线定稿理由与 C 线已知缺口见 PROGRESS「方案方向（2026-10-09）」。

## 并行参考库（只读）

三套开源资料统一存放在 **[references/](./references/README.md)**，各自保持独立目录；本项目自己的调研结论仍放在 `docs/references/`。三套上游参考库**只读参考、不修改、不合并代码、硬件配置或采购清单**（2026-10-09 规则；历史混入的本地修改已提取到 [local-changes/](./local-changes/README.md)）：

| 方案 | 本地入口 | 参考内容 |
| :--- | :--- | :--- |
| A：帆哥教程 | [microduck-build-tutorial](./references/microduck-build-tutorial/README.md) | Pi Zero 2 W / OpenRB / XL330 路线（回退线，基线已存档） |
| B：fanhao375 复刻研究 | [microduck-replica](./references/microduck-replica/README.md) | 机械装配、电控与调试资料；兼论 XL330 与飞特路线 |
| C：jyg9 社区套件 | [microduck-community-kit](./references/microduck-community-kit/README.md) | **主参考**：imu_to_dxl / banana_pcb / dxl_hub 三块板、GD32 固件与升级工具、robotd 飞特补丁、HLS 舵机调试器 |

- 方案 B 遵循其 [LICENSE](./references/microduck-replica/LICENSE) 与 [NOTICE](./references/microduck-replica/NOTICE.md)：不同文件许可不同，不能整目录视为 Apache-2.0 或可商用；其打印 CAD 已迁往上游独立仓 [microduck-replica-cad](https://github.com/fanhao375/microduck-replica-cad)，本地 `cad/`、`print/` 不是完整打印包。
- 方案 C 缺口（`software/microduck_feetech/` 完整源码上游未推送、真机整定值仅可参考等）见 PROGRESS「方案方向」。

## 方案 A 回退线（存档）

A 线（XL330 + OpenRB + Pi Zero 2W）的完整步骤基线（阶段 0-7）、硬件约束（XL330/OpenRB 供电与板级电流限制）、仿真/镜像核查结论与 B 站视频笔记已整体移至 **[docs/route-a-baseline-20260928.md](./docs/route-a-baseline-20260928.md)**。相关入口：

- A 线 BOM 存档：[docs/bom-route-a-20260928.md](./docs/bom-route-a-20260928.md)
- 训练基线说明与验收证据：[docs/a-training.md](./docs/a-training.md)、[docs/a-training-validation.json](./docs/a-training-validation.json)
- 恢复 A 线训练环境前，需先把 [local-changes/microduck-build-tutorial/](./local-changes/microduck-build-tutorial/) 提取件按相对路径复制回位（`export_onnx.py` 内为旧机 WSL 路径，现机无 WSL，复用前须改写）。

## 致谢

感谢 [AI-FanGe/Microduck-build-tutorial](https://github.com/AI-FanGe/Microduck-build-tutorial)、[Rhoban/microban](https://github.com/Rhoban/microban)、[pollen-robotics/microduck](https://github.com/pollen-robotics/microduck) 及方案 B/C 上游作者的开源工作；各参考库内容以其自带许可为准。

## 市场调研

- 2026-10-10：全球消费电子玩具公开资料研究——[研究报告](./docs/references/consumer-electronic-toys-market-20261010/research.md)、[30个产品样本与10个案例](./docs/references/consumer-electronic-toys-market-20261010/competitors.md)、[证据与质量日志](./docs/references/consumer-electronic-toys-market-20261010/evidence.md)。行业中立机会判断，不改变本项目C线硬件路线。
