#!/bin/bash
# Testing script for telegram_userbot.py

echo "🧪 Testing Telegram Userbot"
echo "============================"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create a .env file with required variables:"
    echo "  - TELEGRAM_API_ID"
    echo "  - TELEGRAM_API_HASH"
    echo "  - TELEGRAM_SESSION"
    echo "  - MONGODB_URI"
    echo "  - WEBHOOK_URL"
    echo "  - SUPABASE_URL"
    echo "  - SUPABASE_KEY"
    exit 1
fi

echo "✅ .env file found"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated"
    echo "Activating virtual environment..."
    if [ -d "myenv" ]; then
        source myenv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Virtual environment 'myenv' not found"
        exit 1
    fi
else
    echo "✅ Virtual environment is active"
fi

echo ""
echo "📋 Checking required files..."
if [ ! -f "telegram_userbot.py" ]; then
    echo "❌ telegram_userbot.py not found!"
    exit 1
fi
echo "✅ telegram_userbot.py found"

if [ ! -f "app_config.py" ]; then
    echo "❌ app_config.py not found!"
    exit 1
fi
echo "✅ app_config.py found"

if [ ! -f "utils.py" ]; then
    echo "❌ utils.py not found!"
    exit 1
fi
echo "✅ utils.py found"

echo ""
echo "🔍 Checking environment variables..."
source .env

if [ -z "$TELEGRAM_API_ID" ]; then
    echo "⚠️  TELEGRAM_API_ID not set"
else
    echo "✅ TELEGRAM_API_ID is set"
fi

if [ -z "$TELEGRAM_API_HASH" ]; then
    echo "⚠️  TELEGRAM_API_HASH not set"
else
    echo "✅ TELEGRAM_API_HASH is set"
fi

if [ -z "$TELEGRAM_SESSION" ]; then
    echo "⚠️  TELEGRAM_SESSION not set"
else
    echo "✅ TELEGRAM_SESSION is set: $TELEGRAM_SESSION"
    if [ -f "${TELEGRAM_SESSION}.session" ]; then
        echo "✅ Session file exists: ${TELEGRAM_SESSION}.session"
    else
        echo "⚠️  Session file not found: ${TELEGRAM_SESSION}.session"
        echo "   You may need to create it first using create_production_session.py"
    fi
fi

if [ -z "$MONGODB_URI" ]; then
    echo "⚠️  MONGODB_URI not set"
else
    echo "✅ MONGODB_URI is set"
fi

echo ""
echo "🚀 Starting userbot..."
echo "Press Ctrl+C to stop"
echo ""

# Run the userbot
python3 telegram_userbot.py

