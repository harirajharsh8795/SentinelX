# SentinelX - Windows Startup Script
# This PowerShell script launches the Backend and Frontend concurrently.

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Starting SentinelX Backend..." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Start the FastAPI backend server in a new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .venv\Scripts\activate; uvicorn main:app --port 8000 --reload"

# Wait a brief moment for the backend to initialize
Write-Host "Waiting for backend server to bind to port 8000..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Starting SentinelX Frontend..." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Start the frontend dev server in the current PowerShell terminal
cd frontend
npm run dev
