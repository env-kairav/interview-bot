#!/bin/bash

# Minimal startup script for testing deployment

echo "🚀 Starting Interview Bot (Minimal Mode)..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
echo "📋 Installing dependencies..."
pip install -r requirements.txt

# Start the server (no API key checks)
echo "🌟 Starting server on http://localhost:8000"
echo "   - Health check: http://localhost:8000/health"
echo "   - Note: Some features may be limited without API keys"
echo ""
echo "Press Ctrl+C to stop the server"

uvicorn server_ws:app --host 0.0.0.0 --port 8000
