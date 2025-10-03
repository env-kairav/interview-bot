#!/bin/bash

# Production startup script for Interview Bot (without Wit.ai requirement)

echo "🚀 Starting Interview Bot (without Wit.ai requirement)..."

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

# Check environment variables
echo "🔍 Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please run ./setup_env.sh first"
    exit 1
fi

# Check if OpenAI API key is configured
if grep -q "your_openai_api_key_here" .env; then
    echo "⚠️  Please configure your OpenAI API key in .env file"
    exit 1
fi

# Set up Piper TTS if not already done
if [ ! -f "~/piper/piper/piper" ]; then
    echo "🎤 Setting up Piper TTS..."
    chmod +x setup_piper.sh
    ./setup_piper.sh
fi

# Start the server
echo "🌟 Starting server on http://localhost:8000"
echo "   - Main app: http://localhost:8000"
echo "   - Health check: http://localhost:8000/health"
echo ""
echo "Note: Wit.ai features will be limited without proper token"
echo "Press Ctrl+C to stop the server"

uvicorn server_ws:app --host 0.0.0.0 --port 8000
