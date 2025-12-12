#!/bin/bash
# Quick deployment steps for telegram-userbot

PROJECT_ID="project-00bfaeaf-daab-4874-9bc"
IMAGE_NAME="gcr.io/$PROJECT_ID/telegram-userbot:latest"
SERVICE_NAME="telegram-userbot"
REGION="us-central1"

echo "🚀 Step 1: Configuring Docker authentication..."
gcloud auth configure-docker

echo ""
echo "📤 Step 2: Pushing Docker image to GCR..."
docker push $IMAGE_NAME

echo ""
echo "🔐 Step 3: Make sure your .env file has all required variables"
echo "Required: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION, WEBHOOK_URL, MONGODB_URI, SUPABASE_URL, SUPABASE_KEY, ERROR_NOTIFICATION_BOT_TOKEN, ERROR_NOTIFICATION_CHAT_ID"
echo ""
read -p "Press Enter to continue with deployment..."

# Source environment variables from .env
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    echo "✅ Loaded environment variables from .env"
else
    echo "⚠️  .env file not found. You'll need to set environment variables manually."
fi

echo ""
echo "🚀 Step 4: Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_NAME \
  --region=$REGION \
  --platform=managed \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=3 \
  --timeout=900 \
  --port=8080 \
  --set-env-vars="TELEGRAM_API_ID=$TELEGRAM_API_ID,TELEGRAM_API_HASH=$TELEGRAM_API_HASH,TELEGRAM_SESSION=$TELEGRAM_SESSION,WEBHOOK_URL=$WEBHOOK_URL,MONGODB_URI=$MONGODB_URI,ERROR_NOTIFICATION_BOT_TOKEN=$ERROR_NOTIFICATION_BOT_TOKEN,ERROR_NOTIFICATION_CHAT_ID=$ERROR_NOTIFICATION_CHAT_ID,SUPABASE_URL=$SUPABASE_URL,SUPABASE_KEY=$SUPABASE_KEY" \
  --no-allow-unauthenticated

echo ""
echo "✅ Deployment complete!"
echo "📋 View logs: gcloud logs tail --follow --service=$SERVICE_NAME --region=$REGION"

