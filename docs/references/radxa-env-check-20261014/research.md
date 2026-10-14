# Radxa Zero 3 机器人软件环境核查（2026-10-14）

## 问题与范围

板子重刷 rsdk-b1 镜像救活并配好网络/SSH 后，核查机器人软件环境（Python、串口、工具链、总线接口）是否满足 C 线（飞特 HD-1910 + HAT + robotd）部署需要。仅远程只读检查，未安装/改动任何软件。

## 环境基线（SSH 实测，`ssh radxa`）

- Debian 12 bookworm，内核 6.1.84-10-rk2410-nocsf，4 核，3.8 GiB 内存，eMMC 57G（已用 5.9G）
- 免密登录已配置：本机 `id_ed25519` → 板子 `~/.ssh/authorized_keys`（2026-10-14 验证 KEY_AUTH_OK）；`~/.ssh/config` 已加 `Host radxa` 别名

## 已有（可用）

| 项 | 状态 |
|---|---|
| Python 3.11.2 + pip 23.0.1 | ✅ 系统自带 |
| git 2.39.5 / gcc / make | ✅ |
| i2c-tools、device-tree-compiler | ✅ |
| numpy 1.24.2 | ✅（pip 唯一第三方包） |
| I2C | /dev/i2c-0/3/6 ✅ |
| GPIO | /dev/gpiochip0–5 ✅（用户在 gpio/i2c/spidev/pwm/dialout 组） |
| 网络 | WiFi `CU_M9pw_5G` 已配自动连接 ✅ |

## 缺口（2026-10-14 已全部补齐）

| 项 | 处理 | 结果 |
|---|---|---|
| pyserial | `apt-get install python3-serial` | ✅ 3.5 |
| cmake | `apt-get install cmake` | ✅ 3.25.1 |
| UART2/ttyS2 | 启用 overlay `rk3568-uart2-m0`（rsetup 兼容列表中唯一适配 zero3 的 UART2 overlay；M0 mux = 排针 pin8/pin10，与 HAT A3 实测一致；会禁用 fiq_debugger 调试节点，属官方设计）→ `u-boot-update` → 重启 | ✅ /dev/ttyS2 出现，serial@fe660000 status=okay；蓝牙仍独占 ttyS1（hciattach active），两者不冲突 |

过程要点：

- **overlay 副作用**：rk3568-uart2-m0 的 exclusive 列表含 fiq_debugger——pin8/10 原本是调试串口控制台（DAPLink 抓启动日志用的就是它，1500000 波特）。启用后这对引脚归普通串口驱动（ttyS2），**内核段启动日志不再输出**；U-Boot 阶段输出不受影响。需要抓启动日志时临时把 dtbo 改回 .disabled 重启即可。
- 回环自测（`feetech-ping.py loop`，pin8↔pin10 杜邦短接）验证的是"引脚从 fiq-debugger 切到 8250 驱动后的用户态收发链路"，不重复证明引脚电气连通（调试串口时期已验证）；也**覆盖不到 HAT 74LVC 半双工驱动/换向**，那部分只能在 C4（HAT 上电+舵机）验证。属可选项。

- 板子出境网速慢（deb.debian.org RTT ~220ms，约 25–50 KB/s），apt/pip 前台命令易超时；用远程 `nohup bash -c '...' > /tmp/apt-install.log 2>&1 &` 后台执行 + 轮询日志的方式完成。
- 首次 `apt-get update` 卡死被误杀过一次（pkill -f 匹配到自身 SSH 命令行导致会话断开，改用 `pkill -x apt-get` 精确进程名解决）。
- overlay 启用机制：/boot/dtbo/*.dtbo（去掉 .disabled 后缀）由 u-boot-update 汇总进 /boot/extlinux/extlinux.conf 的 `fdtoverlays` 行；/etc/default/u-boot 的 U_BOOT_FDT_OVERLAYS_DIR=/boot/dtbo/。
- 注：镜像初始 apt 索引不全（package lists 未下载过），直接 install 会 "Unable to locate package"，必须先 update。

## 其他发现

- 家目录有异常文件 `~/udo -S -p  sh`（ASCII 文本，内容是 `less` 帮助页）——系历史上某次命令行误操作把分页器帮助重定向成了文件，与系统功能无关，可删（未擅自删除，待用户确认）。
- `pip list --outdated` 查询超时（可能网络慢），未做升级。
- dtbo 目录（/boot/dtbo）全部是 `.disabled`，当前没有用户启用任何 overlay；UART2 启用方式待按 Radxa Zero 3 文档确认（rsetup → Overlays）。

## 验证状态

- 全部为 SSH 远程只读命令输出（2026-10-14）。
- 未验证：ttyS2 overlay 启用后的实际引脚输出（需动硬件配置，属 HAT 测试单 B4/B5 范畴）。

## 下一步

1. ~~HAT 测试单推进到 B4 前：装 pyserial + cmake，开 UART2 overlay，重启确认 /dev/ttyS2 出现。~~（2026-10-14 已全部完成，见上表）
2. B4（主控 ssh 上 HAT）→ B5（单舵机 ping）按 docs/hat-v1.2-test.md 执行。
