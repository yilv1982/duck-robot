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

## 缺口（部署 C 线前需补）

| 项 | 现状 | 影响 |
|---|---|---|
| **pyserial** | 未安装（`import serial` 报 ModuleNotFoundError） | 舵机/IMU 总线通信必需；`sudo apt install python3-serial` 或 pip 均可 |
| **cmake** | 未安装 | 编译 robotd/社区主机工具需要 |
| **第二个 UART** | 全系统只有 `/dev/ttyS1`，且 **ttyS1 被蓝牙占用**（`rsetup-hciattach@ttyS1.service` active） | HAT 舵机总线设计走 **UART2 = ttyS2**（见 HAT 查证记录），当前未启用——需开 overlay（rsetup 或 dtbo）后出现 /dev/ttyS2，B5 单舵机 ping 的前置条件 |
| udev 规则 | /etc/udev/rules.d 为空 | 后续为串口设备定别名/权限时需要 |
| 机器人软件 | 板上无任何 robotd / 社区套件 / Feetech SDK | 待部署（可先在本机研究，部署阶段再拷入） |

## 其他发现

- 家目录有异常文件 `~/udo -S -p  sh`（ASCII 文本，内容是 `less` 帮助页）——系历史上某次命令行误操作把分页器帮助重定向成了文件，与系统功能无关，可删（未擅自删除，待用户确认）。
- `pip list --outdated` 查询超时（可能网络慢），未做升级。
- dtbo 目录（/boot/dtbo）全部是 `.disabled`，当前没有用户启用任何 overlay；UART2 启用方式待按 Radxa Zero 3 文档确认（rsetup → Overlays）。

## 验证状态

- 全部为 SSH 远程只读命令输出（2026-10-14）。
- 未验证：ttyS2 overlay 启用后的实际引脚输出（需动硬件配置，属 HAT 测试单 B4/B5 范畴）。

## 下一步

1. HAT 测试单推进到 B4 前：装 pyserial + cmake，开 UART2 overlay，重启确认 /dev/ttyS2 出现。
2. B4（主控 ssh 上 HAT）→ B5（单舵机 ping）按 docs/hat-v1.2-test.md 执行。
