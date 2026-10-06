# Builds dist/ for manual upload to a host (Cloudflare Pages, Netlify, etc.).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (Test-Path dist) { Remove-Item dist -Recurse -Force }
New-Item -ItemType Directory dist | Out-Null

Copy-Item index.html dist/
Copy-Item farm dist/farm -Recurse
Copy-Item runner dist/runner -Recurse

$root = (Resolve-Path dist).Path.Length + 1
Get-ChildItem dist -Recurse -File | ForEach-Object { $_.FullName.Substring($root) }
Write-Host "`nDone: upload the dist/ folder to your host."
