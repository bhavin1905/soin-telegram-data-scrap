# Quick fix deployment script for Cloud Run port issue
Write-Host "🔧 Applying quick fix for Cloud Run port issue..." -ForegroundColor Blue

# Get current project
$ProjectId = gcloud config get-value project 2>$null
if (-not $ProjectId) {
    Write-Host "❌ No project selected. Please run 'gcloud config set project YOUR_PROJECT_ID'" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Using project: $ProjectId" -ForegroundColor Green

# Quick deployment with correct settings
Write-Host "🚀 Updating Cloud Run service configuration..." -ForegroundColor Blue

# Load environment variables from .env file
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
} else {
    Write-Host "❌ .env file not found. Creating from template..." -ForegroundColor Red
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "📝 Please edit .env file with your actual values and run this script again." -ForegroundColor Yellow
        exit 1
    }
}

$envVars = @(
    "TELEGRAM_API_ID=$env:TELEGRAM_API_ID",
    "TELEGRAM_API_HASH=$env:TELEGRAM_API_HASH", 
    "TELEGRAM_SESSION=$env:TELEGRAM_SESSION",
    "WEBHOOK_URL=$env:WEBHOOK_URL",
    "MONGODB_URI=$env:MONGODB_URI",
    "ERROR_NOTIFICATION_BOT_TOKEN=$env:ERROR_NOTIFICATION_BOT_TOKEN",
    "ERROR_NOTIFICATION_CHAT_ID=$env:ERROR_NOTIFICATION_CHAT_ID",
    "PORT=8080",
    "PYTHONUNBUFFERED=1"
) -join ","

# Build the latest image
Write-Host "🏗️  Building updated container..." -ForegroundColor Blue
gcloud builds submit --tag="gcr.io/$ProjectId/telegram-listener:latest" --project=$ProjectId

# Deploy with correct configuration
Write-Host "🚀 Deploying with health check support..." -ForegroundColor Blue
gcloud run deploy telegram-listener `
    --image="gcr.io/$ProjectId/telegram-listener:latest" `
    --region=us-central1 `
    --platform=managed `
    --memory=512Mi `
    --cpu=1 `
    --min-instances=1 `
    --max-instances=3 `
    --timeout=900 `
    --concurrency=1 `
    --port=8080 `
    --set-env-vars=$envVars `
    --no-allow-unauthenticated `
    --project=$ProjectId

Write-Host "✅ Quick fix deployment completed!" -ForegroundColor Green

# Check service status
Write-Host "🔍 Checking service status..." -ForegroundColor Blue
$serviceUrl = gcloud run services describe telegram-listener --region=us-central1 --format="value(status.url)" --project=$ProjectId

if ($serviceUrl) {
    Write-Host "🌐 Service URL: $serviceUrl" -ForegroundColor Green
    Write-Host "🏥 Health check: $serviceUrl/health" -ForegroundColor Green
    
    # Test health endpoint
    Write-Host "🧪 Testing health endpoint..." -ForegroundColor Blue
    try {
        $response = Invoke-RestMethod -Uri "$serviceUrl/health" -Method Get -TimeoutSec 30
        Write-Host "✅ Health check passed!" -ForegroundColor Green
        Write-Host "Service status: $($response.status)" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Health check failed, but service might still be starting..." -ForegroundColor Yellow
        Write-Host "Check logs: gcloud logs tail --follow --service=telegram-listener --project=$ProjectId" -ForegroundColor Blue
    }
} else {
    Write-Host "❌ Failed to get service URL" -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 Useful commands:" -ForegroundColor Blue
Write-Host "View logs: gcloud logs tail --follow --service=telegram-listener --project=$ProjectId"
Write-Host "Service info: gcloud run services describe telegram-listener --region=us-central1 --project=$ProjectId"
Write-Host "🎉 Telegram Listener should now be running correctly on Cloud Run!" -ForegroundColor Green
