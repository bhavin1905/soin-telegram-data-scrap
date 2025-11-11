# Updated Google Cloud Run Deployment Command
# Copy and paste this updated command:

gcloud run deploy telegram-listener `
  --image gcr.io/soinglobal-telegram/telegram-listener:latest `
  --platform managed `
  --region us-central1 `
  --memory 512Mi `
  --cpu 1 `
  --min-instances 1 `
  --max-instances 3 `
  --timeout 900 `
  --concurrency 1 `
  --port 8080 `
  --set-env-vars `
  "TELEGRAM_API_ID=28700349,`
TELEGRAM_API_HASH=ef8fb06cffda02c80d4fda3b782e6fd6,`
TELEGRAM_SESSION=cloudrun_production_new,`
WEBHOOK_URL=https://soin-glob-telegram-webhook.onrender.com/cryptoHook,`
MONGODB_URI=mongodb+srv://bhavinparmar1953:123qwerty@cluster0.qndu4.mongodb.net/,`
ERROR_NOTIFICATION_BOT_TOKEN=8448229100:AAHIwUFJ52gEjYe78pt_wuHD5agCpgIC154,`
ERROR_NOTIFICATION_CHAT_ID=-7701886991,`
PYTHONUNBUFFERED=1" `
  --no-allow-unauthenticated `
  --project soinglobal-telegram
