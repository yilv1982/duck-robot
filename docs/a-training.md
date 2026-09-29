# 方案 A：新训练基线与验收记录

更新：**2026-09-29**。状态：**已重建、短训练与安全导出通过；尚无成熟行走策略**。
本页只描述方案 A，不修改或借用方案 B 的环境。正式长训练**尚未启动**，smoke 策略**不得部署上机**。

## 1. 已完成什么，未完成什么

- 主会话已完成固定来源/版本 `check`、模型合同、CUDA reset/step、64 env × 5 iterations 从零训练、512 env × 5 iterations 扩容基准及真实 checkpoint 导出。
- 这是以官方模型重新建立的**新训练基线**，不是恢复原先删除的 A `robot/` 训练工程，也不是复现原 `velocity.pt` 的训练历史。
- 51 维 observation / 14 维 action、normalizer 与关节顺序验收通过，不等于行走收敛、鲁棒性或实机安全验收。
- 原部署 `constants.py`、`walk.onnx`、`velocity.pt` 保持不变。旧部署 sim **仍是 19 DOF，尚未重接**新训练模型；不能把新训练链路称为完整实机验证。
- 文档收尾仅查阅现有文件、字节数、SHA-256；没有再次运行 GPU。运行结果来自主会话验收回报。

入口：[训练项目 README](E:/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck/README.md)、[训练脚本](E:/Projects/duck-robot/scripts/a-training.sh)、[机器可读验收记录](E:/Projects/duck-robot/docs/a-training-validation.json)。

## 2. 来源、环境与物理假设

### 新基线来源

官方 [pollen-robotics/microduck_rl](https://github.com/pollen-robotics/microduck_rl) 固定提交
[`cb70b792312d559a4da09064d92009079671815f`](https://github.com/pollen-robotics/microduck_rl/tree/cb70b792312d559a4da09064d92009079671815f)。
模型 XML/assets 从不可变上游 URL 取得，不是从 B 复制。逐文件来源、SHA-256 与许可证据见
[source_manifest.json](E:/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck/src/mjlab_microduck/robot/source_manifest.json)。
代码为 Apache-2.0；上游 3D 模型声明为 Creative Commons BY-SA-NC，未明确版本，不推定为 4.0 或可商用。

BAM 保持 A 原 doc 系列的固定提交 `0007411bd82c48f1bc12ae8382f98e4d8b879c95`（1.0.0）。
独立 WSL venv：`/home/yilv/.venvs/duck-robot-a-training`；源码固定为
`/mnt/e/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck/src/mjlab_microduck`。
Python 3.12.3；mjlab 1.3.0、torch 2.9.1、warp-lang 1.12.0、mujoco 3.10.0。
`uv sync --locked` 安装 149 个包，`uv lock --check` 通过；保留 protobuf/onnx/zmq overrides，
所以 `uv pip check` 仍有两项已知 BAM metadata 冲突（缺 zmq、protobuf<4 与实际 6.33.6 不一致），
**不是全绿依赖声明**。详细安装说明与冲突解释保留在训练项目 README。

### 5 V 与真实性限制

新 A 训练使用 XL330 BAM m6：名义 **5.0 V**、采样范围 **4.5–5.5 V**、下限 4.5 V、`kp_fw=125`、`max_current=1.75 A`。
压降增益和 actuator delay 当前均为零范围；BAM m6 内部摩擦为固定模型。
这不是对本机舵机、稳压电源、负载、摩擦或通信延迟做过的系统辨识。
上游质量/惯量、碰撞体、接触系数、装配差异、IMU 安装误差及实机零位均需继续校准。
原部署文件的旧电气/模型假设没有随训练重建而被修正；新训练 5 V 不代表旧部署配置已合规。
XL330 应按官方 3.7–6.0 V、推荐 5.0 V 供电，仿真参数不能替代真实电源与限流验证。

## 3. 速度课程：第 3000 / 6000 iteration

每 iteration 每 env 采样 24 个 control steps。课程阈值基于 `common_step_counter`（每 env 的控制步），
**不是将所有 env 的样本数累加**；达到阈值后的首次 reset 应用该阶段。

| 阶段 | 控制步阈值 | vx (m/s) | vy (m/s) | 行进 yaw (rad/s) | 原地 yaw (rad/s) |
| --- | --- | --- | --- | --- | --- |
| 起始 | 0 | -0.25～0.25 | -0.15～0.15 | -0.375～0.375 | -0.75～0.75 |
| 3000 iteration | 72000 | -0.35～0.35 | -0.2～0.2 | -0.75～0.75 | -1.5～1.5 |
| 6000 iteration | 144000 | -0.5～0.7 | -0.3～0.3 | -1.5～1.5 | -3.0～3.0 |

3000 阶段同时启用 no-stepping 惩罚并调整站立/原地旋转比例。
play 配置直接采用末阶段速度范围且关闭课程；这些是**训练/评估指令范围，不是已实现的行走速度**。
合同测试验证了配置及阈值边界；5-iteration smoke 没有实际训练到这两个阶段。
证据：[环境配置](E:/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck/src/mjlab_microduck/tasks/microduck_velocity_env_cfg.py)、
[合同脚本](E:/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck/scripts/validate_contract.py)。

## 4. 实际验收命令与结果

以下按固定 WSL 路径展开已验收命令参数，不代表文档任务重新执行。复测会实际占用 GPU，应另行串行安排。

```bash
bash /mnt/e/Projects/duck-robot/scripts/a-training.sh check
/home/yilv/.venvs/duck-robot-a-training/bin/python -I -B \
  /mnt/e/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck/scripts/validate_contract.py \
  --compile-xml --config --env-steps 100 --device cuda:0
bash /mnt/e/Projects/duck-robot/scripts/a-training.sh smoke
```

- `check`：通过，固定 venv、A 源码及依赖版本正确；主会话独立重跑退出码 0。
- 合同：XML 编译、配置、IMU/关节/课程检查通过；**2 env reset + 100 个有限值 step**，`cuda:0`，actor `[2,51]`，action 14。
- smoke：从零，`resume=False`，64 env，5 iterations，TensorBoard，禁止模型上传，**退出码 0**。
- `model_4.pt`：**4720063 bytes**，`iter=4`；`common_step_counter=120`，总采样 **7680 = 64 × 5 × 24**。
- actor 首层 `(512,51)`、末层 `(14,128)`；首层相对 `model_0.pt` 最大变化 **0.00813435018**，normalizer 已更新。
  `model_0.pt` 是早期保存点，不将其描述为完全未训练的初始化；变化证明发生优化，不证明策略已学会行走。

实际 run：

```text
E:/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck/logs/rsl_rl/mjlab_microduck_velocity/2026-09-29_17-23-46_a-smoke-20260929T092337433891036-16974
```

训练证据：该目录的 `model_0.pt`、`model_4.pt`、`params/agent.yaml`、`params/env.yaml` 与 TensorBoard events 文件。
各绝对路径、字节数和 SHA-256 已写入验收 JSON。未收到独立 check/contract stdout 文件路径，故不虚构日志文件。

### 真实 checkpoint 安全导出

```bash
RUN=/mnt/e/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck/logs/rsl_rl/mjlab_microduck_velocity/2026-09-29_17-23-46_a-smoke-20260929T092337433891036-16974
bash /mnt/e/Projects/duck-robot/scripts/a-training.sh export \
  --checkpoint "$RUN/model_4.pt" --output "$RUN/a-smoke.onnx"
```

此为已执行记录：`a-smoke.onnx` 已存在，再次运行必须改用新输出名，入口不会覆盖。
结果：**退出码 0**，**773823 bytes**。单 env CUDA 创建后关闭；ONNX checker、ORT CPU float32 `[1,51] → [1,14]`、
有限值和关节 metadata 验证通过；保留 normalizer，与正常 actor 的 **3 组**确定性输出比较，
最大绝对误差 **`3.2782555e-07`**（`rtol=1e-4, atol=1e-5`）。
这是实 checkpoint 的结果，与早期 CPU 单元测试 `5.59e-8` 分开记录。
已存在输出的负向测试正确拒绝，退出码 1，未触发 GPU 仿真。Reviewer 最终确认显式 ONNX 的 checkpoint hash 关联正确；
另做 26 组 CPU actor/ORT 对比，最大绝对误差 `1.1920929e-06`（独立复核，不与导出器的 3 组结果混淆）。
只认经过安全导出验收的 `a-smoke.onnx`，不把 runner 自动保存的旁路 ONNX 当成相同证据。

### 512 env 扩容基准（不是正式长训练）

```bash
bash /mnt/e/Projects/duck-robot/scripts/a-training.sh train --num-envs 512 --max-iterations 5
```

退出码 **0**，生成 `model_4.pt`；总采样 **61440 = 512 × 5 × 24**。
最后一次 iteration 约 **7568 steps/s、1.62 s**，5 次更新的训练计时约 **8 s**（不含启动）。
这些是短基准观测，不用于推算正式训练时长。实际 run：

```text
E:/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck/logs/rsl_rl/mjlab_microduck_velocity/2026-09-29_17-26-51_a-train-20260929T092642652039643-17349
```

证据为该目录的 `model_4.pt`、`params/agent.yaml`、`params/env.yaml` 与训练 events。
Reviewer 最终确认 64/512 两次训练的 checkpoint、normalizer、counter 正确，并确认 **195 条 scalar 均有限**。
**512 env 仅验证 5 iterations，不保证长训练后段、课程切换、稳定性或收敛。**

## 5. 原部署文件保持不变

主会话报告与文档只读哈希复核一致：

| 原文件（方案 A 内） | SHA-256 |
| --- | --- |
| `microduck/src/constants.py` | `14a4f1fb5b7d4047ad521e8b57e329dea3b5253846a49455131e357da9c62446` |
| `microduck/src/agents/walk.onnx` | `5707c06da8346ecd4c2ff15dcd74ffabc575e0f14bcbb18076501324f9bbe279` |
| `mjlab_microduck/src/mjlab_microduck/agents/velocity.pt` | `7d06922fd61e25fda88d09c88a2b7ffdae5a05fa9c8ab0c347ca5cb98f9c832a` |

## 6. 下一步正式训练（尚未启动）

```bash
bash /mnt/e/Projects/duck-robot/scripts/a-training.sh train --num-envs 512 --max-iterations 15000
```

**64 env smoke 与 512 env 扩容基准均仅验证 5 iterations；据此正式新训练示例选用 512 env。**
15000 iterations 尚未启动，不代表完成、收敛、后段课程或长期稳定性已验证。
正式训练需人工明确启动，保留新 run 的记录，评估训练/课程/扰动与多种子表现，再讨论 sim-to-real。
在重接并校验部署仿真、动作缩放/零位、IMU 与观测语义、电源/限流及有支撑安全测试之前，
**不替换原策略，不将 smoke 模型部署到真实机器人**。
