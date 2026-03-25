# Telegram Listener — Cloud Run Deployment

## Prerequisites

- Docker Desktop running
- Google Cloud SDK (`gcloud`) installed and authenticated
- `cloud_run_production.session` in project root

## Deploy

```bash
docker build -t gcr.io/project-00bfaeaf-daab-4874-9bc/telegram-listener:latest .
```

```bash
docker push gcr.io/project-00bfaeaf-daab-4874-9bc/telegram-listener:latest
```

```bash
gcloud run deploy telegram-listener --image=gcr.io/project-00bfaeaf-daab-4874-9bc/telegram-listener:latest --region=us-central1 --platform=managed --memory=512Mi --cpu=1 --min-instances=1 --max-instances=1 --timeout=900 --concurrency=1 --port=8080 --set-env-vars='TELEGRAM_API_ID=17749532,TELEGRAM_API_HASH=5589176b4d5b9c6a679c68ab3d905aa8,TELEGRAM_SESSION=cloud_run_production,WEBHOOK_URL=https://soin-glob-telegram-webhook.onrender.com/cryptoHook,MONGODB_URI=mongodb+srv://globalsoin20:Uu5mmE9pqEtfBB1a@cluster0.6k3hcco.mongodb.net/,ERROR_NOTIFICATION_BOT_TOKEN=8599821115:AAFxo-89eykrqVnEYbxoNGkn-r87y9d-oYY,ERROR_NOTIFICATION_CHAT_ID=8094167049,SUPABASE_URL=https://xlgjwdorrhptzrftvmns.supabase.co,SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhsZ2p3ZG9ycmhwdHpyZnR2bW5zIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NTI3MzQ1NywiZXhwIjoyMDgwODQ5NDU3fQ._MsVb0SbCFOAYB2Mo-JvNkKsPsTWZ4hO1EAorEPD1p8,PYTHONUNBUFFERED=1' --no-allow-unauthenticated --project=project-00bfaeaf-daab-4874-9bc
```

## New session file

If the session expires or gets `AuthKeyDuplicatedError`:

```bash
python create_production_session.py
```

Then rebuild and redeploy (all 3 commands above).

## Logs

```bash
gcloud logs tail --follow --service=telegram-listener --project=project-00bfaeaf-daab-4874-9bc
```
