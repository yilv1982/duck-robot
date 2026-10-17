# 舵机 ID 对照表：A 线视频（XL330） vs C 线本机（HD-1910）

> **⚠️ 2026-10-17 重大更新：本机左右腿映射与上游相反，以下"本机 C 线"列为最终生效版。**

## 本机现行映射（部署契约，2026-10-17 用户定案）

用户实物装配验证后确定（物理正确、舵机已按此改号完毕）：

| ID 段 | 部位 | 关节（ID 组内顺序：髋偏航→髋侧摆→髋俯仰→膝→踝） |
|---|---|---|
| **10~14** | **左腿** | left_hip_yaw / left_hip_roll / left_hip_pitch / left_knee / left_ankle |
| **20~24** | **右腿** | right_hip_yaw / right_hip_roll / right_hip_pitch / right_knee / right_ankle |
| 30~34 | 头颈 | neck_pitch / head_pitch / head_yaw / head_roll / mouth |
| 200 | IMU | 链末 |

**与上游 microduck_feetech `model.rs` 的差异：left/right 两组整体互换**（上游 left=20-24、right=10-14；本机相反）。home 角镜像符号跟随关节名（left_ankle=+25.96°、right_ankle=−25.96°），头颈与方向位不变。

**执行记录**：
- 舵机端：用户已按新映射完成改号（物理装配在先、编号对齐在后）；
- 工具端：板上部署副本 `~/hls_servo_debugger` 的 `provision.py` 关节表已由 [scripts/swap-hls-jointmap.py](../scripts/swap-hls-jointmap.py) 交换（参考库 `references/` 未动），服务已重启生效；
- **将来所有控制软件（robotd 补丁或自研主控、策略部署）必须使用本节映射**，不得照抄上游 `model.rs`，否则左右镜像颠倒。

## A 线视频对照（XL330，仅参考机械动作）

- **A 线**（视频所示，官方 microduck / Dynamixel XL330）：ID 1~15 连续分配，用 Dynamixel Wizard 设置；
- **C 线**（本机已初始化，microduck_feetech / HD-1910）：10~14 / 20~24 / 30~34 分组分配，用 hls_servo_debugger（:8765）设置；**ID 1 保留**（总线上出现 ID 1 = 有未编号的出厂舵机），**200 = IMU 专用**。

## 按关节对照（装配时按关节名对号；C 线列为 2026-10-17 本机最终映射）

| 关节 | 部位 | A 线 ID（视频） | 本机 ID |
|---|---|---:|---:|
| left_hip_yaw 左髋偏航 | 左腿 | 10 | **10** |
| left_hip_roll 左髋侧摆 | 左腿 | 9 | **11** |
| left_hip_pitch 左髋俯仰 | 左腿 | 8 | **12** |
| left_knee 左膝 | 左腿 | 7 | **13** |
| left_ankle 左踝 | 左腿 | 6 | **14** |
| right_hip_yaw 右髋偏航 | 右腿 | 5 | **20** |
| right_hip_roll 右髋侧摆 | 右腿 | 4 | **21** |
| right_hip_pitch 右髋俯仰 | 右腿 | 3 | **22** |
| right_knee 右膝 | 右腿 | 2 | **23** |
| right_ankle 右踝 | 右腿 | 1 | **24** |
| neck_pitch 颈部俯仰 | 头颈 | 12 | **30** |
| head_pitch 头部俯仰 | 头颈 | 11 | **31** |
| head_yaw 头部偏航 | 头颈 | 13 | **32** |
| head_roll 头部侧摆 | 头颈 | 14 | **33** |
| mouth 嘴 | 头颈 | 15 | **34** |
| （IMU） | 链末 | — | **200** |

## ⚠️ 高危撞号（跟视频最容易装错的地方）

| ID | A 线含义 | 本机含义 |
|---:|---|---|
| **10** | left_hip_yaw 左髋偏航 | **left_hip_yaw 左髋偏航（碰巧同名同侧）** |
| **11~14** | 头颈四关节 | **左腿四关节** |
| **6~10** | 左腿+左髋偏航 | 6~9 不使用；**10=左髋偏航** |
| **1~5** | 右腿五关节 | **1 = 未编号出厂舵机标志；2~5 不使用** |
| **20~24** | （不存在） | **右腿五关节** |

跟视频装配时**不要听 ID 只看位置**；A 线与本机除 ID 10 碰巧同义外没有数字对应关系（编号方向相反：A 从踝往髋编，本机从髋往踝编；A 左右与本机左右仅在各自体系内自洽）。

## 其他差异（同样别照搬视频）

- A 线视频用 Dynamixel Wizard 设 ID/参数——本机用 :8765 调试器（参数含义也不同，如 A 的 PWM Slope/Shutdown 是 Dynamixel 概念）；
- A 线电气（OpenRB-150/USB）与 本机（HAT/UART2）不同，接线一切以本机 [HAT 接线意向](./photos/hat-v1.2-wiring-plan.png) 为准；
- A 线嘴部舵机"行走策略不使用"——本机 15 颗全编（34=mouth），上游飞特版包含嘴。

来源：A 线表 = [build-tutorial README「舵机 ID」](../references/microduck-build-tutorial/README.md)；上游关节表 = [hls_servo_debugger provision.py](../references/microduck-community-kit/software/hls_servo_debugger/hls_debugger/provision.py)（源自 microduck_feetech `model.rs`，其 left=20-24/right=10-14 与本机相反）；**本机最终映射 = 用户实物装配验证定案（2026-10-17），由 `scripts/swap-hls-jointmap.py` 应用于板上部署副本**。
