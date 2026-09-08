$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$uiDir = Join-Path $root "ui"
$distDir = Join-Path $uiDir "dist"
$publishDir = Join-Path $root "publish\ui"
$webConfigSource = Join-Path $PSScriptRoot "iis-web.config"

Write-Host "Building UI..." -ForegroundColor Cyan

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  throw "npm is not installed or not available in PATH."
}

Push-Location $uiDir
try {
  npm install
  if ($LASTEXITCODE -ne 0) {
    throw "npm install failed."
  }

  npm run build
  if ($LASTEXITCODE -ne 0) {
    throw "npm run build failed."
  }
}
finally {
  Pop-Location
}

if (Test-Path $publishDir) {
  Remove-Item -LiteralPath $publishDir -Recurse -Force
}
New-Item -ItemType Directory -Path $publishDir | Out-Null

Copy-Item -Path (Join-Path $distDir "*") -Destination $publishDir -Recurse -Force
Copy-Item -LiteralPath $webConfigSource -Destination (Join-Path $publishDir "web.config") -Force

Write-Host ""
Write-Host "UI publish folder created:" -ForegroundColor Green
Write-Host $publishDir
Write-Host ""
Write-Host "Share or upload this folder to your web server/IIS site root." -ForegroundColor Yellow
