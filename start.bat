@echo off
echo ================================
echo  Hewmann Experience Chatbot
echo ================================

:: Kill any old server on port 8000 first
echo.
echo [0/2] Clearing old server instances...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: Step 1 — Ingest knowledge base (only if not already done)
echo [1/2] Checking knowledge base...
if exist "data\chunks.json" (
  echo  Knowledge base found - skipping ingest.
) else (
  echo  Building knowledge base from Word doc...
  "C:\Users\AL HAMD TRADERS\AppData\Local\Python\bin\python.exe" backend/ingest.py
)

:: Step 2 — Open Chrome after 3s, then start server
echo.
echo [2/2] Starting server at http://localhost:8000 ...
echo  Press Ctrl+C to stop.
echo.

start "" cmd /c "timeout /t 3 /nobreak >nul && start chrome http://localhost:8000"

"C:\Users\AL HAMD TRADERS\AppData\Local\Python\bin\python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
