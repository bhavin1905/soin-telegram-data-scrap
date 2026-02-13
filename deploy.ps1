# Google Cloud Platform Deployment Script for Telegram Listener (PowerShell)
# This script automates the deployment process to Google Cloud Run

param(
    [string]$ProjectId = "soinglobal-telegram",
    [string]$ServiceName = "telegram-listener",
    [string]$Region = "us-central1"
)

# Configuration
$MEMORY = "512Mi"
$CPU = "1"
$MIN_INSTANCES = "1"
$MAX_INSTANCES = "3"

Write-Host "🚀 Starting Google Cloud deployment for Telegram Listener" -ForegroundColor Blue

# Check if gcloud is installed
try {
    gcloud version | Out-Null
}
catch {
    Write-Host "❌ Google Cloud SDK is not installed. Please install it first." -ForegroundColor Red
    Write-Host "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
}

# Check if user is authenticated
$authStatus = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
if (-not $authStatus) {
    Write-Host "⚠️  You are not authenticated with Google Cloud" -ForegroundColor Yellow
    Write-Host "Running: gcloud auth login"
    gcloud auth login
}

# Get project ID
if (-not $ProjectId) {
    $currentProject = gcloud config get-value project 2>$null
    if (-not $currentProject) {
        Write-Host "⚠️  No project selected" -ForegroundColor Yellow
        Write-Host "Available projects:"
        gcloud projects list
        $ProjectId = Read-Host "Enter your project ID"
        gcloud config set project $ProjectId
    }
    else {
        $ProjectId = $currentProject
    }
}

Write-Host "✅ Using project: $ProjectId" -ForegroundColor Green

# Enable required APIs
Write-Host "🔧 Enabling required Google Cloud APIs..." -ForegroundColor Blue
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com --project=$ProjectId

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found. Please create it with your configuration." -ForegroundColor Red
    Write-Host "Copy .env.example to .env and fill in your values."
    exit 1
}

# Load environment variables from .env file
Get-Content ".env" | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

# Build and deploy using Cloud Build
Write-Host "🏗️  Building and deploying with Cloud Build..." -ForegroundColor Blue
gcloud builds submit --config=cloudbuild.yaml --project=$ProjectId

# Deploy to Cloud Run with environment variables
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Blue
$envVars = @(
    "TELEGRAM_API_ID=$env:TELEGRAM_API_ID",
    "TELEGRAM_API_HASH=$env:TELEGRAM_API_HASH",
    "TELEGRAM_SESSION=$env:TELEGRAM_SESSION",
    "WEBHOOK_URL=$env:WEBHOOK_URL",
    "MONGODB_URI=$env:MONGODB_URI",
    "ERROR_NOTIFICATION_BOT_TOKEN=$env:ERROR_NOTIFICATION_BOT_TOKEN",
    "ERROR_NOTIFICATION_CHAT_ID=$env:ERROR_NOTIFICATION_CHAT_ID",
    "SUPABASE_URL=$env:SUPABASE_URL",
    "SUPABASE_KEY=$env:SUPABASE_KEY",
    "PYTHONUNBUFFERED=1"
) -join ","

gcloud run deploy $ServiceName `
    --image="gcr.io/$ProjectId/telegram-listener:latest" `
    --region=$Region `
    --platform=managed `
    --memory=$MEMORY `
    --cpu=$CPU `
    --min-instances=$MIN_INSTANCES `
    --max-instances=$MAX_INSTANCES `
    --timeout=900 `
    --concurrency=1 `
    --port=8080 `
    --set-env-vars=$envVars `
    --no-allow-unauthenticated `
    --project=$ProjectId

Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green

# Get service URL
$serviceUrl = gcloud run services describe $ServiceName --region=$Region --format="value(status.url)" --project=$ProjectId
Write-Host "🌐 Service URL: $serviceUrl" -ForegroundColor Green

# Show logs command
Write-Host "📋 To view logs, run:" -ForegroundColor Blue
Write-Host "gcloud logs tail --follow --format=json --service=$ServiceName --project=$ProjectId"

Write-Host "📋 To update the service, run:" -ForegroundColor Blue
Write-Host '.\deploy.ps1'

Write-Host '🎉 Telegram Listener is now running on Google Cloud Run!' -ForegroundColor Green
