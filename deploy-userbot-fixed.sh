#!/bin/bash
# Fixed deployment script that cleans environment variables

set -e

PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="telegram-userbot"
REGION="us-central1"

echo "🚀 Deploying telegram-userbot with cleaned environment variables..."

# Read .env file and handle multi-line values
# This handles cases where MONGODB_URI might be split across lines
if [ -f ".env" ]; then
    # Read .env file line by line and reconstruct MONGODB_URI if split
    MONGODB_URI_BUFFER=""
    IN_MONGODB_URI=false
    
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip comments and empty lines
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue
        
        # Check if this line starts MONGODB_URI
        if [[ "$line" =~ ^MONGODB_URI= ]]; then
            MONGODB_URI_BUFFER="${line#MONGODB_URI=}"
            IN_MONGODB_URI=true
        # Check if this is a continuation of MONGODB_URI (contains = but not a full VAR=value pattern)
        elif [[ "$IN_MONGODB_URI" == true ]] && [[ "$line" =~ = ]] && [[ ! "$line" =~ ^[A-Z_]+= ]]; then
            # Add as parameter to MONGODB_URI
            param="${line#*=}"
            param=$(echo "$param" | xargs)  # trim whitespace
            if [[ "$MONGODB_URI_BUFFER" != *"&"* ]] && [[ "$MONGODB_URI_BUFFER" != *"?"* ]]; then
                MONGODB_URI_BUFFER="${MONGODB_URI_BUFFER}?${param}"
            else
                MONGODB_URI_BUFFER="${MONGODB_URI_BUFFER}&${param}"
            fi
        # If we hit a new variable assignment, stop MONGODB_URI reconstruction
        elif [[ "$line" =~ ^[A-Z_]+= ]]; then
            IN_MONGODB_URI=false
            # Export other variables normally
            export "$line" 2>/dev/null || true
        fi
    done < .env
    
    # Set the reconstructed MONGODB_URI
    if [ -n "$MONGODB_URI_BUFFER" ]; then
        export MONGODB_URI="$MONGODB_URI_BUFFER"
    fi
else
    echo "❌ .env file not found"
    exit 1
fi

# Clean all environment variables (remove \r, \n, leading/trailing spaces)
TELEGRAM_API_ID=$(echo "$TELEGRAM_API_ID" | tr -d '\r\n' | xargs)
TELEGRAM_API_HASH=$(echo "$TELEGRAM_API_HASH" | tr -d '\r\n' | xargs)
TELEGRAM_SESSION=$(echo "$TELEGRAM_SESSION" | tr -d '\r\n' | xargs)
WEBHOOK_URL=$(echo "$WEBHOOK_URL" | tr -d '\r\n' | xargs)
MONGODB_URI=$(echo "$MONGODB_URI" | tr -d '\r\n' | xargs)
ERROR_NOTIFICATION_BOT_TOKEN=$(echo "$ERROR_NOTIFICATION_BOT_TOKEN" | tr -d '\r\n' | xargs)
ERROR_NOTIFICATION_CHAT_ID=$(echo "$ERROR_NOTIFICATION_CHAT_ID" | tr -d '\r\n' | xargs)
SUPABASE_URL=$(echo "$SUPABASE_URL" | tr -d '\r\n' | xargs)
SUPABASE_KEY=$(echo "$SUPABASE_KEY" | tr -d '\r\n' | xargs)

# Verify MONGODB_URI is set
if [ -z "$MONGODB_URI" ] || [ "$MONGODB_URI" = "" ]; then
    echo "❌ ERROR: MONGODB_URI is not set in .env file"
    echo "Please add MONGODB_URI to your .env file on a single line:"
    echo "MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority"
    exit 1
fi

echo "✅ Environment variables cleaned and verified"

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image=gcr.io/$PROJECT_ID/telegram-userbot:latest \
  --region=$REGION \
  --platform=managed \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=3 \
  --timeout=900 \
  --port=8080 \
  --set-env-vars="TELEGRAM_API_ID=$TELEGRAM_API_ID,TELEGRAM_API_HASH=$TELEGRAM_API_HASH,TELEGRAM_SESSION=$TELEGRAM_SESSION,WEBHOOK_URL=$WEBHOOK_URL,MONGODB_URI=$MONGODB_URI,ERROR_NOTIFICATION_BOT_TOKEN=$ERROR_NOTIFICATION_BOT_TOKEN,ERROR_NOTIFICATION_CHAT_ID=$ERROR_NOTIFICATION_CHAT_ID,SUPABASE_URL=$SUPABASE_URL,SUPABASE_KEY=$SUPABASE_KEY,PYTHONUNBUFFERED=1" \
  --no-allow-unauthenticated

echo "✅ Deployment complete!"

