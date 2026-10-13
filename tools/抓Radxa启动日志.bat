@echo off
chcp 65001 >nul
echo === Radxa Zero 3W 启动日志抓取 (1500000 8N1) ===
echo 接线: 板排针 8(TX) - DAPLink RX, 板 9(GND) - DAPLink GND (共地)
echo 停止: Ctrl+C, 日志在 docs\references\emmc-flash-radxa-zero3w-20261013\serial-logs\
echo.
"C:\Users\elvis\AppData\Local\Programs\Python\Python313\python.exe" "%~dp0serial-log.py" %*
pause
