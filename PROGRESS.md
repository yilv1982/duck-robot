# 进度记录

事实性的进度流水：什么时候到了什么、做了什么。核对结论与安全边界见 [README](./README.md) 与 [BOM](./BOM.md)。

## 参考库使用规则（2026-10-09 起）

**`microduck-replica/`、`microduck-community-kit/`、`microduck-build-tutorial/` 是别人的方案，只读参考，不在里面做任何修改。** 自己的进度、笔记、补丁一律放工程根目录（本文件、`docs/`、`local-changes/`）。历史上混入参考库的本地修改已于 2026-10-09 提取到 [local-changes/](./local-changes/) 并把参考库还原为上游原样：

| 参考库 | 上游 | 本地状态 | 校验（2026-10-09，逐文件 SHA256，忽略 CRLF/LF） |
|---|---|---|---|
| microduck-replica | fanhao375/microduck-replica `master` | 固定提交快照 `0f2cff6bd7`（2026-09-28，444 文件，与 README 记录一致） | 还原后与该提交 **0 新增 / 0 缺失 / 0 差异** |
| microduck-build-tutorial | AI-FanGe/Microduck-build-tutorial `main` | 内容等于 2026-10-09 上游 main | 还原后 **0 新增 / 0 缺失 / 0 差异** |
| microduck-community-kit | jyg9/microduck-community-kit `main` | 2026-10-09 zip 下载（无 git 历史） | 上游 zip 原样 + 手动补齐 `.gitmodules` 声明的 GD32F30x_Firmware_Library 子模块内容（参考完整性，非代码改动，是本目录唯一保留的添加） |

## 2026-10-09 硬件到位

用户确认到位（照片 + 口头识别；实物复测未做）：

| 物品 | 数量 | 说明 / 待办 |
|---|---|---|
| 微雪 Waveshare Bus Servo Adapter (A) | 1 | 半双工总线转接板，即 replica《电控采购清单》的「半双工总线转接板」待买项；此前台架一直用 FE-URT-2 顶替。整机走它还是飞线，待测 |
| 黑色降压模块（XT60 端子） | 1 | 板上丝印 **7.2-16V**（照片识别，待万用表核）。⚠️ 若输入下限真是 7.2V：2S 电池带载跌到 6.6V 时会掉出稳压——清单要求下限 ≤6V，用前实测 |
| 绿色 IMU 板 | 1 | **用户确认 = ScrapMeta microduck-diy imu_to_dxl v0.3**（STM32G031，板 32×22mm）。三版来源对比与刷机兼容性查证见 [docs/references/imu-to-dxl-variants-20261009](./docs/references/imu-to-dxl-variants-20261009/research.md)；**飞特固件刷写包已备好**（[flash/](./flash/README.md)：校验过的 0.2.0 HEX + OpenOCD + 一键脚本 + imu200 验收工具），⚠️ 该板 LDO 上限 5.5V，**只能 5V 供电**，2S 总线集成时 VCC 须走 5V 支路 |
| 白色鸭图案 HAT（V1.1） | 1 | **原理图已归档查证**（2026-10-09，[docs/references/microduck-hat-20261006](./docs/references/microduck-hat-20261006/research.md)）：官方 RPI Robot HAT 的嘉立创 EDA 派生版，Radxa Zero 3W（舵机总线 UART2=ttyS2）兼容 Pi Zero 2W，比官方多一颗 BNO085。原理图 V1.0 与手上 PCB V1.1 的差异待核 |
| 全部舵机 | 待清点 | 型号/数量/出厂 ID 状态待登记。飞特方案按官方关节表应为 HD-1910-C001 ×15（含嘴） |
| 打印件 | 待清点 | 版本/材料/数量待登记；打印模型以上游独立仓库 microduck-replica-cad 为准 |

台架现状：总线调试用 FE-URT-2 + 飞线；转接线是否随本批到货未记录。

**原理图档案（2026-10-09 建）**：已确认硬件的设计文件统一存 [docs/schematics/](./docs/schematics/README.md)——IMU 板（ScrapMeta v0.3 的 `.eprj2` 真源工程 + 网表，钉 `main @ aa4c32d`）、HAT V1.1（5 页 PDF）；微雪转接板与降压模块为成品模块无公开原理图，暂只记规格待补。

### 由到货衍生的待办

- [ ] 万用表实测降压模块输入下限、输出电压与带载表现
- [x] 确认 IMU 板是哪一版设计（2026-10-09 用户确认：ScrapMeta microduck-diy v0.3）
- [ ] 按手顺完成 IMU 板刷机：购 SWD 调试器（推荐 DAPLink）+ SH1.0 7P 线 → 接线 → 双击 `flash/1-烧录-DAPLink.bat` → 断电重启 → `flash/3-验收-imu200.bat` 全 PASS（详见 [flash/README.md](./flash/README.md)）
- [ ] 清点舵机（型号、数量、ID/零位状态）与打印件（版本、材料、缺件）
- [ ] 微雪转接板上机验证（对比飞线方案）
- [ ] 向板卡来源确认 HAT PCB V1.1 相对原理图 V1.0 的改动（2026-10-06 导出的图为 V1.0）
- [ ] 飞特舵机原线（5264 端子）与 HAT 的 JST EH 3P 舵机座试插；不配则换 5264-3P 座或转接线
- [ ] HAT V1.1 与手头主控/外壳的机械与电气适配核对

## 2026-10-09 参考库清理（提取 → 还原）

- `microduck-replica/调试记录.md`：此前会话把 10-09 到货记录（7 行）写进了上游作者的表格里。用户相关内容已转录到本文件上表；原文件还原为上游版（「手头有的」等小节本来就是上游作者 fanhao375 的库存记录，不是本项目的）。
- `microduck-build-tutorial/`：A 训练重建的库内修改（4 个改文件 + 51 个添加文件，清单见 [local-changes/README](./local-changes/README.md)）全部提取，目录还原为上游原样。A 训练的说明与验收记录不受影响：[docs/a-training.md](./docs/a-training.md)、[docs/a-training-validation.json](./docs/a-training-validation.json)。

## 方案方向（2026-10-09）

- **主参考 = microduck-community-kit（飞特路线）**：HD-1910-C001 + 官方 robotd 的飞特补丁（`firmware/v1/patches/`）+ imu_to_dxl 总线从站（ID 200，双协议）。与手头硬件（飞特舵机、IMU2DXL 板、微雪半双工转接板）直接对口。
- replica 作为机械/装配/电控采购资料来源；build-tutorial 保留 A 训练基线存档（已提取到 local-changes）与教程对照。
- community-kit 已知缺口，用前留意：
  1. `software/microduck_feetech/` 完整源码**未推送**（README 提及但 main 分支没有；补丁文件在，基线官方 `f0d934e`，但完整树比补丁新三处关键修复——删 `tcdrain`、`BURST_IDLE` 2→4ms、同步上游 10 提交）；
  2. 主控↔舵机总线的物理适配层未开源（三块板只覆盖取电/配电/IMU）——**已由手头 HAT 补上**：板上 74LVC 半双工驱动 + UART2（Radxa `ttyS2`）正是 robotd 飞特补丁期望的总线入口，见 [HAT 查证记录](./docs/references/microduck-hat-20261006/research.md)；
  3. 真机整定值只能参考不能照抄：增益默认 32（200 会自激振荡，5A/74°C）、关节方向实测 −1（与 XL330 相反）、电池满/空电压阈值需复测。

## 工程迁移

2026-10-09 工程从 `E:\Projects\duck-robot` 迁到 `C:\Projects\duck-robot`（全部文件时间戳为迁移当日，无法再据时间戳判断改动，版本核对一律以上游哈希为准）。历史文档/脚本里的 `/mnt/e/`、`E:/` 路径已失效；本次已修根 README 的 3 处链接与 `scripts/a-training.sh` 的 2 处路径，`local-changes/` 里的提取件（export_onnx.py 等）仍含旧路径，复用前需改。

**本机新装工具链（2026-10-09）**：Python 3.13（`%LOCALAPPDATA%\Programs\Python\Python313`，含 pyserial）、OpenOCD 0.12.0（工程内 `flash/tools/`）、嘉立创EDA专业版 3.2.149（`%LOCALAPPDATA%\Programs\lceda-pro`，可开 `.eprj2`）。注意：本机无 git（用 GitHub Desktop 内嵌 git 提交）、无 WSL——旧机器的训练环境不在这台机器上。
