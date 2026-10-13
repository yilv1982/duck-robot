# Radxa Zero 3W eMMC 线刷记录（路线 A，2026-10-13）

接续 [TF 卡烧录记录](../sd-flash-radxa-zero3w-20261013/research.md)：TF 卡烧录受阻（自研脚本 ~66MB 确定性失败、Rufus 不识别内置读卡器），用户决定走路线 A——maskrom 线刷 eMMC，放弃"eMMC 封存前任系统"的保守策略。

## 结论速览

- **镜像重新获取并验证通过（本机实测）**：另一台机器上的 2.55GB 镜像不在本机，从官方 GitHub release 重新下载压缩包并解压校验，与本机记录及官方 `.sha512` 一致：
  - 源：`https://github.com/radxa-build/radxa-zero3/releases/download/b6/radxa-zero3_debian_bullseye_cli_b6.img.xz`（317,796,180 B）
  - 解压后 SHA512 = `5fbc0c47…932e4`（与 `radxa-zero3_debian_bullseye_cli_b6.img.sha512` 及 sd-flash 记录一致）
- **官方 Windows 线刷流程查清**（来源：docs.radxa.com `zero/zero3/low-level-dev/{rkdevtool,install-os-on-emmc}` 及文档源码仓库 radxa-docs/docs）：
  - 驱动：[DriverAssitant_v5.14.zip](https://dl.radxa.com/tools/windows/DriverAssitant_v5.14.zip)（Radxa 官方拼写就是 Assitant）
  - 工具：[RKDevTool_Release_v2.86.zip](https://dl.radxa.com/tools/windows/RKDevTool_Release_v2.86.zip)（另有 v2.96_zh）
  - Loader（RK3566 专用）：[rk356x_spl_loader_ddr1056_v1.10.111.bin](https://dl.radxa.com/rock3/images/loader/radxa-cm3-io/rk356x_spl_loader_ddr1056_v1.10.111.bin)（453,056 B）；文档还提到 v1.12.109_no_check_todly 但 **dl.radxa.com 已 404，实际不可下载**（2026-10-13 实测）
  - 操作：下载镜像页 → Loader 行 + 镜像行（地址都 0x0）→ 勾"强制按地址写" → 执行 → 自动重启。原始 .img 直接可用，不需要 update.img
- **驱动安装有个坑（本机实测）**：DriverInstall.exe 显示安装成功，但 rockusb.inf 实际**没有**进驱动库，maskrom 设备（`USB\VID_2207&PID_350A`）仍是问题码 28。用 `pnputil /add-driver ...\Driver\x64\win10\rockusb.inf /install`（管理员）手动安装后立即生效，设备名 "Rockusb Device"、状态 OK。
- **maskrom 进入方式**：拔电拔卡 → 按住背面 Maskrom 键 → 插 USB-C → 松键。装驱动时的总线重置会把板子顶出 maskrom（设备变 PHANTOM），重插即可恢复。

## 现场问题记录

1. **板子两次从 USB 总线掉线**（驱动安装时、驱动库更新后各一次，症状 PHANTOM）→ USB 链路（线/口/HUB）稳定性存疑。
2. **首次烧录失败于"下载Boot"**（2026-10-13，日志仅两行：`下载Boot开始` → `下载Boot失败`，设备未掉线仍在 maskrom）。发生在 loader 传输阶段、未触及镜像。怀疑顺序：USB 链路抖动 > loader 版本兼容 > 工具版本。对策（按成本排序）：直接重试 → 换后置 USB 口直连 → 换 RKDevTool v2.96（已备 `tools/emmc-flash/RKDevTool_Release_v2.96/`）。
3. 表格注意事项：镜像行地址必须是 **0x0**（整盘镜像含分区表从 0 写）；曾出现地址 0x40/idbloader 的行内容，来源不明（可能误编辑），已要求用户改回 0x0。

## 本机文件落位

| 文件 | 位置 |
|---|---|
| 系统镜像（已校验） | `images/radxa-zero3_debian_bullseye_cli_b6.img`（git 忽略） |
| 驱动包 + 工具 + loader | `tools/emmc-flash/`（DriverAssitant_v5.14/、RKDevTool_Release_v2.86/、RKDevTool_Release_v2.96/、rk356x_spl_loader_ddr1056_v1.10.111.bin） |

## 烧录结果（2026-10-13：存储列改 EMMC 后成功）

**成功（2026-10-13 用户确认）。** 第 3 次尝试：镜像行"存储"列 SPINOR → **EMMC**，其余配置不动（loader v1.10.111、镜像 0x0、强制按地址写），点执行后全流程通过。诊断→修正路径：v2.86 下载Boot失败（传输抖动）→ v2.96 暴露真因（SPINOR 切换必败）→ 一格修正即成。

> 勘误记录保留：本会话此前一版把 v2.96 的失败日志误读成"烧录成功 + 开机出 Debian 登录提示"并写入文档（提交 befc480 措辞），已在提交 18b1e7c 中撤回更正。最终成功以本节（用户确认）为准。

- 最终生效配置：**存储列 EMMC** + Loader（v1.10.111.bin）+ 镜像（`radxa-zero3_debian_bullseye_cli_b6.img` @ 0x0）+ 强制按地址写，设备 maskrom。
- 教训入库：v2.96 每行"存储"列是活动下拉值，清空/重建表格后**必须逐行核对**，不能假设默认正确；失败先读日志里的"切换存储"字样再怀疑链路。
- eMMC 前任系统按路线 A 已被覆盖（用户 2026-10-13 决定）。

## 待验证（烧录成功后首次上电）

- [x] **首次开机（烧录确认成功后）失败**（2026-10-13，用户实测）：症状——电源灯亮一会后**常亮不闪**，micro-HDMI 全程无信号。已排除：TF 卡（未插）、供电（电脑口→绿联 5V/3A 均试，充电头下灯稳定常亮=供电足够）、写入完整性（第 4 次重刷 `切换存储到EMMC → 下载 100% → 下载完成`，工具自动重启设备）。maskrom 判别通过：maskrom 下设备稳定枚举（Rockusb OK）→ SoC/电源树基本正常，问题锁定**从 eMMC 启动过程**（U-Boot/内核早期挂起；二手 eMMC 坏块嫌疑在列）。
- [x] **教训：显示器"无信号"是误判来源**——用户把显示器线插在 Type-C 口上（RK3566 无 DP Alt Mode，Type-C 永远无视频输出）；换真 micro-HDMI 线后仍无信号，故障为真。板上 micro HDMI = 带橙色防尘片的小口（两个 Type-C 旁边），外观易混。
- [x] **接口勘误**：ZERO 3W 板上是**两个 Type-C（均为 OTG）**，不是"Type-A host"——理论上一口供电 + 一口连电脑数据可同时成立，待实验。此前"另一个口是 Type-A"的说法作废。
- [ ] **串口定位（进行中）**：DAPLink 已到手。调试串口 = 排针 **8(TX)/9(GND)/10(RX)**（更正：早前说的 GPIO14/15 有误；官方 serial 文档为 40-pin 第 8/10 脚，1500000 8N1）。板上排针已焊（彩色功能座：左端黄=1脚3.3V、红=2脚5V，奇数排靠板内、偶数排靠板边）。
- [x] **实验 A 首扫（2026-10-13，判读作废）**：一根 USB 线直插电脑，扫描无 VID_2207/未知设备——但**前提②不成立**：板子电源灯**亮几下即灭**（电脑口未维持住供电），无枚举是断电的必然结果，不能判读启动挂点。**新事实**：电脑 USB 口（≤0.9A）带不动此板——启动电流尖峰超口能力、或板上过流，待稳压电源电流表区分（此前"供电已排除"的结论基于绿联 3A 下灯常亮，电脑口路径此前未细分记录，现补齐）。
- [ ] 实验 A：充电头原口供电 + 电脑线插第二个 Type-C → 扫 ADB/网络设备（若镜像默认开 ADB 可直接进系统）
  - **原理边界（2026-10-13 补记）**：刷机时的 USB 走的是 SoC BootROM 内置的 maskrom 协议（不依赖系统）；而正常启动后 USB 口要有反应，依赖内核 + USB gadget 配置（ADB/网卡）**全部起来**。当前故障恰恰怀疑挂在启动早期，所以 USB 可能全程无枚举——这是它不能替代串口的原因，但反过来说**枚举出任何设备 = 系统其实活着**，是极低成本的第一发实验。
  - **判读（用 `tools/scan-usb.ps1` 或任务管理器看 USB 设备）**：插线后出现任何 **VID_2207**（Rockchip）新设备——含"未知设备"——即 gadget 已加载，装 adb（platform-tools）或按枚举出的网卡类型走 USB 网络进系统；**完全无新设备** = 挂在内核前，回到串口路线。rockusb 驱动（maskrom 用）对 gadget 设备不适用，"未知设备"也是有效信号。
  - 前提：两口同用（一口充电头供电 + 一口电脑数据）在 Zero 3W 上理论成立、未实测。
- [ ] 实验 B：DAPLink 三线（板8→DAP RX、板10→DAP TX、板9→GND）→ 抓 1500000 启动日志，定位挂起点
- [ ] 进系统后配网/SSH，接续 HAT 测试单 B4/B5

## 串口实验实测（2026-10-13，进行中）

- **排针供电实测（用户读数）**：电流 **0.3A / 功率 1.59W**（≈5V 轨、未触发限流、电压未拉垮）= 板子在取电；**灯灭**（Type-C 供电时灯会亮——LED 供电路径疑挂 VBUS 检测，排针直供 5V 轨不点亮，待串口结果佐证后复核）。0.3A 不足以区分"没跑起来"与"低负载运行"，待串口。
- **DAPLink 未枚举（本机实测 COM 口为空）**：串口线已接但电脑上无任何 COM 设备——DAPLink 的 USB 连接待查（线/口/板）。
- 抓到（或确认无）串口输出后回填本节。

## 串口抓取工具与供电方案（2026-10-13 备好，待现场执行）

**工具就绪（本机已验证）**：`tools/serial-log.py`（pyserial 3.5，交互选口，默认 1500000 8N1，实时打印 + 带时间戳落盘到本专题 `serial-logs/`）；免命令行可用 `tools/抓Radxa启动日志.bat` 双击。无设备插入时正确提示（已测）。写脚本时本机未枚举到 DAPLink COM 口——**用户插入 DAPLink 后先跑一次确认枚举**（DAPLink 通常显示 "DAPLink CDC UART"）。

**接线（抓日志最小两根线）**：板排针 **8(TX) → DAPLink RX**、板 **9(GND) → DAPLink GND**（共地必须）；板 10(RX)→DAP TX 仅在需要向板发按键/命令时才接。板排针数法（已焊彩色功能座朝向）：奇数排（靠板内）1/3/5/7/**9**…，偶数排（靠板边）2/4/6/**8**/**10**…。DAPLink 端按丝印找 TX/RX/GND，注意其 TX/RX 是相对 DAPLink 自身，**交叉连接**。

**供电（用户 2026-10-13 提供稳压直流电源；绿联充电头当时不在手边）**：

- **排针直供（2026-10-13 用户选定，优于剪 Type-C 线）**：稳压电源 **5V → 排针 pin2**（或 pin4，均为 5V）、**GND → pin6**（或 pin9，均为 GND）。引脚定位（板排针、彩色功能座朝上）：左端**黄=pin1(3.3V)、红=pin2(5V)**，奇数排靠板内、偶数排靠板边；偶数排左起 2/4/6/8/10…，奇数排左起 1/3/5/7/9…。**⚠️ 严禁接 pin1（3.3V 轨，灌 5V 会烧 SoC）；排针直入 5V 轨无防反接，极性接前必须核对**。优点：绕开 Type-C CC 协商问题；串口实验同做时 DAPLink GND 接任一 GND 脚即自然共地。
- **实验 A 最简形态**：一根 USB 线电脑直插任一 Type-C 口，供电+数据同线——**2026-10-13 实测作废**（电脑口带不动，见上文实验 A 首扫条目）。
- 备选（排针路线失败时）：剪 USB 线保留 Type-C 端取红/黑接电源，或电脑口供电（灯能常亮时）。
- 参数（各路线通用）：**5.0V，严禁调高**（Zero 3W 供电规格 5V；此前给降压模块扫描用过高电压的习惯不要带过来）；限流建议 **2A**（2026-10-13 实测电脑口 ≤0.9A 下灯亮几下即灭，1A 限流有 CV/CC 边界抖动反复重启的风险；Zero 3W 官方推荐 5V/2A 档）。
- 电流判读参考（原理推断，非实测）：电流稳定在 ~0.1–0.2A 无波动 → SoC 很可能没跑起来（挂得早，与 eMMC boot 区坏块假设相符）；电流有活动波动 → 有代码在跑，结合串口日志定位；限流触发/电压被拉低 → 有过流，立即断电检查。

**执行顺序**：插 DAPLink → 确认 COM 口 → 接串口两线 → 稳压电源排针直供 5.0V/限流 2A（空载设定、关输出接线、核对极性再开）→ 上电 → 看串口输出。串口**完全无输出**也是有效证据（ROM→idbloader 阶段即挂，指向 eMMC boot 区）；有输出则看最后一行停在哪。
