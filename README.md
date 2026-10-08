# duck-robot

Microduck 小型双足机器人的个人复刻项目，记录选型采购、3D 打印、装配、系统部署与实机验证；强化学习训练可在基础验证后再复现。

进度流水与硬件到位记录见 [PROGRESS.md](./PROGRESS.md)。

## 并行参考方案

三套开源资料按独立目录并列保存，**只读参考、不做修改、不合并代码、硬件配置或采购清单**（2026-10-09 规则，历史混入的本地修改已提取到 [local-changes/](./local-changes/README.md) 并还原）：

| 方案 | 本地入口 | 主要参考内容 |
| :--- | :--- | :--- |
| A：帆哥教程 | [microduck-build-tutorial](./microduck-build-tutorial/README.md) | Raspberry Pi Zero 2 W、OpenRB、XL330 路线的教程、部署代码与配套视频；既有核查及视频笔记继续保留。 |
| B：fanhao375 复刻研究 | [microduck-replica](./microduck-replica/README.md) | 机械装配分析、电控与调试资料、训练/工具代码；同时讨论 XL330 与飞特 HD-1910 路线，其主线及接口不能直接套用方案 A。 |
| C：jyg9 社区套件 | [microduck-community-kit](./microduck-community-kit/README.md) | **当前主参考（2026-10-09）**。飞特 HD-1910-C001 路线：imu_to_dxl/banana_pcb/dxl_hub 三块板、GD32 固件与升级工具、官方 robotd 的飞特补丁、HLS 舵机浏览器调试器。`software/microduck_feetech/` 完整源码上游尚未推送。 |

**下文机器人概览、复刻计划及根目录 [BOM](./BOM.md) 仍以方案 A 为基线，不自动适用于方案 B。** 方案 B 的来源说明和实测记录仅作独立参考，本项目尚未逐项核实或运行；舵机型号、供电、电控板、IMU、ID/零位、通信协议、打印件和策略必须按选定路线成套核对。上游有关超规格供电的记录不构成本项目的安全建议。

### 方案 B 快速入口

- [总 BOM](./microduck-replica/BOM.md)、[电控采购清单](./microduck-replica/docs/电控采购清单.md)、[机械采购清单](./microduck-replica/docs/机械采购清单.md)
- [硬件规格速查](./microduck-replica/docs/硬件规格速查.md)、[不打 HAT 的替代方案](./microduck-replica/docs/不打HAT.md)
- [调试记录](./microduck-replica/调试记录.md)、[踩坑记录](./microduck-replica/踩坑记录.md)、[软件说明](./microduck-replica/software/README.md)
- [打印入口](./microduck-replica/print/README.md)：当前上游已将实物 CAD/打印文件迁往独立的 [microduck-replica-cad](https://github.com/fanhao375/microduck-replica-cad)。**该外部 CAD 仓库本次未导入**，本地 `cad/`、`print/` 不能当作完整打印包。

导入日期：**2026-09-28**；来源：[fanhao375/microduck-replica](https://github.com/fanhao375/microduck-replica)，`master` 提交 [`0f2cff6bd76499ef9f57931c53ee76d16ae5c198`](https://github.com/fanhao375/microduck-replica/commit/0f2cff6bd76499ef9f57931c53ee76d16ae5c198)。采用固定提交的源码归档快照，保留全部 444 个文件和原始内容，**不附带 `.git` 历史，也不会自动跟随上游更新**；未安装依赖或执行仓库程序。[导入记录与文件校验](./docs/references/microduck-replica-import.json)用于追溯版本和本地变动。

保留并遵循方案 B 的 [LICENSE](./microduck-replica/LICENSE) 与 [NOTICE](./microduck-replica/NOTICE.md)：其代码、文档、模型等采用不同许可范围，不能将整个目录一概视为 Apache-2.0 或可商用。

## 方案 A：项目现状与使用边界

**2026-09-29 更新：方案 A 已建立新的训练基线，合同检查、CUDA reset/step、64 env × 5 iterations 从零短训练、512 env × 5 iterations 扩容基准及安全 ONNX 导出通过；尚无成熟行走策略，正式训练未启动。**
原始 [AI-FanGe/Microduck-build-tutorial](https://github.com/AI-FanGe/Microduck-build-tutorial) 教程快照保留；训练重建为本地独立增量，不等于教程所有硬件步骤均已验证。

| 内容 | 当前用途与限制 |
| :--- | :--- |
| `microduck/` | 原 Pi 部署代码与策略保持不变；控制 14 个舵机，但旧部署 sim 仍为 **19 DOF，未重接**新训练基线。 |
| `mjlab_microduck/` | 使用官方模型重建；51 observation / 14 action 合同、2 env × 100 finite steps、64/512 env 各 5 iterations 短训练与真实 checkpoint 导出通过。**不是恢复原丢失训练工程。** |
| `microduck3D打印.3mf` | Bambu Studio 打印工程；尚不能保证零件全齐，仍需核对数量、尺寸和切片配置。 |
| `bno08x_calibrate_ui.py`、`scripts/` | 原 IMU 工具不等于自动标定；根 `scripts/a-training.sh` 是新增 A 独立训练入口。 |
| `docs/assets/` | 结构图、演示素材；不同于快照缺失的 `microduck/docs/`。 |

模型来源：官方 [pollen-robotics/microduck_rl](https://github.com/pollen-robotics/microduck_rl/tree/cb70b792312d559a4da09064d92009079671815f) 固定提交 `cb70b792312d559a4da09064d92009079671815f`。
新训练采用名义 5 V BAM m6，速度课程于第 3000 / 6000 iteration 扩展；物理参数未经本机完整辨识，末阶段速度范围不代表已实现的实机性能。

### 方案 A 训练入口

> **2026-10-09**：下述库内修改（`pyproject.toml` 版本钉死、重写的 `export_onnx.py`、env cfg 课程修改、官方 `microduck_rl @ cb70b792` 的 `robot/` 恢复树等）已按「参考库只读」规则提取到 [local-changes/microduck-build-tutorial/](./local-changes/microduck-build-tutorial/)，`microduck-build-tutorial/` 还原为上游原样。**恢复训练环境前需先把提取件按相对路径复制回位**，且 `export_onnx.py` 内的 `/mnt/e/` 路径已随 E→C 迁移失效，须改为 `/mnt/c/`。

- [安装与使用](./local-changes/microduck-build-tutorial/mjlab_microduck/README.md)（提取件位置）
- [验收命令、模型来源、课程与物理限制](./docs/a-training.md)
- [实际 run / checkpoint / ONNX / SHA-256 证据](./docs/a-training-validation.json)

```bash
# WSL：只读来源/版本与任务检查；训练不会自动开始。
bash /mnt/c/Projects/duck-robot/scripts/a-training.sh check
# 正式训练示例：尚未执行，必须由用户明确启动。
bash /mnt/c/Projects/duck-robot/scripts/a-training.sh train --num-envs 512 --max-iterations 15000
```

64 env smoke 与 **512 env 扩容基准均仅验证 5 iterations**，据此正式示例选用 512 env；**15000 iterations 尚未启动，后段稳定性/课程与收敛未验证**。
smoke 已生成 model_4.pt（4720063 bytes）及 a-smoke.onnx（773823 bytes）；3 组正常 actor/ORT 对比最大绝对误差 `3.2782555e-07`，normalizer 保留。
**smoke 仅为工具链验收，不部署上机，不替换原策略，不等于完整实机验证。**

原 `microduck/src/agents/walk.onnx`（773115 bytes）、`mjlab_microduck/src/mjlab_microduck/agents/velocity.pt`（4887111 bytes）与 `constants.py` 的 SHA-256 未变。
实机仍需核对电源、关节 ID/零位/方向、IMU、观测和动作映射，并完成有支撑安全测试。
下文保留的原快照缺失/未测试说明属于早期静态核查基线；涉及 A 训练的最新状态以本节和验收记录为准，B 的内容不受本次 A 重建影响。

## 机器人概览

- **主控**：Raspberry Pi Zero 2 W（控制程序、蓝牙手柄、Wi-Fi / SSH；Wi-Fi 仅支持 2.4GHz）
- **舵机**：Dynamixel XL330-M288-T × 14（双腿 10 个、头颈 4 个），通过 OpenRB-150 接入
- **IMU**：BNO080/BNO085/BNO086（I2C，具体模块的电源与电平需另核）
- **电源**：按实际电路设计与验证；XL330 官方输入 **3.7～6.0V，推荐 5.0V，6.0V 是上限**；Pi 需稳定 5V
- **结构与策略**：PLA 打印件；部署 ONNX 行走策略

采购与接线细项见 [BOM.md](./BOM.md)。[上游教程](./microduck-build-tutorial/README.md) 和 [视频教程](https://www.youtube.com/watch?v=Vep8AjoCnEM) 用于对照，不作为安全规格或复刻成功的保证。

## 复刻计划

### 阶段 0：确认可行性，再决定采购

- [ ] 通读教程与 BOM，核对 14 个舵机的 ID、安装位置、线材、紧固件和供电路径。
- [ ] **供电是采购前必须闭合的关键项**：电池满电、负载变化及电源切换时，舵机端都必须满足官方范围；核对稳压能力、峰值电流、配电、保护与接地，并遵守下文 OpenRB 的板级限制。本次不推荐具体电池型号；禁止将 2S 锂离子/18650 或 2S LiFePO4 电池直接接到 XL330，也不要仅凭 NiMH 的标称电压认定可用。
- [ ] **先确认打印方案**：3MF 元数据为 `BambuStudio-02.07.01.62`，预设 **P1S / 0.4mm 喷嘴 / PLA / 0.2mm 层高**。换机型或喷嘴须重新切片，即便同为 Bambu 也不能无条件复用；核对零件数量、尺寸、方向与装配配合。
- [ ] 确认 2.4GHz 网络、Pi 本机交互终端、可用的机械支撑及停止/关机方法。NVIDIA GPU 只影响后续训练，不是开始硬件核对的前提。

### 阶段 1：分批采购

- [ ] 供电与打印方案确认后，按到货周期采购 14× XL330-M288-T、OpenRB-150 等关键件，**不要未经核对就整套下单**。
- [ ] 准备逐个设 ID 的调试链路：**U2D2 可选**。OpenRB 官方 `usb_to_dynamixel` sketch 是文档所述的出厂固件，可作 USB 串口桥；实际板子须确认固件。该方式支持 Dynamixel Wizard 2.0、最高 1Mbps，足以配置本项目；这不代表 USB 可为整机舵机动态供电。
- [ ] 再采购 Pi Zero 2 W、microSD、具体型号的 BNO08x 模块、经验证的电池/稳压/保护组件及线材紧固件；同步推进打印试件。

### 阶段 2：结构件准备

- [ ] 先试打关键配合件，检查舵机、螺钉和轴孔的尺寸公差，再按核对后的零件清单打印。
- [ ] 不把 3MF 当作完整参数化设计源：现存 **10 个 SCAD 是 STL 背景加简单几何体**，不是全套参数化 CAD。缺件或需改尺寸时，先检查下文的历史恢复候选，恢复后仍需验证。

### 阶段 3：舵机识别与设置

- [ ] **强烈建议装配前逐个上总线设置 ID 并贴标**，避免同 ID 冲突和装后接线困难；不是说装后改 ID 必然要拆机。
- [ ] 用 Dynamixel Wizard 2.0 或经确认的桥接工具核对 ID 1～14、协议 2.0 与部署所用 1Mbps；修改 ID 等 EEPROM 设置前须 `Torque Enable = 0`。其他寄存器设置对照对应型号官方控制表，不直接照抄教程。
- [ ] **保留输入电压错误的 Shutdown 保护**，不要靠关闭保护掩盖欠压、超压或供电波动。先解决电源，再设置与验证控制参数。

### 阶段 4：装配与接线

- [ ] 核对左右腿、关节方向、零位与膝盖 offset；不能只凭 ID 连通就认定机械映射正确。
- [ ] 先完成并验证电源图，再接线：舵机供电符合 XL330 范围，Pi 使用独立稳定 5V，相关电路共地。OpenRB 不是自动降压稳压器；不得未经设计并联 USB 正电源轨。VIN 供电前，在完全断电下核对 `VIN(DXL)` 跳线；本次未验证实物出厂位置。
- [ ] 按部署映射核对三路总线：右腿 5→1、左腿 10→6、头颈 12→11→13→14。OpenRB 有 4 个 TTL 口，额外分线板并非必需；三路布线不等于独立电源、每路独立额定电流或串联供电。
- [ ] **插拔舵机或移动跳线前断开电池、USB 等所有电源，禁止带电操作**；电池不要连接控制器充电。上电前万用表测极性、短路及输出电压；合格接线、绝缘与机械固定缺一不可，热熔胶不能替代它们。IMU 接 I2C bus 1（GPIO2/GPIO3），先核对模块电压与逻辑电平。

### 阶段 5：系统部署与 IMU 检查

**镜像状态**：已核对 [Release `image.v1`](https://github.com/AI-FanGe/Microduck-build-tutorial/releases/tag/image.v1) 元数据：发布于 **2026-09-05**，资产名 `microduck.img.xz`，大小 **768792340 bytes**，公布的 SHA256 为：

```text
096885dc32fb5b1db2ad69ba6bea868d8ab988f2b47c0d884eb63ba0dfdcb5c4
```

本次**未下载检查镜像内容、未刷写或启动验证**；元数据存在不等于镜像可正常部署。

- [ ] 下载后先计算本地文件 SHA256 与上述值比对，再选择正确的 microSD 目标刷写，避免覆盖其他磁盘。
- [ ] `network-config` **仅适用于上游声称已配置相应首启机制的镜像，且需在首次启动前填写**；本次未检验该机制。普通 Pi OS 或已初始化系统不能假设支持，应通过本机终端按实际系统网络管理方式配置 2.4GHz Wi-Fi（如确实使用 NetworkManager，再用 `nmcli`）。
- [ ] 登录后立即修改默认密码，核对系统、部署目录、依赖与串口/I2C 访问条件；不得把镜像内代码版本自动视为与本快照一致。
- [ ] `bno08x_calibrate_ui.py` 在 **Ubuntu PC** 上运行 Tkinter UI，经 SSH 到 Pi 检查/采样。它不是自动保存传感器标定的工具。默认 mount 为 `(0.5,-0.5,-0.5,0.5)`，而当前部署 `constants.py` 的 `IMU_MOUNT_QUAT` 为 `(0.7071068,0,0.7071068,0)`；须显式传 `--mount-quat` 与**当前实际部署**一致，再实际倾斜机器人核对姿态、角速度和重力方向。

例如，在 Ubuntu PC 的上游快照根目录运行（替换实际主机名、用户名；部署常量若变更，参数也须更新）：

```bash
python3 bno08x_calibrate_ui.py --host microduck.local --user user --mount-quat 0.7071068,0,0.7071068,0
```

- [ ] 当前不能直接用 `make sim` / `make viewer` 作为首跑前已通过的验证；其模型问题见下文。`scripts/imu_mujoco_orientation_viewer.py` 默认还依赖缺失 `robot/` 下的 `robot_walk.xml`，需补齐兼容模型才能用。

### 阶段 6：有支撑的实机首跑

> **启动 `main.py` 就会使能扭矩并回中位，不是按 `v` 后才动。** 运行前确认无其他控制循环（包括手柄服务启动的循环），用可靠支架/悬吊防跌，留出关节空间并避开手指夹点。PID 检查不是完整的安全互锁。

- [ ] 完成供电、ID、方向/零位与 IMU 验向，备好停止方法；先验证受支撑的回中位与观测，不直接落地试走。
- [ ] 在 **Pi 的交互终端**运行以下命令，显式选键盘，避免连接手柄时自动切成手柄输入：

```bash
cd ~/microduck
MICRODUCK_INPUT=keyboard PYTHONPATH=src .venv/bin/python src/main.py
```

| 键盘操作 | 实际含义 |
| :--- | :--- |
| `v` | 切换行走策略；程序启动时的使能扭矩/回中位已先发生。 |
| 方向键 | 累计调整速度指令；**松开不会自动归零**。 |
| `x` | 清零速度指令，不是停止控制程序或安全断电。 |
| `q` | 请求停止控制循环；正常清理会关闭扭矩，机器人可能失去支撑，须先扶稳。 |

- [ ] 受支撑验证通过后，再以保守速度逐步验证落地行走，记录实际电压、姿态及异常；预训练策略不构成安全或行走保证。
- [ ] 最后才验证蓝牙手柄和无头服务；以下限制必须先理解。

**手柄、Wi-Fi 与关机**

- `gamepad_daemon` 检测到 `/dev/input/js*` 后，默认通过 `rfkill` 屏蔽 Wi-Fi，SSH 可能断开；不能只靠 SSH 作为唯一停机通道。
- 服务待机时，长按 START 2 秒启动控制循环。运行时 `run_session()` 使用 `proc.wait()` 等待子进程退出：**关闭/断开手柄只会清零速度，不退出控制循环，也不保证恢复 Wi-Fi**。应先扶稳并按 **B** 退出，确认服务回到待机，再关闭手柄；解除 Wi-Fi 屏蔽也不等于一定重连成功。
- **双扳机按住 2 秒的关机手势只在 daemon 待机阶段监听，不是运行中的急停。** 正常关机顺序：先扶稳 → 按 B（手柄）或 q（键盘）退出控制循环 → 确认待机后双扳机关机，或在 Pi 本机执行 `sudo shutdown -h now`。
- 也可在电脑端的部署目录 `microduck-build-tutorial/microduck/` 执行 `make shutdown HOST=user@microduck.local`，但必须具备相应命令环境且 SSH 可达；替换实际账号/主机名。
- **正常情况下，先停程序、关 Pi，确认系统关机完成后才断电**；10～15 秒只是上游参考等待时间，不是关机完成的判据。若冒烟、短路、失控或发生夹伤风险，优先紧急切断动力，不等待操作系统关机；事先准备可触及的动力断电措施并防止机器人跌落。

### 阶段 7（可选）：新训练基线、显式导出与部署前验收

方案 A 已重建训练基线，64/512 env 各 5 iterations 短训练与安全导出通过；这不是恢复原丢失训练工程，也不代表策略已收敛。安装、正式训练命令和验收记录见 [A 训练说明](./docs/a-training.md)。

- 现行导出必须显式指定 `--checkpoint` 与 `--output`；不会自动选择 latest checkpoint，也不会默认向当前目录输出 `policy.onnx`。
- 使用 `a-training.sh export --checkpoint /absolute/path/model_N.pt --output /absolute/path/new-policy.onnx`；输出必须是不存在的新路径，已有目标拒绝覆盖。
- **smoke 仅验证工具链，不替换原 `walk.onnx` 或其他原策略，不部署上机。** 正式训练尚未启动；需在训练收敛、独立评估及部署接口、模型/观测/动作映射和安全验证完成后，才考虑受控部署，不能仅因导出成功就复制覆盖原策略。

## 当前阻塞与恢复线索

### 仿真与部署不是同一套模型

部署 `MOTOR_TO_ID` 为 **14 个舵机（10 腿 + 4 头颈）**；`microduck/src/model/mjcf/robot.xml` 则有 **19 个 motor（12 腿 + 6 臂 + 1 头）**。模型有 `right_ankle_pitch` / `right_ankle_roll`，但缺部署要求的**精确关节名** `right_ankle`。

- `make sim`：若依赖与 MJCF 加载成功，随后 `mujoco_controller.py` 的关节/执行器名字校验仍会失败。
- `make viewer`：走的是 **Placo / MeshCat**，在 `placo_controller.py` 设置 `NEUTRAL_POSE` 时同样存在关节名不匹配；不是同一个 MuJoCo 校验报错。该 viewer 只注册头部与下蹲动作，未注册行走策略。

以上为静态源码结论，**未运行**上述命令；需先补齐兼容模型，不能声称仿真已验证。

### 缺失目录可以查历史，但恢复后仍需核验

GitHub 历史显示 **2026-09-11 是三个独立删除提交**：`34656ce` 删除训练 `robot/`，`570e0c2` 删除 `microduck/cad/`，`4967821` 删除 `microduck/docs/`。教程引用的 `microduck/docs/dev/clone_sd.md` 当前也缺失。

可先查看[删除前历史 tree：`9a11a406a73c8d809daf6de939ef4df3f19f1656`](https://github.com/AI-FanGe/Microduck-build-tutorial/tree/9a11a406a73c8d809daf6de939ef4df3f19f1656)，作为 CAD、机器人定义和文档的**恢复候选**；再按需对照 [Rhoban/microban](https://github.com/Rhoban/microban) 或 [pollen-robotics/microduck](https://github.com/pollen-robotics/microduck)。历史存在不保证文件完整、版本兼容或恢复后可直接运行，本次未执行恢复。

### 供电以官方规格和实测为准

XL330 的 **3.7～6.0V（推荐 5.0V）**是硬件约束。源码里的 `BAM_VIN = 7.5` **高于**官方上限，`BAM_VIN_MIN = 6.0` **等于**上限；这些仿真参数不能证明真实电池、稳压或舵机端电压。不要据此推断作者为何选择某种电源。Shutdown/电压报警寄存器的默认值或允许设置范围，也不能突破供电规格：保留保护、出现报警先排查，不能靠保护代替稳压。

- **OpenRB 输入范围不等于舵机范围**：板子支持 USB 5V、VIN 3.7～12.6V，但不能把 VIN 的高电压直接视为 XL330 可用电压；板子不是自动降压稳压器。
- **板级电流有限**：官方标注 DYNAMIXEL PORTs 额定电流 **3,000mA**，不是每口 3A，也不是已证实的自动限流保护阈值。若负载超过板额定，须设计并验证独立配电与保护；“电池→开关→OpenRB→全部舵机”不是本次已验证的方案。
- **USB 与板载 5V 不可承担整机动力**：USB 有 **500mA 保险丝**，不能通过 Pi USB 为 14 个舵机动态供电；OpenRB 的 5V 引脚新版额定 **150mA**、旧版 **300mA**，不要用它给 Pi 供电。

采购前先闭合 [BOM.md](./BOM.md) 中的供电待办，并验证电源轨、满电/动态电压、峰值负载及保护方案；本次未给出已通过实测的整机供电方案。

## 复刻记录

待实际完成后记录打印清单、供电测量、关节与 IMU 验证、镜像版本及受支撑测试结果；目前不把静态核查记为实机成果。

## 致谢与核查范围（2026-09-28）

感谢 [原教程项目](https://github.com/AI-FanGe/Microduck-build-tutorial)、[Rhoban/microban](https://github.com/Rhoban/microban) 与 [pollen-robotics/microduck](https://github.com/pollen-robotics/microduck) 的开源工作。

本次依据：本地静态源码与文件/3MF 元数据；[ROBOTIS XL330-M288 官方规格](https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/)与 [OpenRB-150 官方手册](https://emanual.robotis.com/docs/en/parts/controller/openrb-150/)；GitHub Release 元数据和删除历史。软件核对重点包括部署 `main.py`、输入/调度与 `gamepad_daemon.py`、`constants.py`、`Makefile`、仿真控制器、IMU 工具，以及训练环境配置和 `export_onnx.py`。

**未进行硬件上电、打印装配、镜像下载检查/刷写、机器人运行、仿真运行或训练/导出测试。** 真实供电、模型兼容性、镜像首启机制与最终行走能力仍待验证；上游教程保留原样，冲突处按当前源码、官方规格与实测处理。

## 配套 B 站视频学习笔记

[BV1uUbG6FEfb：分章记录、时间索引与供电/装配关键帧](./docs/video-notes/BV1uUbG6FEfb/README.md)。基于公开全片音轨本地 ASR 和关键帧核读；区分作者做法与本项目安全要求，不替代上述核查。
