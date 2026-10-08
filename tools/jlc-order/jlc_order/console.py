"""终端交互：价格表打印、下单前确认。"""

from __future__ import annotations

import json
import sys


def print_json(payload: dict | list) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def print_price_table(quote: dict) -> None:
    """计价结果友好打印；字段名对齐前尽力兼容常见命名。"""
    if not quote:
        print("（计价返回空数据）")
        return
    total = quote.get("totalPrice") or quote.get("total") or quote.get("amount")
    if total is not None:
        print(f"  合计: {total}")
    for key, value in quote.items():
        if isinstance(value, (str, int, float)) and "price" not in key.lower():
            print(f"  {key}: {value}")


def confirm_order(prompt: str, *, yes: bool = False) -> bool:
    """下单类操作的最后闸门：--yes 显式跳过，非交互环境拒绝。"""
    if yes:
        return True
    if not sys.stdin.isatty():
        print("非交互环境运行，未收到 --yes，已拒绝执行。")
        return False
    answer = input(f"{prompt} [输入 yes 确认 / 其他取消]: ").strip().lower()
    return answer == "yes"
