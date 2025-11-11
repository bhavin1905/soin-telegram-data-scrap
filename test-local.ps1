# Quick local test script for Docker deployment (PowerShell)
Write-Host "🧪 Testing Telegram Listener locally with Docker..." -ForegroundColor Blue

# Check if Docker is installed
try {
    docker --version | Out-Null
} catch {
    Write-Host "❌ Docker is not installed. Please install Docker first." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found. Please create it with your configuration." -ForegroundColor Red
    Write-Host "Copy .env.example to .env and fill in your values."
    exit 1
}

Write-Host "🏗️  Building Docker image..." -ForegroundColor Blue
docker build -t telegram-listener:test .

Write-Host "🚀 Running container locally..." -ForegroundColor Blue
docker run --rm -it --env-file .env --name telegram-listener-test telegram-listener:test

Write-Host "✅ Local test completed!" -ForegroundColor Green
