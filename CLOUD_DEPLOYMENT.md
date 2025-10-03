# ☁️ Cloud Deployment Guide

## 🚀 **Recommended Platforms for Interview Bot**

### **1. Railway (Easiest - Recommended)**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables
railway variables set OPENAI_API_KEY=your_key
railway variables set WITAI_TOKEN=your_token
```

**Pros:**
- ✅ Automatic deployments from Git
- ✅ Built-in health checks
- ✅ Easy environment variable management
- ✅ WebSocket support
- ✅ Free tier available

### **2. Render (Great for Python)**
1. Connect GitHub repo at https://render.com
2. Choose "Web Service"
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server_ws:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`

**Pros:**
- ✅ Free tier available
- ✅ Automatic SSL
- ✅ Easy GitHub integration
- ✅ WebSocket support

### **3. Heroku (Classic)**
```bash
# Install Heroku CLI
# Create app
heroku create your-interview-bot

# Set environment variables
heroku config:set OPENAI_API_KEY=your_key
heroku config:set WITAI_TOKEN=your_token

# Deploy
git push heroku main
```

**Pros:**
- ✅ Mature platform
- ✅ Great documentation
- ✅ Add-ons available
- ⚠️ Paid plans only (no free tier)

### **4. DigitalOcean App Platform**
1. Connect GitHub repo
2. Choose "Web Service"
3. Set environment variables
4. Deploy

**Pros:**
- ✅ Good performance
- ✅ Reasonable pricing
- ✅ WebSocket support

## 🔧 **Platform-Specific Setup**

### **For Railway:**
- Uses `railway.json` configuration
- Automatic Python detection
- Health check on `/health`

### **For Render:**
- Uses `Procfile` for start command
- Uses `runtime.txt` for Python version
- Health check on `/health`

### **For Heroku:**
- Uses `Procfile` for start command
- Uses `runtime.txt` for Python version
- Health check on `/health`

## 🚫 **Platforms That Won't Work**

### **Netlify**
- ❌ No WebSocket support
- ❌ No long-running processes
- ❌ No file system access
- ❌ Serverless functions only

### **Vercel**
- ❌ Limited WebSocket support
- ❌ Serverless functions only
- ❌ No persistent connections

### **AWS Lambda**
- ❌ No WebSocket support
- ❌ Execution time limits
- ❌ No persistent connections

## 🎯 **Quick Start with Railway (Recommended)**

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login to Railway
railway login

# 3. Initialize project
railway init

# 4. Set environment variables
railway variables set OPENAI_API_KEY=your_actual_key_here
railway variables set WITAI_TOKEN=your_actual_token_here

# 5. Deploy
railway up

# 6. Get your app URL
railway domain
```

## 🔧 **Environment Variables Setup**

All platforms need these environment variables:
```bash
OPENAI_API_KEY=your_openai_api_key_here
WITAI_TOKEN=your_witai_token_here
DEFAULT_JOB_DESCRIPTION=Software Engineer focusing on backend Python services.
DEFAULT_EXPERIENCE_REQUIRED=3
DEFAULT_CANDIDATE_NAME=Candidate
```

## 📊 **Platform Comparison**

| Platform | Free Tier | WebSocket | Ease | Cost |
|----------|-----------|-----------|------|------|
| Railway  | ✅ Yes    | ✅ Yes    | ⭐⭐⭐ | $5/month |
| Render   | ✅ Yes    | ✅ Yes    | ⭐⭐  | $7/month |
| Heroku   | ❌ No     | ✅ Yes    | ⭐⭐  | $7/month |
| DigitalOcean | ❌ No | ✅ Yes    | ⭐   | $5/month |

## 🚀 **Deployment Steps**

### **Step 1: Choose Your Platform**
- **Beginners**: Railway
- **Budget-conscious**: Render
- **Enterprise**: Heroku or DigitalOcean

### **Step 2: Prepare Your Code**
```bash
# Make sure you have these files:
# - requirements.txt ✅
# - Procfile ✅
# - runtime.txt ✅
# - railway.json ✅ (for Railway)
```

### **Step 3: Deploy**
Follow the platform-specific instructions above.

### **Step 4: Configure Environment Variables**
Set your API keys in the platform's dashboard.

### **Step 5: Test**
Visit your deployed app and test the health endpoint.

## 🔍 **Troubleshooting**

### **Common Issues:**
1. **WebSocket not working**: Check platform WebSocket support
2. **TTS not working**: Verify file system access
3. **Environment variables**: Check they're set correctly
4. **Health checks failing**: Verify `/health` endpoint

### **Debug Commands:**
```bash
# Check logs
railway logs
# or
heroku logs --tail
```

## 🎉 **Success!**

Once deployed, your Interview Bot will be available at your platform's URL:
- Railway: `https://your-app.railway.app`
- Render: `https://your-app.onrender.com`
- Heroku: `https://your-app.herokuapp.com`

Test the health endpoint: `https://your-app-url/health`
