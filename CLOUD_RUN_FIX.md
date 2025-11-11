# 🔧 Cloud Run Port Issue - Troubleshooting Guide

## 🚨 **Problem**
```
ERROR: Revision 'telegram-listener-xxxxx' is not ready and cannot serve traffic. 
The user-provided container failed to start and listen on the port defined 
provided by the PORT=8080 environment variable within the allocated timeout.
```

## 🎯 **Root Cause**
Google Cloud Run expects all services to listen on an HTTP port (default: 8080), but your Telegram listener is a background service that connects to Telegram's API, not a web server.

## ✅ **Solution Applied**

I've fixed this by adding:

### 1. **Health Check Web Server**
- Added an `aiohttp` web server that listens on port 8080
- Provides health check endpoints: `/health`, `/ready`, `/`
- Reports Telegram client connection status

### 2. **Service Monitoring**
- Real-time connection monitoring
- Heartbeat checks every 30 seconds
- Status reporting for Cloud Run health checks

### 3. **Updated Configuration**
- Added proper port configuration
- Extended timeout to 900 seconds
- Set concurrency to 1 (appropriate for background service)

## 🚀 **Quick Fix - Run This Now**

```powershell
# Run the quick fix script
.\quick-fix.ps1
```

This will:
1. ✅ Build the updated container with health checks
2. ✅ Deploy with correct Cloud Run settings
3. ✅ Test the health endpoint
4. ✅ Show you the service status

## 🔍 **What Changed**

### **New Files/Updates:**
- `aiohttp` added to `requirements.txt`
- Health check endpoints in `telegram_listener.py`
- Updated `Dockerfile` with curl for health checks
- Fixed deployment scripts with correct parameters

### **New Endpoints Available:**
- `https://your-service-url/` - Service info
- `https://your-service-url/health` - Health status
- `https://your-service-url/ready` - Readiness check

## 🧪 **Testing**

After deployment, test the endpoints:

```bash
# Check if service is running
curl https://your-service-url/

# Check health status
curl https://your-service-url/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "telegram_connected": true,
  "uptime_seconds": 125.5,
  "last_heartbeat": "2024-01-15T14:30:25.123456",
  "timestamp": "2024-01-15T14:32:30.654321"
}
```

## 📊 **Monitoring**

### **View Real-time Logs:**
```bash
gcloud logs tail --follow --service=telegram-listener --project=YOUR_PROJECT
```

### **Check Service Status:**
```bash
gcloud run services describe telegram-listener --region=us-central1
```

### **Health Check in Console:**
Visit: Google Cloud Console > Cloud Run > telegram-listener > Logs

## ⚠️ **If Still Having Issues**

### **Common Problems:**

1. **Environment Variables Missing:**
   ```bash
   # Check if all env vars are set
   gcloud run services describe telegram-listener --region=us-central1 --format="export"
   ```

2. **Telegram Session Invalid:**
   - Regenerate your session file locally
   - Make sure it's included in the container build

3. **MongoDB Connection:**
   - Verify MongoDB URI is accessible from Google Cloud
   - Check firewall/network settings

4. **Memory/CPU Limits:**
   ```bash
   # Increase resources if needed
   gcloud run services update telegram-listener \
     --memory=1Gi \
     --cpu=2 \
     --region=us-central1
   ```

## 📈 **Performance Optimization**

### **Current Settings:**
- **Memory:** 512Mi (should be sufficient)
- **CPU:** 1 vCPU (appropriate for background service)
- **Timeout:** 900 seconds (15 minutes)
- **Concurrency:** 1 (prevents conflicts)

### **If You Need More Resources:**
```bash
gcloud run services update telegram-listener \
  --memory=1Gi \
  --cpu=2 \
  --timeout=1800 \
  --region=us-central1
```

## 🎉 **Success Indicators**

✅ **Service is healthy when:**
- Health endpoint returns HTTP 200
- `telegram_connected: true` in health response
- No error logs in Cloud Run console
- Your error notifications are working
- MongoDB operations are successful

## 🆘 **Need Help?**

If you're still experiencing issues:

1. **Run the logs command** to see real-time errors
2. **Check the health endpoint** to see connection status
3. **Verify all environment variables** are correctly set
4. **Test locally first** using Docker: `.\test-local.ps1`

The service should now start correctly and handle the Cloud Run port requirements while maintaining your Telegram listener functionality! 🚀
