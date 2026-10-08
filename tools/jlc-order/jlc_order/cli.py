"""命令行入口：python -m jlc_order <组> <子命令>。

安全约定：所有下单类命令（pcb order / pcb reorder / pcb quick）
默认交互确认；--yes 跳过；--dry-run 只打印签名后的请求、绝不发网络包。
"""

from __future__ import annotations

import argparse
import email.utils
import sys
import time
from pathlib import Path

from . import __version__, api_spec
from .client import ApiError, ApiResponse, JlcClient
from .config import Config, ConfigError, load_config
from .console import confirm_order, print_json, print_price_table
from .gerber import default_output_zip, pack_directory, validate_zip
from .orders import Ledger, ledger_path
from .pcb_params import ParamsError, PcbParams

TOOL_ROOT = Path(__file__).resolve().parent.parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jlc_order",
        description="嘉立创开放平台（open.jlc.com）PCB 打样自动化下单工具",
    )
    parser.add_argument("--config", type=Path, default=None, help="配置文件路径")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="自检：配置/签名/IP 白名单/接口对齐状态")
    sub.add_parser("ledger", help="查看最近调用台账")

    p_file = sub.add_parser("file", help="资料文件")
    file_sub = p_file.add_subparsers(dest="action", required=True)
    p_up = file_sub.add_parser("upload", help="上传 Gerber zip，返回文件 ID")
    p_up.add_argument("zip_path", type=Path)

    p_pcb = sub.add_parser("pcb", help="PCB 打样")
    pcb_sub = p_pcb.add_subparsers(dest="action", required=True)
    p_quote = pcb_sub.add_parser("quote", help="PCB 在线计价")
    p_quote.add_argument("-p", "--params", type=Path, required=True, help="参数模板 toml")
    p_quote.add_argument("--file-id", default=None, help="已上传的资料文件 ID")
    p_order = pcb_sub.add_parser("order", help="创建 PCB 订单")
    _add_order_flags(p_order, params=True, file_id=True)
    p_reorder = pcb_sub.add_parser("reorder", help="按历史订单返单")
    p_reorder.add_argument("--order-no", required=True)
    _add_order_flags(p_reorder)
    p_quick = pcb_sub.add_parser("quick", help="一键：打包→校验→上传→计价→确认→下单")
    p_quick.add_argument("--project", type=Path, required=True, help="KiCad 工程目录")
    _add_order_flags(p_quick, params=True)

    p_order_q = sub.add_parser("order", help="订单查询")
    order_sub = p_order_q.add_subparsers(dest="action", required=True)
    p_get = order_sub.add_parser("get", help="查询订单信息")
    p_get.add_argument("--order-no", required=True)
    p_prog = order_sub.add_parser("progress", help="查询生产进度")
    p_prog.add_argument("--order-no", required=True)
    p_prog.add_argument("--watch", action="store_true", help="每 60 秒轮询直至完成")

    return parser


def _add_order_flags(
    parser: argparse.ArgumentParser,
    *,
    params: bool = False,
    file_id: bool = False,
) -> None:
    if params:
        parser.add_argument("-p", "--params", type=Path, required=True, help="参数模板 toml")
    if file_id:
        parser.add_argument("--file-id", required=True, help="资料文件 ID")
    parser.add_argument("--yes", action="store_true", help="跳过交互确认")
    parser.add_argument("--dry-run", action="store_true", help="只打印请求不发送")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _dispatch(args)
    except (ConfigError, ParamsError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2
    except ApiError as exc:
        print(f"接口错误: {exc}", file=sys.stderr)
        return 3
    except ConnectionError as exc:
        print(f"网络错误: {exc}", file=sys.stderr)
        return 4


def _make_client(args, *, dry_run: bool = False) -> tuple[Config, JlcClient]:
    config = load_config(args.config)
    ledger = Ledger(ledger_path(config))
    client = JlcClient(config, dry_run=dry_run, on_call=ledger.append)
    return config, client


def _dispatch(args) -> int:
    command = args.command
    if command == "doctor":
        return _doctor(args)
    if command == "ledger":
        config = load_config(args.config)
        for record in Ledger(ledger_path(config)).tail(20):
            print_json(record)
        return 0
    if command == "file":
        return _file_upload(args)
    if command == "pcb":
        return {
            "quote": _pcb_quote,
            "order": _pcb_order,
            "reorder": _pcb_reorder,
            "quick": _pcb_quick,
        }[args.action](args)
    if command == "order":
        return _order_progress(args) if args.action == "progress" else _order_get(args)
    raise AssertionError(f"未知命令 {command}")  # pragma: no cover


def _doctor(args) -> int:
    print("== jlc-order 自检 ==")
    config = load_config(args.config)
    print(f"网关: {config.endpoint}")
    print(f"密钥: appid={config.credentials.app_id[:4]}*** 已配置")

    pending = api_spec.pending_endpoints()
    if pending:
        print(f"\n注意: {len(pending)} 个接口路径尚未与控制台文档对齐（仅占位）:")
        for ep in pending:
            print(f"  - {ep.name}: {ep.path}（{ep.description}）")
        print("对齐入口: open.jlc.com → 控制台 → 接口文档（需登录）")

    print("\n发起真实探活请求（查询订单，空单号）...")
    client = JlcClient(config)
    try:
        resp = client.post_json(api_spec.ORDER_GET.path, {"orderNo": ""}, retries=0)
    except ConnectionError as exc:
        print(f"✗ 网络不通: {exc}")
        return 4
    _report_clock_skew(resp)
    if resp.status == 200:
        print("✓ 验签通过、IP 放行（有业务应答即代表开放平台接受了本次签名）")
        print(f"  应答: {resp.body_text[:200]}")
        return 0
    if resp.status == 401:
        print("✗ 验签不通过：检查 secret_key 与系统时间")
        return 3
    if resp.status == 403:
        print("✗ 请求被拒：大概率 IP 白名单未放行本机出口 IP")
        return 3
    print(f"? HTTP {resp.status}: {resp.body_text[:200]}")
    return 3


def _report_clock_skew(resp: ApiResponse) -> None:
    date_value = (resp.headers or {}).get("date") or (resp.headers or {}).get("Date")
    if not date_value:
        return
    try:
        server_time = email.utils.parsedate_to_datetime(date_value).timestamp()
    except (TypeError, ValueError):
        return
    skew = abs(time.time() - server_time)
    if skew > 120:
        print(f"⚠ 本机时间与服务器相差 {skew:.0f} 秒，可能导致验签失败，请校准时钟")


def _file_upload(args) -> int:
    report = validate_zip(args.zip_path)
    print(report.summary())
    if not report.ok:
        return 2
    _, client = _make_client(args)
    resp = client.upload_file(
        api_spec.FILE_UPLOAD.path, {"fileType": "gerber"}, args.zip_path
    )
    print_json(resp.data())
    return 0


def _pcb_quote(args) -> int:
    params = PcbParams.load(args.params)
    if problems := params.validate():
        print("参数问题:", *problems, sep="\n  - ")
        return 2
    print(f"计价参数: {params.describe()}")
    _, client = _make_client(args)
    payload = params.to_payload()
    if args.file_id:
        payload["fileId"] = args.file_id
    resp = client.post_json(api_spec.PCB_QUOTE.path, payload)
    print_price_table(resp.data())
    print_json(resp.data())
    return 0


def _pcb_order(args) -> int:
    params = PcbParams.load(args.params)
    if problems := params.validate():
        print("参数问题:", *problems, sep="\n  - ")
        return 2
    _, client = _make_client(args, dry_run=args.dry_run)
    payload = params.to_payload()
    payload["fileId"] = args.file_id
    prompt = (
        f"即将创建真实 PCB 订单并产生费用：{params.describe()}，资料 {args.file_id}。确认下单?"
    )
    if args.dry_run:
        print(prompt, "（dry-run 模式，不会发送）")
    elif not confirm_order(prompt, yes=args.yes):
        print("已取消。")
        return 1
    resp = client.post_json(api_spec.PCB_CREATE_ORDER.path, payload, retries=0)
    print_json(resp.data() if resp.json else {"raw": resp.body_text})
    return 0


def _pcb_reorder(args) -> int:
    _, client = _make_client(args, dry_run=args.dry_run)
    prompt = f"将按历史订单 {args.order_no} 创建返单（产生真实费用）。确认?"
    if args.dry_run:
        print(prompt, "（dry-run 模式，不会发送）")
    elif not confirm_order(prompt, yes=args.yes):
        print("已取消。")
        return 1
    resp = client.post_json(
        api_spec.PCB_REORDER.path, {"orderNo": args.order_no}, retries=0
    )
    print_json(resp.data() if resp.json else {"raw": resp.body_text})
    return 0


def _order_get(args) -> int:
    _, client = _make_client(args)
    resp = client.post_json(api_spec.ORDER_GET.path, {"orderNo": args.order_no})
    print_json(resp.data())
    return 0


def _order_progress(args) -> int:
    _, client = _make_client(args)
    while True:
        resp = client.post_json(
            api_spec.ORDER_PROGRESS.path, {"orderNo": args.order_no}
        )
        data = resp.data()
        print_json(data)
        if not args.watch:
            return 0
        status_text = str(data.get("status") or data.get("progress") or "")
        if any(word in status_text for word in ("完成", "发货", "已出货")):
            print("订单已完结，停止轮询。")
            return 0
        print("60 秒后再次查询（Ctrl+C 退出）...")
        try:
            time.sleep(60)
        except KeyboardInterrupt:
            return 0


def _pcb_quick(args) -> int:
    project = args.project.resolve()
    zip_path = default_output_zip(project)
    if not zip_path.is_file():
        gerber_dirs = sorted(
            d for d in project.iterdir() if d.is_dir() and "gerber" in d.name.lower()
        )
        if not gerber_dirs:
            print(f"未找到 {zip_path}，工程目录下也没有 gerber 目录，无法打包")
            return 2
        zip_path = pack_directory(gerber_dirs[0], zip_path)
        print(f"已打包 {gerber_dirs[0]} → {zip_path}")

    report = validate_zip(zip_path)
    print(report.summary())
    if not report.ok:
        return 2

    params = PcbParams.load(args.params)
    if problems := params.validate():
        print("参数问题:", *problems, sep="\n  - ")
        return 2

    config = load_config(args.config)
    ledger = Ledger(ledger_path(config))
    client = JlcClient(config, dry_run=args.dry_run, on_call=ledger.append)

    print("\n[1/3] 上传 Gerber...")
    if args.dry_run:
        client.upload_file(api_spec.FILE_UPLOAD.path, {"fileType": "gerber"}, zip_path)
        print("（dry-run：未真实上传）")
        return 0
    upload_resp = client.upload_file(
        api_spec.FILE_UPLOAD.path, {"fileType": "gerber"}, zip_path
    )
    file_id = upload_resp.data().get("fileId")
    if not file_id:
        print(f"上传成功但未返回 fileId: {upload_resp.body_text[:300]}")
        return 3
    print(f"fileId: {file_id}")

    print("[2/3] 计价...")
    payload = params.to_payload()
    payload["fileId"] = file_id
    quote_resp = client.post_json(api_spec.PCB_QUOTE.path, payload)
    print_price_table(quote_resp.data())

    print("[3/3] 下单...")
    prompt = f"以上价格确认下单？{params.describe()}，fileId={file_id}"
    if not confirm_order(prompt, yes=args.yes):
        print("已取消（未下单）。")
        return 1
    order_resp = client.post_json(api_spec.PCB_CREATE_ORDER.path, payload, retries=0)
    print_json(order_resp.data())
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
