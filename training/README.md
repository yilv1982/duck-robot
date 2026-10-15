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
.venv/Scripts/python.exe train.py --steps 200000 --envs 8
.venv/Scripts/python.exe play.py checkpoints/duck_stand_v0/final.zip
```

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
| HD-1910 BAM armature/frictionloss、堵转力矩上限 | 训练入口与超参 |
| 脚底碰撞体 HOME 世界位形与 AABB 尺寸（上游 mesh 对照导出） | 自碰撞 exclude 集合、IMU site 之外的 site/camera |

## 当前状态与已知差距

- 2026-10-15：模型生成 → 静置验证（HOME 站稳，关节漂 <0.002 rad）→ 环境冒烟 → 两轮各 100 万步 PPO（8 env，CPU fps ~1900）。**仅仿真学习，无任何实物操作/部署。**
- **站立策略尚未收敛**：两轮训练回合存活均停在 ~11–12 步/500（摔倒约 0.22 s）。第一轮（原始奖励/扰动）：ep_rew_mean≈24、|action|≈0.35；第二轮（组合调整：初始扰动减半、加 -0.01 动作幅度惩罚、log_std_init=-1）：std 降到 0.33、explained_variance 0.6，但存活未提升——策略噪声不是瓶颈。
- 失败分析（待下轮逐项验证）：脚支撑面小（0.054×0.043 m），随机动作使膝/髋偏 0.1–0.2 rad 即失稳触发终止（z<0.6×HOME），探索难以命中"安静站立"区域；对照上游速度任务为 4096 env×数万 iteration 量级并带站立课程，本机 1M×8 env 的样本量与课程设计差距明显。
- 下轮迭代候选（一次只改一项）：① 终止条件放宽（z 阈值降到 0.4×HOME 或按倾角单独判）；② 动作低通/EMA 滤波或减小 ACTION_SCALE；③ 站立课程（先零扰动零动作学保持，再加扰动）；④ 并行环境数与步数提升（SubprocVecEnv / WSL+GPU）。
- 长期步骤不变：站立收敛 → 速度命令任务 → 执行器 BAM 化 → 域随机化 → 实物称重/量测替换关键参数（research.md 6.2 十阶段）。
- 模型层已知差距：质量惯量为 XL330 版 CAD 值（C 线 HD-1910 整机更重）；执行器为简化 PD+armature/摩擦，未实现完整 BAM（负载相关摩擦/Stribeck/电压 sag/命令延迟）；无域随机化；静置有轻微接触抖动（接触参数待调）。

## 边界声明

- 本工程产物（模型/策略/checkpoint）仅用于仿真学习，**不接入 Radxa、不驱动实物**；上机须满足 research.md 6.2 第 9 步的防烧板与支撑前提。
- `checkpoints/`、`.venv/` 不入版本库（见 `.gitignore`）。
