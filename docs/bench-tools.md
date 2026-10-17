# 台架/装机工具索引（2026-10-17 整理）

按用户指示整理的现行工具清单：**能复用参考工程现成工具的不再自研**。来源分三类：本项目自研、社区 kit（`references/microduck-community-kit/`，只读，部署=拷贝不改源）、replica（只读参考）。

## 一、改号与初始化（当前主任务）

### hls_servo_debugger（社区 kit，**主力复用**）

- 位置：`references/microduck-community-kit/software/hls_servo_debugger/`
- 形态：**浏览器交互式调试器**（Flask + pyserial，前端免构建）。虽然名字带 HLS，但上游就是拿 **HD-1910-C001（固件 3.46）×16 台实测**的（README 330/584 行），FT-SCS 协议完全覆盖本机舵机。
- 能力（README 全表）：
  - **整机 15 台初始化**：出厂 ID 1 → 按内置 microduck 关节表编号 **10~14 / 20~24 / 30~34**，含初始位置校准、回读校验、写锁保护（解锁 55 号 → 改 ID → 上锁，自动流程）；
  - PING/扫描、实时反馈（56~70 共 15 字节：位置/速度/负载/电压/温度/电流 + 趋势图）、位置/速度/电流/PWM 控制、全内存表参数界面（0~86）、同步读写、原始十六进制帧调试；
  - `selftest.py` 无硬件协议自检（含从站模拟，可离线验证整个初始化流程）。
- 部署（Radxa，链路即 /dev/ttyS2）——**2026-10-17 已部署完成**：
  ```bash
  # 源码已拷至板上 ~/hls_servo_debugger/（自参考库原样拷贝，未改动）；
  # python3-flask 2.2.2 已装（python3-serial 原有）
  cd ~/hls_servo_debugger
  nohup python3 -m hls_debugger --host 0.0.0.0 > /tmp/hls_debugger.log 2>&1 &
  # 电脑浏览器访问 http://192.168.1.35:8765（实际端口 8765，非 Flask 默认 5000）
  ```
- 安全特性：初始化带回读校验；`hw_test.py` 是真机只读连通测试（PING/READ，不产生动作）。
- 关键内存表事实（Rust 工具 registers.rs 权威核对）：**ID=5、波特率=6（0=1Mbps）、应答级别=8、卸载条件=19（BIT3 过流，出厂只开过热）、写锁=55（0=解锁才能改 EPROM/1=上锁）**、位置 2048=关节角 0、方向位 −1（上游实测）。

## 二、IMU 测试

| 工具 | 来源 | 用途 | 入口 |
|---|---|---|---|
| `imu200.py` | 本项目 | **板②验收主力**：13 项判据（ID 200 在线、@56 读遥测、四元数范数、计数递增、sync_read 时延等），URT-2/COM 口电脑侧跑 | [flash/tools/imu200/](../flash/tools/imu200/)（双击 `flash/3-验收-imu200.bat`） |
| `sensor_probe.py` | 社区 kit `firmware/v1/host/tools/` | 深度表征：陀螺/加计统计、四元数范数、重力一致性、采样率与计数连续性、静态零偏、SFLP 重启检查、PASS/FAIL（只读+一个复位厂商命令） | 参考；`--port` 适配串口 |

## 三、舵机测试

| 工具 | 来源 | 用途 |
|---|---|---|
| hls_servo_debugger | 社区 kit | 主力（见上，反馈/控制/参数全覆盖） |
| `feetech-ping.py` | 本项目 scripts/（已部署板上 ~/） | 快速 ping/scan/回环；2026-10-17 修复 checksum 公式 bug（见排障记录） |
| `servo_probe.py` | 社区 kit host/tools | 只读排障探测：56~70 块布局、寄存器账本、READ/PING/SYNC_READ 时序、坏校验应答行为 |
| `bus_smoke.py` | 社区 kit host/tools | IMU 节点双协议（DXL/飞特）冒烟 |
| HD1910M Rust 工具 | replica `tools/FeeTech_HD1910M_Servo/` | **不做部署**：`src/protocol.rs`（FT-SCS 权威实现）、`src/registers.rs`（内存表权威）、TUTORIAL.md（协议教学）作参考源码 |

## 四、已验证事实备忘（2026-10-17 联调）

- 链路：`ssh radxa` → /dev/ttyS2 → HAT 74LVC → 舵机 ID 1 ✓ / IMU ID 200 ✓（错误码均 0x00）。
- 串口权限：radxa 已入 dialout 组；ttyS2 需 fiq_debugger 已移除（`/etc/kernel/cmdline` 无 `console=ttyFIQ0`）。
- 微雪转接板（COM4）验证可用，作电脑侧备用主机。
- HD-1910 规格：信号高电平 2–5V（3.3V 逻辑兼容）、出厂 ID 1 @1Mbps、ID 范围 0–253。
- **待办**：15 颗逐颗改号（工具就绪后执行）；第一颗"嫌疑坏"舵机隔离待复核。
