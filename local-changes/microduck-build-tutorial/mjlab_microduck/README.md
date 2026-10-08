# Microduck A：独立训练工具链

本目录是重建方案 A，任务名 `Mjlab-Velocity-Microduck`。**2026-09-29 已通过合同、64/512 env 各 5 iterations 短训练和真实 checkpoint 安全导出；尚无成熟策略，正式训练未启动，smoke 不部署上机。** 与方案 B 隔离：

- 源码固定：`/mnt/e/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck/src/mjlab_microduck`。
- WSL venv 固定：`/home/yilv/.venvs/duck-robot-a-training`。
- 不复制 B 的包、egg metadata 或环境；仅共享 uv 下载缓存。
- 不修改原部署 `walk.onnx`、`velocity.pt`、`constants.py`。

## 依赖与安装（WSL Ubuntu）

固定 mjlab 1.3.0、torch 2.9.1、warp-lang 1.12.0、mujoco 3.10.0。
BAM 1.0.0 固定 A 原 doc 分支 commit `0007411bd82c48f1bc12ae8382f98e4d8b879c95`，不跟随分支。
显式安装 ONNX、ONNX Runtime（CPU 验证后端）和 TensorBoard。
移除直接依赖 placo：本训练与导出路径不使用它，不为其他运动学工具引入额外依赖。
`uv.lock` 应提交，记录实际解析版本。

```bash
cd /mnt/e/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck
export UV_PROJECT_ENVIRONMENT=/home/yilv/.venvs/duck-robot-a-training
uv lock --python 3.12
uv sync --locked --python 3.12
```

首次解析或明确更新依赖时才运行 `uv lock`；已有锁文件的复现安装只需 `uv sync --locked --python 3.12`。
日常入口不隐式安装，也不使用 `uv run`。需可用的 NVIDIA CUDA 驱动与 WSL GPU；
mjwarp CPU 仿真不是本入口支持的回退路径。默认导出设备为 `cuda:0`，ORT 验证使用 CPU。

### 原 overrides 的已知影响

保留原 protobuf/onnx/zmq overrides。BAM commit 的原始 metadata 要求 `protobuf>=3.20,<4.0` 与 `zmq`，
但本项目有意覆盖为 `protobuf>=4,<7` 并排除 `zmq`。因此 `uv pip check` 会报告这两项声明冲突；
这不等同于 `uv lock --check` 或 `uv sync --locked` 失败，也不能声称 `pip check` 全通过。
这些 overrides 针对本 A 训练路径；不要据此假定 BAM 所有其他工具都可用。

## 固定入口

```bash
cd /mnt/e/Projects/duck-robot
bash scripts/a-training.sh check
bash scripts/a-training.sh list
# 从零开始，固定 64 env / 5 iterations；唯一 run-name，期望 model_4.pt。
bash scripts/a-training.sh smoke
# 训练必须显式给出 env 数与迭代数，绝不自动长训练，也不隐式续训。
bash scripts/a-training.sh train --num-envs 64 --max-iterations 5
# 必须指定新 checkpoint 和新输出路径，已有目标一律拒绝覆盖。
bash scripts/a-training.sh export --checkpoint /absolute/path/model_4.pt --output /absolute/path/new-policy.onnx
```

`check/list` 不创建仿真；`check` 是依赖、源码和任务注册静态检查，不代表 GPU 合同验收。
入口用 `-I -B` 校验解释器 `sys.prefix` 与 A 源文件精确路径，忽略外部 PYTHONPATH、
用户 site-packages 和其他 venv，并验证固定核心版本与 BAM commit。
导出的相对路径以调用者的当前目录为基准；训练则固定在 A 项目目录运行。

### smoke 的最终训练命令

入口生成 UTC 纳秒时间戳与 PID 组成的唯一 `run-name`，然后执行以下等价命令：

```bash
cd /mnt/e/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck
/home/yilv/.venvs/duck-robot-a-training/bin/python -I -B -m mjlab.scripts.train \
  Mjlab-Velocity-Microduck \
  --env.scene.num-envs 64 \
  --agent.max-iterations 5 \
  --agent.resume False \
  --agent.logger tensorboard \
  --agent.upload-model False \
  --agent.run-name "a-smoke-$(date -u +%Y%m%dT%H%M%S%N)-$$"
```

训练日志位于 A 项目的 `logs/rsl_rl/mjlab_microduck_velocity/`。
正常完成 5 iterations 后预期保存 `model_4.pt`；请使用实际 run 目录，不要自动选择“最新” checkpoint。
5 iterations 只验证工具链，**不是可部署的行走策略**。
mjlab 的 Velocity runner 可能在保存 checkpoint 时生成旁路 ONNX；该文件不代替下面的安全导出与验证。

## 安全导出约定

- 强制 `--checkpoint` 与 `--output`，不推断路径、不自动覆盖。
- 拒绝已有文件/目录/断链、原部署文件名，以及 B、部署、源码和 venv 目录；处理 Windows 大小写路径别名。
- 单 env，默认 `cuda:0`；`finally` 关闭环境。仅导出，不训练、不恢复优化器。
- 用 `torch.load(weights_only=True)` 读取新格式 checkpoint，再 `runner.alg.load(..., load_cfg={"actor": True}, strict=True)`。
  不调用 mjlab 1.3.0 内部硬编码 `weights_only=False` 的 `runner.load()`，也不自动迁移旧部署 checkpoint。
- 强制包含 normalizer 的 mean/var/std/count，严格恢复并逐项比对；拒绝非有限 actor 权重。
- 保留 normalizer 的完整推理路径。ONNX 必须是单个 float32 `[1,51]` 输入、`[1,14]` 输出。
- 验证实际 observation/action 关节顺序与原部署 `OBSERVATION_DOF_ORDER` 一致；metadata 保留关节、动作比例、
  默认关节位置、观测项等基础信息，并附 checkpoint SHA-256、维度与 normalizer 标记。
- ONNX checker + ORT CPU 检查，使用 reset 观测、零向量、固定随机向量三组输入，
  对比**正常 actor forward** 的确定性输出（不是只对比 export wrapper），要求有限值且 `rtol=1e-4, atol=1e-5`。
- 全部通过后使用同目录 staging 与 `os.link` 原子发布；并发出现目标也会拒绝，不使用覆盖式 rename。

## 实测状态（2026-09-29）

| 项目 | 结果 |
| --- | --- |
| 独立 venv 安装 | 通过：Python 3.12.3，`uv sync --locked` 安装 149 个包 |
| 固定来源/版本 | 通过：sys.prefix、A `__file__`、四个核心版本与 BAM commit |
| 其他实际锁定版本 | rsl-rl-lib 5.0.1、onnx 1.23.0、onnxruntime 1.30.0、tensorboard 2.21.0、protobuf 6.33.6 |
| 锁一致性 | `uv lock --check` 通过；`uv pip check` 的两项预期 overrides 冲突见上文 |
| 静态验证 | Bash 语法、Python 编译、入口/export help、缺少 train 显式参数拒绝、UTF-8/LF 通过 |
| CPU 导出单元验证 | 真实 512/256/128 actor + PPO.load + 非平凡 normalizer，3 组 ORT 对比通过；最大绝对误差 `5.59e-8` |
| 负向验证 | 丢失 normalizer、关节 metadata 错序、缺失/非有限权重、不允许的 pickle 对象、已有目标/断链/受保护路径、原子禁止覆盖均按预期拒绝 |
| A check / 模型合同 | 主会话验收通过：固定来源/版本、XML 编译、配置、关节/IMU/课程合同；check 独立重跑退出 0 |
| GPU reset / step | `cuda:0`，2 env，reset + 100 个有限值 step，通过；actor `[2,51]` / action 14 |
| smoke / model_4.pt | 从零 64 env × 5 iterations，退出 0；4720063 bytes，iter 4，common_step_counter 120，总采样 7680 |
| 学习状态 | actor 首/末层 `(512,51)` / `(14,128)`；首层相对 model_0.pt max delta `0.00813435018`，normalizer 更新 |
| 真实 checkpoint export | a-smoke.onnx，退出 0，773823 bytes；checker/ORT 51→14/关节 metadata/3 组正常 actor 对比通过，max abs error `3.2782555e-07` |
| 512 env 扩容基准 | 512 env × 5 iterations，退出 0，61440 总采样，生成 model_4.pt；末次约 7568 steps/s、1.62 s，更新训练计时约 8 s（不含启动） |
| 覆盖拒绝 | 已存在 a-smoke.onnx 正确拒绝，退出 1，未触发 GPU 仿真 |
| Reviewer 最终复核 | 64/512 checkpoint、normalizer、counter 正确；195 条 scalar 有限；显式 ONNX checkpoint hash 关联正确；另 26 组 CPU actor/ORT max abs error `1.1920929e-06` |
| 原部署保护 | constants.py / walk.onnx / velocity.pt 的 SHA-256 未变，详见验收记录 |
| 正式训练 / 实机 | 尚未启动正式训练，未完成新策略实机验证，smoke 禁止部署 |

上述 GPU/训练/实 checkpoint 结果由主会话串行验收提供；本次文档回填没有重跑 GPU。
`list` 是可用入口，不将其额外宣称为独立实测项目。完整命令、来源、证据路径及哈希见
[A 训练验收说明](E:/Projects/duck-robot/docs/a-training.md) 和
[验收 JSON](E:/Projects/duck-robot/docs/a-training-validation.json)。

### 已验收 run 与命令

```bash
bash /mnt/e/Projects/duck-robot/scripts/a-training.sh check
/home/yilv/.venvs/duck-robot-a-training/bin/python -I -B \
  /mnt/e/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck/scripts/validate_contract.py \
  --compile-xml --config --env-steps 100 --device cuda:0
bash /mnt/e/Projects/duck-robot/scripts/a-training.sh smoke
RUN=/mnt/e/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck/logs/rsl_rl/mjlab_microduck_velocity/2026-09-29_17-23-46_a-smoke-20260929T092337433891036-16974
bash /mnt/e/Projects/duck-robot/scripts/a-training.sh export \
  --checkpoint "$RUN/model_4.pt" --output "$RUN/a-smoke.onnx"
```

这是已执行参数的固定 WSL 路径表示，不是再次执行请求；输出已存在，复测导出需使用新输出名。
Windows run 目录为 `E:/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck/logs/rsl_rl/mjlab_microduck_velocity/2026-09-29_17-23-46_a-smoke-20260929T092337433891036-16974`。
证据含 model_0.pt、model_4.pt、a-smoke.onnx、params/agent.yaml、params/env.yaml 及 TensorBoard events。

### 新基线与后续训练边界

模型来自官方 `pollen-robotics/microduck_rl` 的固定提交 `cb70b792312d559a4da09064d92009079671815f`；
这是新基线，**不是恢复已丢失训练工程或原 velocity.pt 的训练过程**。
逐文件来源与许可见 [source_manifest.json](E:/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck/src/mjlab_microduck/robot/source_manifest.json)。

训练采用 5.0 V 名义 BAM m6（4.5–5.5 V），并非实机系统辨识。每 iteration 为每 env 的 24 个 control steps；
速度课程在第 3000 / 6000 iteration 对应 72000 / 144000 控制步阈值后的首次 reset 扩展。
末阶段 vx `[-0.5,0.7]` m/s、vy `[-0.3,0.3]` m/s、行进 yaw `[-1.5,1.5]` rad/s、原地 yaw `[-3,3]` rad/s。
配置边界已测，不代表 smoke 已训练到这些阶段或达到这些实机速度。

正式训练命令示例（**尚未启动**）：

```bash
bash /mnt/e/Projects/duck-robot/scripts/a-training.sh train --num-envs 512 --max-iterations 15000
```

64 env smoke 和 512 env 扩容基准均已通过 **5 iterations**；据此正式示例选用 512 env。
**15000 iterations 尚未启动，后段课程、完成/收敛与长期稳定性未验证。** 上游质量/惯量/接触与本机真实性、BAM 摩擦/压降/延迟、
IMU 与装配/零位仍需校准；旧部署 sim 仍为 19 DOF 且未重接，原部署电气/模型假设没有被自动修正。
完整实机验证尚未完成，不能把此 smoke 策略上机。

512 env 已执行扩容基准命令（不是 15000 iterations 正式训练）：

```bash
bash /mnt/e/Projects/duck-robot/scripts/a-training.sh train --num-envs 512 --max-iterations 5
```

实际 run：`E:/Projects/duck-robot/microduck-build-tutorial/mjlab_microduck/logs/rsl_rl/mjlab_microduck_velocity/2026-09-29_17-26-51_a-train-20260929T092642652039643-17349`；checkpoint 为该目录下 `model_4.pt`。
具体命令/路径与限制同步记录在验收 JSON；短基准不用于估算正式训练时长。
