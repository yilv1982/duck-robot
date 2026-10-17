#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IMU(ID 200) 实时姿态可视化：SSE 推流 + 浏览器 CSS 3D 立方体跟随。

数据契约照 flash/tools/imu200/imu200.py（= 主控 imu.rs/bus.rs 的可执行版）：
READ @56 len15 = gyro x/y/z (i16 LE, 17.5 mdps/LSB) + quat x/y/z (half LE)
               + 采样计数 + 状态 + 保留；w 由 sqrt(1-|v|²) 恢复。

用法（Radxa，与 hls_servo_debugger 不同时占用串口）：
  python3 imu-viewer.py                      # /dev/ttyS2 @1Mbps，网页 :8766
  python3 imu-viewer.py --sim                # 无硬件模拟自测（本地验证页面用）
  python3 imu-viewer.py --port COM4          # 电脑侧经微雪板看同一块 IMU
"""
import argparse
import json
import math
import struct
import threading
import time

from flask import Flask, Response

IMU_ID = 200
BLOCK_ADDR = 56
BLOCK_LEN = 15
GYRO_LSB_DPS = 0.0175

app = Flask(__name__)
_lock = threading.Lock()
_state = {"ok": False, "err": "未开始", "quat": [1, 0, 0, 0], "gyro": [0, 0, 0],
          "counter": 0, "status": 0, "hz": 0.0}


def build_packet(sid: int, inst: int, params: bytes = b"") -> bytes:
    length = len(params) + 2
    body = bytes([sid, length, inst]) + params
    chk = (~sum(body)) & 0xFF
    return b"\xFF\xFF" + body + bytes([chk])


def read_frame(port, timeout=0.05) -> bytes:
    deadline = time.monotonic() + timeout
    buf = b""
    while time.monotonic() < deadline:
        n = port.in_waiting
        if n:
            buf += port.read(n)
            if len(buf) >= 5 and buf[:2] == b"\xFF\xFF":
                total = 4 + buf[3]
                if len(buf) >= total:
                    return buf[:total]
        else:
            time.sleep(0.001)
    return buf


def parse_block(blk: bytes):
    gx, gy, gz = struct.unpack_from("<hhh", blk, 0)
    qx, qy, qz = (struct.unpack("<e", struct.pack("<H", h))[0]
                  for h in struct.unpack_from("<HHH", blk, 6))
    w2 = 1.0 - (qx * qx + qy * qy + qz * qz)
    w = math.sqrt(w2) if w2 > 0 else 0.0
    n = math.sqrt(w * w + qx * qx + qy * qy + qz * qz)
    if n > 1e-6:
        w, qx, qy, qz = w / n, qx / n, qy / n, qz / n
    return ([w, qx, qy, qz], [gx * GYRO_LSB_DPS, gy * GYRO_LSB_DPS, gz * GYRO_LSB_DPS],
            blk[12], blk[13])


def reader_real(port_name: str, baud: int):
    import serial
    global _state
    try:
        port = serial.Serial(port_name, baud, timeout=0.05)
    except Exception as e:
        with _lock:
            _state.update(ok=False, err=f"串口打不开：{e}（若被 hls_servo_debugger 占用请先断开）")
        return
    pkt = build_packet(IMU_ID, 0x02, bytes([BLOCK_ADDR, BLOCK_LEN]))  # READ
    t0, cnt = time.monotonic(), 0
    while True:
        port.reset_input_buffer()
        port.write(pkt)
        port.flush()
        frame = read_frame(port)
        if frame and len(frame) >= 7 and frame[2] == IMU_ID:
            data = frame[5:-1]
            if len(data) >= BLOCK_LEN:
                quat, gyro, ctr, st = parse_block(data[:BLOCK_LEN])
                cnt += 1
                now = time.monotonic()
                hz = cnt / (now - t0) if now - t0 > 0.5 else 0
                with _lock:
                    _state.update(ok=True, err="", quat=quat, gyro=gyro,
                                  counter=ctr, status=st, hz=round(hz, 1))
                if now - t0 > 5:
                    t0, cnt = now, 0
        else:
            with _lock:
                _state.update(ok=False, err="IMU 无应答", hz=0)
        time.sleep(0.02)


def reader_sim():
    global _state
    t = 0.0
    while True:
        a, b = math.radians(30) * math.sin(t), math.radians(40) * t
        ca, sa, cb, sb = math.cos(a / 2), math.sin(a / 2), math.cos(b / 2), math.sin(b / 2)
        with _lock:
            _state.update(ok=True, err="（模拟数据）",
                          quat=[ca * cb, sa * cb, ca * sb, 0], gyro=[0, 0, 0],
                          counter=int(t * 100) % 256, status=0, hz=50.0)
        t += 0.02
        time.sleep(0.02)


@app.route("/stream")
def stream():
    def gen():
        while True:
            with _lock:
                yield f"data: {json.dumps(_state)}\n\n"
            time.sleep(0.03)
    return Response(gen(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache"})


@app.route("/")
def index():
    return HTML


HTML = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>IMU 姿态实时查看</title><style>
body{font-family:system-ui,sans-serif;background:#111;color:#ddd;margin:0;padding:16px;display:flex;gap:24px;flex-wrap:wrap}
.stage{width:340px;height:340px;perspective:700px;display:flex;align-items:center;justify-content:center}
.cube{width:160px;height:160px;position:relative;transform-style:preserve-3d;transition:none}
.face{position:absolute;inset:0;border:2px solid #b8860b;background:rgba(255,215,0,.18);
 display:flex;align-items:center;justify-content:center;font-size:20px;color:#ffd700;font-weight:700}
.front {transform:translateZ(80px)} .back {transform:rotateY(180deg) translateZ(80px)}
.right {transform:rotateY(90deg) translateZ(80px)} .left {transform:rotateY(-90deg) translateZ(80px)}
.top {transform:rotateX(90deg) translateZ(80px)} .bottom{transform:rotateX(-90deg) translateZ(80px)}
.panel{font-size:13px;line-height:1.7;min-width:300px}
.panel h2{margin:0 0 6px;font-size:16px}
.mono{font-family:ui-monospace,Consolas,monospace;color:#9fe8ff}
.bad{color:#ff7b72}.good{color:#7ee787}
</style></head><body>
<div class="stage"><div class="cube" id="cube">
<div class="face front">前</div><div class="face back">后</div>
<div class="face right">右</div><div class="face left">左</div>
<div class="face top">上</div><div class="face bottom">下</div>
</div></div>
<div class="panel"><h2>IMU ID 200 姿态（传感器坐标，未含安装旋转）</h2>
<div id="conn" class="bad">连接中…</div>
<div>四元数 wxyz：<span id="q" class="mono">-</span></div>
<div>陀螺 dps：<span id="g" class="mono">-</span></div>
<div>采样计数：<span id="c" class="mono">-</span>　状态：<span id="s" class="mono">-</span>　读取率：<span id="hz" class="mono">-</span> Hz</div>
<p style="color:#888;max-width:420px">晃动 IMU 板，立方体应实时跟随。若显示"无应答"：检查 IMU 是否在链末、总线上是否只有本工具在用串口。</p>
</div>
<script>
const cube=document.getElementById('cube');
const es=new EventSource('/stream');
es.onmessage=e=>{
 const d=JSON.parse(e.data);
 const conn=document.getElementById('conn');
 conn.textContent=d.ok?('数据流正常 '+d.err):('异常：'+d.err);
 conn.className=d.ok?'good':'bad';
 if(!d.ok)return;
 const [w,x,y,z]=d.quat;
 document.getElementById('q').textContent=[w,x,y,z].map(v=>v.toFixed(3)).join(' ');
 document.getElementById('g').textContent=d.gyro.map(v=>v.toFixed(1)).join(' ');
 document.getElementById('c').textContent=d.counter;
 document.getElementById('s').textContent='0x'+d.status.toString(16);
 document.getElementById('hz').textContent=d.hz;
 // 四元数 -> 旋转矩阵（行主序）
 const m=[1-2*(y*y+z*z),2*(x*y-w*z),2*(x*z+w*y),
          2*(x*y+w*z),1-2*(x*x+z*z),2*(y*z-w*x),
          2*(x*z-w*y),2*(y*z+w*x),1-2*(x*x+y*y)];
 // CSS matrix3d 列主序；Y 轴翻转以符合屏幕直觉
 cube.style.transform='matrix3d('+[m[0],-m[3],m[6],0, m[1],-m[4],m[7],0, m[2],-m[5],m[8],0, 0,0,0,1].join(',')+')';
};
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser(description="IMU 姿态实时可视化（SSE + CSS 3D）")
    ap.add_argument("--port", default="/dev/ttyS2")
    ap.add_argument("--baud", type=int, default=1_000_000)
    ap.add_argument("--http", type=int, default=8766)
    ap.add_argument("--sim", action="store_true", help="模拟数据自测")
    args = ap.parse_args()
    threading.Thread(target=reader_sim if args.sim else
                     lambda: reader_real(args.port, args.baud), daemon=True).start()
    app.run(host="0.0.0.0", port=args.http, threaded=True)


if __name__ == "__main__":
    main()
