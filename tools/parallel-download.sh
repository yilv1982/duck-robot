#!/bin/bash
# GitHub release 大文件分段并行下载（curl Range 多连接，失败段自动补传）
# 用法: parallel-download.sh <URL> <输出文件> [总字节数] [分段数]
set -u
URL="$1"; OUT="$2"
N="${4:-12}"
cd "$(dirname "$OUT")"
BASE="$(basename "$OUT")"

TOTAL="$(curl -sIL --max-time 30 "$URL" | grep -i content-length | tail -1 | tr -dc '0-9')"
[ -z "$TOTAL" ] && { echo "无法获取文件大小"; exit 1; }
echo "total=$TOTAL bytes, $N segments"
SEG=$(( (TOTAL + N - 1) / N ))

expected_size() {  # 段 i 应有字节数
  local i=$1 s=$(( i * SEG )) e=$(( (i+1)*SEG - 1 ))
  [ $e -ge $TOTAL ] && e=$((TOTAL-1))
  echo $(( e - s + 1 ))
}

for round in 1 2 3; do
  pids=()
  for i in $(seq 0 $((N-1))); do
    exp=$(expected_size $i)
    act=$(stat -c %s "part_${i}" 2>/dev/null || echo 0)
    if [ "$act" = "$exp" ]; then continue; fi
    rm -f "part_${i}"
    START=$(( i * SEG )); END=$(( (i+1)*SEG - 1 ))
    [ $END -ge $TOTAL ] && END=$((TOTAL-1))
    curl -sL -r ${START}-${END} --retry 5 --retry-delay 3 -o "part_${i}" "$URL" &
    pids+=($!)
  done
  [ ${#pids[@]} -eq 0 ] && break
  echo "round $round: ${#pids[@]} 段下载中..."
  wait
done

# 校验所有段
ok=1
for i in $(seq 0 $((N-1))); do
  exp=$(expected_size $i); act=$(stat -c %s "part_${i}" 2>/dev/null || echo 0)
  if [ "$act" != "$exp" ]; then echo "段 $i 不完整: $act/$exp"; ok=0; fi
done
[ $ok -eq 1 ] || { echo "仍有缺段，退出"; exit 2; }

cat $(for i in $(seq 0 $((N-1))); do echo "part_${i}"; done) > "$BASE"
rm -f part_*
act=$(stat -c %s "$BASE")
echo "done: $BASE $act/$TOTAL"
[ "$act" = "$TOTAL" ] || exit 3
