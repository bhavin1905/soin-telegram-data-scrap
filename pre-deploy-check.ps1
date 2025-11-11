# Pre-deployment verification script
Write-Host "🔍 Pre-deployment verification..." -ForegroundColor Blue

# Check if image exists
Write-Host "📦 Checking if container image exists..." -ForegroundColor Yellow
$imageCheck = gcloud container images list --repository=gcr.io/soinglobal-telegram --filter="name:telegram-listener" --format="value(name)" 2>$null

if ($imageCheck) {
    Write-Host "✅ Container image found: $imageCheck" -ForegroundColor Green
} else {
    Write-Host "❌ Container image not found. Building now..." -ForegroundColor Red
    Write-Host "🏗️  Building container image..." -ForegroundColor Blue
    gcloud builds submit --tag gcr.io/soinglobal-telegram/telegram-listener:latest --project soinglobal-telegram
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Container image built successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Container build failed!" -ForegroundColor Red
        exit 1
    }
}

# Check session file
Write-Host "📁 Checking session file..." -ForegroundColor Yellow
if (Test-Path "your_session_name.session") {
    Write-Host "✅ Session file found: your_session_name.session" -ForegroundColor Green
} else {
    Write-Host "❌ Session file not found! Make sure your_session_name.session exists." -ForegroundColor Red
    Write-Host "   Available session files:" -ForegroundColor Yellow
    Get-ChildItem *.session | ForEach-Object { Write-Host "   - $($_.Name)" -ForegroundColor Yellow }
}

# Verify environment variables
Write-Host "🔐 Verifying environment variables..." -ForegroundColor Yellow
$envVars = @{
    "TELEGRAM_API_ID" = "28700349"
    "TELEGRAM_API_HASH" = "ef8fb06cffda02c80d4fda3b782e6fd6"
    "TELEGRAM_SESSION" = "your_session_name"
    "WEBHOOK_URL" = "https://soin-glob-telegram-webhook.onrender.com/cryptoHook"
    "MONGODB_URI" = "mongodb+srv://bhavinparmar1953:123qwerty@cluster0.qndu4.mongodb.net/"
    "ERROR_NOTIFICATION_BOT_TOKEN" = "8448229100:AAHIwUFJ52gEjYe78pt_wuHD5agCpgIC154"
    "ERROR_NOTIFICATION_CHAT_ID" = "-7701886991"
}

foreach ($var in $envVars.GetEnumerator()) {
    if ($var.Value -and $var.Value -ne "your_value_here") {
        Write-Host "✅ $($var.Key): Set" -ForegroundColor Green
    } else {
        Write-Host "❌ $($var.Key): Not set or placeholder value" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🚀 Ready to deploy! Run the deployment command:" -ForegroundColor Green
Write-Host ""
Write-Host "gcloud run deploy telegram-listener \\" -ForegroundColor Cyan
Write-Host "  --image gcr.io/soinglobal-telegram/telegram-listener:latest \\" -ForegroundColor Cyan
Write-Host "  --platform managed \\" -ForegroundColor Cyan
Write-Host "  --region us-central1 \\" -ForegroundColor Cyan
Write-Host "  --memory 512Mi \\" -ForegroundColor Cyan
Write-Host "  --cpu 1 \\" -ForegroundColor Cyan
Write-Host "  --min-instances 1 \\" -ForegroundColor Cyan
Write-Host "  --max-instances 3 \\" -ForegroundColor Cyan
Write-Host "  --timeout 900 \\" -ForegroundColor Cyan
Write-Host "  --concurrency 1 \\" -ForegroundColor Cyan
Write-Host "  --port 8080 \\" -ForegroundColor Cyan
Write-Host "  --set-env-vars \\" -ForegroundColor Cyan
Write-Host "`"TELEGRAM_API_ID=28700349,\\" -ForegroundColor Cyan
Write-Host "TELEGRAM_API_HASH=ef8fb06cffda02c80d4fda3b782e6fd6,\\" -ForegroundColor Cyan
Write-Host "TELEGRAM_SESSION=your_session_name,\\" -ForegroundColor Cyan
Write-Host "WEBHOOK_URL=https://soin-glob-telegram-webhook.onrender.com/cryptoHook,\\" -ForegroundColor Cyan
Write-Host "MONGODB_URI=mongodb+srv://bhavinparmar1953:123qwerty@cluster0.qndu4.mongodb.net/,\\" -ForegroundColor Cyan
Write-Host "ERROR_NOTIFICATION_BOT_TOKEN=8448229100:AAHIwUFJ52gEjYe78pt_wuHD5agCpgIC154,\\" -ForegroundColor Cyan
Write-Host "ERROR_NOTIFICATION_CHAT_ID=-7701886991,\\" -ForegroundColor Cyan
Write-Host "PYTHONUNBUFFERED=1`" \\" -ForegroundColor Cyan
Write-Host "  --no-allow-unauthenticated \\" -ForegroundColor Cyan
Write-Host "  --project soinglobal-telegram" -ForegroundColor Cyan
