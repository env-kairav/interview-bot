# 🚀 Interview Bot Deployment Guide

This guide covers multiple deployment options for the Interview Bot application.

## 📋 Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- OpenAI API key
- Wit.ai API token

## 🔧 Local Development Deployment

### Quick Start

```bash
# 1. Clone and navigate to the project
cd final_working_bot

# 2. Set up environment
chmod +x setup_env.sh
./setup_env.sh

# 3. Configure API keys in .env file
# Edit .env and add your actual API keys:
# OPENAI_API_KEY=your_actual_openai_key
# WITAI_TOKEN=your_actual_witai_token

# 4. Start the application
chmod +x start.sh
./start.sh
```

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up TTS
chmod +x setup_piper.sh
./setup_piper.sh

# Start server
uvicorn server_ws:app --host 0.0.0.0 --port 8000
```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# 1. Create .env file with your API keys
cp .env.example .env
# Edit .env with your actual API keys

# 2. Start the application
docker-compose up -d

# 3. Check logs
docker-compose logs -f
```

### Using Docker directly

```bash
# Build the image
docker build -t interview-bot .

# Run the container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e WITAI_TOKEN=your_token \
  interview-bot
```

## ☁️ Cloud Deployment Options

### AWS ECS/Fargate

1. Build and push Docker image to ECR
2. Create ECS task definition
3. Configure environment variables
4. Set up load balancer

### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/interview-bot
gcloud run deploy --image gcr.io/PROJECT_ID/interview-bot --platform managed
```

### Azure Container Instances

```bash
# Deploy to Azure
az container create \
  --resource-group myResourceGroup \
  --name interview-bot \
  --image your-registry/interview-bot \
  --ports 8000
```

### Heroku

```bash
# Create Procfile
echo "web: uvicorn server_ws:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku create your-app-name
git push heroku main
```

## 🔧 Environment Configuration

### Required Environment Variables

```bash
OPENAI_API_KEY=your_openai_api_key_here
WITAI_TOKEN=your_wit_ai_token_here
```

### Optional Environment Variables

```bash
DEFAULT_JOB_DESCRIPTION=Software Engineer focusing on backend Python services.
DEFAULT_EXPERIENCE_REQUIRED=3
DEFAULT_CANDIDATE_NAME=Candidate
```

## 📊 Monitoring and Health Checks

### Health Endpoints

- `GET /health` - Basic health check
- `GET /health/tts` - TTS system health check

### Logging

The application logs to stdout. For production, consider:

- Structured logging with JSON format
- Log aggregation (ELK stack, Fluentd)
- Monitoring with Prometheus/Grafana

## 🔒 Security Considerations

### API Key Management

- Never commit API keys to version control
- Use environment variables or secret management services
- Rotate keys regularly

### Network Security

- Use HTTPS in production
- Configure proper CORS settings
- Implement rate limiting
- Use a reverse proxy (nginx) for additional security

### Container Security

- Use non-root user in containers
- Keep base images updated
- Scan for vulnerabilities
- Use minimal base images

## 📈 Performance Optimization

### Production Settings

```bash
# Use production ASGI server
pip install gunicorn
gunicorn server_ws:app -w 4 -k uvicorn.workers.UvicornWorker

# Or with uvicorn workers
uvicorn server_ws:app --workers 4 --host 0.0.0.0 --port 8000
```

### Resource Limits

```yaml
# docker-compose.yml
services:
  interview-bot:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
```

## 🚨 Troubleshooting

### Common Issues

1. **TTS not working**

   - Check Piper installation
   - Verify voice model files
   - Check `/health/tts` endpoint

2. **WebSocket connection issues**

   - Verify CORS settings
   - Check firewall rules
   - Ensure WebSocket support in proxy

3. **API key errors**
   - Verify environment variables
   - Check API key validity
   - Ensure proper permissions

### Debug Commands

```bash
# Check application logs
docker-compose logs interview-bot

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/tts

# Check environment variables
docker-compose exec interview-bot env
```

## 📝 Production Checklist

- [ ] API keys configured and secure
- [ ] HTTPS enabled
- [ ] Health checks configured
- [ ] Logging and monitoring set up
- [ ] Backup strategy for interview data
- [ ] Performance testing completed
- [ ] Security scan passed
- [ ] Documentation updated

## 🔄 Updates and Maintenance

### Rolling Updates

```bash
# Update with zero downtime
docker-compose up -d --no-deps interview-bot
```

### Backup Strategy

- Regular backups of `interview_records.json`
- Database snapshots if using external storage
- Configuration backups

## 📞 Support

For deployment issues:

1. Check the logs first
2. Verify environment configuration
3. Test health endpoints
4. Review this documentation

## 🎯 Next Steps

After successful deployment:

1. Set up monitoring and alerting
2. Configure automated backups
3. Implement CI/CD pipeline
4. Set up staging environment
5. Plan for scaling
