# 🚀 Google Cloud Platform Deployment Guide

This guide will help you deploy your Telegram Listener service to Google Cloud Platform using Cloud Run.

## 📋 Prerequisites

1. **Google Cloud Account**: Sign up at [cloud.google.com](https://cloud.google.com)
2. **Google Cloud SDK**: Install from [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install)
3. **Docker** (optional, for local testing): Install from [docker.com](https://www.docker.com/get-started)
4. **Active MongoDB Database**: Make sure your MongoDB is accessible from the internet

## 🔧 Setup Steps

### 1. **Prepare Your Environment**

```bash
# Clone/navigate to your project directory
cd "telegram listner"

# Copy environment template
copy .env.example .env

# Edit .env with your actual values
notepad .env  # Windows
# or
nano .env     # Linux/Mac
```

### 2. **Google Cloud Setup**

```bash
# Install Google Cloud SDK (if not already installed)
# Follow instructions at: https://cloud.google.com/sdk/docs/install

# Authenticate with Google Cloud
gcloud auth login

# Create a new project (optional)
gcloud projects create telegram-listener-project --name="Telegram Listener"

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable billing for your project (required for Cloud Run)
# Go to: https://console.cloud.google.com/billing
```

### 3. **Deploy Using Scripts**

#### **Option A: PowerShell (Windows)**
```powershell
# Make sure you're in the project directory
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\deploy.ps1
```

#### **Option B: Bash (Linux/Mac/WSL)**
```bash
chmod +x deploy.sh
./deploy.sh
```

#### **Option C: Manual Deployment**
```bash
# Enable required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com

# Build and push container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/telegram-listener

# Deploy to Cloud Run
gcloud run deploy telegram-listener \
  --image gcr.io/YOUR_PROJECT_ID/telegram-listener \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 3 \
  --no-allow-unauthenticated
```

## 🔐 Environment Variables Setup

Your `.env` file should contain:

```env
# Telegram Configuration
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_SESSION=your_session_name

# Webhook Configuration  
WEBHOOK_URL=https://your-webhook-endpoint.com/webhook

# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database

# Error Notification Configuration
ERROR_NOTIFICATION_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
ERROR_NOTIFICATION_CHAT_ID=-1001234567890
```

## 📊 Monitoring and Logs

### **View Logs**
```bash
# Real-time logs
gcloud logs tail --follow --service=telegram-listener

# Specific time range
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=telegram-listener" --limit=50

# Error logs only
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=telegram-listener AND severity>=ERROR" --limit=20
```

### **Service Status**
```bash
# Check service status
gcloud run services describe telegram-listener --region=us-central1

# List all revisions
gcloud run revisions list --service=telegram-listener --region=us-central1
```

## 💰 Cost Optimization

Cloud Run pricing is based on:
- **CPU allocation**: $0.0000024 per vCPU-second
- **Memory allocation**: $0.0000025 per GiB-second  
- **Requests**: $0.0000004 per request

**Estimated monthly cost for your service:**
- Running 24/7 with 1 vCPU, 512MB RAM: ~$15-20/month
- With auto-scaling (average 50% usage): ~$8-12/month

### **Cost Optimization Tips:**
```bash
# Reduce memory if possible
--memory 256Mi

# Set aggressive scaling
--min-instances 0
--max-instances 2

# Optimize for cost
--cpu-throttling
```

## 🔧 Updating Your Service

### **Option 1: Rebuild and Deploy**
```bash
# PowerShell
.\deploy.ps1

# Bash
./deploy.sh
```

### **Option 2: Update Environment Variables Only**
```bash
gcloud run services update telegram-listener \
  --set-env-vars="NEW_VAR=value" \
  --region=us-central1
```

### **Option 3: Scale Resources**
```bash
gcloud run services update telegram-listener \
  --memory=1Gi \
  --cpu=2 \
  --region=us-central1
```

## 🛡️ Security Best Practices

1. **Use Secret Manager** for sensitive data:
```bash
# Store secrets
echo -n "your-secret-value" | gcloud secrets create telegram-api-hash --data-file=-

# Update service to use secrets
gcloud run services update telegram-listener \
  --set-secrets="TELEGRAM_API_HASH=telegram-api-hash:latest"
```

2. **Restrict access** (already configured):
```bash
--no-allow-unauthenticated
```

3. **Enable audit logging**:
```bash
gcloud logging sinks create telegram-listener-audit \
  bigquery.googleapis.com/projects/YOUR_PROJECT_ID/datasets/audit_logs \
  --log-filter='resource.type="cloud_run_revision"'
```

## 🔍 Troubleshooting

### **Common Issues:**

1. **Service won't start:**
```bash
# Check logs for errors
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=telegram-listener AND severity>=ERROR" --limit=10
```

2. **Environment variables not set:**
```bash
# Verify environment variables
gcloud run services describe telegram-listener --region=us-central1 --format="value(spec.template.spec.template.spec.containers[0].env[].name,spec.template.spec.template.spec.containers[0].env[].value)"
```

3. **MongoDB connection issues:**
```bash
# Test MongoDB connection
gcloud run jobs create test-mongo --image=gcr.io/YOUR_PROJECT_ID/telegram-listener --command="python" --args="-c,\"from config import test_collection; print('MongoDB connected successfully')\""
```

4. **Telegram session issues:**
   - Re-generate session file locally
   - Upload to Cloud Storage and mount as volume

## 📞 Support

If you encounter issues:

1. Check the [Cloud Run documentation](https://cloud.google.com/run/docs)
2. Review your logs using the commands above
3. Test locally first using Docker:
   ```bash
   docker-compose up
   ```
4. Ensure all environment variables are correctly set

## 🎉 Success!

Your Telegram Listener is now running on Google Cloud Run with:
- ✅ Automatic scaling
- ✅ Error notifications via Telegram
- ✅ MongoDB integration
- ✅ Container-based deployment
- ✅ Managed infrastructure
- ✅ Built-in monitoring and logging
