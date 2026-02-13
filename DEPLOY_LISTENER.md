# Deploy telegram_listener.py to Cloud Run (with production session)

This describes how to deploy **telegram_listener.py** and how to redeploy when you update the **production session file** (`cloud_run_production.session`).

## One-time setup

1. **Production session file**  
   Have `cloud_run_production.session` in the project root (created with `create_production_session.py` or copied from your auth flow).

2. **`.env` for production**  
   In `.env`, set the session name so the app uses the production file:

   ```env
   TELEGRAM_SESSION=cloud_run_production
   ```

   The app will load `cloud_run_production.session` (Telethon uses `{TELEGRAM_SESSION}.session`).

3. **Other `.env` variables**  
   Ensure `.env` has the rest of what `deploy.ps1` needs, e.g.:
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - `WEBHOOK_URL`
   - `MONGODB_URI`
   - `ERROR_NOTIFICATION_BOT_TOKEN`
   - `ERROR_NOTIFICATION_CHAT_ID`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

## Deploy (PowerShell)

From the project root:

```powershell
.\deploy.ps1
```

This will:

- Use `cloudbuild.yaml` to build the image (including `cloud_run_production.session` via `.gcloudignore`)
- Deploy the **telegram-listener** Cloud Run service
- Pass env vars from `.env` (including `TELEGRAM_SESSION=cloud_run_production`)

## When you update the production session file

After you change or regenerate `cloud_run_production.session`:

1. Save `cloud_run_production.session` in the project root (overwrite the old one).
2. Run the same deploy command:

   ```powershell
   .\deploy.ps1
   ```

No need to change `.env` unless you also change the session name. The new session file is included in the next build and deployed with the service.

## Optional parameters

```powershell
.\deploy.ps1 -ProjectId "soinglobal-telegram" -ServiceName "telegram-listener" -Region "us-central1"
```

## View logs

```powershell
gcloud logs tail --follow --format=json --service=telegram-listener --project=soinglobal-telegram
```

## Notes

- **Dockerfile** runs `telegram_listener.py` (not `telegram_bot_test_one.py`).
- **`.gcloudignore`** is set up so `cloud_run_production.session` is **not** ignored and is included in the image. Other sensitive files (e.g. `.env`) stay out of the image; env vars are set at deploy time by `deploy.ps1`.

gcloud run deploy telegram-listener `  --image=gcr.io/project-00bfaeaf-daab-4874-9bc/telegram-listener:latest`
--region=us-central1 `  --platform=managed`
--memory=512Mi `  --cpu=1`
--min-instances=1 `  --max-instances=3`
--timeout=900 `  --concurrency=1`
--port=8080 `  --set-env-vars="TELEGRAM_API_ID=17749532,TELEGRAM_API_HASH=5589176b4d5b9c6a679c68ab3d905aa8,TELEGRAM_SESSION=cloud_run_production,WEBHOOK_URL=...,MONGODB_URI=,ERROR_NOTIFICATION_BOT_TOKEN=...,ERROR_NOTIFICATION_CHAT_ID=...,PYTHONUNBUFFERED=1"`
--no-allow-unauthenticated `
--project=project-00bfaeaf-daab-4874-9bc

gcloud run deploy telegram-listener `  --image=gcr.io/project-00bfaeaf-daab-4874-9bc/telegram-listener:latest`
--region=us-central1 `  --platform=managed`
--memory=512Mi `  --cpu=1`
--min-instances=1 `  --max-instances=3`
--timeout=900 `  --concurrency=1`
--port=8080 `  --set-env-vars='TELEGRAM_API_ID=17749532,TELEGRAM_API_HASH=5589176b4d5b9c6a679c68ab3d905aa8,TELEGRAM_SESSION=cloud_run_production,WEBHOOK_URL=https://soin-glob-telegram-webhook.onrender.com/cryptoHook,MONGODB_URI=mongodb+srv://globalsoin20:Uu5mmE9pqEtfBB1a@cluster0.6k3hcco.mongodb.net/,ERROR_NOTIFICATION_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz,ERROR_NOTIFICATION_CHAT_ID=-1001234567890,PYTHONUNBUFFERED=1'`
--no-allow-unauthenticated `
--project=project-00bfaeaf-daab-4874-9bc
