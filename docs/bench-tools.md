# 台架/装机工具索引（2026-10-20 更新）

按用户指示整理的现行工具清单：**能复用参考工程现成工具的不再自研**。来源分三类：本项目自研、社区 kit（`references/microduck-community-kit/`，只读，部署=拷贝不改源）、replica（只读参考）。

## 一、改号与装配校准（ID 已完成，零位待校准）

### hls_servo_debugger（社区 kit，**主力复用**）

- 位置：`references/microduck-community-kit/software/hls_servo_debugger/`
- 形态：**浏览器交互式调试器**（Flask + pyserial，前端免构建）。上游记录使用 **HD-1910-C001（固件 3.46）×16 台**；本机 15 颗已用它完成 ID 初始化，但不能由此认定本机固件版本和全部参数行为都已核验。
- 能力（README 全表）：
  - **整机 15 台初始化**：出厂 ID 1 → 按内置 microduck 关节表编号 **10~14 / 20~24 / 30~34**，提供可选初始位置校准、回读校验、写锁保护（解锁 55 号 → 改 ID → 上锁，自动流程）；本机 2026-10-17 选择“不校准只改 ID”，零位尚未完成；
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
- 关键寄存器参考：**ID=5、波特率=6（0=1Mbps）、应答级别=8、卸载条件=19（BIT3 过流）、写锁=55（0=解锁/1=上锁）**。以厂商适用版本资料为依据、工具实现作对照；本机保护位仍需在带载动作前回读。2048 对应关节角 0 以正确机械零姿态已校准为前提，方向 −1 是上游记录，不能当成本机逐关节验收。

### 装盘、CAL 与恢复扭矩（2026-10-20 复核）

- 未装盘且轴未受机构约束时，推荐先到 2048、按正确朝向选最近齿位，再支撑并关扭矩、扶到该关节机械零姿态执行 CAL。这是减少剩余修正的装配工艺，不是 CAL 的协议前提；已有未知 offset 时仅归中不保证最终偏移绝对值小，不自动清 offset。已装好的不因 offset 大就一律拆盘。
- **“转到中位”会实际运动**：社区 `provision.py:881–898` 先使能，再写限速/2048 目标，已装机构不能盲点。CAL 则是重定义当前位置；`protocol.py:629–646` 关扭矩 → 解锁 → `0x0B` → 上锁，不写目标 42，也不重新使能。
- **CAL 成功提示不能替代结果确认**：校后先确认当前位置约为 2048（本机容差未定），恢复扭矩前须以当前坐标对齐目标并回读。C 线 `/api/torque` 直接使能，没有自动对齐；B 线 servo-web 的“先对齐再使能”实现不能算作 C 工具已有功能。未确认前保持关扭矩。
- 正确零姿态不是带非零角度的 home/站姿；孔位能装上也不等于零位正确。单圈目标限制不保证反馈永远在 `0…4095` 内，异常/超窗时再排查，不自动切多圈、改相位或重启。完整厂商证据、上游反例与源码定位见[装配与 CAL 调研](references/assembly-check-20261017/research.md)。

## 二、IMU 测试

### imu-viewer.py（本项目自研，**姿态实时可视化**）

- 位置：`scripts/imu-viewer.py`（2026-10-17 建；已部署板上 `~/imu-viewer.py`，运行于 **http://192.168.1.35:8766**）
- **浏览器打开即用：3D 立方体实时跟随 IMU 姿态**（晃动板子立方体跟着转），并显示四元数/陀螺 dps/采样计数/状态/读取率。
- 实现零新依赖：Flask（板上已有）+ SSE 推流 + CSS 3D（无 three.js/CDN，离线可用）。数据契约照 imu200.py（@56 读 15 字节：gyro i16×3 + quat half×3，w 由归一恢复）。
- 用法：`python3 imu-viewer.py [--port /dev/ttyS2] [--http 8766] [--sim]`（`--sim` 为无硬件模拟自测；经微雪板看时 `--port COM4`）。
- ⚠️ 与 hls_servo_debugger **不同时占用串口**（后连的会打不开 ttyS2，页面会显示串口错误）。

### 其他 IMU 工具

| 工具 | 来源 | 用途 | 入口 |
|---|---|---|---|
| `imu200.py` | 本项目 | **板②验收**：13 项判据（URT-2/COM 口电脑侧跑） | [flash/tools/imu200/](../flash/tools/imu200/)（双击 `flash/3-验收-imu200.bat`） |
| `sensor_probe.py` | 社区 kit `firmware/v1/host/tools/` | 深度表征：陀螺/加计统计、四元数范数、采样率、静态零偏、PASS/FAIL（只读+复位厂商命令） | 参考；`--port` 适配串口 |

## 三、舵机测试

| 工具 | 来源 | 用途 |
|---|---|---|
| hls_servo_debugger | 社区 kit | 主力（见上，反馈/控制/参数全覆盖） |
| `feetech-ping.py` | 本项目 scripts/（已部署板上 ~/） | 快速 ping/scan/回环；2026-10-17 修复 checksum 公式 bug（见排障记录） |
| `servo_probe.py` | 社区 kit host/tools | 只读排障探测：56~70 块布局、寄存器账本、READ/PING/SYNC_READ 时序、坏校验应答行为 |
| `bus_smoke.py` | 社区 kit host/tools | IMU 节点双协议（DXL/飞特）冒烟 |
| HD1910M Rust 工具 | replica `tools/FeeTech_HD1910M_Servo/` | **不做部署**：`src/protocol.rs`（FT-SCS 实现）、`src/registers.rs`（寄存器定义）、TUTORIAL.md（协议教学）作参考源码；型号/固件适用性仍以厂商资料及实际回读核对 |

## 四、已验证事实备忘（2026-10-17 联调）

- 链路：`ssh radxa` → /dev/ttyS2 → HAT 74LVC → 舵机 ID 1 ✓ / IMU ID 200 ✓（错误码均 0x00）。
- 串口权限：radxa 已入 dialout 组；ttyS2 需 fiq_debugger 已移除（`/etc/kernel/cmdline` 无 `console=ttyFIQ0`）。
- 微雪转接板（COM4）验证可用，作电脑侧备用主机。
- HD-1910 规格：信号高电平 2–5V（3.3V 逻辑兼容）、出厂 ID 1 @1Mbps、ID 范围 0–253。
- **当前状态**：15 颗 ID 已于 2026-10-17 逐颗完成（10–14 / 20–24 / 30–34），零位待按[装配校准流程](references/assembly-check-20261017/research.md)逐关节确认；第一颗“嫌疑坏”舵机继续隔离，不在装机批内。
