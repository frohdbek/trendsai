@echo off
echo Starting Trend Analiz App...
echo.

echo [1/2] Starting FastAPI backend on http://localhost:8000
start "FastAPI Backend" cmd /k "cd /d %~dp0 && venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

echo [2/2] Starting frontend server on http://localhost:3000
start "Frontend" cmd /k "cd /d %~dp0\frontend && python -m http.server 3000"

echo.
echo Both servers starting...
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to close this window (servers will keep running in separate windows)
pause