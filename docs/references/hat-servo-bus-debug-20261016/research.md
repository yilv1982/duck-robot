# HAT→舵机总线联调排障（2026-10-16/17）

## 问题与范围

HAT V1.2 + Radxa Zero 3W 对插、7.4V 焊盘进电、舵机经杜邦过渡线接 SERVOS 座：`feetech-ping.py scan` 全范围 0–253 **0 个舵机应答**。逐步隔离定位。本文所有结论均为本机实测（用户现场万用表读数 + ssh 远程命令）。

## 时间线与已排除项

| 排查步骤 | 结果 | 结论 |
|---|---|---|
| 舵机口电压 | pin2(Vcc) 对地 7.4V ✓ | 舵机供电正常 |
| Signal 电平 | 舵机座 DATA 针对地 1V（发送 0x55 时也不变） | HAT 输出侧异常，立为疑点 |
| 插舵机后 Radxa 起不来 | 用户定位为杜邦线接触不良，重接后系统正常 | 接触问题结案（该现象与 DATA 疑点无关） |
| ttyS2 权限 | Permission denied → sudo 可跑；radxa 已入 dialout 组 | 已修 |
| fiq_debugger | `/proc/cmdline` 有 `console=ttyFIQ0,1500000n8`；数据写 /dev/ttyS2 被截 | **已修**：从 `/etc/kernel/cmdline` 删除该参数 + `/etc/default/u-boot` 显式设 `U_BOOT_FDT_OVERLAYS="rk3568-uart2-m0.dtbo"` + `u-boot-update` 重生成。重启后 `/dev/ttyFIQ0` 消失、DT fiq-debugger 节点 disabled。备份：`/etc/kernel/cmdline.bak-fiq`、`/boot/extlinux/extlinux.conf.bak-fiq`（板上） |
| 修 fiq 后复扫 | 仍 0 舵机；DATA 针仍 1V 不动 | fiq 是必要修复但不是全部根因 |
| pinmux | `pinmux-pins`: gpio0-24/25 = fe660000.serial, function uart2, group uart2m0-xfer ✓ | overlay/mux 生效 |
| pin8 上游电平 | 3.16V（TX 空闲高），发送窗口内量"不动"（疑错过 120s 窗口） | 见回环 |
| **回环测试**（排母 pin8↔pin10 短接） | **PASS**（发 36 字节收 36 字节） | **Radxa 串口全链正常** |

## 当前结论（待 HAT 侧证据）

- Radxa 侧完整无问题：驱动、mux（uart2m0）、pin8/10 物理收发全部实测通过。
- **故障域收敛到 HAT 板内 74LVC 半双工驱动一侧**：pin8 空闲 3.16V 正常进 HAT，但舵机座 DATA 针 1V 且不随发送变化。
- 未解：74LVC 供电（3.3V 来自主控 pin1/17？）/ 使能或换向电路 / V1.2 与 V1.0 图差异（V1.2 多一颗 GD32F3xx，A4 蜂鸣档不连 pin3/8/10 但隔电阻连接测不出）——**无 V1.2 图纸，深挖性价比低**。

## 下一步（进行中）

**绕过 HAT 驱动直连舵机**：FE-URT-2（台架验证过与 HD-1910 @1Mbps 兼容）DATA/GND 接舵机口，舵机电源继续走 HAT 座 7.4V，电脑侧 `scripts/feetech-ping.py --port COMx` ping。
- URT-2 通 → 舵机 OK + ID 确认 → 台架期主控通信先用 URT-2 或评估飞线；HAT 驱动问题挂起，向板卡来源索取 V1.2 图纸后再修。
- URT-2 不通 → 舵机本身或波特率问题。

## 附带发现：pin8/10 短接状态下上电会锁死 U-Boot（用户实测）

pin8/10 即 U-Boot 调试串口。**先短接再上电 → U-Boot 打印的 banner 直接回灌自己的 RX，被当作键盘输入，卡在 U-Boot 交互界面无法引导内核**（现象：灯亮、HDMI 无信号、ping 不通）。回环 PASS 那次未锁，是因为短接在上电后才接触好——U-Boot 只在开机头 1–2 秒监听串口。**纪律：不在 pin8/10 短接状态上电；回环测试已做完（PASS），不需要再做。** 此发现同时提示：任何把 pin8 信号回灌 pin10 的总线侧故障都会表现成"无法启动"，排查启动失败时须考虑串口回灌路径。

## 附带环境事实

- Radxa 重启后 WiFi 就绪需 1–2 分钟（NetworkManager 服务序 + DHCP；KDE 镜像服务多），期间 ping 不通不代表没启动。后续可做静态 IP / 禁 IPv6 优化，未做。
- `~/.ssh` 免密配置丢失事件与重建见 [radxa-env-check 2026-10-16 补充](../radxa-env-check-20261014/research.md)。
- 舵机座针序/杜邦交叉纪律见 [EH 采购调研](../eh-crimp-purchase-20261012/research.md)。
