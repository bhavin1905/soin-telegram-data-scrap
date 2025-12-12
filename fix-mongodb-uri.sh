#!/bin/bash
# Quick fix script to update MONGODB_URI in Cloud Run

PROJECT_ID="project-00bfaeaf-daab-4874-9bc"
SERVICE_NAME="telegram-userbot"
REGION="us-central1"

echo "🔧 Updating MONGODB_URI in Cloud Run service..."

# Check if .env file exists and has MONGODB_URI
if [ -f ".env" ]; then
    source .env
    if [ -z "$MONGODB_URI" ]; then
        echo "❌ MONGODB_URI not found in .env file"
        echo "Please add it to your .env file or provide it now:"
        read -p "Enter MONGODB_URI: " MONGODB_URI
    fi
else
    echo "⚠️  .env file not found"
    read -p "Enter MONGODB_URI: " MONGODB_URI
fi

# Get all current env vars
echo "📋 Getting current environment variables..."
CURRENT_ENV=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(spec.template.spec.containers[0].env)" --project=$PROJECT_ID 2>/dev/null)

# Update the service with MONGODB_URI
echo "🚀 Updating service with MONGODB_URI..."
gcloud run services update $SERVICE_NAME \
  --region=$REGION \
  --update-env-vars="MONGODB_URI=$MONGODB_URI" \
  --project=$PROJECT_ID

echo "✅ MONGODB_URI updated successfully!"
echo "🔄 The service will restart automatically with the new configuration."

