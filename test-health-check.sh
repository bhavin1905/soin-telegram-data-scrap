#!/bin/bash
# Test health check endpoints locally

echo "🏥 Testing Health Check Endpoints"
echo "=================================="
echo ""

# Check if userbot is running
echo "1. Make sure telegram_userbot.py is running in another terminal"
echo "   Run: python3 telegram_userbot.py"
echo ""
read -p "Press Enter when the userbot is running..."

echo ""
echo "2. Testing health check endpoints..."
echo ""

# Test root endpoint
echo "📋 Testing GET /"
curl -s http://localhost:8080/ | python3 -m json.tool
echo ""

# Test health endpoint
echo "📋 Testing GET /health"
curl -s http://localhost:8080/health | python3 -m json.tool
echo ""

# Test ready endpoint
echo "📋 Testing GET /ready"
curl -s http://localhost:8080/ready | python3 -m json.tool
echo ""

echo "✅ Health check tests completed!"
echo ""
echo "Expected responses:"
echo "  - Status 200: Service is healthy and Telegram is connected"
echo "  - Status 503: Service is unhealthy or Telegram is disconnected"

