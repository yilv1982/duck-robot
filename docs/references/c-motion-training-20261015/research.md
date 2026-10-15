# C 线机器人动作训练：软件研究与分阶段步骤

- 日期：**2026-10-15**。
- 范围：本项目 C 线动作训练的软件研究。**2026-10-15 用户调整当前目标：先用现成仿真模型学习训练，暂不做仿真与实物对齐，也不部署真机。** B 线 `mjlab` / HD1910 平地任务作为学习材料，后续 C 线实物适配研究保留但不作为当前前置条件。
- 状态：**研究与步骤已完成；本轮未安装环境、未训练、未运行策略、未连接或操作硬件。C 线训练尚未开始，尚无本项目验收通过的 C 线模型、策略或部署链路。**
- 当前结论不修改用户已确认的 v2 单链供电决定，不扩展采购；上线前只保留防烧板及必要动作安全约束，不新增串口回环等低价值软件前置测试。

## 1. 先看结论

**当前学习路线（用户确认）：使用现成 HD1910 平地仿真任务 → 按默认配置训练 → 看日志与回放 → 学习续训和单项调参 → 导出 ONNX。** 暂不测量实物、不校准模型、不处理 14→15 舵机映射、不等待完整 runtime；这些只影响未来上机，不阻塞当前仿真学习。以后面向真机再考虑站稳 → 慢走/停步 → 转向等分阶段课程。Radxa 暂不参与，本阶段全部在训练电脑完成。

现成模型、网格、执行器参数与任务配置已经在本地参考工程中；选择 **`Mjlab-Velocity-Flat-MicroDuck-HD1910`**，先不选 Rough。**有仿真模型不等于已经有训练好的策略**；本轮未确认现机存在可用 checkpoint。学习时可以原样使用这套 14 维模型，成果标注为“参考模型仿真学习”，不改称 C 实机成果。以下差异保留给未来上机处理：

1. B 的本地训练工程完整包含 `Mjlab-Velocity-Flat-MicroDuck-HD1910` / `Mjlab-Velocity-Rough-MicroDuck-HD1910`；它们用公开的 1910 BAM 参数替换 XL330 执行器，但保留原 Microduck 几何、质量惯量、默认站姿及 **14 维动作**。
2. C 线采购/补丁口径是 **15 个舵机**；“总线设备数”不能直接当“策略动作维数”。哪一个关节独立控制、是否需要扩展策略、每个输出映射到哪个 ID，须取得完整 runtime 后确定；**禁止补零/截断/重排来凑维度**。
3. C 的 `microduck-feetech.patch` 是旧快照；README 描述的后续串口修复不在补丁中。主会话查证当前公开 `main` 指定提交的 `software/` 也没有 `microduck_feetech/` 完整工程，不能写成“部署代码齐全”。
4. A 的 51→14、B 的 61→14 短训练记录都是历史链路证据，不是当前 C 的成熟步态或落地行走验收。

## 2. 证据等级、来源与定位

### 2.1 阅读方法

- **L：本轮本地静态证据**——读取代码/配置/文档、解析 XML、核对哈希；不等于执行通过。
- **H：历史本项目记录**——2026-09-29 的 A/B 验收、2026-10-14 的 Radxa 操作；本轮没有重跑。
- **U：上游声明/上游实测记录**——C 作者台架结果、公开参数来源；不得写成本项目实测。
- **M：主会话本轮核查回报**——工具命令与 GitHub API 的实际输出；本分析角色未重复探测。
- **P：本轮建议/待验证设计**——下面的 C 线课程、模型适配和验收安排；不是已存在的实现。

以下本地路径均相对 **`E:/Projects/duck-robot/`**；缩写 **T** = [`references/microduck-replica/software/training/`](../../../references/microduck-replica/software/training/README.md)。行号对应本轮读取快照，可用函数名/小节名重新定位。

| 编号 | 来源与关键定位 | 等级与支持的结论 |
|---|---|---|
| E01 | [T/UPSTREAM.md](../../../references/microduck-replica/software/training/UPSTREAM.md)，固定来源/作者与许可证；`T/README.md` 快速开始、任务表 | L/U：训练源码来自 `fanhao375/microduck_rl@d9e1926c5220a0eb79fa5aab9df7b336f8e9a226`，Pollen 基线 `d424a0c899f6b33cbd3daeb279913134349c0b63`；HD1910 是参考基线，不是本机测量模型 |
| E02 | [T/pyproject.toml](../../../references/microduck-replica/software/training/pyproject.toml) 14–43、`tool.uv.sources`；`T/uv.lock` | L：Python `>=3.12,<3.13`、mjlab `1.3.0`、Warp `1.12.0`、torch `2.9.1`；BAM 分支来源由锁文件固定；没有证明现机依赖已就绪 |
| E03 | [T/src/mjlab_microduck/train_cli.py](../../../references/microduck-replica/software/training/src/mjlab_microduck/train_cli.py) 1–31；[tasks/__init__.py](../../../references/microduck-replica/software/training/src/mjlab_microduck/tasks/__init__.py) 71–101 | L：不带 `--hf-jobs` 时转交 `mjlab.scripts.train`；注册了 XL330 和独立 HD1910 Flat/Rough 任务 |
| E04 | [microduck_hd1910_env_cfg.py](../../../references/microduck-replica/software/training/src/mjlab_microduck/tasks/microduck_hd1910_env_cfg.py) 17–50 | L：复制基类机器人再替换 Feetech BAM；`kp_fw=5`、仿真电压 7.4–8.0 V、lag 3–6；独立日志名 `microduck_hd1910_velocity`；均非本机调参结果 |
| E05 | [1910 参数来源](../../../references/microduck-replica/software/training/src/mjlab_microduck/robot/hd1910/README.md)，固定来源/当前应用；[feetech_bam.py](../../../references/microduck-replica/software/training/src/mjlab_microduck/actuator/feetech_bam.py) 16–44 | L/U：公开 1910 M6 参数、飞特目标角度历史初始化适配；不是本项目系统辨识；不能把 `q_offset` 当装配零位 |
| E06 | [microduck_constants.py](../../../references/microduck-replica/software/training/src/mjlab_microduck/robot/microduck_constants.py) 14–28、73–95、120–133、159–166；[robot_walk.xml](../../../references/microduck-replica/software/training/src/mjlab_microduck/robot/microduck/robot_walk.xml) 411–426 | L：步行 MJCF 路径、HOME、XL330 BAM 原始假设；本轮只读 XML 实际数出 14 个 position actuator，不是加载仿真后的性能验证 |
| E07 | [microduck_velocity_env_cfg.py](../../../references/microduck-replica/software/training/src/mjlab_microduck/tasks/microduck_velocity_env_cfg.py) 263–355、532–633、637–727、776–908、912–949 | L：动作缩放、奖励、观测、命令、课程与 PPO 配置，详见第 4 节 |
| E08 | [mdp.py](../../../references/microduck-replica/software/training/src/mjlab_microduck/tasks/mdp.py) `reset_action_history`(229)、`standing_envs_curriculum`(3295)、`reward_weight`(3442)、`VelocityCommandCommandOnly`(4505)、`head_pose_tracking`(5128)；[训练规则](../../../references/microduck-replica/software/training/AGENTS.md) 42–78、Commands/observations 与 Curricula | L/U：命令/课程接口与共享契约；本轮只读，未执行其中的 smoke/test 要求，也不把它们另列成本项目软件前置门槛 |
| E09 | [scripts/export.py](../../../references/microduck-replica/software/training/scripts/export.py) 24–39、176–201、220–241；[scripts/infer_policy.py](../../../references/microduck-replica/software/training/scripts/infer_policy.py) 39–61、587–601、829–836、882–898、984–1028 | L：官方导出包含 normalizer/metadata；通用 CPU 演示需要正确观测模式且仍用 XML position/XL330 限流假设，不是 C 仿真验收器 |
| E10 | [test_hd1910_cfg.py](../../../references/microduck-replica/software/training/tests/test_hd1910_cfg.py) 39–58；[test_hd1910_rollout.py](../../../references/microduck-replica/software/training/tests/test_hd1910_rollout.py) 18 | L：源码断言 14 动作、61 actor 输入、控制周期 0.02 s；**本轮未运行这些测试** |
| E11 | [docs/a-training.md](../../a-training.md) 3–14、22–43、74–100；[docs/b-training.md](../../b-training.md) 3–45；[local-changes/README.md](../../../local-changes/README.md) | H/L：A/B 旧短训练与归档边界；A 提取件不是可直接运行的工程 |
| E12 | [C 补丁 README](../../../references/microduck-community-kit/firmware/v1/patches/README.md) 7–23、316–367、第六节；[microduck-feetech.patch](../../../references/microduck-community-kit/firmware/v1/patches/microduck-feetech.patch) 471、911 等 | L/U/M：旧补丁与后续工作树描述不等同；台架、参数、保护与接口边界见第 5 节；不推断工作树是否私有 |
| E13 | [Radxa 环境记录](../radxa-env-check-20261014/research.md)，处理表/验证状态；[PROGRESS](../../../PROGRESS.md) 2026-10-14 环境核查 | H：pyserial/cmake 与 UART2 overlay 已在当日处理；不是本轮再次 SSH 核验，更不代表 robotd 已部署 |
| E14 | 主会话 2026-10-15 核查命令及 GitHub API 回报，完整关键信息见第 3/5 节 | M：工具存在性、公开路径缺失；不证明训练环境功能或硬件性能 |

可追溯上游 URL：

- [B 训练导入版本](https://github.com/fanhao375/microduck_rl/tree/d9e1926c5220a0eb79fa5aab9df7b336f8e9a226)。来源版本来自本地 `UPSTREAM.md`，本轮没有重新下载核验该整树。
- [LuwuDynamics 1910 参数固定版本](https://github.com/LuwuDynamics/xgoduck_rl/blob/326d77a1122870bdefa2c36403937502c958e69c/src/mjlab_microduck/robot/xgoduck/params/1910_m6.json)，来源记录的 SHA-256 为 `ef2d51adfb1cc0831b9b02ca19aa9176fceecdf725148d084378d7d9a64afceb`；本轮未重新开展辨识或核验其试验条件。
- [Pollen Microduck RL](https://github.com/pollen-robotics/microduck_rl)、[BAM](https://github.com/Rhoban/bam)、[mjlab](https://github.com/mujocolab/mjlab)、[C 社区套件](https://github.com/jyg9/microduck-community-kit)。代码/模型许可分别适用，Microduck 网格不是因训练代码为 Apache-2.0 就可直接商用。

## 3. 当前能先做什么：电脑与机载端分工

### 3.1 主会话本轮工具清点（M）

| 查询 | 回报 | 能确认 / 不能确认 |
|---|---|---|
| Windows `nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader` | `NVIDIA GeForce RTX 4080, 16376 MiB, 616.92` | 约 16 GB 显存 GPU 与 Windows 驱动可查询；不代表 WSL CUDA/PyTorch/Warp 已可训练 |
| `wsl --list --quiet`，后续 `wsl --list --verbose` | Ubuntu / docker-desktop；后者明确 Ubuntu **Running / VERSION 2**，docker-desktop Stopped / VERSION 2 | WSL2 Ubuntu 已注册且运行；未验证 Linux 内训练依赖、旧 venv 或 CUDA 功能 |
| `uv --version` | `0.10.8` | 本次 Windows PATH 的 uv 可用；不等于 WSL uv 或历史 uv 版本 |
| PATH 查询 | `cargo.exe` 不在 Windows PATH；`python.exe` 命中非本项目工具 venv | 不推断 Rust 完全未安装或 WSL 无 Rust；不复用无关工具 venv 作为项目环境 |

**现在可以先做**：确定动作目标与验收尺度；选择 B 的 HD1910 平地框架作为工作副本来源；列出 C 线缺失的模型/映射/执行器响应数据；设计观测—策略—runtime 契约。下一轮实施时再盘点 Ubuntu 内环境并在可写副本建立独立 Python 3.12 环境。工具盘点是资源选择，不是要求先跑一套无关软件自检。

本轮没有创建训练工作副本、没有执行 `uv sync`，也没有写入 `references/`。后续训练的日志、checkpoint、模型修订和锁文件更新必须留在本项目明确建立的**可写工作区**，不能直接在只读参考树中跑训练。

### 3.2 Radxa 端（H，不是本轮实测）

2026-10-14 记录已完成 `python3-serial 3.5`、`cmake 3.25.1`、`rk3568-uart2-m0` overlay；当日已确认 `/dev/ttyS2` 出现。无需再把“安装这两包/启用 UART2”列为未完成项。该记录不证明 C runtime、ONNX 推理依赖或端到端 50 Hz 已就绪。

训练电脑产出策略；机载端以后承担观测采集、ONNX 推理、关节目标发送、故障处理和人工停机。**不能因为 Radxa 有 Python/串口就跳到加载旧策略上机。**

## 4. B 线可以借鉴的训练链路与不可混用的契约

### 4.1 入口、依赖、模型与训练算法（L）

- 入口：Python 包的 `mjlab.tasks` 插件注册任务；项目 `train` CLI 默认调用 `mjlab.scripts.train`。HD1910 平地任务比 XL330 或翻滚/起身任务更接近本轮目标。云端 `--hf-jobs` 不是本轮必需，不提交云作业。
- 依赖：Python 3.12，mjlab 1.3.0、Warp 1.12.0、torch 2.9.1；BAM 源码锁定 `62bd8ce12154340be97e06f7f41a0ca8f116d967`（来源见 E01/E02），配套 ONNXRuntime。不能把 Radxa 的 Python 3.11 或 PATH 中无关 Python 当该训练环境。
- 机器人：步行使用 `robot_walk.xml`，HOME 来自 `microduck_constants.py`；14 个主动关节 = 左腿 5 + 颈/头 4 + 右腿 5，`passive_*` 不进入动作/关节观测。HD1910 工厂只替换执行器，不自动校正实物几何、重心、惯量、足底、零位和限位。
- HD1910 M6 公开参数中的 `actuator: "sts3215"` 选择飞特控制器实现，不是证实本机等于 STS3215。`kp_fw=5`、电压/压降与延迟是该参考仿真设置；`max_velocity=100` 用于目标斜率近似放开，不是实物转速；`q_offset` 不是装配零位，JSON delay 与队列 lag 不应机械相加。
- PPO：actor/critic MLP 均为 `(512,256,128)` + ELU，启用观测归一化；每轮每环境采样 24 控制步，参考默认最多 50,000 iterations、每 250 保存一次。**默认上限不是收敛保证或本机建议预算**；4096 环境等上游规模也不能当本机吞吐结论。

### 4.2 观测与动作（L；50 Hz 来自源码约定/测试断言，未运行）

B 新策略的 actor 输入是 **61 维**，顺序如下：

```text
角速度(3) + 机体坐标重力方向(3)
+ 相对 HOME 的关节角(14) + 关节速度(14) + 上次动作(14)
+ 速度命令 twist[vx,vy,wz](3)
+ 头部姿态偏移[neck_pitch,head_pitch,head_yaw,head_roll](4)
+ 身体姿态偏移[x,y,z,roll,pitch,yaw](6)
= 61
```

默认使用 projected gravity；actor 不使用仿真真值 base linear velocity，critic 可使用额外特权信息。IMU 坐标、单位、关节速度延迟、噪声及编码器偏差必须保持训练/部署一致。B 配置中 IMU 观测有 0–1 个控制步延迟、joint velocity 有 1 个控制步延迟；不能把这些参考值宣布成 C 的已测时延。

14 维输出是关节位置偏移，参考关系为 `q_target = HOME + action × 1.0`；上次动作反馈、最终限幅位置、归一化、动作顺序与各关节 ID 映射同样属于接口。策略周期参考 0.02 s（50 Hz），不是默认主控总线已经达到该频率。无动作 EMA 的训练不能悄悄部署成有 EMA 的控制器，反之亦然。

C 适配时须形成一份**尚待建立**的接口表：输入名称/索引/单位/坐标系/归一化、输出关节名/ID/方向/零点/限位、额外关节处理、实际周期/延迟/丢帧策略。若选择沿用 61→14，必须先证明与 C runtime 和机械布局相容；若需要新维度，则训练配置、导出和 runtime 一起改，不把旧 ONNX 当通用文件。

### 4.3 奖励、命令与课程（L）

- 已有主奖励：线速度跟踪 `2.0`、角速度跟踪 `2.0`、upright `2.0`、腿部 HOME pose `1.0`、head pose tracking `2.0`；脚抬升/腾空/打滑、自碰撞、身体角速度、动作变化构成步态与平滑约束。**这里列实际配置权重，不是 C 的最佳权重。**
- 身体姿态槽虽然保留，`body_pose_tracking` 实际 weight 为 **0**；不能说默认速度任务已经学会身体姿态控制。配置中的“tiny weight”等旧注释不能覆盖实际 `0.0`。
- 默认速度命令已经同时覆盖 `vx ±0.4 m/s`、`vy ±0.3 m/s`、`wz ±1 rad/s`，并有 15% 原地转向分桶；站立占比由 2% 起随课程增加。**这不是下面建议的 C 线“先站稳再慢走”课程**，需要未来在工作副本显式收窄/分阶段设置。
- 头部命令为 HOME 偏移，身体命令为 6D 偏移；各任务保留完整命令槽，不随便删维。纯站立阶段可以暂时固定目标，进入下一阶段再逐渐训练新增命令区域；不能声称从未采样的命令已被学习。
- 随机化包括质量/惯量、重心、摩擦、转子惯量、IMU 安装误差、编码器偏置及推扰；`ENABLE_KP_RANDOMIZATION` / `ENABLE_KD_RANDOMIZATION` 当前为 False。不能因为有 DR 就省略主要物理参数匹配。
- 动作变化惩罚从 `-0.1` 分段增至 `-1.0`；课程步数是 `iteration × 24`，不是乘上环境数。奖励函数有返回正 cost 和返回负 penalty 两种，迁移时按函数实际符号解释；总 reward 升高也可能只是学会不动，必须看动作指标与视频。

### 4.4 play / export / 部署边界（L/H）

1. `play` 是固定 checkpoint 的离线回放/评估，不是训练实时直播，也不代表硬件验收。B 的历史文档明确未验收交互 native/viser；本轮没有补做。
2. `scripts/export.py` 用指定 task 的 play 配置重建 env/runner，载入 checkpoint，调用 `runner.export_policy_to_onnx`，将 observation normalizer 包进图，再附 metadata。导出时也要保留确切的模型、配置和 checkpoint，不手工删 normalizer。
3. `infer_policy.py` 的 `--new-cmd-obs` 才选择 61 维命令布局；缺省旧布局是 51 维。更重要的是它使用 XML position actuator，并从 `xl330/m6` 取 `kt` 做限流近似（882–898 行），**不是 HD1910 BAM 的等价 replay**。不能仅加该 flag 就把它称作 C 的 sim2sim/部署验收脚本。
4. 未来 C 的离线导出评估需在**匹配 C 模型与执行器的推理环境**中，使用与 runtime 相同的观测处理和动作后处理；这一过程就是策略交付的一部分，不另加回环/全套软件自检门槛。
5. `scripts/b-training.sh` 默认固定 XL330 task，路径仍指向只读参考树，且没有长训练模式；它是历史入口，不能直接作为当前 C 启动器。

仅供理解入口的 **B 线 HD1910 参考命令，不可当作 C 命令，也不要在本仓库只读 `references/` 中执行**。假设以后已取得可写训练副本及配套环境，当前目录是该副本根，`CHECKPOINT` 是人工选定的真实 checkpoint，输出路径为新文件：

```bash
TASK=Mjlab-Velocity-Flat-MicroDuck-HD1910
# 示例离线预算，不是 C 的推荐规模或收敛保证；本轮未执行。
uv run --frozen train "$TASK" --env.scene.num-envs 512 --agent.max-iterations 500 --agent.logger tensorboard
uv run --frozen play "$TASK" --checkpoint-file "$CHECKPOINT" --num-envs 1 --viewer native
uv run --frozen python scripts/export.py "$TASK" --checkpoint-file "$CHECKPOINT" --num-envs 1 --onnx-file "$OUTPUT_ONNX"
```

这些参数由 E02/E03/E09 与 `scripts/b-training.sh` 155–164 行交叉确认；CLI 实际运行、显存占用和收敛均未验证。`CHECKPOINT`/`OUTPUT_ONNX` 未预设为存在的产物。

## 5. C runtime 当前缺口与上线风险

### 5.1 完整源码缺失与旧补丁矛盾（M + L/U）

主会话本轮成功查询：

1. [GitHub 仓库 API](https://api.github.com/repos/jyg9/microduck-community-kit) 返回默认分支 `main`。
2. [main 提交 API](https://api.github.com/repos/jyg9/microduck-community-kit/commits/main) 本轮解析为 `923708b6d446f335a9110649cf670f65e29fb2be`。
3. [固定提交 software 目录 API](https://api.github.com/repos/jyg9/microduck-community-kit/contents/software?ref=923708b6d446f335a9110649cf670f65e29fb2be) 完整返回 `.gitignore`（file）、`hls_servo_debugger`（dir），**没有 `microduck_feetech`**；本地目录也如此。

只证明该公开提交的该路径缺失，不推断其他分支、私有仓库或作者本机是否有源码。此查询未下载/改动源码。

本地 `microduck-feetech.patch` SHA-256：`60f2d90c70fc65bed83be4e8f99563b5b05c672122337131a25448eb2e1e2810`，本分析角色本轮独立只读复核一致。README 7–23 声明基线为 Pollen `f0d934e`，后续删除 `flush()`、`BURST_IDLE` 2→4 ms、同步上游 10 提交；实际补丁 471 行仍是 2 ms，911 等行仍调用 `flush()`。**不要宣称这个公开补丁已经包含恢复 50 Hz 的后续修复。**

可行后续是取得与文档匹配的源码/版本；或在可写 runtime 工程按旧补丁建立有来源记录的移植，再逐项补齐差异。后者是新的开发工作，不能预先写成现成可安装的包或照搬编译部署命令。

### 5.2 与训练直接相关的边界（U，不是本项目实测）

- 关节正方向、装配零点、`DEFAULT_POSITION` 必须按 C001 实机核对，原 XL330 值不通用；IMU ID 200 必须排除在舵机列表之外，安装矩阵需与实际安装一致。
- `gain=32` 只有上游悬空/台面单点证据；8/26 是比例派生，Kd 保持 0 的负载稳定性仍未证明。B 仿真 `kp_fw=5`、飞特寄存器 Kp 和 MuJoCo 物理 PD `kp` **不是可互抄的同一标度**；不能用一个参数名相同推导响应相同。
- 上游记录 200 导致约 5 A/74°C，自激风险说明增益确实影响安全；32 不是本机上电推荐的整定终值。未来针对 C 真机优化时再匹配主要执行器响应；当前参考模型仿真学习不以此为前置条件。真实保护位/限流检查仍按现行安全操作单，不靠降增益替代过流保护。
- README 第六节的 50 Hz、15/15 跟随是**上游 x86 `/dev/ttyACM0` 台架**结果，不是本项目 Radxa `/dev/ttyS2` 实测，更不是落地行走。
- 电池满/空阈值来自旧 XL330 测量；地址 60 负载方向/65 状态错误位未完整暴露到 `Sensors`。未来 runtime 故障处理不能假装已有完整保护反馈。
- `robotctl init`/舵机收养/改 ID/重启等流程可能使能扭矩、归位或写 EEPROM，不列为本轮可执行的“软件检查”；本轮不提供让用户直接上机的初始化命令。

## 6. 当前执行顺序：先学仿真训练（2026-10-15 用户确认；待实施）

用户明确“对齐仿真模型与实物现在先不做，我先学习怎么训练，如果有现成的仿真模型先用着”。这取代此前把 C 模型/接口适配列为开训前提的安排；不是否认未来 sim2real 需要适配，也不是授权本轮立即安装、长时间训练或操作硬件。

### 6.1 用现成模型学习的七步

| 步骤 | 当前做什么 | 学会什么 / 留下什么 |
|---|---|---|
| 1. 选现成平地任务 | 在注明来源/许可的独立可写副本中使用 `Mjlab-Velocity-Flat-MicroDuck-HD1910`；保留随附几何、网格、质量、执行器参数与 14 维接口，不改参考库 | 认识仿真机器人与任务；不需要实物测量、改模型或补齐第 15 个舵机 |
| 2. 准备训练环境 | 使用电脑的 Ubuntu / NVIDIA GPU，按工程锁文件准备 Python 3.12 和依赖；模型、配置、日志保存在明确位置 | 可重复使用的训练入口；目前 Linux 内依赖仍未核实，不冒充已装好 |
| 3. 按默认任务开始训练 | 保留已有速度命令、奖励和随机化配方，只选择适合电脑的并行环境数与训练预算；不先重写“只站立”课程 | 理解 observation、action、reward、PPO iteration 与 checkpoint；不另加串口回环或固定 5 轮 smoke 等强制前置自检 |
| 4. 看训练日志 | 看 reward、episode length、速度跟踪误差与终止情况，结合后续视频判断；不把 reward 上升直接当“走得好” | 知道训练是否改善、是否只学会不动；极短训练不是成熟步态 |
| 5. 回放 checkpoint | 使用同一个 HD1910 task 的 `play` 加载已保存 checkpoint，看动作从不稳到逐渐改善；没有 checkpoint 时先训练，不假定预训练策略存在 | 学会选模型、观察行走/转向与失败；viewer 是否可用留待实际运行确认 |
| 6. 学习续训与单项调参 | 先学从已有 checkpoint 恢复训练；再在副本中一次只改一个参数，比如速度范围或动作平滑奖励，分别保存配置和日志 | 对比改动前后效果；续训 CLI 按实际安装版本确认，不把“重新训练”误当“恢复训练” |
| 7. 学习导出 | 用相同 task/config 导出包含 normalizer 的 ONNX，并保留来源 checkpoint | 理解训练权重与部署格式的区别；仅练习导出，不传给 Radxa、不驱动真机 |

默认 Flat 是现成速度任务，并非“先站立后走路”的独立阶段课程。先原样学会训练工具链，再决定是否设计自己的动作/奖励；暂不增加 Rough、身体参数辨识、真实总线软件开发等支线。示例命令见第 4.4 节，仍只允许在可写副本中执行，示例预算不代表学会行走所需预算。

**本阶段完成标准**：能说明任务输入/输出和奖励的作用，启动训练、找到 checkpoint、回放并比较两个 checkpoint，再完成一次有记录的调参/续训及导出。不是“模型匹配实物”或“机器人能落地走”。本轮仅更新学习计划，未创建训练副本、安装依赖或启动训练。

### 6.2 未来面向 C 真机的十阶段参考（暂缓；不是当前学习前置条件）

先完成离线准备，不必等整机所有硬件流程结束；但**没有通过既定防烧板检查、动作映射未确定、无可靠支撑/停机措施时，不转入真机动作**。每阶段留下配置版本、checkpoint、回放与指标，是否升级看动作是否达到目标，不看某个固定 iteration 数。

| 步骤 | 做什么 | 本阶段应留下的结果 / 进入下一步条件 |
|---|---|---|
| 1. 定义动作与用途 | 第一版只要站稳、慢速直行/停止、左右转；点头/摆头作为小幅关键帧候选。暂不做跳跃、翻滚、摔倒起身或导航视觉 | 动作清单、指令定义、成功/失败判据；区分平衡 locomotion 与表情动作 |
| 2. 建立可写软件基线 | 从 B 的 HD1910 平地工程建立注明来源/许可的独立副本；在训练电脑 Ubuntu 环境中配置 Python 3.12 与锁定依赖；日志独立命名 | 模型/代码来源、配置与依赖版本、实际训练入口；环境安装需下一轮实施，本轮未做 |
| 3. 对齐 C 线模型和接口 | 校对机械尺寸、质量分布、足底接触、关节方向/HOME/限位、执行器响应/延迟、IMU 坐标；明确 15 个总线舵机与策略关节的关系，并锁定 runtime 版本方案 | C 的 MJCF/执行器配置和接口表；暂缺实物数据可用有标签的估值做离线探索，但不能标“C 已校准”或用于上机 |
| 4. 先学站稳 | 从可支撑的站姿开始，显式给零速度；奖励直立/足部支撑/保持位置，抑制抖动、滑移、撞限位；先简化推扰/命令，不删未来所需输入槽 | 多种初始轻微偏差下能稳定站立；看倾角、站立漂移、跌倒率、动作变化与视频，而非只看 reward；阶段结果未达标就不升级 |
| 5. 慢速直行与停步 | 从站稳策略继续，逐渐增加小幅正向速度；先不混侧移/快速旋转，保留明确的零速度样本和“走→停→再走”切换 | 速度跟踪、停步漂移、跌倒/打滑、足部摆动可接受；不能只训练非零随机命令后假定会停 |
| 6. 加左右转向 | 先小角速度/缓转，再加入原地转向样本；保持站立与直行样本，避免学转向后忘记停步 | 左右方向均成功，转向跟踪和切换不明显增加跌倒；先不追求极限转速 |
| 7. 再加鲁棒性 | 逐步扩大可解释的重心、质量、足底摩擦、供电/执行器响应、IMU/编码器误差和时延变化；受控推扰先在仿真；需要地形时再转 Rough | 不同种子/未参与训练的条件下评估成功率、跟踪误差、倾角、动作平滑及跌倒；不能用随机化掩盖错误的方向/零位/坐标系 |
| 8. 固定策略并导出 | 选择真实表现好的 checkpoint，不只选最后一个；同 task/同模型导出带 normalizer 的 ONNX，记录哈希、观测/动作合同与依赖 | 在匹配 C 模型的离线推理环境复现站/走/停/转；避免直接使用仍带 XL330 假设的 `infer_policy.py` 作为 C 验收依据 |
| 9. 受控上机 | 取得匹配 runtime 后，结合现行 HAT/IMU 操作单核极性、电压轨、限流和真实保护位；可靠支撑、小幅低负载动作，核映射再短时站立/慢走 | 记录温度/电流/电压异常、动作误差和停机原因；异常立即停，不能直接整机放地播放旧策略；本轮没有进行此步骤 |
| 10. 用实机结果回修 | 将实际质量分布、跟踪滞后、摩擦/间隙、稳定性及失败场景写回仿真，再训练/离线评估；每次保留可回退模型与策略包 | sim2real 差异闭环；不能只靠持续提高 Kp 或放宽限制掩盖模型错误 |

**评估可以很小但必须围绕动作**：每阶段选择固定的站/走/停/转命令序列，加若干随机初始条件；报告跌倒次数/总回合、目标速度与实际速度误差、停步位移、倾角和动作变化。阈值先按本机目标协商并记录，本文不虚构已达到的速度、训练时长、通过率或“第几轮必定学会”。离线策略评估属于训练交付，不是额外软件前置自检。

### 6.3 点头、摆头为什么可以不用 RL

有固定支撑、运动幅度小且不明显影响平衡时，用“中位→目标姿态→中位”的时间关键帧，经平滑插值、角度/速度限幅即可表达；实施时仍需已确认的关节映射和机械限位。**这只是实现建议，本仓库本轮没有新增 C 关键帧播放器。**

若在自主站立/行走时动作会影响重心，不能让两个控制器同时争写同一关节：优先通过已训练的 head command 槽请求动作，或在明确的姿态/策略切换机制下协调。B 的头部命令槽可借鉴，但其极限角度、HOME 与头部动力学不能直接搬上 C 实机。

## 7. A/B 历史资产与归档边界

| 资产 | 能复用的知识 | 不能据此声称 |
|---|---|---|
| A：`docs/a-training.md` / `a-training-validation.json` | 2026-09-29 重建的 51→14 基线、64×5 短训练与带归一化导出经验，模型源固定为 `cb70b792...` | 成熟步态已收敛、旧 19 DOF 部署仿真已修通，或 C 可直接用 A ONNX；文档已明确这些未完成 |
| B：`docs/b-training.md` | 2026-09-29 XL330 64×5 的链路、61→14 导出记录；5 轮只有 7680 环境步 | 该历史验收是 HD1910/C 验收，当前 Ubuntu 旧 venv/日志仍存在，或 native/viser 行走已验收 |
| B：HD1910 接入代码/上游说明 | 公开 M6 参数、初始化适配、任务工厂可借鉴 | 上游自称“本项目”的实验就是 duck-robot 的实验，或 C 模型已被实物校准 |
| `local-changes/` | 2026-10-09 从参考库提取的 A 训练修改、模型来源清单、历史调试记录 | 一个完整可运行工程，或未经授权可复制回只读参考库；旧路径必须逐项核对 |

A 的 3000/6000 iteration 速度扩展课程与 B 当前固定速度范围是两条历史/参考配置，不能混写成同一 C 课程。原始来源和证据保留，未来 C 改动应独立标注；不修改任何上游参考目录。

## 8. 本轮验证、失败/未查证项与下一步

### 已完成的验证

- 阅读根及训练目录 `AGENTS.md`，核对 A/B 历史记录、任务注册、HD1910 工厂、执行器适配、MJCF、奖励/观测/动作、导出与 CPU 演示源码。
- PowerShell 只读解析步行 XML 得到 14 个 actuator，并核对关节顺序；未加载 MuJoCo、未启动训练/推理。
- C patch 哈希及 `BURST_IDLE=2 ms`、保留 `flush()` 与 README 后续修复声明交叉核对；结合主会话公开目录 API 结果记录源码缺口。
- 主会话工具清点仅记 M 级，不升级为环境/训练验收。本地读取曾出现一次 `Select-Object -Skip` 参数笔误、一次 Windows `rg` glob 写法错误，均已更正后重读；不形成源码缺失结论。

- 文档自审：5 个授权文件共核对 150 处本地 Markdown 链接（排除代码片段），目标均存在；新研究无尾随空白，已跟踪文件的 git diff --check 通过。Git 仅提示行尾 LF/CRLF 转换；只读参考库与 BOM 无差异。首次正则链接检查误把代码块维度表达式识别为链接，排除代码后结果为零缺失。

- 同日用户调整学习目标后的复核：仅更新 README、PROGRESS 与本文；148 处本地 Markdown 链接目标存在，`git diff --check` 通过，参考库未改。仅核对现成任务 README 与计划一致性，未运行训练或硬件。

### 未查证 / 当前限制

- 没有运行 Ubuntu 内 `uv`/Python/CUDA/mjlab，不知道旧训练 venv/checkpoint 是否仍在；没有执行 Radxa SSH 复测、编译 Rust runtime、训练、play 或 ONNX 推理。
- 没有取得公开目录缺失的最新 `microduck_feetech` 完整源码；旧 patch 未实际应用/编译；不确认它能与最新官方 main 直接兼容。
- 没有本机 C001 的完整动力学辨识、零位/限位表、15 舵机与策略维数映射、真实闭环时延或机载故障处理实现；当前只能给适配计划，不能给可直接实机执行的 C 命令。
- 第三方 `mjlab` 的完整安装树本轮未载入；继承行为结合仓内配置、静态测试断言与历史说明交叉阅读，不声称现机库执行结果。公开 1910 参数原始试验/固件/供电条件不完整，参数真实性与本机适配仍有限制。
- 本文主要是本地源码研究；除主会话 E14 API 外，其他上游链接用于来源追溯，没有重新获取所有网页/依赖/二进制。

### 文档勘误（不是新增硬件实测）

2026-10-15 更新 README、PROGRESS 和 `.goal/PROJECT_KNOWLEDGE.md` 中“现机无 WSL/旧 E 路径一律失效”的现行指导：当前工作区在 E 盘，WSL2 Ubuntu 已列为 Running，旧训练环境是否可复用仍待查；10-09/10-10 原始历史事实保留并限定日期。A 恢复说明改为可写工作副本，禁止未经授权回填参考树。

Radxa 10-14 研究开头/结尾“全只读、未改软件”和末段“overlay 当前全 disabled”与同页处理表冲突，本轮仅更正为“初检只读；同日已补包并启用 `rk3568-uart2-m0`”。没有声称本轮新增 Radxa 测试。

**下一步最小交付（按用户新指示）**：建立现成 HD1910 Flat 的可写仿真学习副本，准备环境，按默认配方学习训练、日志、checkpoint 回放、续训与导出。C 实物对齐、14/15 关节映射、runtime 获取及真机部署全部暂缓，不作为学习开训门槛。当前仅完成研究与计划更新，训练未开始。
