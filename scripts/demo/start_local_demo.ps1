# ==============================================================================
# LFMT Intelligent Thermographic Slag Detection Platform - Local Demo Starter
# ==============================================================================
# Starts FastAPI backend (port 8000) and Next.js frontend (port 3000) for live
# conference and classroom demonstrations.

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  LFMT Intelligent Thermographic Defect Analysis Platform" -ForegroundColor Yellow
Write-Host "  Live Demonstration & Simulation Lab Starter" -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $RepoRoot

# 1. Environment & MATLAB Discovery
Write-Host "[1/4] Verifying MATLAB and Python Environment..." -ForegroundColor White
$MatlabExe = $env:LFMT_MATLAB_EXECUTABLE
if (-not $MatlabExe) {
    if (Test-Path "E:\MATLAB\bin\matlab.exe") {
        $MatlabExe = "E:\MATLAB\bin\matlab.exe"
    } elseif (Get-Command "matlab.exe" -ErrorAction SilentlyContinue) {
        $MatlabExe = (Get-Command "matlab.exe").Source
    }
}

if ($MatlabExe -and (Test-Path $MatlabExe)) {
    Write-Host "  -> MATLAB Executable: $MatlabExe" -ForegroundColor Green
    $env:LFMT_MATLAB_EXECUTABLE = $MatlabExe
} else {
    Write-Host "  -> MATLAB: Not found in default path (Fallback simulation active)" -ForegroundColor Yellow
}

# 2. Check Python packages
Write-Host "[2/4] Verifying Python Environment..." -ForegroundColor White
python -c "import uvicorn, fastapi, scipy, numpy, torch, scikit_fem; print('  -> Core Python scientific packages verified.')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [!] Warning: Missing some Python dependencies. Run pip install -r requirements.txt" -ForegroundColor Red
}

# 3. Start Backend in Background
Write-Host "[3/4] Launching FastAPI Backend Server (port 8000)..." -ForegroundColor White
$BackendProcess = Start-Process -FilePath "python" -ArgumentList "-m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload" -PassThru -NoNewWindow

# 4. Start Next.js Frontend
Write-Host "[4/4] Launching Next.js Frontend Portal (port 3000)..." -ForegroundColor White
Set-Location "$RepoRoot\web"
$FrontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -PassThru -NoNewWindow
Set-Location $RepoRoot

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  DEMO PLATFORM READY FOR LIVE PRESENTATION!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  * Simulation Lab UI : http://localhost:3000/simulate" -ForegroundColor Cyan
Write-Host "  * Main Web Portal   : http://localhost:3000" -ForegroundColor Cyan
Write-Host "  * REST API OpenAPI  : http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  * MATLAB Backend    : MATLAB_FDM (3-D Transient Heat Transfer)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C or close this console to terminate the servers." -ForegroundColor Gray
Write-Host ""

# Keep process alive and monitor
try {
    while ($true) {
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Host "Shutting down servers..." -ForegroundColor Yellow
    if ($BackendProcess -and -not $BackendProcess.HasExited) { Stop-Process -Id $BackendProcess.Id -Force }
    if ($FrontendProcess -and -not $FrontendProcess.HasExited) { Stop-Process -Id $FrontendProcess.Id -Force }
}
