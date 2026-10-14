#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飞特 Feetech 舵机总线 ping/扫描工具（microduck C 线 B5 步）

在 Radxa Zero 3 上运行，走 /dev/ttyS2（UART2-M0，排针 pin8=TX / pin10=RX）。

用法：
  python3 feetech-ping.py loop                 # 回环自测：需杜邦线短接 pin8↔pin10，无电源
  python3 feetech-ping.py scan [--id N]        # 逐个 ping 舵机（默认扫 ID 0-6，--id 指定单个）
  python3 feetech-ping.py scan --range A B     # 扫 ID A..B（0-253）

注意：
- HAT 74LVC 半双工驱动自动换向；飞线/回环测试时请直接短接 pin8 与 pin10。
- 回环(loop)模式仅在未接 HAT、pin8/pin10 被跳线短接时有效，用于验证 ttyS2 通路。
"""

import argparse
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("缺少 pyserial：sudo apt-get install python3-serial")

DEFAULT_PORT = "/dev/ttyS2"
DEFAULT_BAUD = 1_000_000  # 飞特出厂默认 1 Mbps


def build_packet(servo_id: int, inst: int, params: bytes = b"") -> bytes:
    length = len(params) + 2  # INST + CHK
    body = bytes([servo_id, length, inst]) + params
    chk = (~sum(body)) & 0xFF
    return b"\xFF\xFF" + body + bytes([chk])


def read_status(port: serial.Serial, timeout: float = 0.05) -> bytes:
    """读一帧状态包：FF FF ID LEN ERR ... CHK"""
    deadline = time.monotonic() + timeout
    buf = b""
    while time.monotonic() < deadline:
        n = port.in_waiting
        if n:
            buf += port.read(n)
            # 至少收齐 6 字节帧头+基本字段后按 LEN 判定完整帧
            if len(buf) >= 5 and buf[:2] == b"\xFF\xFF":
                total = 4 + buf[3]  # FF FF + ID + LEN + LEN 字节内容
                if len(buf) >= total:
                    return buf[:total]
        else:
            time.sleep(0.001)
    return buf


def checksum_ok(frame: bytes) -> bool:
    if len(frame) < 6 or frame[:2] != b"\xFF\xFF":
        return False
    return (sum(frame[2:-1]) & 0xFF) == 0xFF


def cmd_loop(port_name: str, baud: int) -> int:
    """回环自测：发固定字节流，原样收回即通过（pin8↔pin10 短接）。"""
    payload = b"RADXA-UART2-LOOPBACK-TEST-0123456789"
    with serial.Serial(port_name, baud, timeout=0.2) as port:
        port.reset_input_buffer()
        port.write(payload)
        port.flush()
        got = b""
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline and len(got) < len(payload):
            n = port.in_waiting
            if n:
                got += port.read(n)
            else:
                time.sleep(0.002)
    print(f"发送 {len(payload)} 字节，收到 {len(got)} 字节")
    if got == payload:
        print("回环测试 PASS：ttyS2 收发通路正常")
        return 0
    print(f"回环测试 FAIL：期望 {payload!r}，实际 {got!r}")
    return 1


def cmd_scan(port_name: str, baud: int, ids) -> int:
    found = []
    with serial.Serial(port_name, baud, timeout=0.05) as port:
        for servo_id in ids:
            port.reset_input_buffer()
            port.write(build_packet(servo_id, 0x01))  # PING
            port.flush()
            frame = read_status(port)
            if frame and checksum_ok(frame):
                err = frame[4]
                print(f"  ID {servo_id}: 在线（错误码 0x{err:02X}）")
                found.append(servo_id)
            else:
                print(f"  ID {servo_id}: 无响应")
    print(f"\n共发现 {len(found)} 个舵机：{found if found else '无'}")
    return 0 if found else 2


def main() -> int:
    ap = argparse.ArgumentParser(description="飞特舵机 ping/扫描（B5 步）")
    ap.add_argument("mode", choices=["loop", "scan"])
    ap.add_argument("--port", default=DEFAULT_PORT)
    ap.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    ap.add_argument("--id", type=int, default=None, help="只 ping 指定 ID")
    ap.add_argument("--range", nargs=2, type=int, metavar=("A", "B"),
                    help="扫 ID A..B（默认 0..6）")
    args = ap.parse_args()

    if args.mode == "loop":
        return cmd_loop(args.port, args.baud)

    if args.id is not None:
        ids = [args.id]
    elif args.range:
        lo, hi = args.range
        ids = range(max(0, lo), min(253, hi) + 1)
    else:
        ids = range(0, 7)
    return cmd_scan(args.port, args.baud, ids)


if __name__ == "__main__":
    sys.exit(main())
