# ⚡ Quick Start Guide

## 🚀 Deploy in 3 Steps

### 1. Configure API Keys

```bash
# Edit .env file
nano .env

# Add your actual API keys:
OPENAI_API_KEY=your_actual_openai_key_here
WITAI_TOKEN=your_actual_witai_token_here
```

### 2. Start the Application

```bash
# Option A: Use startup script (recommended)
./start.sh

# Option B: Manual start
source venv/bin/activate
uvicorn server_ws:app --host 0.0.0.0 --port 8000
```

### 3. Open in Browser

- **Main App**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

## 🐳 Docker Deployment

```bash
# Quick Docker start
docker-compose up -d

# Check logs
docker-compose logs -f
```

## 🔧 Troubleshooting

### API Keys Not Working

```bash
# Check if keys are set
grep -E "(OPENAI_API_KEY|WITAI_TOKEN)" .env
```

### TTS Issues

```bash
# Test TTS health
curl http://localhost:8000/health/tts
```

### Port Already in Use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

## 📞 Need Help?

- Check `DEPLOYMENT.md` for detailed instructions
- Verify API keys are correct
- Ensure all dependencies are installed
- Check health endpoints for system status
