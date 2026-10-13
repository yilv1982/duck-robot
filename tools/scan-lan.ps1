[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$base = '192.168.1'
Write-Host "扫描网段: $base.0/24 ..."
$jobs = 1..254 | ForEach-Object {
  Start-Job -ScriptBlock { param($ip) $r = & ping.exe -n 1 -w 400 $ip 2>&1 | Out-String; if ($r -match 'TTL=') { $ip } } -ArgumentList "$base.$_"
}
$null = $jobs | Wait-Job
$alive = @($jobs | Receive-Job | Where-Object { $_ })
$jobs | Remove-Job -Force
Write-Host ("存活主机: " + ($alive -join ', '))
Write-Host "`n=== ARP 表 ==="
arp -a | Select-String '192\.168\.1\.' | ForEach-Object { $_.Line.Trim() } | Where-Object { $_ -notmatch 'ff-ff-ff-ff-ff-ff|\.255 ' }
