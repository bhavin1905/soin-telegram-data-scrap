# Telegram Userbot - Google Cloud Run Deployment Guide

This guide will help you deploy the Telegram Userbot to Google Cloud Run.

## Prerequisites

1. Google Cloud SDK (gcloud) installed and configured
2. A Google Cloud Project with billing enabled
3. Required APIs enabled (Cloud Run, Cloud Build, Container Registry)
4. Environment variables configured in `.env` file

## Required Environment Variables

Make sure your `.env` file contains:

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_SESSION=your_session_name
WEBHOOK_URL=your_webhook_url
MONGODB_URI=your_mongodb_uri
ERROR_NOTIFICATION_BOT_TOKEN=your_bot_token
ERROR_NOTIFICATION_CHAT_ID=your_chat_id
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Deployment Methods

### Method 1: Using the Deployment Script (Recommended)

```bash
./deploy-userbot.sh
```

This script will:
- Check prerequisites
- Enable required APIs
- Build and push the Docker image
- Deploy to Cloud Run with environment variables

### Method 2: Using Cloud Build

```bash
gcloud builds submit --config=cloudbuild-userbot.yaml
```

Then manually set environment variables:

```bash
gcloud run deploy telegram-userbot \
  --image=gcr.io/$PROJECT_ID/telegram-userbot:latest \
  --region=us-central1 \
  --set-env-vars="TELEGRAM_API_ID=...,TELEGRAM_API_HASH=..." \
  --no-allow-unauthenticated
```

### Method 3: Manual Docker Build and Deploy

1. Build the Docker image:
```bash
docker build -f Dockerfile.userbot -t gcr.io/$PROJECT_ID/telegram-userbot:latest .
```

2. Push to Container Registry:
```bash
docker push gcr.io/$PROJECT_ID/telegram-userbot:latest
```

3. Deploy to Cloud Run:
```bash
gcloud run deploy telegram-userbot \
  --image=gcr.io/$PROJECT_ID/telegram-userbot:latest \
  --region=us-central1 \
  --platform=managed \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=3 \
  --timeout=900 \
  --port=8080 \
  --set-env-vars="TELEGRAM_API_ID=...,TELEGRAM_API_HASH=..." \
  --no-allow-unauthenticated
```

## Health Check Endpoints

Once deployed, the service exposes these endpoints:

- `GET /` - Root endpoint with service info
- `GET /health` - Health check endpoint (returns 200 if healthy, 503 if unhealthy)
- `GET /ready` - Readiness check endpoint

## Monitoring

View logs:
```bash
gcloud logs tail --follow --service=telegram-userbot
```

Check service status:
```bash
gcloud run services describe telegram-userbot --region=us-central1
```

## Troubleshooting

1. **Container fails to start**: Check logs for errors
2. **Health check fails**: Ensure PORT=8080 is set and health server starts
3. **Telegram connection issues**: Verify API credentials and session file
4. **Database connection errors**: Check MongoDB URI and network access

## Notes

- The service requires a minimum of 1 instance to stay running
- Health checks run every 30 seconds
- The service listens on port 8080 (required for Cloud Run)
- Session files should be persisted if you need to maintain login state

