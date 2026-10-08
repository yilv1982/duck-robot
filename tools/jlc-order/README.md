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
python -m jlc_order file upload <gerber.zip>                 # 上传资料 → fileId
python -m jlc_order pcb quote -p examples/banana_pcb.toml    # 在线计价
python -m jlc_order pcb order -p examples/banana_pcb.toml \
        --file-id <id> [--yes|--dry-run]                     # 创建订单
python -m jlc_order pcb reorder --order-no <单号> [--yes]     # 返单
python -m jlc_order order get --order-no <单号>               # 订单信息
python -m jlc_order order progress --order-no <单号> [--watch]# 生产进度/轮询
python -m jlc_order pcb quick --project ../../hardware/banana_pcb \
        -p examples/banana_pcb.toml [--yes]                  # 一键全流程
python -m jlc_order ledger                                   # 最近调用台账
```

参数模板见 `examples/banana_pcb.toml`（banana_pcb 电池转接板，39.2×6.8mm 双层板）。

## 安全机制

- **下单/返单/quick 默认交互确认**，`--yes` 显式跳过；非交互环境没有 `--yes` 会直接拒绝。
- **`--dry-run` 零网络发送**（有专门测试保证），打印签名后的完整请求供检查。
- 下单类接口**失败不自动重试**（防重复下单）；查询类接口失败自动重试。
- 密钥只存 `jlc-order.toml`（已 gitignore）或环境变量；日志/台账/dry-run 输出一律脱敏。
- 每次调用追加写入 `orders.jsonl` 台账（接口、状态、业务码、J-Trace-ID），
  报障时把 J-Trace-ID 提供给官方客服（18665386054）。

## 接口对齐状态

`jlc_order/api_spec.py` 集中管理接口路径。签名协议（JOP / HmacSHA256）已用
[官方文档示例](https://open.jlc.com/develop-guide?doc=signature)的期望签名值做过
逐字节 golden 验证（`tests/test_auth.py`）。部分业务接口路径为占位，`doctor`
会列出未对齐项；对齐方式：登录 open.jlc.com 控制台 → 接口文档，按文档修正
`api_spec.py` 的 `path` 与字段映射（`PcbParams.to_payload`）。

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
