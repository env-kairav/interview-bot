# 🔑 Get Your Wit.ai Token

## Step 1: Go to Wit.ai

1. Visit: https://wit.ai/apps
2. Sign in with your GitHub account

## Step 2: Create or Select an App

1. Click "Create new app" or select an existing app
2. Give it a name like "interview-bot"

## Step 3: Get Your Token

1. Go to Settings → API Details
2. Copy the "Server Access Token"
3. It will look like: `ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890`

## Step 4: Update .env File

```bash
# Edit the .env file
nano .env

# Replace this line:
WITAI_TOKEN=your_wit_ai_token_here

# With your actual token:
WITAI_TOKEN=ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890
```

## Step 5: Start the Application

```bash
./start.sh
```

## Alternative: Skip Wit.ai for Now

If you want to test without Wit.ai, you can temporarily comment out the Wit.ai check in the startup script.
