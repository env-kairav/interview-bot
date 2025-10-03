#!/bin/bash

echo "Setting up environment for Interview Bot with Wit.ai..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << 'ENVEOF'
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Wit.ai API Token
WITAI_TOKEN=your_wit_ai_token_here

# Optional: Default interview settings
DEFAULT_JOB_DESCRIPTION=Software Engineer focusing on backend Python services.
DEFAULT_EXPERIENCE_REQUIRED=3
DEFAULT_CANDIDATE_NAME=Candidate
ENVEOF
    echo "✅ Created .env file"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "📝 Next steps:"
echo "1. Edit .env file and add your actual API keys:"
echo "   - Get OpenAI API key from: https://platform.openai.com/api-keys"
echo "   - Get Wit.ai token from: https://wit.ai/apps"
echo ""
echo "2. Install dependencies:"
echo "   pip install -r requirements.txt"
echo ""
echo "3. Start the server:"
echo "   uvicorn server_ws:app --reload"
echo ""
echo "4. Open in browser:"
echo "   - Main app: http://localhost:8000"
echo "   - Wit.ai console: http://localhost:8000/wit"
echo "   - Live streaming: http://localhost:8000/live"
