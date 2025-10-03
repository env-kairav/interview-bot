#!/usr/bin/env python3
"""
Fix TTS endpoint to use synthesize_to_file method correctly
"""

# Read the current server file
with open('server_ws.py', 'r') as f:
    content = f.read()

# Find and replace the TTS endpoint with the correct implementation
old_tts = '''@app.get("/tts")
async def tts_endpoint(text: str):
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    if piper_tts is None:
        raise HTTPException(status_code=503, detail="Piper TTS not available on server")

    import tempfile
    import os

    def _synthesize_to_temp_file() -> str:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = tmp.name
        ok = piper_tts.synthesize(text, output_path)
        if not ok:
            try:
                os.unlink(output_path)
            except Exception:
                pass
            raise RuntimeError("Piper synthesis failed")
        return output_path

    try:
        path = await asyncio.to_thread(_synthesize_to_temp_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to synthesize: {e}")

    def _iterfile():
        try:
            with open(path, "rb") as f:
                yield from f
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass

    return StreamingResponse(_iterfile(), media_type="audio/wav")'''

new_tts = '''@app.get("/tts")
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

    return StreamingResponse(_iterfile(), media_type="audio/wav")'''

# Replace the old TTS endpoint
content = content.replace(old_tts, new_tts)

# Write back
with open('server_ws.py', 'w') as f:
    f.write(content)

print("✅ Fixed TTS endpoint to use synthesize_to_file correctly")
