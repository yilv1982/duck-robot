[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "=== 串口 ==="
[System.IO.Ports.SerialPort]::GetPortNames()
Write-Host "`n=== 所有 USB 设备（VID_） ==="
Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPDeviceID -like 'USB\VID_*' } |
  Select-Object Name, Status, PNPDeviceID | Format-Table -AutoSize | Out-String -Width 220
Write-Host "`n=== 异常设备 ==="
Get-CimInstance Win32_PnPEntity | Where-Object { $_.Status -ne 'OK' } |
  Select-Object Name, Status | Format-Table -AutoSize
