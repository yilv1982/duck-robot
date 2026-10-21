param(
    [ValidateSet('viser', 'native')][string]$Viewer = 'viser',
    [switch]$Simple,
    [string]$Checkpoint,
    [int]$Port = 8080,
    [double]$Velocity = 0,
    [double]$Duration = 0,
    [string]$Metrics,
    [string]$Distro
)

$ErrorActionPreference = 'Stop'
$wslArgs = @()
if ($Distro) { $wslArgs += @('-d', $Distro) }

function Convert-ToWslPath([string]$Value) {
    if ($Value.StartsWith('/')) { return $Value }
    $absolute = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Value)
    $converted = & wsl.exe @wslArgs --exec wslpath -a -u $absolute
    if ($LASTEXITCODE -ne 0) { throw "WSL 无法转换路径：$absolute" }
    return ($converted | Select-Object -Last 1).Trim()
}

$trainingPath = Convert-ToWslPath $PSScriptRoot
$pythonPath = "$trainingPath/.venv-wsl/bin/python"
& wsl.exe @wslArgs --exec test -x $pythonPath
if ($LASTEXITCODE -ne 0) {
    throw "找不到现有 WSL Python：$pythonPath。若环境在另一发行版，请加 -Distro 指定已有环境。"
}

$programArgs = @('--viewer', $Viewer, '--port', "$Port", '--velocity', $Velocity.ToString([Globalization.CultureInfo]::InvariantCulture))
if ($Simple) { $programArgs += '--simple' }
if ($Checkpoint) { $programArgs += @('--checkpoint', (Convert-ToWslPath $Checkpoint)) }
if ($Duration -gt 0) { $programArgs += @('--duration', $Duration.ToString([Globalization.CultureInfo]::InvariantCulture)) }
if ($Metrics) { $programArgs += @('--metrics', (Convert-ToWslPath $Metrics)) }

if ($Viewer -eq 'native') { Write-Host 'native 为实验入口；本机 WSLg 软件渲染低速，建议使用默认 Viser。' }
Write-Host '启动 MuJoCo 单环境回放；界面地址以程序打印为准。'
& wsl.exe @wslArgs --cd $trainingPath --exec env PYTHONUTF8=1 $pythonPath "$trainingPath/play_mujoco.py" @programArgs
exit $LASTEXITCODE
