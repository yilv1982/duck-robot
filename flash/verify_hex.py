"""Verify the replica imu_to_dxl 0.2.0 prebuilt HEX against the author's published digest.

Decodes the Intel HEX records, rebuilds the flash image from 0x08000000, and compares
SHA-256 with the value documented in references/microduck-replica/hardware/imu_to_dxl/firmware/README.md.
"""
import hashlib
import sys

EXPECTED = "66bc7c532f5a1ad87e3dfff71a4b51f8c4f20840a8f62436874fa5b7c665938e"
EXPECTED_LEN = 10724

hex_path = sys.argv[1] if len(sys.argv) > 1 else "imu_to_dxl-0.2.0-feetech.hex"
mem = {}
base_hi = 0
with open(hex_path) as f:
    for line in f:
        line = line.strip()
        if not line.startswith(":"):
            continue
        n = int(line[1:3], 16)
        addr = int(line[3:7], 16)
        rtype = int(line[7:9], 16)
        data = bytes.fromhex(line[9 : 9 + 2 * n])
        if rtype == 4:
            base_hi = int.from_bytes(data, "big") << 16
        elif rtype == 0:
            a = base_hi + addr
            for i, b in enumerate(data):
                mem[a + i] = b

lo, hi = min(mem), max(mem) + 1
img = bytes(mem[a] for a in range(lo, hi))
digest = hashlib.sha256(img).hexdigest()
print(f"image : 0x{lo:08X}-0x{hi:08X} len={len(img)} bytes")
print(f"sha256: {digest}")
print(f"expect: {EXPECTED}")
ok_len = len(img) == EXPECTED_LEN
ok_hash = digest == EXPECTED
print(f"length match: {ok_len}, hash match: {ok_hash}")
sys.exit(0 if (ok_len and ok_hash) else 1)
