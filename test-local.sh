#!/bin/bash

# Quick local test script for Docker deployment
echo "🧪 Testing Telegram Listener locally with Docker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with your configuration."
    echo "Copy .env.example to .env and fill in your values."
    exit 1
fi

echo "🏗️  Building Docker image..."
docker build -t telegram-listener:test .

echo "🚀 Running container locally..."
docker run --rm -it \
  --env-file .env \
  --name telegram-listener-test \
  telegram-listener:test

echo "✅ Local test completed!"
