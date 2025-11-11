# FINAL WORKING Google Cloud Run Deployment Command
# This version fixes the environment variable parsing issue

Write-Host "🚀 Deploying to Cloud Run with properly formatted environment variables..." -ForegroundColor Blue

# Define environment variables individually to avoid concatenation issues
$env_vars = @()
$env_vars += "TELEGRAM_API_ID=28700349"
$env_vars += "TELEGRAM_API_HASH=ef8fb06cffda02c80d4fda3b782e6fd6"
$env_vars += "TELEGRAM_SESSION=cloud_run_production"  # Ensure this matches your session name
$env_vars += "WEBHOOK_URL=https://soin-glob-telegram-webhook.onrender.com/cryptoHook"
$env_vars += "MONGODB_URI=mongodb+srv://globalsoin20:Uu5mmE9pqEtfBB1a@cluster0.6k3hcco.mongodb.net/soin-pump?retryWrites=true&w=majority&appName=Cluster0/"
$env_vars += "ERROR_NOTIFICATION_BOT_TOKEN=8448229100:AAHIwUFJ52gEjYe78pt_wuHD5agCpgIC154"
$env_vars += "ERROR_NOTIFICATION_CHAT_ID=-7701886991"
$env_vars += "PYTHONUNBUFFERED=1"

$env_string = $env_vars -join ","

Write-Host "Environment variables: $env_string" -ForegroundColor Yellow

# Deploy with proper environment variable formatting
gcloud run deploy telegram-listener `
    --image gcr.io/soinglobal-telegram/telegram-listener:latest `
    --platform managed `
    --region us-central1 `
    --memory 1Gi `
    --cpu 2 `
    --min-instances 1 `
    --max-instances 3 `
    --timeout 900 `
    --concurrency 1 `
    --port 8080 `
    --set-env-vars $env_string `
    --no-allow-unauthenticated `
    --project soinglobal-telegram

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
    
    # Get service URL
    $serviceUrl = gcloud run services describe telegram-listener --region=us-central1 --format="value(status.url)" --project=soinglobal-telegram
    Write-Host "🌐 Service URL: $serviceUrl" -ForegroundColor Green
    
    # Test health endpoint
    Write-Host "🧪 Testing health endpoint..." -ForegroundColor Blue
    try {
        Start-Sleep -Seconds 30  # Wait for service to be ready
        $response = Invoke-RestMethod -Uri "$serviceUrl/health" -Method Get -TimeoutSec 30
        Write-Host "✅ Health check passed!" -ForegroundColor Green
        Write-Host "Service status: $($response.status)" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️  Health check failed, checking logs..." -ForegroundColor Yellow
        gcloud run services logs read telegram-listener --region=us-central1 --project=soinglobal-telegram --limit=10
    }
}
else {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    Write-Host "Checking logs..." -ForegroundColor Yellow
    gcloud run services logs read telegram-listener --region=us-central1 --project=soinglobal-telegram --limit=10
}
