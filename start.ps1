# Trend Analiz Uygulaması - Başlatma Scripti
Write-Host "Starting Trend Analiz App..." -ForegroundColor Green
Write-Host ""

# Backend'i başlat
Write-Host "[1/2] Starting FastAPI backend on http://localhost:8000" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000"

# Frontend'i başlat
Write-Host "[2/2] Starting frontend server on http://localhost:3000" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; python -m http.server 3000"

Write-Host ""
Write-Host "Both servers starting..." -ForegroundColor Green
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to close this window (servers will keep running in separate windows)" -ForegroundColor Gray
Read-Host