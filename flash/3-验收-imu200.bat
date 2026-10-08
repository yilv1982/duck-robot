@echo off
chcp 65001 >nul
cd /d "%~dp0tools\imu200"
echo === imu200 check: 13 acceptance criteria over the servo bus ===
echo Board wiring: URT-2/Waveshare TTL bus to J1 (GND/GND, DATA/DATA), board 5V powered, common GND.
set /p COMX=Input URT-2 COM number only (e.g. 7 for COM7):
"C:\Users\elvis\AppData\Local\Programs\Python\Python313\python.exe" imu200.py check --port COM%COMX%
pause
