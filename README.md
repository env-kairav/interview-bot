# 🎤 Interview Bot - AI-Powered Voice Assistant

A sophisticated interview bot with real-time speech recognition using Wit.ai and text-to-speech using Piper TTS.

## ✨ Features

- **Real-time Speech Recognition**: Powered by Wit.ai for accurate transcription
- **Text-to-Speech**: High-quality voice synthesis using Piper TTS with Amy voice
- **WebSocket Communication**: Real-time bidirectional audio streaming
- **Interview Management**: Structured interview sessions with conversation logging
- **Multiple Interfaces**: Web-based UI with different interaction modes

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
```bash
chmod +x setup_env.sh
./setup_env.sh
```

### 3. Set Up TTS (Optional)
```bash
chmod +x setup_piper.sh
./setup_piper.sh
```

### 4. Start the Server
```bash
uvicorn server_ws:app --reload
```

### 5. Open in Browser
- **Main App**: http://127.0.0.1:8000
- **Wit.ai Console**: http://127.0.0.1:8000/wit
- **Wit.ai Call**: http://127.0.0.1:8000/call-witai

## 🔧 Configuration

### Environment Variables
Create a `.env` file with:
```bash
OPENAI_API_KEY=your_openai_api_key
WITAI_TOKEN=your_witai_token
```

### TTS Setup
The bot uses Piper TTS with the Amy voice model. Voice files are located in the `voices/` directory.

## 📁 Project Structure

```
call-agent/
├── server_ws.py              # Main FastAPI server
├── tts_piper.py              # TTS module with Piper integration
├── speech_to_text.py          # Legacy STT implementation
├── requirements.txt           # Python dependencies
├── setup_env.sh              # Environment setup script
├── setup_piper.sh            # TTS setup script
├── interview_records.json     # Conversation data
├── voices/                   # TTS voice models
├── vosk-model-small-en-us-0.15/  # Legacy STT model
└── Handy-main/               # Tauri desktop app
```

## 🎯 Usage

### Main Interview Interface
1. Open http://127.0.0.1:8000
2. Fill in job description, experience level, and candidate name
3. Click "Start Interview"
4. Use microphone to speak with the AI interviewer
5. The bot will respond with voice and text

### Wit.ai Console
- Test speech recognition directly
- Debug transcription issues
- View raw Wit.ai responses

### Wit.ai Call Interface
- Dedicated interface for Wit.ai transcription
- Optimized for voice conversations

## 🔧 Technical Details

### Speech Recognition
- **Primary**: Wit.ai server-side STT
- **Fallback**: Browser SpeechRecognition API
- **Format**: WebM → WAV conversion for Wit.ai compatibility

### Text-to-Speech
- **Engine**: Piper TTS
- **Voice**: Amy (en_US-amy-medium)
- **Format**: WAV audio output

### Audio Processing
- **Input**: WebM/Opus from browser
- **Processing**: Server-side conversion to WAV
- **Output**: WAV audio for TTS

## 🛠️ Development

### Server Endpoints
- `GET /` - Main interview interface
- `GET /wit` - Wit.ai console
- `GET /call-witai` - Wit.ai call interface
- `POST /transcribe` - Speech-to-text endpoint
- `GET /tts` - Text-to-speech endpoint
- `WebSocket /ws` - Main interview WebSocket
- `WebSocket /ws-witai` - Wit.ai WebSocket

### Key Components
- **FastAPI**: Web framework
- **WebSockets**: Real-time communication
- **Wit.ai**: Speech recognition
- **Piper TTS**: Text-to-speech
- **OpenAI**: Chat completion

## 📝 License

This project is for educational and development purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!
