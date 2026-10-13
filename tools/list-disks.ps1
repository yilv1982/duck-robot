[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Get-Disk | Where-Object { $_.BusType -ne 'NVMe' -and $_.BusType -ne 'SATA' } |
  Select-Object Number, FriendlyName, BusType, @{n='SizeGB';e={[math]::Round($_.Size/1GB,1)}}, PartitionStyle, OperationalStatus |
  Format-Table -AutoSize
Write-Host "`n=== 分区/盘符 ==="
Get-Disk | Where-Object { $_.BusType -eq 'USB' -or $_.BusType -eq 'SD' -or $_.BusType -eq 'MMC' } | ForEach-Object {
  $d = $_
  Get-Partition -DiskNumber $d.Number -ErrorAction SilentlyContinue | ForEach-Object {
    $vol = $_ | Get-Volume -ErrorAction SilentlyContinue
    [PSCustomObject]@{
      Disk = $d.Number; DiskName = $d.FriendlyName; Partition = $_.PartitionNumber
      Letter = $_.DriveLetter; FileSystem = $vol.FileSystem; Label = $vol.FileSystemLabel
      SizeMB = [math]::Round($_.Size/1MB)
    }
  }
} | Format-Table -AutoSize
