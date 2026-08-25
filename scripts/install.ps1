#Requires -Version 5.1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Write-Host "Cortex Hub install from $Root"

$py = $null
if (Get-Command py -ErrorAction SilentlyContinue) { $py = "py" }
elseif (Get-Command python -ErrorAction SilentlyContinue) { $py = "python" }
else { Write-Error "Python 3.10+ required." }

$envFile = Join-Path $Root "cortex.env"
if (-not (Test-Path $envFile)) {
  Copy-Item (Join-Path $Root ".env.example") $envFile
  Write-Host "Created cortex.env — paste CORTEX_API_KEY=sk-... then re-run."
  notepad $envFile
  exit 1
}

& $py -3 (Join-Path $PSScriptRoot "install_opencode.py") $Root
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Restart OpenCode. Hub: .\hub\start.cmd"
