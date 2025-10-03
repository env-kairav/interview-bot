from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
import asyncio
import json
import uuid
from datetime import datetime

load_dotenv()

DEFAULT_JOB_DESCRIPTION = os.getenv(
    "DEFAULT_JOB_DESCRIPTION", "Software Engineer focusing on backend Python services."
)
DEFAULT_EXPERIENCE_REQUIRED = os.getenv("DEFAULT_EXPERIENCE_REQUIRED", "3")
DEFAULT_CANDIDATE_NAME = os.getenv("DEFAULT_CANDIDATE_NAME", "Candidate")

app = FastAPI(title="Interview Bot WS")

DB_PATH = os.path.join(os.path.dirname(__file__), "interview_records.json")


def load_db() -> Dict[str, Any]:
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_db(db: Dict[str, Any]) -> None:
    tmp_path = DB_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, DB_PATH)


# Initialize OpenAI client only if API key is available
client = None
if os.getenv("OPENAI_API_KEY"):
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception as e:
        print(f"Warning: Failed to initialize OpenAI client: {e}")
        client = None


async def chat_completion(messages, temperature=0.3):
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    return await asyncio.to_thread(
        client.chat.completions.create,
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=temperature,
    )


# Initialize TTS only if available
piper_tts = None
try:
    from tts_piper import PiperTTS

    model_path = os.path.join(os.path.dirname(__file__), "en_US-amy-medium.onnx")
    if not os.path.isfile(model_path):
        alt_model_path = os.path.join(
            os.path.dirname(__file__), "voices", "en_US-amy-medium.onnx"
        )
        model_path = alt_model_path if os.path.isfile(alt_model_path) else None
    piper_tts = PiperTTS(voice=model_path or "en_US-amy-medium")
except Exception as e:
    print(f"Warning: Failed to initialize TTS: {e}")
    piper_tts = None


@app.get("/health", response_class=JSONResponse)
async def health_check():
    """Health check endpoint for container orchestration"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "interview-bot",
        "openai_configured": client is not None,
        "tts_configured": piper_tts is not None,
    }


@app.get("/", response_class=HTMLResponse)
async def main():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Interview Bot</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { padding: 20px; background: #f0f0f0; border-radius: 8px; margin: 20px 0; }
            .success { background: #d4edda; color: #155724; }
            .warning { background: #fff3cd; color: #856404; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 Interview Bot</h1>
            <div class="status success">
                <h3>✅ Server is running!</h3>
                <p>Your Interview Bot is successfully deployed and running.</p>
            </div>
            <div class="status warning">
                <h3>⚠️ Configuration Status</h3>
                <p>Check the <a href="/health">health endpoint</a> to see which features are configured.</p>
            </div>
            <h3>Available Endpoints:</h3>
            <ul>
                <li><a href="/health">Health Check</a> - System status</li>
                <li><a href="/wit">Wit.ai Console</a> - Speech recognition testing</li>
                <li><a href="/call-witai">Interview Interface</a> - Main application</li>
            </ul>
            <div class="status">
                <h3>🔧 WebSocket Fix Applied</h3>
                <p>WebSocket connections now automatically use WSS for HTTPS sites.</p>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/health/tts", response_class=JSONResponse)
async def tts_health():
    return {"ready": piper_tts is not None, "tts_available": piper_tts is not None}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
