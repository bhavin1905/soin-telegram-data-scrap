# Docker Image Build Script for Telegram Listener
# This script provides multiple ways to build the latest Docker image

param(
    [string]$Method = "local",
    [string]$Tag = "latest",
    [string]$ProjectId = "soinglobal-telegram"
)

Write-Host "🐳 Docker Image Build Script for Telegram Listener" -ForegroundColor Blue
Write-Host "Method: $Method | Tag: $Tag | Project: $ProjectId" -ForegroundColor Green

switch ($Method.ToLower()) {
    "local" {
        Write-Host "🏗️  Building Docker image locally..." -ForegroundColor Blue
        
        # Check if Docker is running
        try {
            docker version | Out-Null
            Write-Host "✅ Docker is running" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
            exit 1
        }
        
        # Build the image
        Write-Host "Building image with tag: telegram-listener:$Tag" -ForegroundColor Yellow
        docker build -t "telegram-listener:$Tag" .
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Local Docker image built successfully!" -ForegroundColor Green
            Write-Host "📋 To run the image locally:" -ForegroundColor Blue
            Write-Host "docker run -p 8080:8080 telegram-listener:$Tag" -ForegroundColor White
        } else {
            Write-Host "❌ Local Docker build failed!" -ForegroundColor Red
        }
    }
    
    "gcr" {
        Write-Host "🏗️  Building Docker image for Google Container Registry..." -ForegroundColor Blue
        
        # Check if gcloud is installed
        try {
            gcloud version | Out-Null
            Write-Host "✅ Google Cloud SDK is installed" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Google Cloud SDK is not installed. Please install it first." -ForegroundColor Red
            Write-Host "Visit: https://cloud.google.com/sdk/docs/install"
            exit 1
        }
        
        # Check authentication
        $authStatus = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
        if (-not $authStatus) {
            Write-Host "⚠️  You are not authenticated with Google Cloud" -ForegroundColor Yellow
            Write-Host "Running: gcloud auth login"
            gcloud auth login
        }
        
        # Configure Docker for GCR
        Write-Host "🔧 Configuring Docker for Google Container Registry..." -ForegroundColor Blue
        gcloud auth configure-docker
        
        # Build and tag for GCR
        Write-Host "Building image for GCR: gcr.io/$ProjectId/telegram-listener:$Tag" -ForegroundColor Yellow
        docker build -t "gcr.io/$ProjectId/telegram-listener:$Tag" .
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker image built successfully!" -ForegroundColor Green
            
            # Push to GCR
            Write-Host "📤 Pushing image to Google Container Registry..." -ForegroundColor Blue
            docker push "gcr.io/$ProjectId/telegram-listener:$Tag"
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Image pushed to GCR successfully!" -ForegroundColor Green
                Write-Host "🌐 Image URL: gcr.io/$ProjectId/telegram-listener:$Tag" -ForegroundColor Green
            } else {
                Write-Host "❌ Failed to push image to GCR!" -ForegroundColor Red
            }
        } else {
            Write-Host "❌ Docker build failed!" -ForegroundColor Red
        }
    }
    
    "cloudbuild" {
        Write-Host "🏗️  Building Docker image using Google Cloud Build..." -ForegroundColor Blue
        
        # Check if gcloud is installed
        try {
            gcloud version | Out-Null
            Write-Host "✅ Google Cloud SDK is installed" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Google Cloud SDK is not installed. Please install it first." -ForegroundColor Red
            exit 1
        }
        
        # Check authentication
        $authStatus = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
        if (-not $authStatus) {
            Write-Host "⚠️  You are not authenticated with Google Cloud" -ForegroundColor Yellow
            Write-Host "Running: gcloud auth login"
            gcloud auth login
        }
        
        # Enable required APIs
        Write-Host "🔧 Enabling required Google Cloud APIs..." -ForegroundColor Blue
        gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com --project=$ProjectId
        
        # Submit build
        Write-Host "🚀 Submitting build to Google Cloud Build..." -ForegroundColor Blue
        gcloud builds submit --config=cloudbuild.yaml --project=$ProjectId
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Cloud Build completed successfully!" -ForegroundColor Green
            Write-Host "🌐 Image URL: gcr.io/$ProjectId/telegram-listener:$Tag" -ForegroundColor Green
        } else {
            Write-Host "❌ Cloud Build failed!" -ForegroundColor Red
            Write-Host "📋 Check the build logs for more details" -ForegroundColor Yellow
        }
    }
    
    default {
        Write-Host "❌ Invalid method. Use: local, gcr, or cloudbuild" -ForegroundColor Red
        Write-Host "Usage examples:" -ForegroundColor Blue
        Write-Host "  .\build-docker-image.ps1 -Method local" -ForegroundColor White
        Write-Host "  .\build-docker-image.ps1 -Method gcr -Tag v1.0.0" -ForegroundColor White
        Write-Host "  .\build-docker-image.ps1 -Method cloudbuild" -ForegroundColor White
    }
}

Write-Host "🎉 Script completed!" -ForegroundColor Green
