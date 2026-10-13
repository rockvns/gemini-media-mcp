# Self-update script for Gemini & Veo Media MCP Server standalone executable
param(
    [string]$Destination = "$HOME\Downloads\gemini-media-mcp-standalone.exe"
)

$ErrorActionPreference = "Stop"
$repo = "rockvns/gemini-media-mcp"
$url = "https://github.com/$repo/releases/latest/download/gemini-media-mcp-standalone.exe"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Gemini & Veo Media MCP Server - Self Updater" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Fetching latest release binary from GitHub..." -ForegroundColor Yellow
Write-Host "Source: $url"
Write-Host "Destination: $Destination"

try {
    $parentDir = Split-Path -Parent $Destination
    if ($parentDir -and -not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }

    Invoke-WebRequest -Uri $url -OutFile $Destination -UseBasicParsing
    Write-Host "`nUpdate Successful!" -ForegroundColor Green
    Write-Host "Standalone executable saved to: $Destination" -ForegroundColor Green
} catch {
    Write-Host "`nUpdate Failed: $_" -ForegroundColor Red
    exit 1
}
