# Testing Guide for Telegram Userbot

This guide will help you test the `telegram_userbot.py` before deploying to Cloud Run.

## Prerequisites

1. **Environment Variables**: Make sure your `.env` file has all required variables:
   ```env
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_SESSION=your_session_name
   MONGODB_URI=your_mongodb_uri
   WEBHOOK_URL=your_webhook_url
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ERROR_NOTIFICATION_BOT_TOKEN=your_bot_token
   ERROR_NOTIFICATION_CHAT_ID=your_chat_id
   ```

2. **Session File**: You need a valid Telegram session file
   - If you don't have one, create it using: `python3 create_production_session.py`
   - The session file should be named: `{TELEGRAM_SESSION}.session`

## Testing Methods

### Method 1: Quick Test Script (Recommended)

```bash
./test-userbot.sh
```

This script will:
- Check if all required files exist
- Verify environment variables
- Check if session file exists
- Start the userbot

### Method 2: Manual Testing

1. **Activate virtual environment**:
   ```bash
   source myenv/bin/activate
   ```

2. **Run the userbot**:
   ```bash
   python3 telegram_userbot.py
   ```

3. **Expected output**:
   ```
   DEBUG ENV VARIABLES:
   TELEGRAM_API_ID: your_api_id
   TELEGRAM_API_HASH: your_api_hash
   TELEGRAM_SESSION: your_session_name
   🚀 Starting Telegram Userbot service...
   🏥 Health check server started on port 8080
   🚀 Telegram client connected successfully
   🚀 Telegram userbot started and healthy...
   ```

## Testing Health Check Endpoints

### Option 1: Using the test script

In a **new terminal** (while userbot is running):
```bash
./test-health-check.sh
```

### Option 2: Manual testing with curl

1. **Test root endpoint**:
   ```bash
   curl http://localhost:8080/
   ```

2. **Test health endpoint**:
   ```bash
   curl http://localhost:8080/health
   ```

3. **Test ready endpoint**:
   ```bash
   curl http://localhost:8080/ready
   ```

### Expected Health Check Response

**When healthy** (Status 200):
```json
{
  "status": "healthy",
  "telegram_connected": true,
  "uptime_seconds": 123.45,
  "last_heartbeat": "2025-12-09T14:30:00.000000",
  "timestamp": "2025-12-09T14:30:15.000000"
}
```

**When unhealthy** (Status 503):
```json
{
  "status": "unhealthy",
  "telegram_connected": false,
  "uptime_seconds": 123.45,
  "last_heartbeat": null,
  "timestamp": "2025-12-09T14:30:15.000000"
}
```

## Testing Message Processing

1. **Add the userbot to a Telegram group/channel**
2. **Send a message with a contract address** (e.g., Ethereum: `0x1234...`, Solana: `ABC123...`)
3. **Check the logs** for:
   - Address detection
   - Dexscreener data fetching
   - Database insertion
   - Webhook notification

### Example Test Message

```
Check out this token: 0x1234567890123456789012345678901234567890
```

## Testing Webhook

1. **Set up a test webhook URL** (e.g., using webhook.site or ngrok)
2. **Send a message with contract address**
3. **Check webhook endpoint** for the payload

Expected webhook payload:
```json
{
  "channel": "Group Name",
  "message": "Message text with contract address",
  "contracts": [{"address": "0x1234..."}],
  "username": "username",
  "timestamp": "2025-12-09T14:30:00",
  "message_link": "https://t.me/...",
  "dexscreener_data": [...]
}
```

## Common Issues and Solutions

### Issue 1: "Session file not found"
**Solution**: Create session file using `python3 create_production_session.py`

### Issue 2: "MONGODB_URI is empty"
**Solution**: Add `MONGODB_URI` to your `.env` file

### Issue 3: "Telegram client not connecting"
**Solution**: 
- Check API credentials
- Verify session file exists and is valid
- Check internet connection

### Issue 4: "Health check returns 503"
**Solution**: 
- Wait a few seconds for Telegram to connect
- Check logs for connection errors
- Verify API credentials

## Testing Before Cloud Run Deployment

1. **Test locally first** using the methods above
2. **Verify all endpoints work** (/, /health, /ready)
3. **Test message processing** with real contract addresses
4. **Check database inserts** are working
5. **Verify webhook** is sending data correctly

Once all tests pass locally, you're ready to deploy to Cloud Run!

## Quick Test Checklist

- [ ] Environment variables set in `.env`
- [ ] Session file exists and is valid
- [ ] Userbot starts without errors
- [ ] Health check endpoints return 200
- [ ] Telegram client connects successfully
- [ ] Message with contract address is processed
- [ ] Data is saved to MongoDB
- [ ] Webhook receives payload (if configured)

