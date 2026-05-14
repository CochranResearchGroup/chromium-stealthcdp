param(
  [ValidateSet("Launch", "Cleanup")]
  [string]$Mode = "Launch",
  [string]$ChromePath,
  [string]$UserDataDir,
  [string]$LogPath,
  [int]$ProcessId = 0,
  [string]$RemoteDebuggingAddress = "127.0.0.1"
)

$ErrorActionPreference = "Stop"

if ($Mode -eq "Cleanup") {
  if ($ProcessId -gt 0) {
    $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -ne $process) {
      Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    }
  }
  exit 0
}

if (-not $ChromePath) {
  throw "ChromePath is required"
}
if (-not (Test-Path -LiteralPath $ChromePath)) {
  throw "chrome.exe not found: $ChromePath"
}
if (-not $UserDataDir) {
  throw "UserDataDir is required"
}
if (-not $LogPath) {
  throw "LogPath is required"
}

New-Item -ItemType Directory -Force -Path $UserDataDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LogPath) | Out-Null
$ErrorLogPath = "$LogPath.err"

$versionInfo = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($ChromePath)
$productName = $versionInfo.ProductName
$productVersion = $versionInfo.ProductVersion
if ($productName -and $productVersion) {
  $versionOutput = "$($productName.Trim()) $($productVersion.Trim())"
} elseif ($productVersion) {
  $versionOutput = $productVersion.Trim()
} else {
  $versionOutput = ""
}

$arguments = @(
  "--headless=new",
  "--disable-gpu",
  "--disable-dev-shm-usage",
  "--enable-logging",
  "--log-file=$LogPath",
  "--remote-debugging-address=$RemoteDebuggingAddress",
  "--remote-debugging-port=0",
  "--user-data-dir=$UserDataDir",
  "--no-first-run",
  "--disable-default-apps",
  "about:blank"
)

$process = Start-Process `
  -FilePath $ChromePath `
  -ArgumentList $arguments `
  -WorkingDirectory (Split-Path -Parent $ChromePath) `
  -WindowStyle Hidden `
  -PassThru

$result = [ordered]@{
  processId = $process.Id
  chromePath = $ChromePath
  chromeVersion = $versionOutput
  userDataDir = $UserDataDir
  devtoolsActivePortPath = Join-Path $UserDataDir "DevToolsActivePort"
  logPath = $LogPath
  errorLogPath = $ErrorLogPath
  remoteDebuggingAddress = $RemoteDebuggingAddress
}

$result | ConvertTo-Json -Compress
