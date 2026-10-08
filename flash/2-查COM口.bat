@echo off
chcp 65001 >nul
echo === COM ports on this machine ===
"C:\Users\elvis\AppData\Local\Programs\Python\Python313\python.exe" -c "import serial.tools.list_ports;[print(p.device,'-',p.description)for p in serial.tools.list_ports.comports()]"
pause
