# 方案 B：XL330 平地训练入口

默认任务固定为 **`Mjlab-Velocity-Flat-MicroDuck`（XL330）**，不是 HD1910。
入口是项目根目录下的 `scripts/b-training.sh`，仅用于 Linux／WSL，不会执行传感器、舵机或其他硬件控制程序，也没有隐式长训练模式。

## 前提与边界

- 已验收环境（2026-09-29）：WSL Ubuntu 24.04，用户 `yilv`，Python 3.12.3，RTX 4080；依赖安装、CUDA 检查和 GPU 短训练均已通过。
- 下方实测记录由主会话完成，本次文档更新归档结果；交互 `play`（`native`／`viser`）尚未实际验收。
- Linux `uv` 0.12.20 已安装到 `~/.local/bin/uv`。迁移环境时需先安装 `uv`；脚本不执行 `sudo` 或系统包安装。
- 每次调用固定使用 `UV_PROJECT_ENVIRONMENT="$HOME/.venvs/duck-robot-training"`、`UV_HTTP_TIMEOUT=600`、`UV_LINK_MODE=copy`。用户 `yilv` 对应 `/home/yilv/.venvs/duck-robot-training`；无需激活环境。
- 所有 `uv run` 使用 `--frozen`，不更新锁文件；`uv` 仍可能按已有锁文件同步依赖，本次安装已完成，后续仍应避免并发安装／同步同一虚拟环境。入口不会修改上游源码，但实际训练会在训练工程内生成日志／checkpoint。
- 5 次迭代只验证“注册任务 → 仿真 → GPU → 优化 → 保存”的链路，**不会学会走路**，不能作为可部署策略。

## 2026-09-29 实际验收记录

以下路径均相对于训练目录 `microduck-replica/software/training`。本轮已完成：

| 项目 | 实测结果 |
| --- | --- |
| 依赖安装 | `uv sync --frozen` 成功，142 packages。 |
| 实际版本 | Python 3.12.3；PyTorch 2.9.1，CUDA 12.8；Warp 1.12.0；MuJoCo 3.10.0；BAM 1.0.1；ONNXRuntime 1.24.4。这里是本次记录，入口 `check` 仍从实际环境动态读取版本。 |
| 环境检查 | `check`、`list` 通过，注册任务共 47 个。 |
| GPU 短训练 | 64 env × 5 iter，退出码 0，共 7,680 环境步；5 次 `nan_state` 均为 0。 |
| CPU 测试 | `test_nan_guard`／`test_obs_nan_guard`／`test_head_pose_bias` 共 20 项通过。 |
| 标准 ONNX 导出 | 成功；`onnx.checker` 通过；CPU ORT 5 组输入／输出均为有限值，shape `[1,61] → [1,14]`，图中包含 `obs_normalizer._mean`。 |
| 渲染 | MuJoCo GLFW 离屏渲染成功，实际 14 个执行器；静态 STAND 图不是策略行走截图。交互 `play/native/viser` 尚未验收。 |
| TensorBoard | 主会话已后台启动 `127.0.0.1:6007`，WSL PID `14727`；HTTP 200，scalar API 已加载本轮日志。 |

产物与证据：

- checkpoint（4,842,943 bytes）：`logs/rsl_rl/velocity/2026-09-29_16-57-58_b-xl330-smoke-20260929T085748488208732-14346-23015/model_4.pt`。
- ONNX：`logs/setup/20260929-165723/xl330-smoke.onnx`。
- 详细验证记录：`logs/setup/20260929-165723/validation.json`。
- 静态 STAND 预览：`logs/setup/20260929-165723/model-preview.png`。
- TensorBoard pidfile／日志：`logs/setup/20260929-165723/tensorboard.pid`、`logs/setup/20260929-165723/tensorboard.log`。

`pyproject.toml` 与 `uv.lock` 的 SHA-256 均与安装前一致：

```text
pyproject.toml  45f3476af2b5bba1c3199aadb8372ec1bb08496ca91b08dec78543addd5c8440
uv.lock         2eeeb680025baa737e7ccf3a87da3695a9d49b228de0bb60d8af0c022ab5f1aa
```

上游有非致命的 tyro tuple/list 警告和正则匹配到 site 的警告（实际为 14 个执行器）；本轮没有为此修改上游源码。以上证明训练／导出链路可用，**不表示策略已学会走路、可直接部署或已完成实机验证**；本次没有触碰实机。

## 快速开始

以下为复现命令，本次已执行通过，无需为了查看结果重复训练。PowerShell 命令每行可以单独复制；不要求当前目录是项目根目录：

```powershell
wsl.exe -d Ubuntu -u yilv -- bash /mnt/e/Projects/duck-robot/scripts/b-training.sh check
wsl.exe -d Ubuntu -u yilv -- bash /mnt/e/Projects/duck-robot/scripts/b-training.sh list
wsl.exe -d Ubuntu -u yilv -- bash /mnt/e/Projects/duck-robot/scripts/b-training.sh smoke
```

脚本根据自身真实路径定位 `microduck-replica/software/training`，不依赖固定盘符或调用时的工作目录。上面 `/mnt/e/...` 只是本机示例；移动项目时改脚本路径即可。含空格的路径请加双引号。

WSL Bash 等价命令：

```bash
entry="/mnt/e/Projects/duck-robot/scripts/b-training.sh"
bash "$entry" check
bash "$entry" list
bash "$entry" smoke
```

| 模式 | 行为 |
| --- | --- |
| `check` | 输出 Python、PyTorch、mjlab、Warp、MuJoCo、BAM、ONNX、TensorBoard 等版本；校验虚拟环境、训练包来源、XL330 任务注册及 CUDA 可用性；执行一个极小的 PyTorch CUDA 运算。失败返回非零，不训练。 |
| `list` | 调用 `python -m mjlab.scripts.list_envs`，显示注册任务；绕过 mjlab 1.3.0 的 `list-envs` console 入口把任务数量当作退出码的问题，真实执行错误仍返回非零。显示其他任务不代表入口默认任务变更。 |
| `smoke` | 固定 64 个环境、5 次迭代、`tensorboard` logger；每次使用带纳秒时间、PID 和随机数的独立 run name。拒绝追加训练参数。 |
| `play <checkpoint> [native\|viser]` | 仅一个环境；默认 `native`，可显式选 `viser`。 |
| `export <checkpoint> [output.onnx]` | 使用上游 `scripts/export.py`，保留其观测归一化导出逻辑；仅一个环境。默认写调用目录的 `output.onnx`。 |
| `tensorboard [port]` | 只绑定 `127.0.0.1`，默认端口 `6007`，不占用已有 `6006`；前台运行，`Ctrl+C` 停止。 |

缺少模式、错误模式、缺少 checkpoint、错误 viewer、无效端口或多余参数都报错并返回非零；`--help` 查看用法。没有 `train` 模式，不会意外使用上游默认 50k 迭代。底层 `uv`／Python 命令失败也会返回非零。

## 日志、回放和导出

XL330 日志位于训练目录的 **`logs/rsl_rl/velocity/`**。`smoke` 会打印 run name 与日志根目录，checkpoint 通常为某次运行目录中的 `model_*.pt`；请以实际产生的文件为准，不能假设某个迭代编号一定存在。

在 WSL Bash 中列出 checkpoint，再手动选定一个可信文件：

```bash
entry="/mnt/e/Projects/duck-robot/scripts/b-training.sh"
training="/mnt/e/Projects/duck-robot/microduck-replica/software/training"
find "$training/logs/rsl_rl/velocity" -type f -name 'model_*.pt' -print
# 本次已验收的 checkpoint；以后可换成上一步列出的其他可信文件。
checkpoint="$training/logs/rsl_rl/velocity/2026-09-29_16-57-58_b-xl330-smoke-20260929T085748488208732-14346-23015/model_4.pt"
bash "$entry" play "$checkpoint" native
# 无原生窗口时可尝试浏览器 viewer；使用程序实际打印的 URL。
bash "$entry" play "$checkpoint" viser
```

`native` 需要 WSLg／可用显示环境。`viser` 的监听地址和端口由上游 viewer 决定，**不要把其服务暴露到不可信网络**；入口只保证 TensorBoard 绑定 loopback。

相对 checkpoint 和相对导出路径均在切换训练目录**之前**，按调用者的 Linux 当前目录解析。PowerShell 传入参数时请使用 Linux 绝对路径（例如 `/mnt/e/...`），不要传 `E:\...`；这样也不受 PowerShell → WSL 当前目录映射影响。

```bash
# 接上节：entry 和 checkpoint 已设置。父目录须已存在，输出文件须不存在。
cd "$HOME"
bash "$entry" export "$checkpoint" "$HOME/b-xl330-smoke.onnx"
# 省略输出参数则写当前目录的 output.onnx；同样禁止覆盖。
# bash "$entry" export "$checkpoint"
```

存在的文件、目录或符号链接都会被拒绝；重新导出请换一个新的 `.onnx` 路径。不要让其他进程同时写同一个输出路径（上游导出器并不提供原子 no-clobber 写入）。导出需要训练依赖和仿真初始化；本入口不是仅复制 checkpoint。

## TensorBoard

**本次实例已由主会话在后台启动，不必重复启动**，直接打开下方 URL 即可。WSL PID `14727` 仅为本次记录，重启后不能据此判断进程身份。重启 WSL 后按以下原命令重新开启（此入口前台运行，`Ctrl+C` 停止）；不要仅凭旧 PID／pidfile 终止进程，需先核验实际进程身份。

需要重新启动时，在另一个 PowerShell 终端中运行：

```powershell
wsl.exe -d Ubuntu -u yilv -- bash /mnt/e/Projects/duck-robot/scripts/b-training.sh tensorboard
# 若 6007 已占用，可明确指定另一个端口。
wsl.exe -d Ubuntu -u yilv -- bash /mnt/e/Projects/duck-robot/scripts/b-training.sh tensorboard 6008
```

默认在浏览器打开 [http://127.0.0.1:6007](http://127.0.0.1:6007)。Windows 访问依赖 WSL localhost 转发；失败时检查 WSL 网络配置，不要改绑 `0.0.0.0` 规避。两条示例是端口选择，通常只需启动其中一条。

## 验收与安全提醒

1. 本次 `check` 已通过；更换环境后需重新确认训练包来自当前项目的 `software/training/src/mjlab_microduck/__init__.py`，且 CUDA 设备为预期 GPU。
2. 本次 `list` 已通过，共 47 个任务，包含 `Mjlab-Velocity-Flat-MicroDuck`。
3. 本次 `smoke`、checkpoint、ONNX 验证和 TensorBoard 已通过，证据见上方实测记录；5 次迭代不代表学会走路，也不是可部署策略。
4. 标准导出和静态离屏渲染已通过，**交互 `play/native/viser` 尚未实际验收**。静态 STAND 图不能作为策略行走表现的证据。
5. **方案 B 的 61 维观测 ONNX 不能直接替换方案 A 的 51 维模型**：观测、关节顺序、动作缩放、归一化和 runtime 必须配套验证。
6. **不能根据仿真中的电压参数给 XL330 超规格供电**。实际硬件供电必须遵守具体 XL330 型号的官方额定规格；本入口不接入真实硬件。
