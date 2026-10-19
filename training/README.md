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
| `duckstand/env.py` | 自编 gymnasium 环境：当前为 v0.8 速度命令与相位任务；历史站立策略接口不同 |
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
.venv/Scripts/python.exe train.py --steps 1000000 --envs 8  # 当前49维任务的新训练，不是旧站立任务
```

**checkpoint 兼容性**：当前 49 维环境不能直接回放或续训历史 45 维站立、47 维行走策略；`play.py`、`interact.py` 和评估脚本的旧默认 checkpoint 不再作为现行用法示范。即使维数匹配，也要核对模型、观测语义、scale、EMA 和奖励；旧存档没有完整环境快照。本轮没有运行上述命令。

**推扰（v0.3 起加入）**：`DuckStandEnv` 默认每回合随机对躯干施加 1–3 次水平脉冲力（1–4 N × 0.2–0.4 s，首次 ≥1 s）；此分布固定，尚非由易到难的课程。`env.push_enabled=False` 可关闭（`interact.py` 已默认关闭以免覆写手推的力）；`info["push_force"]` 暴露当前力幅。历史初标定的恒零 2N=62%、3N=12% 来自 8 方向；正式 `eval_push.py` 为 5 时刻×4 方向、全 seed=0 的 20 个 3N 场景，历史恒零汇总为 50%，两组不能直接对比。随机推扰满额 35% 也只是另一条件下的历史汇总。

**交互工具**（`interact.py`）：在策略/环境契约匹配后，可在 viewer 窗口**双击身体选中 → Ctrl+左键拖动**手工施加外力；摔倒 1s 自动重置。历史文字记载侧推 0.5/1/2 N×0.3s 均活满回合，本轮未复验；忽略地面接触的冲量换算不能当作机身实际速度。

## 当前接口（2026-10-19，源码基线 bf9a977；仅仿真）

- **观测 49 维**：机体系重力方向(3) + 相对 HOME 关节角(14, rad) + 关节速度(14, rad/s) + 动作状态(14) + `[vx_cmd, vx_actual]`(2) + `[sin(phase), cos(phase)]`(2)。动作状态因 `step()` 更新顺序晚一拍；机身角速度与侧向速度仍未观测。
- **动作 14 维** ∈ [-1,1]：先 EMA（α=0.25），再 `q_target = HOME + 0.5 × filtered_action`；一阶电机模型输出 motor 力矩。当前错误地用 motor `ctrlrange=±0.94 N·m` 裁剪目标角 rad，尚未修为关节角限位；不能宣称此接口已经正确或可部署。
- **关节顺序**（上游执行器声明序）：`left_hip_yaw, left_hip_roll, left_hip_pitch, left_knee, left_ankle, neck_pitch, head_pitch, head_yaw, head_roll, right_hip_yaw, right_hip_roll, right_hip_pitch, right_knee, right_ankle`。
- 控制周期 50 Hz（timestep 0.002 × decimation 10）；回合 10 s。
- 当前奖励：upright=1、height=1、joint_home=0.1、action_rate=−0.5、action_mag=−0.01、vel_track=4、feet_air=1、phase_foot=2、alive=0.25；`action_rate` 实际比较当前 raw action 与上一 filtered action。终止：重力水平分量范数 >0.9 或躯干高度 <0.6×HOME。
- 历史 v0.3c 站立是 45 维、scale=0.1；v0.6/v0.7 为 47 维，v0.8 起 49 维。当前 PPO 新建策略为普通 MLP `[128,128]`、`log_std_init=-1.0`，没有观测历史；旧站立 checkpoint 的初始化字段为 −1.9，不能混用说明。

## 自建与借鉴边界（v0）

| 借鉴数值（有溯源） | 自建内容 |
|---|---|
| 连杆质量/质心/惯量（Pollen CAD，XL330 版） | 胶囊/盒简化几何及尺寸 |
| 关节安装 pos/quat/axis/限位（同 CAD） | 执行器增益（历史 v0 的 kp=25/kv=2、当前电压环 KV=200 自选）、场景、地面 |
| HOME 站姿（上游 STAND2） | 观测/奖励/终止/重置设计 |
| HD-1910 BAM 电机参数（kt/R/armature/摩擦）、速度/力矩上限 | 执行器固件电压环增益 KV（自选）、训练入口与超参 |
| 脚底碰撞体 HOME 世界位形与 AABB 尺寸（上游 mesh 对照导出） | 自碰撞 exclude 集合、IMU site 之外的 site/camera |

## 当前状态与已知差距

- **2026-10-19 失败复核**：[原因分析与证据](../docs/references/c-motion-training-20261015/failure-analysis-20261019.md)。优先候选为机身速度观测缺失、EMA 状态晚一拍、raw/filtered 混合惩罚、动作尺度/滤波同时变更与缺少课程；因果贡献尚未单项验证。撤回“物理不可达、脚被钉住、无 EMA 必败、架构穷尽、必须数周或 MJX”的旧定论。本轮只做静态核查和文档勘误，未修执行逻辑或重训。
- **站立推扰历史结果**：v0.3c 的 3N×0.3s 满额率 50%=恒零基线，原 ≥80% 目标未达；响应 11.4×、4N 25% vs 0%、无扰 10/10 与每步 |Δa|=0.0041 都是缺逐场原始数据的历史汇总，不能作为普遍恢复已通过的证明。v0.2.2 的无扰 10/10、3 倍初始扰动 5/5、|Δa|=0.000 同属历史记录。
- **v0.4/v0.4b、v0.9 崩溃证据**：现存 checkpoint 末 100 训练回合平均长度分别为 63.95/37.85/69.62 控制步，满 500 步均 0/100；这支持各次训练末段失败，不是新评估，也不能推广到所有无 EMA 配置。v0.4/v0.5 实验环境未完整存档。
- **v0.8/v0.9 日期改为 2026-10-19**：checkpoint 时间和提交时间一致，旧 10-17 错标撤回。v0.8 修命令并同时加相位，不是单项对照；历史 100% 存活是无扰动速度档结果，3N 仅 10–15%，不能称推扰全档稳定。当前环境沿用 v0.8 配置；49 维环境 reset 未重置相位，`eval_walk.py` 改命令未更新首步观测，均待修。
- **记录完整性**：23 个 final（含 2 个 smoke），21 个非 smoke 的 `num_timesteps` 合计 107,311,104，仅为现存字段合计；旧“19 轮约 1.35 亿步”无法复核。checkpoint 没有环境/模型/父 checkpoint/Git SHA 快照，训练 seed 均为 null。详见[元数据](../docs/references/c-motion-training-20261015/checkpoint-metadata-20261019.json)。
- 下一步建议：先冻结可重建的策略/环境契约，修接口问题，再在同场景做小规模单项对照与渐进推扰课程；不直接用堆步数或改 MJX 代替定位。长期步骤见 research.md 6.2 十阶段。
- 模型层已知差距：质量惯量为 XL330 版 CAD 值（上机前须实测替换）；静置有轻微接触抖动。

## 边界声明

- 本工程产物（模型/策略/checkpoint）仅用于仿真学习，**不接入 Radxa、不驱动实物**；上机须满足 research.md 6.2 第 9 步的防烧板与支撑前提。
- `checkpoints/`、`.venv/` 不入版本库（见 `.gitignore`）。
