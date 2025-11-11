# Telegram Listener with Error Notifications

This Telegram listener now includes comprehensive error handling and automatic error notifications via Telegram.

## 🚨 Error Notification Features

- **Real-time Error Alerts**: Get instant Telegram notifications when errors occur in production
- **Detailed Error Information**: Includes timestamp, error message, and stack traces
- **Multiple Error Types Covered**:
  - Critical application crashes
  - Message processing errors
  - Database connection issues
  - Webhook communication failures
  - Address processing errors

## 🔧 Setup Error Notifications

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Chat ID

#### Option A: Use the helper script
```bash
# Add your bot token to .env first
python get_chat_id.py
```

#### Option B: Manual method
1. Start a chat with your bot or add it to a group
2. Send any message to the bot/group
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id":123456789}` in the response

### 3. Configure Environment Variables

Add these to your `.env` file:

```env
# Error notification bot token (from BotFather)
ERROR_NOTIFICATION_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Chat ID where errors will be sent
ERROR_NOTIFICATION_CHAT_ID=-1001234567890
```

### 4. Test the Setup

You can test error notifications by temporarily adding this code to trigger an error:

```python
# Temporary test code - remove after testing
raise Exception("Test error notification")
```

## 📱 Error Notification Format

When an error occurs, you'll receive a message like:

```
🚨 **SERVER ERROR ALERT** 🚨

**Time:** 2024-01-15 14:30:25 UTC
**Error:** Critical Message Handler Error

**Details:**
```
Telegram Listener encountered a critical error: division by zero

Full traceback:
Traceback (most recent call last):
  File "telegram_listener.py", line 125, in handler
    result = 1/0
ZeroDivisionError: division by zero
```

⚠️ Please check the server logs for more information.
```

## 🛡️ Error Handling Levels

1. **Address Processing Errors**: Non-critical errors for individual addresses
2. **Webhook Errors**: Communication failures with your webhook endpoint
3. **Critical Handler Errors**: Serious errors that could crash the message handler
4. **Application Crashes**: Fatal errors that stop the entire application

## 🔍 Monitoring and Debugging

- Check your server logs for detailed error information
- Error notifications include timestamps for correlation
- Stack traces help identify the exact location of errors
- Rate limiting prevents notification spam

## 🚀 Production Deployment

1. Ensure all environment variables are properly set
2. Test error notifications in a staging environment first
3. Monitor the error notification chat for any issues
4. Set up log rotation and backup monitoring as well

## 📝 Optional: Enhanced Monitoring

For production environments, consider also setting up:

- Log aggregation (ELK stack, Grafana)
- Health check endpoints
- Uptime monitoring
- Database connection monitoring

The error notification system provides immediate alerts, while these tools offer deeper insights into application health.
