#!/usr/bin/env python3
"""
Text-to-Speech using Piper TTS with amy-medium voice.
"""

import os
import glob
import tempfile
import subprocess
import pygame
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PiperTTS:
    """Text-to-Speech using Piper TTS with amy-medium voice."""

    def __init__(self, voice: Optional[str] = None):
        """
        Initialize Piper TTS.

        Args:
            voice: Voice alias or full path to .onnx model. If None, tries:
                   1) env PIPER_MODEL_PATH
                   2) local voices/en_US-amy-medium.onnx
                   3) alias en_US-amy-medium (requires installed voice)
        """
        self.piper_path = self._find_piper()
        self._init_pygame()

        self.model_path, self.config_path, self.alias = self._resolve_model_paths(voice)
        if not self.model_path and not self.alias:
            # As a last resort, attempt to auto-download alias
            self.alias = "en_US-amy-medium"
            self._ensure_voice_available(self.alias)

    def _find_piper(self) -> str:
        """Find Piper TTS executable."""
        # Allow explicit override
        env_piper = os.getenv("PIPER_BIN")
        if env_piper and (os.path.exists(env_piper) or self._command_exists(env_piper)):
            logger.info(f"Using Piper from PIPER_BIN: {env_piper}")
            return env_piper

        # Try common locations
        possible_paths = [
            "piper",
            "/usr/local/bin/piper",
            "/opt/homebrew/bin/piper",
            os.path.expanduser("~/piper/piper/piper"),
            os.path.expanduser("~/piper/piper.exe"),
        ]

        for path in possible_paths:
            if os.path.exists(path) or self._command_exists(path):
                logger.info(f"Found Piper at: {path}")
                return path

        raise RuntimeError(
            "Piper TTS not found. Please install it from https://github.com/rhasspy/piper\n"
            "Or download the binary and place it in your PATH"
        )

    def _command_exists(self, command: str) -> bool:
        """Check if command exists in PATH."""
        try:
            subprocess.run([command, "--help"], capture_output=True, timeout=5)
            return True
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            subprocess.SubprocessError,
        ):
            return False

    def _init_pygame(self):
        """Initialize pygame mixer for audio playback."""
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            logger.info("Pygame mixer initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize pygame mixer: {e}")

    def _resolve_model_paths(
        self, voice: Optional[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Resolve model path, config path, or alias from input/env/common locations.
        Returns (model_path, config_path, alias)
        """
        # 1) Env overrides
        env_model = os.getenv("PIPER_MODEL_PATH")
        env_config = os.getenv("PIPER_CONFIG_PATH")
        if env_model and os.path.isfile(env_model):
            cfg = (
                env_config
                if env_config and os.path.isfile(env_config)
                else self._guess_config_from_model(env_model)
            )
            return env_model, cfg, None

        # 2) If voice is a path
        if voice and os.path.isfile(voice):
            return voice, self._guess_config_from_model(voice), None

        # 3) Look into voices directory
        voices_dir = os.getenv("PIPER_VOICES_DIR", os.path.join(os.getcwd(), "voices"))
        candidates = [
            os.path.join(voices_dir, "en_US-amy-medium.onnx"),
            os.path.join(voices_dir, "amy-medium.onnx"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c, self._guess_config_from_model(c), None

        # 4) Alias if provided
        if voice and not os.path.sep in voice:
            return None, None, voice

        # 5) Default alias
        return None, None, "en_US-amy-medium"

    def _guess_config_from_model(self, model_path: str) -> Optional[str]:
        base, _ = os.path.splitext(model_path)
        json_path = base + ".onnx.json"
        if os.path.isfile(json_path):
            return json_path
        # Some repos name the config ...-medium.onnx.json without double extension handling
        alt_json = base + ".json"
        if os.path.isfile(alt_json):
            return alt_json
        # Try glob in same dir
        for p in glob.glob(os.path.join(os.path.dirname(model_path), "*.json")):
            if "amy" in os.path.basename(p).lower():
                return p
        return None

    def _ensure_voice_available(self, alias: str) -> None:
        try:
            probe = subprocess.run(
                [self.piper_path, "--model", alias, "--help"],
                capture_output=True,
                text=True,
            )
            if probe.returncode == 0:
                return
        except Exception:
            pass

        try:
            logger.info(f"Attempting to download Piper voice: {alias}")
            subprocess.run(
                [
                    "python3",
                    "-m",
                    "piper.download_voices",
                    "--voice",
                    alias,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        except Exception as e:
            logger.warning(f"Could not auto-download Piper voice {alias}: {e}")

    def speak(self, text: str, blocking: bool = True) -> bool:
        """
        Convert text to speech and play it.

        Args:
            text: Text to convert to speech
            blocking: Whether to wait for speech to finish

        Returns:
            True if successful, False otherwise
        """
        if not text.strip():
            return False

        try:
            # Create temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name

            # Generate speech using Piper
            cmd = [self.piper_path]
            if self.model_path:
                cmd += ["--model", self.model_path]
                if self.config_path:
                    cmd += ["--config", self.config_path]
            else:
                cmd += ["--model", self.alias]
            cmd += ["--output_file", temp_path]

            logger.info(f"Generating speech for: {text[:50]}...")
            result = subprocess.run(
                cmd, input=text, text=True, capture_output=True, timeout=60
            )

            if result.returncode != 0:
                logger.error(f"Piper failed: {result.stderr}")
                return False

            # Play the generated audio
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                played = self._play_audio(temp_path, blocking)
                try:
                    os.unlink(temp_path)  # Clean up
                except Exception:
                    pass
                return played
            else:
                logger.error("Audio file not generated")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Piper TTS timed out")
            return False
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return False

    def synthesize_to_file(self, text: str) -> Optional[str]:
        """
        Generate speech to a WAV file and return the file path without playback.
        Caller is responsible for deleting the file after use.
        """
        if not text.strip():
            return None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            cmd = [self.piper_path]
            if self.model_path:
                cmd += ["--model", self.model_path]
                if self.config_path:
                    cmd += ["--config", self.config_path]
            else:
                cmd += ["--model", self.alias]
            cmd += ["--output_file", temp_path]
            result = subprocess.run(
                cmd, input=text, text=True, capture_output=True, timeout=60
            )
            if result.returncode != 0:
                logger.error(f"Piper failed: {result.stderr}")
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
                return None
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                return temp_path
            try:
                os.unlink(temp_path)
            except Exception:
                pass
            return None
        except Exception as e:
            logger.error(f"synthesize_to_file error: {e}")
            return None

    def _play_audio(self, file_path: str, blocking: bool = True) -> bool:
        """Play audio file using pygame."""
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            if blocking:
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
            return True
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
            return False

    def stop(self):
        """Stop current speech."""
        try:
            pygame.mixer.music.stop()
        except Exception as e:
            logger.warning(f"Error stopping speech: {e}")


def main():
    """Test the TTS functionality."""
    import sys

    text = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "Hello, this is a test of the text to speech system."
    )

    print(f"Speaking: {text}")

    try:
        # Allow passing a specific model path via env or default resolution
        tts = PiperTTS()
        success = tts.speak(text)
        if success:
            print("Speech completed successfully!")
        else:
            print("Speech failed!")
    except Exception as e:
        print(f"Error: {e}")
        print("\nTo install Piper TTS:")
        print("1. Download from: https://github.com/rhasspy/piper/releases")
        print("2. Ensure 'piper' is in PATH or use setup_piper.sh")
        print(
            "3. Place model in ./voices (e.g., voices/en_US-amy-medium.onnx) or set PIPER_MODEL_PATH"
        )


if __name__ == "__main__":
    main()
