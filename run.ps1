$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".venv")) {
  Write-Host "Missing .venv. Run: .\setup.ps1" -ForegroundColor Yellow
  exit 1
}

.\.venv\Scripts\python app.py


