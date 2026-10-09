# jlc-order：嘉立创官方 API 自动下单工具（PCB 打样）

基于 [嘉立创开放平台](https://open.jlc.com) 官方 API 的命令行工具，把
「Gerber 打包 → 上传 → 计价 → 确认 → 下单 → 跟进度」整条 PCB 打样流程脚本化。
运行时**零第三方依赖**（纯 Python 标准库），Python ≥ 3.11。

## 快速开始

```bash
cd tools/jlc-order
cp config.example.toml jlc-order.toml   # 填入你的 appid / AccessKey / SecretKey
uv sync                                 # 仅测试/开发需要；日常直接用系统 python 即可
uv run python -m jlc_order doctor       # 自检：验签、IP 白名单、时间同步
```

密钥来源：open.jlc.com → 控制台 → 创建应用（一键生成）。
也可以用环境变量 `JLC_APP_ID` / `JLC_ACCESS_KEY` / `JLC_SECRET_KEY` 提供密钥。

## 命令一览

```bash
python -m jlc_order doctor                                   # 自检
python -m jlc_order pcb quote -p examples/banana_pcb.toml    # 在线计价（无需文件）
python -m jlc_order pcb order -p examples/banana_pcb.toml \
        [--file-url <url>] [--yes|--dry-run]                 # 创建订单
python -m jlc_order pcb reorder --order-no <customerOrderId> [--yes]      # 返单
python -m jlc_order order get --order-no <customerOrderId>   # 订单信息
python -m jlc_order order progress --order-no <customerOrderId> [--watch] # 进度/轮询
python -m jlc_order pcb quick --project ../../hardware/banana_pcb \
        -p examples/banana_pcb.toml [--yes]                  # 打包校验→计价→确认→下单
python -m jlc_order ledger                                   # 最近调用台账
```

参数模板见 `examples/banana_pcb.toml`（banana_pcb 电池转接板，39.2×6.8mm 双层板）。
下单信息（资料 URL/收货人/发票/快递）配置在 `jlc-order.toml` 的 `[order]` 段，
注释模板见 `config.example.toml`；`order get/progress/reorder` 的单号是整数
`customerOrderId`（`--order-type examples|batch`，样板默认 examples）。

## 安全机制

- **下单/返单/quick 默认交互确认**，`--yes` 显式跳过；非交互环境没有 `--yes` 会直接拒绝。
- **`--dry-run` 零网络发送**（有专门测试保证），打印签名后的完整请求供检查。
- 下单类接口**失败不自动重试**（防重复下单）；查询类接口失败自动重试。
- 密钥只存 `jlc-order.toml`（已 gitignore）或环境变量；日志/台账/dry-run 输出一律脱敏。
- 每次调用追加写入 `orders.jsonl` 台账（接口、状态、业务码、J-Trace-ID），
  报障时把 J-Trace-ID 提供给官方客服（18665386054）。

## 接口对齐状态

**2026-10-09 已对齐并线上验证**：签名（JOP/HmacSHA256）、网关、14 个已授权 PCB 接口。
路径出自官方 PCB 业务 SDK jar（控制台→SDK下载）与各接口 PDF 文档
（已下载到 `api-docs/`，gitignore，重下入口：控制台→应用管理→管理→查看文档）。

- 计价全链路已通：`pcb quote` 用工艺参数即可算价（无需文件），实测返回真实价格。
- **下单全链路已实测跑通**（2026-10-09 首单 customerOrderId 85073604）：文件以
  `pcbFileUrl`+`fileName` 传入（开放平台无上传接口；用百度网盘分享链接，上传/分享
  脚本见 `tools/baidu-pan-mcp/`）；联系人/收货信息按官方示例明文提交；`advancePayment=false`
  默认只建单不扣款。API 下单三个坑（都已内置处理）：`charFontColor` 下单必填、
  个人发票必须 `invoiceType="personal"`、**快递 JYM 会被拒需用 SF_DSBZ_JF 等**。
  使用前在 `jlc-order.toml` 补 `[order]` 段（见 `config.example.toml`）。
- 应用（microduck-replica）当前只开通了 PCB 业务线；3D 打印另有独立接口
  （`/3dp-open/order/uploadModelFile`、`submitOrder` 等，3DP 业务 SDK 可从控制台下载），
  需在控制台为应用加开 3DP 业务线后可用。

## 常见问题

- **401 验签不通过**：检查 secret_key 是否复制完整、系统时间是否准确（秒级校验）。
- **403 请求被拒**：多为 IP 白名单未放行本机出口 IP，去控制台→应用管理→IP 白名单添加，或关闭白名单。
- **新客免费打样**：API 下单是否叠加平台优惠由平台决定，本工具不承诺价格。
- **Windows / WSL**：纯标准库实现，两边都能跑；`uv run` 会自动用本项目 `.venv`。

## 测试

```bash
uv run pytest        # 33 个用例：官方签名 golden、dry-run 零发包、确认闸门等
uv run ruff check .
```
