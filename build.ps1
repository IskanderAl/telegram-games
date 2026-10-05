# Builds dist/ for manual upload to a host (Cloudflare Pages, Netlify, etc.).
# Unlike GitHub Pages, this includes local-only files: config.js and sprites.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (Test-Path dist) { Remove-Item dist -Recurse -Force }
New-Item -ItemType Directory dist | Out-Null

Copy-Item index.html dist/
Copy-Item farm dist/farm -Recurse
Copy-Item runner dist/runner -Recurse

if (Test-Path config.js) {
    Copy-Item config.js dist/
} else {
    Copy-Item config.example.js dist/config.js
    Write-Warning "config.js not found: using empty template, ads will run in demo mode."
}

$root = (Resolve-Path dist).Path.Length + 1
Get-ChildItem dist -Recurse -File | ForEach-Object { $_.FullName.Substring($root) }
Write-Host "`nDone: upload the dist/ folder to your host."
