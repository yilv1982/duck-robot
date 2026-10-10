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
| 微雪 Waveshare Bus Servo Adapter (A) | 1 | 半双工总线转接板，即 replica《电控采购清单》的「半双工总线转接板」待买项；此前台架一直用 FE-URT-2 顶替。整机走它还是飞线，待测。2026-10-10 照片归档+元件标注（[docs/photos/](./docs/photos/README.md)）：实物 v1.1，输入**直通舵机口不稳压**（HD-1910 台架喂 2S，严禁 12V），跳线 A=UART/B=USB（CH343） |
| 黑色降压模块（XT60 端子） | 1 | 2026-10-10 照片细读（[存档](./docs/photos/README.md)）+ **空载实测**（[操作单](./docs/buck-module-test.md)）：板名 **BUS SERVO POWER SUPPLY V1.3**（By 造物の乐趣，社区自研件，公开无资料，二维码待扫）；丝印 PWR IN 7.2-18V / OUT PWR 5V or 7.4V MAX 6A。**实测**：VCC（3P）12V→6.00V、6.6V→6.00V、6.3V→5.99V——选压桥 **6V 档**、稳压下限 **≈6.3V**（跌落跟随非关机，远好于丝印 7.2V），**2S 最差工况可用**；PWR OUT（2P）全程跟随输入 = **电池直通口**（舵机总线，对上 HD-1910 直挂 7.8-8.1V 用法）。接口分工闭环（~~DC 母座~~系照片误判，实物无此件）。**接 IMU 前须改焊 5V 档**（LDO 上限 5.5V），带载复测待台架 |
| 绿色 IMU 板 | 1 | **用户确认 = ScrapMeta microduck-diy imu_to_dxl v0.3**（STM32G031，板 32×22mm）。三版来源对比与刷机兼容性查证见 [docs/references/imu-to-dxl-variants-20261009](./docs/references/imu-to-dxl-variants-20261009/research.md)；**飞特固件刷写包已备好**（[flash/](./flash/README.md)：校验过的 0.2.0 HEX + OpenOCD + 一键脚本 + imu200 验收工具），⚠️ 该板 LDO 上限 5.5V，**只能 5V 供电**，2S 总线集成时 VCC 须走 5V 支路 |
| 白色鸭图案 HAT（**实物丝印 V1.2**，2026-10-10 照片更正，此前误记 V1.1） | 1 | **原理图已归档查证**（2026-10-09，[docs/references/microduck-hat-20261006](./docs/references/microduck-hat-20261006/research.md)）：官方 RPI Robot HAT 的嘉立创 EDA 派生版，Radxa Zero 3W（舵机总线 UART2=ttyS2）兼容 Pi Zero 2W，比官方多一颗 BNO085。**2026-10-10 正反面照片归档+元件标注**（[docs/photos/](./docs/photos/README.md)）：实物 V1.2 与存档原理图 V1.0 差异大——**背面多一颗 F303 类 MCU（LQFP48）+ 正面多一颗超级电容（疑 RTC 备份），V1.0 图中均无**；RS485 座未焊。接线/上电前须索取 V1.2 原理图 |
| 全部舵机 | 待清点 | 型号/数量/出厂 ID 状态待登记。飞特方案按官方关节表应为 HD-1910-C001 ×15（含嘴） |
| 打印件 | 待清点 | 版本/材料/数量待登记；打印模型以上游独立仓库 microduck-replica-cad 为准 |

台架现状：总线调试用 FE-URT-2 + 飞线；转接线是否随本批到货未记录。

**工具与耗材到位（2026-10-09 用户口头确认，实物未复测）**：

| 物品 | 数量 | 说明 / 待办 |
|---|---|---|
| 万用表 | 1 | 解锁「降压模块实测」待办（与直流电源配合） |
| 稳定直流电源 | 1 | 做降压模块输入下限/输出电压扫描；带载表现后续用台架实测 |
| 电烙铁 | 1 | 解锁 IMU 板 J2 焊接、banana_pcb 焊接工序。焊锡/助焊剂已确认有 |
| 电池盒 | 1 | 对应 banana_pcb 取电方案；化学体系/串数/触点形式待登记 |
| 杜邦线 | 若干 | 可走 IMU J2「杜邦线直焊焊盘」路线（替代 BM07B-SRSS-TB 座 + SH1.0 7P 线） |
| 无头电子线 | 若干 | banana_pcb「拆电池焊接出线」备选线材；线径须按 3-5A 核对，具体线规待登记 |

**工具照片存档（2026-10-10 建，同日降压模块正反面入档）**：[docs/photos/](./docs/photos/README.md)——万用表、直流电源、降压模块正反面（含元件标注图）实拍照片已从微信缓存拷入永久保存；后续照片（J2 焊盘、HAT、舵机/打印件清点）同规则补入。

**在途（2026-10-09 用户确认已发货）**：DAPLink SWD 调试器、U6068 插针 ×2、电池。到齐后 IMU 刷机链路（J2 焊接 → DAPLink 烧录 → imu200 验收）与 banana_pcb 装配的硬件缺件清零；电池到货后登记化学体系/串数/触点，与电池盒、降压模块实测结果一起定供电方案。

**原理图档案（2026-10-09 建）**：已确认硬件的设计文件统一存 [docs/schematics/](./docs/schematics/README.md)——IMU 板（ScrapMeta v0.3 的 `.eprj2` 真源工程 + 网表，钉 `main @ aa4c32d`）、HAT（5 页 PDF，图版本 V1.0；实物 2026-10-10 照片确认为 V1.2，目录已更名 `microduck-hat-v1.0-sch`）；微雪转接板与降压模块为成品模块无公开原理图，暂只记规格待补。

**banana_pcb 打板已下单（2026-10-09 用户确认），等板回来。** 到板后手顺：焊 U6068 插针 ×2（未购则先买）→ 打印 `banana_pcb_locker` → 拆电池焊接出线（线径按 3-5A 选）→ 万用表直流档核极性 → 断电机械试装（插针与电池触点配合、locker 保持力）→ 只带主控支路验证 5V。

### 由到货衍生的待办

- [ ] 万用表实测降压模块（[操作单](./docs/buck-module-test.md)）：**2026-10-10 空载扫描已完成**——选压桥 6V 档、实测稳压下限 ≈6.3V（压差 0.3V 跌落跟随，远好于丝印 7.2V）、2S 最差点 6.6V 时输出仍 6.00V，**2S 初判可用**；接口分工闭环（XT60 入 / PWR OUT 直通 / 3P VCC 稳压；"DC 母座"系照片误判，实物无此件）。剩余：改焊 5V 档 + 空载复验 5.00V（IMU LDO 上限 5.5V 的前置）→ 台架带载复测
- [x] 确认 IMU 板是哪一版设计（2026-10-09 用户确认：ScrapMeta microduck-diy v0.3）
- [ ] 按手顺完成 IMU 板刷机：购 SWD 调试器（推荐 DAPLink）→ J2 接线（⚠️ 实物 J2 未焊插座只有焊盘，2026-10-10 看实物标注图确认：焊 BM07B-SRSS-TB 座 + SH1.0 7P 线，或杜邦线直接焊盘）→ 双击 `flash/1-烧录-DAPLink.bat` → 断电重启 → `flash/3-验收-imu200.bat` 全 PASS（详见 [flash/README.md](./flash/README.md)）
- [ ] 清点舵机（型号、数量、ID/零位状态）与打印件（版本、材料、缺件）
- [ ] 微雪转接板上机验证（对比飞线方案）
- [ ] 向板卡来源索取 HAT **V1.2** 原理图或改动说明（存档图为 V1.0；2026-10-10 照片发现实物 V1.2 多 F303 类 MCU + 超级电容，图物差异大，见 [docs/photos/](./docs/photos/README.md) HAT 小节）
- [ ] 飞特舵机原线（5264 端子）与 HAT 的 JST EH 3P 舵机座试插；不配则换 5264-3P 座或转接线
- [ ] HAT V1.2 与手头主控/外壳的机械与电气适配核对（电气功能确认按 [docs/hat-v1.2-test.md](./docs/hat-v1.2-test.md) 操作单执行：断电通断核对 + 限流上电分步验证）
- [ ] banana_pcb 到板装配与取电验证（焊 U6068 ×2、locker 打印、核极性、断电试装、主控支路验证）

## 2026-10-09 参考库清理（提取 → 还原）

- `microduck-replica/调试记录.md`：此前会话把 10-09 到货记录（7 行）写进了上游作者的表格里。用户相关内容已转录到本文件上表；原文件还原为上游版（「手头有的」等小节本来就是上游作者 fanhao375 的库存记录，不是本项目的）。
- `microduck-build-tutorial/`：A 训练重建的库内修改（4 个改文件 + 51 个添加文件，清单见 [local-changes/README](./local-changes/README.md)）全部提取，目录还原为上游原样。A 训练的说明与验收记录不受影响：[docs/a-training.md](./docs/a-training.md)、[docs/a-training-validation.json](./docs/a-training-validation.json)。

## 供电架构定稿（2026-10-10）

基于电源板空载实测 + IMU 网表 + HAT 查证记录，整机供电拓扑定稿并建档：docs/power-architecture-v1.md。当天评审证伪其中两处前提（IMU LDO 上限实为 13.2V 非 5.5V；HAT 的 F1 在数据线而非舵机电源路），已修订为现行版 [docs/power-architecture-v2.md](./docs/power-architecture-v2.md)：IMU 直挂总线（混血线与改焊 5V 任务取消）、电源板降为可选转接件、F1 未定项关闭、新增全链无保险与 EH 座分流两个风险项。

## 主文档路线审计（2026-10-10）

逐份检查主要文档中「确定路线（2026-10-09 主参考 C 飞特）之前」的遗留信息，修复如下：

- **根 BOM.md 重写为 C 线现行清单**（核心件/供电充电/线材/结构件/安全边界，按供电架构 v2 口径：IMU 直挂总线、电源板可选、新增 5A 保险采购项）；原 A 线清单（2026-09-28，XL330 + OpenRB + Pi Zero）原样存档 [docs/bom-route-a-20260928.md](./docs/bom-route-a-20260928.md)，仅回退 A 线时使用——其供电安全研究（XL330 6.0V 上限、OpenRB 板级电流限制）仍有效。
- **README.md**：路线状态段更新（主线 = C，指向架构 v2）；「机器人概览」「复刻计划」两节加 A 线基线横幅（原文保留不删——A 训练资产仍有效）。
- **.goal/PROJECT_KNOWLEDGE.md**：IMU 版本行更正（"v1.0 待核"→已确认 v0.3）；「已安装环境与入口」节加旧机横幅（现机无 WSL，训练环境不在本机，/mnt/e/ 路径失效）。
- **power-architecture-v2.md** 两处残留 "实物 V1.1" 更正为 V1.2（与 PROGRESS/照片一致）。
- 检查过、无需改：docs/a-training.md、docs/b-training.md（明确的 A/B 线训练存档，属历史资产）；flash/、docs/photos/、PROGRESS 本体均为 C 线现行档。
- 审计移交用户的待确认项：① NP-F550 充电器是否已有（BOM 已列）② HAT V1.2 图纸索取（到货待办已列）。

## 方案方向（2026-10-09）

- **主参考 = microduck-community-kit（飞特路线）**：HD-1910-C001 + 官方 robotd 的飞特补丁（`firmware/v1/patches/`）+ imu_to_dxl 总线从站（ID 200，双协议）。与手头硬件（飞特舵机、IMU2DXL 板、微雪半双工转接板）直接对口。
- replica 作为机械/装配/电控采购资料来源；build-tutorial 保留 A 训练基线存档（已提取到 local-changes）与教程对照。
- community-kit 已知缺口，用前留意：
  1. `software/microduck_feetech/` 完整源码**未推送**（README 提及但 main 分支没有；补丁文件在，基线官方 `f0d934e`，但完整树比补丁新三处关键修复——删 `tcdrain`、`BURST_IDLE` 2→4ms、同步上游 10 提交）；
  2. 主控↔舵机总线的物理适配层未开源（三块板只覆盖取电/配电/IMU）——**已由手头 HAT 补上**：板上 74LVC 半双工驱动 + UART2（Radxa `ttyS2`）正是 robotd 飞特补丁期望的总线入口，见 [HAT 查证记录](./docs/references/microduck-hat-20261006/research.md)；
  3. 真机整定值只能参考不能照抄：增益默认 32（200 会自激振荡，5A/74°C）、关节方向实测 −1（与 XL330 相反）、电池满/空电压阈值需复测。

## 工程迁移

2026-10-09 工程从 `E:\Projects\duck-robot` 迁到 `C:\Projects\duck-robot`（全部文件时间戳为迁移当日，无法再据时间戳判断改动，版本核对一律以上游哈希为准）。历史文档/脚本里的 `/mnt/e/`、`E:/` 路径已失效；本次已修根 README 的 3 处链接与 `scripts/a-training.sh` 的 2 处路径，`local-changes/` 里的提取件（export_onnx.py 等）仍含旧路径，复用前需改。

**本机新装工具链（2026-10-09）**：Python 3.13（`%LOCALAPPDATA%\Programs\Python\Python313`，含 pyserial）、OpenOCD 0.12.0（工程内 `flash/tools/`）、嘉立创EDA专业版 3.2.149（`%LOCALAPPDATA%\Programs\lceda-pro`，可开 `.eprj2`）、Git for Windows 2.55（winget 安装于 `C:\Program Files\Git`；`~/.gitconfig` 里失效的本地代理已移除，可直连，user.name/email 已配好）。无 WSL——旧机器的训练环境不在这台机器上。

## 嘉立创开放平台 API 打通（2026-10-09）

- 应用 **microduck-replica**（AppID 631092845187391489）PCB 业务线 API 已开通；密钥与 RSA 脱敏密钥已配置到 `tools/jlc-order/jlc-order.toml`（gitignore）。
- 之前 doctor 401 的根因：示例配置里的 appid/密钥是**官方文档教学示例值**，示例路径 `/order/v1/createOrder` 也只是签名示例，真实接口路径完全不同。
- 真实路径从控制台→SDK下载的官方 Java SDK jar 提取，14 个已授权 PCB 接口全部对齐进 `api_spec.py` 并探活验证；14 份接口 PDF 文档已下载到 `tools/jlc-order/api-docs/`（gitignore）。
- **计价链路全通**：`python -m jlc_order pcb quote -p examples/banana_pcb.toml` 实测返回真实价格（banana_pcb 39.2×6.8mm 双层 5 片 ≈ **¥55.04**：喷镀 30.04 + 特价 20 + 税 5）。
- 关键报文事实：板长宽在 `stencilLength/stencilWidth` 且单位是 **cm**；层数=`stencilLayer`、数量=`stencilCounts`；计价无需文件。
- **下单未完**：`/pcb/order/create` 需 `pcbFileUrl`+`fileName`（平台无上传接口，文件需先有可访问 URL）+ RSA 加密的 `orderReceive` 收货信息；cli 的 order/quick 命令待实现，字段表见 `api-docs/创建订单接口.pdf`。
- 3D 打印有独立 API（`/3dp-open/order/uploadModelFile`/`submitOrder`，有上传接口），但需在控制台为应用加开 3DP 业务线。

## jlc-order 下单命令实现（2026-10-09 下午）

- 通读《创建订单接口》PDF 后实现完整下单：`pcb order` / `pcb quick`（打包校验→计价→确认→下单）已对齐真实报文，dry-run 全链路验证（含 JOP 签名）。
- 关键结论：官方示例收货信息**明文**提交（RSA 脱敏密钥用于解密响应，不加密请求）；`pcbFileUrl` 可为任意公网 URL（示例用网盘）；`advancePayment=false` 只建单不扣款（默认）。
- 下单信息存 `jlc-order.toml [order]` 段（gitignore）；查询/返单单号=`customerOrderId`（整数）+ `orderType`（examples 样板/batch 小批量）。
- 待用户侧两件事即可真实下单：① gerber zip 托管到公网 URL 填入 `[order].pcb_file_url`；② 填收货人/发票/快递信息。

## banana_pcb 首单 API 下单成功（2026-10-09 下午）

- **订单 customerOrderId 85073604**（生产单 86482706/Y2）：39.2×6.8mm 双层 1.6mm 5 片 FR-4 绿色无铅喷锡全部测试，顺丰电商标快寄付，**¥50.04 待支付**（状态 1=等待嘉立创审核，未自动扣款），去 jlc.com 订单页人工支付。
- 全自动链路首次跑通：KiCad gerber → 百度网盘（官方 MCP stdio 上传）→ 分享链接（SSE `file_sharelink_set`，30 天提取码 jlc8）→ `[order].pcb_file_url` → 计价 → `/pcb/order/create`。
- API 下单踩坑实录（均已写进代码注释/README）：
  1. `charFontColor`（丝印字符颜色）下单必填（计价可省）；
  2. 个人发票必须显式 `invoiceType="personal"`，否则默认 company 报「发票主体与类型不符」；
  3. **`expressType=JYM` API 下单被拒**（报笼统「提交订单错误」），换 `SF_DSBZ_JF` 即过——浪费 4 次尝试才定位；
  4. 同一 pcbFileUrl 短时间重复提交会报「存在重复文件」——解法是换文件名重新上传+新分享链接（`tools/baidu-pan-mcp/run_upload_share.py` + `share_link.py` 一分钟搞定）。
- 百度网盘 MCP 双服务器已配进 `~/.zcode/cli/config.json`（baidu-pan SSE + baidu-pan-upload stdio），个人 token 30 天有效（2026-11-08 前需重新授权）。

## 嘉立创开放平台上传能力调查（2026-10-09）

用户问「API 没有上传功能么」→ 逐一验证各业务 SDK（控制台 SDK下载 逐个提取路径常量）：
- **PCB（已开通 14 接口）**：无上传，下单只能 pcbFileUrl；审核失败重传也只在 jlc.com 网页（askGuest 通道）
- **SMT（已开通）**：54 个类全是 /smtOpenApi/ 元器件邮寄管理+查单，无上传
- **CNC（已开通）**：官方描述即"下载图纸、查单"，无上传
- **云ERP（未开通）**：/open/api/saas/erp/* 进销存单据，无关
- **3DP（审核中）**：唯一有上传的业务线（/3dp-open/order/uploadModelFile），3D 打印专用
- SDK 基础包有 UploadRequest 基类、SDK 文档演示过 UploadFileRequest(orderNo,file)，但无任何业务包实现；控制台自己的 /api/file/fileUpload 仅限控制台内用
- 结论：**PCB 下单文件上传不存在 API 通道**；pcbFileUrl 需"直接下载字节流"的直链（百度分享页→爬虫抓到网页→"压缩包损坏"）；后续自动下单需直链托管方案（GitHub release / 对象存储）
- 附：应用管理页的"已获得/申请中/可申请（86）"是静态标签非页签；业务线状态 SMT、CNC 已开通，3DP、元器件&MRO 审核中

## GitHub 直链实测（2026-10-09，结论：不可行）

- 仓库 duck-robot 已转公开，`raw.githubusercontent.com` 链接本机直连可下载且 md5 一致；
- 但 API 下单实测两种结果：`raw.githubusercontent.com` 域名 → 报「PCB文件资源路径无效」；`github.com/.../raw/...`（302 重定向式）→ 通过校验但 JLC 服务端**同步抓取超时**（客户端 30s/120s 两档均超时，未产生幽灵订单）——嘉立创履约侧网络到海外源基本不可达，「有海外业务」不等于国内工厂的爬虫有海外出口；
- 另确认：下单去重键=文件名+内容哈希（换 fileName 标签可绕「存在重复文件」）；
- 待选替代：Gitee raw 直链（需码云账号）/ 问客服 pcbFileUrl 支持形式 / jlc.com 网页上传（当单急救）。

## 全自动下单链路收官（2026-10-09 15:06）

- **Gitee 镜像方案成功**：duck-robot 已镜像到 gitee.com/yilv1982/duck-robot（双远程 origin=GitHub / gitee=Gitee，推送凭证已存 GCM）；gerber zip 的国内直链 = `https://gitee.com/yilv1982/duck-robot/raw/main/hardware/banana_pcb/production/banana_pcb.zip`（匿名下载 1 秒、md5 一致）。
- **订单 85078132 审核通过**（下单后 26 秒过审，"单片出货，数量:5片"）——JLC 爬虫从 Gitee 抓文件秒下（对比 GitHub 120s 超时）。¥50.04 待支付，19:30 前付款排当晚生产。
- 旧订单 85073604（百度网盘链接"压缩包损坏"那单）停留在审核询问状态，需在 jlc.com 网页取消。
- ** pcbFileUrl 最终结论**：用国内代码托管 raw 直链（Gitee）；网盘分享页（爬虫抓到网页）、海外源（GitHub 超时）都不可行。以后改版重下单流程：改 PCB → 导 gerber → commit+push 两边 → 更新 [order] 的 file_name（避开文件名+哈希去重）→ `pcb order --yes`。
