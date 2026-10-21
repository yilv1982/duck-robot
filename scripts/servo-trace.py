#!/usr/bin/env python3
"""手掰关节行程记录器（2026-10-20）。

在板上运行，轮询 hls_servo_debugger(:8765) 的 /api/read 读 15 颗舵机
56 号当前位置，逐轮写入 CSV；出现停止文件后输出每颗的 min/max/行程汇总。

用法（板上）：
    nohup python3 servo-trace.py --out ~/servo-trace.csv &
    # 手掰关节做行程检查；结束后：
    touch /tmp/stop-servo-trace
    cat ~/servo-trace.csv.summary

汇总把读数折回单圈 0..4095 后取极值（手掰过快时圈计数可能出窗，
折回后才是物理行程）。角度为相对中位 2048 的度数，未含关节方向系数；
回填训练参数表时按关节表方向正式换算。
"""
import argparse
import csv
import json
import os
import time
import urllib.request

IDS = [10, 11, 12, 13, 14, 20, 21, 22, 23, 24, 30, 31, 32, 33, 34]


def read_pos(url, sid):
    """读一颗的 56 号当前位置，BIT15 符号幅值解码；失败返回 None。"""
    req = urllib.request.Request(
        url + "/api/read",
        data=json.dumps({"id": sid, "addr": 56, "length": 2}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=2) as r:
        d = json.loads(r.read())["data"]
        raw = d["data"][0] | (d["data"][1] << 8)
    return -(raw & 0x7FFF) if raw & 0x8000 else raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8765")
    ap.add_argument("--out", default="/home/radxa/servo-trace.csv")
    ap.add_argument("--stop-file", default="/tmp/stop-servo-trace")
    a = ap.parse_args()

    t0 = time.time()
    samples = {sid: [] for sid in IDS}
    rounds = 0
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_s"] + ["id%d" % i for i in IDS])
        while not os.path.exists(a.stop_file):
            row = ["%.2f" % (time.time() - t0)]
            for sid in IDS:
                try:
                    p = read_pos(a.url, sid)
                except Exception:
                    p = None
                row.append("" if p is None else p)
                if p is not None:
                    samples[sid].append(p)
            w.writerow(row)
            rounds += 1

    dur = time.time() - t0
    lines = ["轮数 %d，时长 %.1f s，平均 %.2f 轮/s" % (
        rounds, dur, rounds / dur if dur else 0)]
    lines.append("ID   min   max  span   下限   上限   下限°   上限°")
    for sid in IDS:
        if not samples[sid]:
            lines.append("%2d  无数据" % sid)
            continue
        vals = [((p % 4096) + 4096) % 4096 for p in samples[sid]]
        lo, hi = min(vals), max(vals)
        lines.append("%2d  %4d  %4d  %4d  %+5d  %+5d  %+6.1f  %+6.1f" % (
            sid, lo, hi, hi - lo, lo - 2048, hi - 2048,
            (lo - 2048) * 360 / 4096, (hi - 2048) * 360 / 4096))
    report = "\n".join(lines)
    print(report)
    with open(a.out + ".summary", "w") as f:
        f.write(report + "\n")


if __name__ == "__main__":
    main()
