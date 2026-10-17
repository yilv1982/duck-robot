# 舵机 ID 对照表：A 线视频（XL330） vs C 线本机（HD-1910）

2026-10-17 建。用途：跟 A 线教程视频（`references/microduck-build-tutorial/README.md`，YouTube `Vep8AjoCnEM`）学**机械装配动作**时，视频里念的舵机 ID 是 A 线体系；本机 C 线编号完全不同，**装哪颗、认哪颗，一律以"本机 C 线"列为准**，用此表换算。

- **A 线**（视频所示，官方 microduck / Dynamixel XL330）：ID 1~15 连续分配，用 Dynamixel Wizard 设置；
- **C 线**（本机已初始化，microduck_feetech / HD-1910）：10~14 / 20~24 / 30~34 分组分配，用 hls_servo_debugger（:8765）设置；**ID 1 保留**（总线上出现 ID 1 = 有未编号的出厂舵机），**200 = IMU 专用**。

## 按关节对照（装配时按关节名对号）

| 关节 | 部位 | A 线 ID（视频） | C 线 ID（本机） |
|---|---|---:|---:|
| right_hip_yaw 右髋偏航 | 右腿 | 5 | **10** |
| right_hip_roll 右髋侧摆 | 右腿 | 4 | **11** |
| right_hip_pitch 右髋俯仰 | 右腿 | 3 | **12** |
| right_knee 右膝 | 右腿 | 2 | **13** |
| right_ankle 右踝 | 右腿 | 1 | **14** |
| left_hip_yaw 左髋偏航 | 左腿 | 10 | **20** |
| left_hip_roll 左髋侧摆 | 左腿 | 9 | **21** |
| left_hip_pitch 左髋俯仰 | 左腿 | 8 | **22** |
| left_knee 左膝 | 左腿 | 7 | **23** |
| left_ankle 左踝 | 左腿 | 6 | **24** |
| neck_pitch 颈部俯仰 | 头颈 | 12 | **30** |
| head_pitch 头部俯仰 | 头颈 | 11 | **31** |
| head_yaw 头部偏航 | 头颈 | 13 | **32** |
| head_roll 头部侧摆 | 头颈 | 14 | **33** |
| mouth 嘴 | 头颈 | 15 | **34** |
| （IMU） | 链末 | — | **200** |

## ⚠️ 高危撞号（跟视频最容易装错的地方）

| ID | A 线含义 | C 线含义 |
|---:|---|---|
| **10** | left_hip_yaw 左髋偏航 | **right_hip_yaw 右髋偏航** |
| **11~14** | 头颈四关节 | **右腿四关节** |
| **1~5** | 右腿五关节 | **1 = 未编号出厂舵机标志；2~5 不使用** |

跟视频装到头颈/腿部时**不要听 ID 只看位置**；两套体系除关节名外没有任何数字对应关系（编号方向相反：A 从踝往髋编，C 从髋往踝编）。

## 其他差异（同样别照搬视频）

- A 线视频用 Dynamixel Wizard 设 ID/参数——C 线用 :8765 调试器（参数含义也不同，如 A 的 PWM Slope/Shutdown 是 Dynamixel 概念）；
- A 线电气（OpenRB-150/USB）与 C 线（HAT/UART2）不同，接线一切以本机 [HAT 接线意向](./photos/hat-v1.2-wiring-plan.png) 为准；
- A 线嘴部舵机"行走策略不使用"——C 线 15 颗全编（34=mouth），上游飞特版包含嘴。

来源：A 线表 = [build-tutorial README「舵机 ID」](../references/microduck-build-tutorial/README.md)；C 线表 = [hls_servo_debugger provision.py 关节表](../references/microduck-community-kit/software/hls_servo_debugger/hls_debugger/provision.py)（上游 microduck_feetech `model.rs` JOINT_IDS/JOINT_NAMES），2026-10-17 本机已按此表完成 15 颗初始化。
