from typing import List, Dict, Any, Optional

import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from openai import OpenAI
import asyncio
import json
import uuid
from datetime import datetime
from tts_piper import PiperTTS

load_dotenv()

DEFAULT_JOB_DESCRIPTION = os.getenv(
    "DEFAULT_JOB_DESCRIPTION", "Software Engineer focusing on backend Python services."
)
DEFAULT_EXPERIENCE_REQUIRED = os.getenv("DEFAULT_EXPERIENCE_REQUIRED", "3")
DEFAULT_CANDIDATE_NAME = os.getenv("DEFAULT_CANDIDATE_NAME", "Candidate")


def build_system_prompt(job_desc: str, years_exp: str) -> str:
    return (
        "You are Interview Bot. Your job is to conduct a structured job interview.\n"
        f"Role: Interview candidates for this position: {job_desc}.\n"
        f"Target seniority: ~{years_exp} years of relevant experience.\n\n"
        "Rules:\n"
        "- Stay strictly in scope of the job description; do not answer unrelated questions.\n"
        "- Assess communication clarity and professionalism.\n"
        "- Ask short, focused questions one at a time.\n"
        "- Cover: brief background, relevant projects, core skills, problem-solving, and a quick scenario.\n"
        "- After a few questions, politely end the interview and thank the candidate.\n"
        "- Keep responses concise and conversational.\n"
    )


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


piper_tts: Optional[PiperTTS] = None


@app.on_event("startup")
async def _init_tts():
    global piper_tts
    try:
        # Prefer bundled model file to avoid relying on system voice alias
        model_path = os.path.join(os.path.dirname(__file__), "en_US-amy-medium.onnx")
        if not os.path.isfile(model_path):
            # Fallback to voices directory if present
            alt_model_path = os.path.join(
                os.path.dirname(__file__), "voices", "en_US-amy-medium.onnx"
            )
            model_path = alt_model_path if os.path.isfile(alt_model_path) else None
        piper_tts = PiperTTS(voice=model_path or "en_US-amy-medium")
    except Exception:
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


@app.get("/health/tts", response_class=JSONResponse)
async def tts_health():
    info: Dict[str, Any] = {"ready": False}
    try:
        info["PIPER_BIN"] = os.getenv("PIPER_BIN")
        info["PIPER_MODEL_PATH_env"] = os.getenv("PIPER_MODEL_PATH")
        info["PIPER_CONFIG_PATH_env"] = os.getenv("PIPER_CONFIG_PATH")
        info["cwd"] = os.getcwd()
        info["bundle_model_exists"] = os.path.isfile(
            os.path.join(os.path.dirname(__file__), "en_US-amy-medium.onnx")
        )
        info["voices_dir_model_exists"] = os.path.isfile(
            os.path.join(os.path.dirname(__file__), "voices", "en_US-amy-medium.onnx")
        )
        info["initialized"] = piper_tts is not None
        if piper_tts is not None:
            info["model_path"] = getattr(piper_tts, "model_path", None)
            info["config_path"] = getattr(piper_tts, "config_path", None)
            info["alias"] = getattr(piper_tts, "alias", None)
            info["ready"] = True
    except Exception as e:
        info["error"] = str(e)
    return info


@app.get("/tts")
async def tts_endpoint(text: str):
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    if piper_tts is None:
        raise HTTPException(status_code=503, detail="Piper TTS not available on server")
    path = await asyncio.to_thread(piper_tts.synthesize_to_file, text)
    if not path:
        raise HTTPException(status_code=500, detail="Failed to synthesize")

    def _iterfile():
        try:
            with open(path, "rb") as f:
                yield from f
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass

    return StreamingResponse(_iterfile(), media_type="audio/wav")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Allow overrides via query params from UI
    params = websocket.query_params
    job_desc = params.get("job") or DEFAULT_JOB_DESCRIPTION
    years_exp = params.get("exp") or DEFAULT_EXPERIENCE_REQUIRED
    candidate_name = params.get("name") or DEFAULT_CANDIDATE_NAME

    # Create interview record with UUID
    interview_id = str(uuid.uuid4())
    db = load_db()
    db[interview_id] = {
        "id": interview_id,
        "job_description": job_desc,
        "experience_required": years_exp,
        "candidate_name": candidate_name,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "messages": [],
        "transcript": None,
        "summary": None,
        "score": None,
    }
    save_db(db)

    system_prompt = build_system_prompt(job_desc, years_exp)
    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    conversation_log: List[Dict[str, str]] = []
    assistant_turns = 0
    max_assistant_turns = 30  # aim for ~15-20 questions before concluding
    ended = False

    greeting = f"Hi {candidate_name}, let's start the interview. Can you please introduce yourself?"
    await websocket.send_text(greeting)
    messages.append({"role": "assistant", "content": greeting})
    conversation_log.append({"speaker": "assistant", "text": greeting})

    # Inform client of interview id
    await websocket.send_text(f"[INTERVIEW_ID] {interview_id}")

    try:
        while True:
            user_text = await websocket.receive_text()
            if not user_text:
                await websocket.send_text("[error] Empty message")
                continue

            conversation_log.append({"speaker": "user", "text": user_text})
            messages.append({"role": "user", "content": user_text})

            if ended:
                await websocket.send_text("Interview already concluded.")
                continue

            try:
                resp = await chat_completion(messages, temperature=0.3)
                answer = resp.choices[0].message.content.strip()
            except Exception as e:
                answer = f"[error] OpenAI error: {e}"

            await websocket.send_text(answer)
            messages.append({"role": "assistant", "content": answer})
            conversation_log.append({"speaker": "assistant", "text": answer})
            assistant_turns += 1

            if assistant_turns >= max_assistant_turns:
                closing = (
                    "Thanks for participating in the interview. We will get back to you regarding the "
                    "next steps. Please keep an eye on your email for further instructions."
                )
                await websocket.send_text(closing)
                messages.append({"role": "assistant", "content": closing})
                conversation_log.append({"speaker": "assistant", "text": closing})
                ended = True

                try:
                    transcript = "\n".join(
                        [f"{t['speaker']}: {t['text']}" for t in conversation_log]
                    )
                    db = load_db()
                    if interview_id in db:
                        db[interview_id]["messages"] = conversation_log
                        db[interview_id]["transcript"] = transcript
                        db[interview_id]["updated_at"] = (
                            datetime.utcnow().isoformat() + "Z"
                        )
                        save_db(db)
                    await websocket.send_text("[INFO] Interview transcript saved.")
                    # Close the WebSocket after persisting transcript
                    try:
                        await websocket.close()
                    except Exception:
                        pass
                except Exception as e:
                    await websocket.send_text(f"[error] Failed to save transcript: {e}")
    except WebSocketDisconnect:
        # Persist whatever transcript exists on disconnect
        try:
            if conversation_log:
                transcript = "\n".join(
                    [f"{t['speaker']}: {t['text']}" for t in conversation_log]
                )
                db = load_db()
                # interview_id may not exist if disconnect before creation, guard it
                if "interview_id" in locals():
                    rec = db.get(interview_id) or {}
                    rec.update(
                        {
                            "id": interview_id,
                            "job_description": job_desc,
                            "experience_required": years_exp,
                            "candidate_name": candidate_name,
                            "messages": conversation_log,
                            "transcript": transcript,
                            "updated_at": datetime.utcnow().isoformat() + "Z",
                        }
                    )
                    db[interview_id] = rec
                    save_db(db)
        except Exception:
            # Silently ignore save errors on disconnect
            pass


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Interview Bot</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 0; background: #0f172a; color: #e2e8f0; }
    .container { max-width: 960px; margin: 0 auto; padding: 24px; }
    .card { background: #0b1220; border: 1px solid #1e293b; border-radius: 16px; padding: 24px; box-shadow: 0 10px 20px rgba(0,0,0,0.25); }
    .grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
    @media (min-width: 800px) { .grid { grid-template-columns: 1fr 1fr; } }
    label { display: block; font-size: 14px; color: #94a3b8; margin-bottom: 6px; }
    input, textarea { width: 100%; background: #0a0f1c; color: #e2e8f0; border: 1px solid #23324a; border-radius: 10px; padding: 12px 14px; outline: none; }
    textarea { min-height: 120px; resize: vertical; }
    input:focus, textarea:focus { border-color: #4f46e5; box-shadow: 0 0 0 3px rgba(79,70,229,0.25); }
    .btn { background: linear-gradient(135deg,#4f46e5,#7c3aed); color: white; border: 0; padding: 12px 16px; border-radius: 10px; cursor: pointer; font-weight: 600; }
    .btn:hover { filter: brightness(1.1); }
    .row { display: flex; gap: 12px; align-items: center; }
    .row .btn { flex: 1; }
    .header { text-align: center; margin-bottom: 20px; }
    .header h1 { font-size: 28px; margin: 0 0 8px; }
    .sub { color: #94a3b8; }
    .messages { height: 320px; overflow-y: auto; background: #0a0f1c; border: 1px solid #1e293b; border-radius: 12px; padding: 12px; }
    .message { padding: 8px 10px; border-radius: 8px; margin: 8px 0; }
    .user { background: #1e293b; }
    .assistant { background: #111827; border: 1px solid #374151; }
    .muted { color: #94a3b8; font-size: 12px; }
  </style>
</head>
<body>
  <div class=\"container\">
    <div class=\"header\">
      <h1>Voice Interview Bot</h1>
      <div class=\"sub\">Configure interview and speak. The bot will conduct a short interview and provide an evaluation.</div>
    </div>

    <div class=\"card\">
      <div class=\"grid\">
        <div>
          <label for=\"job\">Job Description</label>
          <textarea id=\"job\" placeholder=\"Frontend Engineer (React, TypeScript)\"></textarea>
        </div>
        <div>
          <label for=\"exp\">Years of Experience</label>
          <input id=\"exp\" type=\"number\" placeholder=\"5\" />
          <label for=\"name\" style=\"margin-top:12px\">Candidate Name</label>
          <input id=\"name\" type=\"text\" placeholder=\"John Doe\" />
        </div>
      </div>

      <div class=\"row\" style=\"margin-top:16px\">
        <button id=\"start\" class=\"btn\">Start Interview</button>
        <button id=\"stop\" class=\"btn\" style=\"background:#ef4444\">Stop</button>
      </div>

      <div style=\"margin-top:16px\">
        <div class=\"muted\">Conversation</div>
        <div id=\"messages\" class=\"messages\"></div>
      </div>
      <div class=\"muted\" style=\"margin-top:8px\">Mic is used locally in your browser; assistant audio uses Piper amy from server.</div>
    </div>
  </div>

  <script>
    const messagesEl = document.getElementById('messages');
    const startBtn = document.getElementById('start');
    const stopBtn = document.getElementById('stop');
    const jobEl = document.getElementById('job');
    const expEl = document.getElementById('exp');
    const nameEl = document.getElementById('name');

    // TTS toggle (server voice)
    const ttsToggle = document.createElement('label');
    ttsToggle.style.cssText = 'display:flex;align-items:center;gap:8px;margin:8px 0 0 0;font-size:12px;color:#94a3b8;';
    const ttsCheckbox = document.createElement('input');
    ttsCheckbox.type = 'checkbox';
    ttsCheckbox.checked = true;
    ttsToggle.appendChild(ttsCheckbox);
    ttsToggle.appendChild(document.createTextNode('Play assistant with Piper (server)'));
    document.querySelector('.card').insertBefore(ttsToggle, document.querySelector('.card').firstChild);

    let ws = null;
    let recognition = null;
    let listening = false;
    let interviewId = null;
    let assistantSpeaking = false;
    let currentAudio = null;

    function stopAssistantAudio() {
      try {
        if (currentAudio) { currentAudio.pause(); currentAudio.src = ''; currentAudio = null; }
      } catch (e) {}
      assistantSpeaking = false;
    }

    async function playServerVoice(text) {
      if (!ttsCheckbox.checked) return;
      stopAssistantAudio();
      const url = '/tts?text=' + encodeURIComponent(text);
      assistantSpeaking = true;
      try {
        const resp = await fetch(url);
        if (!resp.ok) {
          assistantSpeaking = false;
          addMessage('[tts error] ' + (await resp.text()), 'system');
          return;
        }
        const blob = await resp.blob();
        const blobUrl = URL.createObjectURL(blob);
        currentAudio = new Audio(blobUrl);
        currentAudio.onended = () => { assistantSpeaking = false; URL.revokeObjectURL(blobUrl); };
        currentAudio.onerror = () => { assistantSpeaking = false; URL.revokeObjectURL(blobUrl); };
        await currentAudio.play().catch(() => { assistantSpeaking = false; URL.revokeObjectURL(blobUrl); });
      } catch (_) {
        assistantSpeaking = false;
        addMessage('[tts error] failed to fetch audio', 'system');
      }
    }

    function addMessage(text, who) {
      const div = document.createElement('div');
      div.className = `message ${who}`;
      div.textContent = text;
      messagesEl.appendChild(div);
      messagesEl.scrollTop = messagesEl.scrollHeight;
      if (who === 'assistant') playServerVoice(text);
    }

    function connect() {
      const job = encodeURIComponent(jobEl.value.trim());
      const exp = encodeURIComponent(expEl.value.trim());
      const name = encodeURIComponent(nameEl.value.trim());
      const url = `ws://${location.host}/ws?job=${job}&exp=${exp}&name=${name}`;
      ws = new WebSocket(url);

      ws.onopen = () => { console.log('[connected] Waiting for greeting...'); };
      ws.onmessage = (ev) => {
        const text = ev.data;
        if (typeof text === 'string' && text.startsWith('[INTERVIEW_ID]')) {
          interviewId = text.replace('[INTERVIEW_ID]', '').trim();
          const note = document.createElement('div');
          note.className = 'muted';
          note.textContent = 'Interview ID: ' + interviewId;
          messagesEl.parentElement.appendChild(note);
          return;
        }
        if (typeof text === 'string' && text.startsWith('[INFO]')) {
          console.log(text);
          return;
        }
        // Stop recognition to avoid echo; it will auto-restart after onend
        try { if (recognition && listening) { recognition.stop(); listening = false; } } catch(e) {}
        addMessage(text, 'assistant');
      };
      ws.onclose = () => addMessage('[disconnected]', 'system');
      ws.onerror = (e) => addMessage('[error] ' + (e && e.message ? e.message : 'ws error'), 'system');
    }

    function startListening() {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR) {
        addMessage('[error] Browser SpeechRecognition not supported', 'system');
        return;
      }
      recognition = new SR();
      recognition.lang = 'en-US';
      recognition.interimResults = true; // needed for VAD-ish behavior
      recognition.continuous = true;
      recognition.onstart = () => { console.log('SR start - listening...'); };
      recognition.onresult = (e) => {
        // When interim results appear, consider it as user started speaking
        const res = e.results[e.resultIndex];
        if (res && res.isFinal) {
          const text = res[0].transcript;
          console.log('SR final:', text);
          if (text && text.trim()) {
            addMessage(text, 'user');
            if (ws && ws.readyState === WebSocket.OPEN) {
              ws.send(text);
            }
          }
        } else {
          // Interim speech detected -> barge-in: stop assistant audio
          if (assistantSpeaking) {
            console.log('Barge-in: user speaking, stopping assistant');
            stopAssistantAudio();
          }
        }
      };
      recognition.onend = () => {
        console.log('SR end - keep active');
        listening = false;
        // Keep running
        if (ws && ws.readyState === WebSocket.OPEN) {
          try { recognition.start(); listening = true; } catch(e) {}
        }
      };
      recognition.onerror = (ev) => { console.warn('SR error:', ev.error); listening = false; };
      recognition.start();
      listening = true;
    }

    startBtn.addEventListener('click', () => {
      if (!ws || ws.readyState !== WebSocket.OPEN) connect();
      // start listening immediately (no delay) and keep continuous
      startListening();
    });

    stopBtn.addEventListener('click', () => {
      if (recognition && listening) { try { recognition.stop(); } catch(e) {} }
      listening = false;
      if (ws) { ws.close(); ws = null; }
    });

    // Auto re-listen after each assistant response for hands-free flow
    const _origAddMessage = addMessage;
    addMessage = function(text, who) {
      _origAddMessage(text, who);
      if (who === 'assistant') {
        // Wait a bit before enabling next user turn
        setTimeout(() => {
          if (!listening) startListening();
        }, 500);
      }
    }
  </script>
  </body>
 </html>
"""


@app.get("/interviews/{interview_id}", response_class=JSONResponse)
async def get_interview(interview_id: str):
    db = load_db()
    item = db.get(interview_id)
    if not item:
        raise HTTPException(status_code=404, detail="Interview not found")
    return item


@app.get("/interviews/{interview_id}/summary", response_class=JSONResponse)
async def get_summary(interview_id: str):
    db = load_db()
    item = db.get(interview_id)
    if not item:
        raise HTTPException(status_code=404, detail="Interview not found")
    if item.get("summary"):
        return {"id": interview_id, "summary": item["summary"]}

    transcript = item.get("transcript")
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript not available yet")

    prompt = (
        "Summarize the following interview transcript in 5-8 concise bullet points focusing on the candidate's background, key skills, notable projects, and areas of concern.\n\n"
        + transcript
    )
    try:
        resp = await chat_completion(
            [
                {
                    "role": "system",
                    "content": "You are an expert technical interviewer and evaluator.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        summary = resp.choices[0].message.content.strip()
        item["summary"] = summary
        item["updated_at"] = datetime.utcnow().isoformat() + "Z"
        db[interview_id] = item
        save_db(db)
        return {"id": interview_id, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {e}")


@app.get("/interviews/{interview_id}/score", response_class=JSONResponse)
async def get_score(interview_id: str):
    db = load_db()
    item = db.get(interview_id)
    if not item:
        raise HTTPException(status_code=404, detail="Interview not found")

    # If breakdown already computed, return it
    if item.get("score_breakdown"):
        return {"id": interview_id, **item["score_breakdown"]}

    transcript = item.get("transcript")
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript not available yet")

    job_desc = item.get("job_description")
    years_exp = item.get("experience_required")

    schema_hint = (
        "Return ONLY valid minified JSON with this exact structure and keys, no prose, no markdown, no comments.\n"
        "{\n"
        '  "overall": { "value": <int 1-10>, "scale": 10 },\n'
        '  "communication": { "value": <int 1-10>, "scale": 10 },\n'
        '  "relevance": { "value": <int 1-10>, "scale": 10 },\n'
        '  "technical": { "value": <int 1-10>, "scale": 10 },\n'
        '  "confidence": { "value": <int 1-10>, "scale": 10 },\n'
        '  "next_steps": [ <short actionable suggestions as strings> ]\n'
        "}\n"
    )

    prompt = (
        "Score the candidate based on the transcript using a 1-10 scale for each category. Be fair and forgiving about minor transcription errors; focus on intent and content.\n"
        f"Role: {job_desc}\nTarget Experience: ~{years_exp} years\n\n"
        "Transcript (speaker: text):\n" + transcript + "\n\n" + schema_hint
    )

    try:
        resp = await chat_completion(
            [
                {
                    "role": "system",
                    "content": "You are a fair and pragmatic technical interviewer. Be forgiving about ASR/STT mistakes and focus on the candidate's likely intent. Always return strict JSON per the user's schema.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()

        # Parse and validate
        import json as _json

        def _parse_score(text: str):
            try:
                return _json.loads(text)
            except Exception:
                # Try to extract first JSON object
                import re

                m = re.search(r"\{[\s\S]*\}", text)
                if not m:
                    return None
                try:
                    return _json.loads(m.group(0))
                except Exception:
                    return None

        data = _parse_score(raw)
        if not isinstance(data, dict):
            raise ValueError("Model did not return JSON")

        def _norm_bucket(d, key):
            bucket = d.get(key) or {}
            val = bucket.get("value")
            scale = bucket.get("scale", 10)
            if not isinstance(val, int):
                if isinstance(val, str) and val.isdigit():
                    val = int(val)
            if not isinstance(val, int) or val < 1 or val > 10:
                raise ValueError(f"Invalid {key}.value: {val}")
            if scale != 10:
                scale = 10
            return {"value": val, "scale": scale}

        breakdown = {
            "overall": _norm_bucket(data, "overall"),
            "communication": _norm_bucket(data, "communication"),
            "relevance": _norm_bucket(data, "relevance"),
            "technical": _norm_bucket(data, "technical"),
            "confidence": _norm_bucket(data, "confidence"),
            "next_steps": data.get("next_steps") or [],
        }
        if not isinstance(breakdown["next_steps"], list):
            breakdown["next_steps"] = []

        # Persist breakdown and simple score for compatibility
        item["score_breakdown"] = breakdown
        item["score"] = breakdown["overall"]["value"]
        item["updated_at"] = datetime.utcnow().isoformat() + "Z"
        db[interview_id] = item
        save_db(db)

        return {"id": interview_id, **breakdown}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate score breakdown: {e}"
        )


@app.get("/interviews/{interview_id}/score_simple", response_class=JSONResponse)
async def get_score_simple(interview_id: str):
    db = load_db()
    item = db.get(interview_id)
    if not item:
        raise HTTPException(status_code=404, detail="Interview not found")
    if item.get("score") is not None:
        return {"id": interview_id, "score": item["score"], "scale": 10}
    # compute via the breakdown endpoint and then return
    await get_score(interview_id)
    item = load_db().get(interview_id) or {}
    return {"id": interview_id, "score": item.get("score"), "scale": 10}
