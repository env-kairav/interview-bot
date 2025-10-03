#!/bin/bash
# Setup script for Piper TTS with amy-medium voice

echo "Setting up Piper TTS with amy-medium voice..."

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

echo "Detected OS: $OS"

# Create piper directory
mkdir -p ~/piper
cd ~/piper

# Download Piper binary
echo "Downloading Piper binary..."
if [ "$OS" == "macos" ]; then
    curl -L -o piper.tar.gz "https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz"
elif [ "$OS" == "linux" ]; then
    curl -L -o piper.tar.gz "https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz"
fi

# Extract
tar -xzf piper.tar.gz
chmod +x piper/piper
rm piper.tar.gz

# Download amy-medium voice
echo "Downloading amy-medium voice model..."
cd piper
curl -L -o amy-medium.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx"
curl -L -o amy-medium.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json"

echo "Setup complete!"
echo "Piper installed at: ~/piper/piper/piper"
echo "Voice model: ~/piper/piper/amy-medium.onnx"
echo ""
echo "To test:"
echo "  ~/piper/piper/piper --model amy-medium --output_file test.wav"
echo "  echo 'Hello world' | ~/piper/piper/piper --model amy-medium --output_file test.wav"
