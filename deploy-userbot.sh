#!/bin/bash

# Google Cloud Platform Deployment Script for Telegram Userbot
# This script automates the deployment process to Google Cloud Run

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="telegram-userbot"
REGION="us-central1"
MEMORY="512Mi"
CPU="1"
MIN_INSTANCES="1"
MAX_INSTANCES="3"

echo -e "${BLUE}🚀 Starting Google Cloud deployment for Telegram Userbot${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud SDK is not installed. Please install it first.${NC}"
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}⚠️  You are not authenticated with Google Cloud${NC}"
    echo "Running: gcloud auth login"
    gcloud auth login
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}⚠️  No project selected${NC}"
    echo "Available projects:"
    gcloud projects list
    echo ""
    read -p "Enter your project ID: " PROJECT_ID
    gcloud config set project $PROJECT_ID
fi

echo -e "${GREEN}✅ Using project: $PROJECT_ID${NC}"

# Enable required APIs
echo -e "${BLUE}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    --project=$PROJECT_ID

# Build and deploy using Cloud Build
echo -e "${BLUE}🏗️  Building and deploying with Cloud Build...${NC}"
gcloud builds submit \
    --config=cloudbuild-userbot.yaml \
    --project=$PROJECT_ID

# Set environment variables
echo -e "${BLUE}🔐 Setting environment variables...${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found. Please create it with your configuration.${NC}"
    echo "Copy .env.example to .env and fill in your values."
    exit 1
fi

# Source environment variables
set -a  # automatically export all variables
source .env
set +a

# Deploy to Cloud Run with environment variables
echo -e "${BLUE}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image=gcr.io/$PROJECT_ID/telegram-userbot:latest \
    --region=$REGION \
    --platform=managed \
    --memory=$MEMORY \
    --cpu=$CPU \
    --min-instances=$MIN_INSTANCES \
    --max-instances=$MAX_INSTANCES \
    --set-env-vars="TELEGRAM_API_ID=$TELEGRAM_API_ID,TELEGRAM_API_HASH=$TELEGRAM_API_HASH,TELEGRAM_SESSION=$TELEGRAM_SESSION,WEBHOOK_URL=$WEBHOOK_URL,MONGODB_URI=$MONGODB_URI,ERROR_NOTIFICATION_BOT_TOKEN=$ERROR_NOTIFICATION_BOT_TOKEN,ERROR_NOTIFICATION_CHAT_ID=$ERROR_NOTIFICATION_CHAT_ID,SUPABASE_URL=$SUPABASE_URL,SUPABASE_KEY=$SUPABASE_KEY" \
    --no-allow-unauthenticated \
    --project=$PROJECT_ID

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)
echo -e "${GREEN}🌐 Service URL: $SERVICE_URL${NC}"

# Show logs command
echo -e "${BLUE}📋 To view logs, run:${NC}"
echo "gcloud logs tail --follow --format=json --service=$SERVICE_NAME --project=$PROJECT_ID"

echo -e "${BLUE}📋 To update the service, run:${NC}"
echo "./deploy-userbot.sh"

echo -e "${GREEN}🎉 Telegram Userbot is now running on Google Cloud Run!${NC}"

