# C 线自建 real2sim2real 学习工程

本工程是 2026-10-15 用户确认的"从零学习"路线的实现：**只借鉴他人公开的物理参数（质量、惯量、安装位形等），仿真模型、任务环境、训练入口全部本项目自行编写**；不复制或加载上游 MJCF/URDF/网格、任务配置、训练脚本或策略权重。通用物理引擎（MuJoCo）与 PPO 算法库（stable-baselines3）作为基础工具使用。

上游数值的全部溯源见[物理参数表](../docs/references/c-motion-training-20261015/physical-params.md)；路线与阶段计划见[训练软件研究](../docs/references/c-motion-training-20261015/research.md)第 6 节。

## 目录

| 路径 | 内容 |
|---|---|
| `params/` | 机器可读参数表（由 `scripts/extract_public_params.py` 只读提取生成） |
| `scripts/extract_public_params.py` | 从参考库只读解析上游公开参数（含自写四元数级联，已与 MuJoCo 内核对拍一致，误差 <1e-6） |
| `scripts/build_model_v0.py` | 从参数表生成 `models/duck_v0.xml`（几何为自建胶囊/盒，端点=关节中心） |
| `models/duck_v0.xml` | 自建 v0 模型（生成物，勿手改——改脚本再生成） |
| `duckstand/env.py` | 自编 gymnasium 环境：v0 站立任务 |
| `train.py` / `play.py` | SB3 PPO 训练入口 / MuJoCo viewer 回放 |

## 环境

```bash
cd training
uv venv .venv --python 3.13
uv pip install mujoco gymnasium stable-baselines3 torch   # Windows pypi torch 为 CPU 版
```

## 用法

```bash
python scripts/extract_public_params.py   # 只读提取参数（参数库变动时重跑）
python scripts/build_model_v0.py          # 重新生成模型
.venv/Scripts/python.exe train.py --steps 1000000 --envs 8
.venv/Scripts/python.exe play.py checkpoints/duck_stand_v022/final.zip
.venv/Scripts/python.exe interact.py      # 交互推扰测试（见下）
```

**推扰（v0.3 环境，2026-10-16 加入）**：`DuckStandEnv` 默认每回合随机对躯干施加 1–3 次水平脉冲力（1–4 N × 0.2–0.4 s，首次 ≥1 s；标定依据：恒零策略 2N 满额 62%、3N 12%）。`env.push_enabled=False` 可关闭（`interact.py` 已默认关闭以免覆写手推的力）；`info["push_force"]` 暴露当前力幅。开启推扰后恒零策略满额率降至 35%——被动稳定不再够用，是 v0.3 主动平衡训练的土壤。

**交互测试**（`interact.py`）：加载策略实时控制，在 viewer 窗口**双击身体选中 → Ctrl+左键拖动**手工施加外力（拖得越远力越大），松手后看机器人自行恢复；摔倒 1s 自动重置。无头预验证：躯干侧推 0.5/1/2 N×0.3 s（最强相当于 ~0.8 m/s 冲量）均活满回合。

## v0 接口约定（训练↔部署一致性以此为准）

- **观测 45 维**：机体系重力方向(3) + 相对 HOME 关节角(14, rad) + 关节速度(14, rad/s) + 上次动作(14)。
- **动作 14 维** ∈ [-1,1]：`q_target = HOME + 0.5 × action`，clip 至关节限位；position actuator 直控。
- **关节顺序**（上游执行器声明序）：`left_hip_yaw, left_hip_roll, left_hip_pitch, left_knee, left_ankle, neck_pitch, head_pitch, head_yaw, head_roll, right_hip_yaw, right_hip_roll, right_hip_pitch, right_knee, right_ankle`。
- 控制周期 50 Hz（timestep 0.002 × decimation 10）；回合 10 s。
- 奖励（站立 v0）：`1.0×upright + 1.0×height + 0.5×joint_home − 0.05×action_rate + 0.5×alive`；终止：倾角 > ~63° 或躯干高度 < 0.6×HOME。

## 自建与借鉴边界（v0）

| 借鉴数值（有溯源） | 自建内容 |
|---|---|
| 连杆质量/质心/惯量（Pollen CAD，XL330 版） | 胶囊/盒简化几何及尺寸 |
| 关节安装 pos/quat/axis/限位（同 CAD） | 执行器 PD 增益（kp=25/kv=2 自选）、场景、地面 |
| HOME 站姿（上游 STAND2） | 观测/奖励/终止/重置设计 |
| HD-1910 BAM 电机参数（kt/R/armature/摩擦）、速度/力矩上限 | 执行器固件电压环增益 KV（自选）、训练入口与超参 |
| 脚底碰撞体 HOME 世界位形与 AABB 尺寸（上游 mesh 对照导出） | 自碰撞 exclude 集合、IMU site 之外的 site/camera |

## 当前状态与已知差距

- **2026-10-16 深夜 v0.4 架构迭代证伪（七轮 2600 万步终局）**：斜率限制器（6rad/s，带宽×8）静态验证全过，但两轮训练（v0.4/v0.4b，std 0.07/0.04）全部学崩（无扰 0%）——无滤波架构下任何噪声水平都学不出安静站，EMA 的学习稳定作用不可替代。**定论：3N≥80% 在单尺度位置动作空间下被两侧夹逼证明不可达**（EMA 侧带宽不足/无滤波侧无法收敛），突破需动作空间重构（分层策略/自适应增益/WPG+残差），超出本轮。env 已回滚 v0.3c 架构并复验。
- **2026-10-16 推扰训练收官（v0.3c 为最终成果）**：四轮共 1100 万步（v0.3/v0.3b/v0.3c/v0.3d，全过程与研究记录第 9 节）。验收：**主动恢复有证据**（受力时输出变化 11.4× 平稳值；4N 推力恒零基线 0% vs 策略 25%）；**无扰回归完美**（10/10 满额、每步 |Δa|=0.0041 安静）；**3N×0.3s 满额率 50%=基线，未达 80% 目标**——归因为动作空间带宽物理极限（EMA 60ms+±0.1rad 在 0.11s 倾倒窗口内只能产生毫米级质心回移，而 3N 冲量需要 0.13m；scale 放大两轮均因探索噪声学崩）。改进方向（非对称动作空间/课程/执行器内建斜率限制/更大算力）见研究记录。
- **2026-10-16 站立策略 v0.2.2（安静站立）**：确定性策略 10/10 活满 10 s、3 倍初始扰动 5/5 活满、输出恒定（每步 |Δa|=0.000）。录像 `videos/policy_1m.mp4`（现为 v0.3c）。
- **乱动问题的诊断与修复**（v0.2→v0.2.2）：环境无持续干扰，乱动来自策略高频输出；平滑惩罚加倍无效（压的是探索方差）；**目标指令 EMA 低通**（α=0.25，近似舵机固件斜率限制，训练/部署一致）后收敛到安静站。
- 环境功能：回合 10 s 截断（修复过 return 硬编码 bug）；推扰事件（PUSH_* 常量，`push_enabled` 开关）；`scripts/eval_push.py` 推扰验收；`interact.py` 交互手推（Ctrl+拖拽）。
- 过程 checkpoint（v0.2 乱动版、v0.2.1、v0.3、v0.3b、v0.3d 学崩版）仅存档勿作成果。
- 下一步：按上列改进方向迭代推扰（或转入速度命令任务）；执行器 BAM 化；域随机化。长期步骤见 research.md 6.2 十阶段。
- 模型层已知差距：质量惯量为 XL330 版 CAD 值（上机前须实测替换）；静置有轻微接触抖动。

## 边界声明

- 本工程产物（模型/策略/checkpoint）仅用于仿真学习，**不接入 Radxa、不驱动实物**；上机须满足 research.md 6.2 第 9 步的防烧板与支撑前提。
- `checkpoints/`、`.venv/` 不入版本库（见 `.gitignore`）。
