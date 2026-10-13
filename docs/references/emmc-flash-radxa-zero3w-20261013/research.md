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

## 烧录结果（2026-10-13，本机实测，用户操作）

**成功。** 重试一次后全流程通过，日志依次为：

```
下载Boot开始 → 下载Boot成功 → 下载镜像开始
→ 正在下载镜像【未写入设备】0→100%   （镜像读入 PC 内存）
→ 正在写入设备 0→100%                （写入 eMMC）
→ 下载镜像成功
```

- 首次失败确认为**一次性传输抖动**：同一 loader（v1.10.111）、同一表格配置，重试即通过；未换 USB 口、未换工具版本。
- 最终生效配置：下载镜像页两行——Loader（v1.10.111.bin）+ 镜像（`radxa-zero3_debian_bullseye_cli_b6.img` @ 0x0），勾选"强制按地址写"，设备处于 maskrom。
- 前任 eMMC 系统按路线 A 决定已被覆盖（用户 2026-10-13 确认）。

## 待验证（烧录后首次上电）

- [ ] 拔 USB-C 后独立供电，电源灯/启动灯行为；HDMI 控制台是否出登录提示（radxa/radxa）
- [ ] 进系统通路三选一：HDMI+键盘 / USB 串口（DAPLink 到货后接 GPIO 调试口 1500000 8N1）/ 配网后 SSH
- [ ] 之后接续 HAT 测试单 B4/B5（USB 出 COM 口 → WiFi → ssh → 舵机 ping）
