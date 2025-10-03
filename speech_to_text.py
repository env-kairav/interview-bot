import speech_recognition as sr
import pyaudio
import time
import os
from typing import Optional, List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechToText:
    """
    A comprehensive speech-to-text class using multiple recognition backends.
    """
    
    def __init__(self, 
                 default_backend: str = "google",
                 timeout: int = 15,
                 phrase_time_limit: Optional[int] = None,
                 energy_threshold: int = 300,
                 dynamic_energy_threshold: bool = True):
        """
        Initialize the SpeechToText recognizer.
        
        Args:
            default_backend: Default recognition backend ('google', 'sphinx', 'azure', 'bing')
            timeout: Timeout for listening in seconds
            phrase_time_limit: Maximum time to wait for speech
            energy_threshold: Energy level for speech detection
            dynamic_energy_threshold: Whether to adjust energy threshold dynamically
        """
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Configure recognizer settings
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.dynamic_energy_threshold = dynamic_energy_threshold
        self.recognizer.pause_threshold = 1.0
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.6
        
        self.default_backend = default_backend
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit
        
        # Calibrate microphone for ambient noise
        self._calibrate_microphone()
    
    def _calibrate_microphone(self):
        """Calibrate the microphone for ambient noise."""
        try:
            logger.info("Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("Microphone calibration complete.")
        except Exception as e:
            logger.warning(f"Microphone calibration failed: {e}")
    
    def listen_for_audio(self, timeout: Optional[int] = None, phrase_time_limit: Optional[int] = None) -> Optional[sr.AudioData]:
        """
        Listen for audio input from the microphone.
        
        Args:
            timeout: Timeout for listening (uses instance default if None)
            phrase_time_limit: Maximum time to wait for speech (uses instance default if None)
            
        Returns:
            AudioData object if audio is captured, None otherwise
        """
        timeout = self.timeout if timeout is None else timeout
        phrase_time_limit = self.phrase_time_limit if phrase_time_limit is None else phrase_time_limit
        
        try:
            logger.info("Listening for audio...")
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
            logger.info("Audio captured successfully.")
            return audio
        except sr.WaitTimeoutError:
            logger.warning("No speech detected within timeout period.")
            return None
        except Exception as e:
            logger.error(f"Error listening for audio: {e}")
            return None
    
    def recognize_google(self, audio: sr.AudioData, language: str = "en-US") -> Optional[str]:
        """
        Recognize speech using Google Speech Recognition.
        
        Args:
            audio: AudioData object to recognize
            language: Language code for recognition
            
        Returns:
            Recognized text or None if recognition fails
        """
        try:
            logger.info("Recognizing speech using Google...")
            text = self.recognizer.recognize_google(audio, language=language)
            logger.info(f"Recognition successful: {text}")
            return text
        except sr.UnknownValueError:
            logger.warning("Google could not understand the audio.")
            return None
        except sr.RequestError as e:
            logger.error(f"Google recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Google recognition: {e}")
            return None
    
    def recognize_sphinx(self, audio: sr.AudioData) -> Optional[str]:
        """
        Recognize speech using PocketSphinx (offline).
        
        Args:
            audio: AudioData object to recognize
            
        Returns:
            Recognized text or None if recognition fails
        """
        try:
            logger.info("Recognizing speech using PocketSphinx...")
            text = self.recognizer.recognize_sphinx(audio)
            logger.info(f"Recognition successful: {text}")
            return text
        except sr.UnknownValueError:
            logger.warning("Sphinx could not understand the audio.")
            return None
        except sr.RequestError as e:
            logger.error(f"Sphinx recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Sphinx recognition: {e}")
            return None
    
    def recognize_azure(self, audio: sr.AudioData, key: str, region: str, language: str = "en-US") -> Optional[str]:
        """
        Recognize speech using Azure Speech Services.
        
        Args:
            audio: AudioData object to recognize
            key: Azure Speech Services API key
            region: Azure region
            language: Language code for recognition
            
        Returns:
            Recognized text or None if recognition fails
        """
        try:
            logger.info("Recognizing speech using Azure...")
            text = self.recognizer.recognize_azure(audio, key=key, location=region, language=language)
            logger.info(f"Recognition successful: {text}")
            return text
        except sr.UnknownValueError:
            logger.warning("Azure could not understand the audio.")
            return None
        except sr.RequestError as e:
            logger.error(f"Azure recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Azure recognition: {e}")
            return None
    
    def recognize_bing(self, audio: sr.AudioData, key: str, language: str = "en-US") -> Optional[str]:
        """
        Recognize speech using Microsoft Bing Speech API.
        
        Args:
            audio: AudioData object to recognize
            key: Bing Speech API key
            language: Language code for recognition
            
        Returns:
            Recognized text or None if recognition fails
        """
        try:
            logger.info("Recognizing speech using Bing...")
            text = self.recognizer.recognize_bing(audio, key=key, language=language)
            logger.info(f"Recognition successful: {text}")
            return text
        except sr.UnknownValueError:
            logger.warning("Bing could not understand the audio.")
            return None
        except sr.RequestError as e:
            logger.error(f"Bing recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Bing recognition: {e}")
            return None
    
    def recognize_speech(self, 
                         audio: sr.AudioData, 
                         backend: Optional[str] = None,
                         **kwargs) -> Optional[str]:
        """
        Recognize speech using the specified backend.
        
        Args:
            audio: AudioData object to recognize
            backend: Recognition backend to use
            **kwargs: Additional arguments for specific backends
            
        Returns:
            Recognized text or None if recognition fails
        """
        backend = backend or self.default_backend
        
        if backend == "google":
            return self.recognize_google(audio, **kwargs)
        elif backend == "sphinx":
            return self.recognize_sphinx(audio)
        elif backend == "azure":
            return self.recognize_azure(audio, **kwargs)
        elif backend == "bing":
            return self.recognize_bing(audio, **kwargs)
        else:
            logger.error(f"Unsupported backend: {backend}")
            return None
    
    def listen_and_recognize(self, 
                           backend: Optional[str] = None,
                           timeout: Optional[int] = None,
                           phrase_time_limit: Optional[int] = None,
                           **kwargs) -> Optional[str]:
        """
        Listen for audio and recognize speech in one step.
        
        Args:
            backend: Recognition backend to use
            timeout: Timeout for listening
            phrase_time_limit: Maximum time to wait for speech
            **kwargs: Additional arguments for specific backends
            
        Returns:
            Recognized text or None if recognition fails
        """
        audio = self.listen_for_audio(timeout, phrase_time_limit)
        if audio is None:
            return None
        
        return self.recognize_speech(audio, backend, **kwargs)
    
    def continuous_listening(self, 
                           callback: callable,
                           backend: Optional[str] = None,
                           timeout: Optional[int] = None,
                           phrase_time_limit: Optional[int] = None,
                           **kwargs):
        """
        Continuously listen for speech and call the callback function with recognized text.
        
        Args:
            callback: Function to call with recognized text
            backend: Recognition backend to use
            timeout: Timeout for listening
            phrase_time_limit: Maximum time to wait for speech
            **kwargs: Additional arguments for specific backends
        """
        logger.info("Starting continuous listening...")
        
        while True:
            try:
                text = self.listen_and_recognize(backend, timeout, phrase_time_limit, **kwargs)
                if text:
                    callback(text)
            except KeyboardInterrupt:
                logger.info("Continuous listening stopped by user.")
                break
            except Exception as e:
                logger.error(f"Error in continuous listening: {e}")
                time.sleep(1)  # Wait before retrying
    
    def get_available_microphones(self) -> List[Dict[str, Any]]:
        """
        Get list of available microphones.
        
        Returns:
            List of microphone information dictionaries
        """
        microphones = []
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            microphones.append({
                "index": index,
                "name": name
            })
        return microphones
    
    def set_microphone(self, device_index: int):
        """
        Set the microphone device to use.
        
        Args:
            device_index: Index of the microphone device
        """
        self.microphone = sr.Microphone(device_index=device_index)
        self._calibrate_microphone()


def main():
    """
    Example usage of the SpeechToText class.
    """
    # Initialize the speech recognizer
    stt = SpeechToText()
    
    print("Speech-to-Text Demo")
    print("Available microphones:")
    for mic in stt.get_available_microphones():
        print(f"  {mic['index']}: {mic['name']}")
    
    print("\nListening for speech... (Press Ctrl+C to stop)")
    
    def on_speech_detected(text: str):
        print(f"Recognized: {text}")
    
    try:
        # Continuous listening
        stt.continuous_listening(
            callback=on_speech_detected,
            backend="google",
            timeout=15,
            phrase_time_limit=None
        )
    except KeyboardInterrupt:
        print("\nStopping speech recognition...")


if __name__ == "__main__":
    main()
