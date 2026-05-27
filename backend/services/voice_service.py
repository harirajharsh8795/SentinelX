import os
import tempfile
from utils.logger import get_logger

logger = get_logger(__name__)

# Lazy model loader to avoid locking VRAM on application startup
_model_instance = None

def get_whisper_model():
    """Lazily loads the Whisper model to save startup memory."""
    global _model_instance
    if _model_instance is None:
        try:
            logger.info("Loading faster-whisper model (tiny, int8 quantization)...")
            from faster_whisper import WhisperModel
            # Using 'tiny' model with int8 quantization for ultra-fast, low-memory performance on CPU/Jetson
            # Hindi and English are supported out-of-the-box in the multilingual version.
            _model_instance = WhisperModel("tiny", device="cpu", compute_type="int8")
            logger.info("faster-whisper model loaded successfully.")
        except ImportError:
            logger.warning("faster-whisper package not installed. Speech-to-text will fall back to simulation mode.")
            _model_instance = "MOCK"
        except Exception as e:
            logger.error(f"Error loading faster-whisper model: {e}")
            _model_instance = "MOCK"
    return _model_instance

def transcribe_audio_bytes(audio_bytes: bytes, suffix: str = ".wav") -> str:
    """
    Saves audio bytes to a temp file, runs faster-whisper transcription,
    and returns the transcribed text (English or Hindi).
    """
    if not audio_bytes or len(audio_bytes) < 100:
        return ""

    model = get_whisper_model()
    
    # Normalize suffix
    if suffix and not suffix.startswith("."):
        suffix = f".{suffix}"
    
    # Create a temporary file to hold the audio data
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_audio:
        temp_audio.write(audio_bytes)
        temp_path = temp_audio.name

    try:
        if model == "MOCK":
            # Simple simulation translation if library is missing
            logger.info("Running in transcription simulation mode.")
            # Let's inspect bytes to return a realistic mock text
            if len(audio_bytes) % 2 == 0:
                return "RBI cybersecurity incident reporting timeline guidelines"
            else:
                return "kyc registration guidelines for digital onboarding"

        # Model is loaded successfully, perform actual transcription
        segments, info = model.transcribe(temp_path, beam_size=2)
        transcribed_text = []
        for segment in segments:
            transcribed_text.append(segment.text)
            
        result = "".join(transcribed_text).strip()
        logger.info(f"Transcription complete. Language: {info.language} (Confidence: {info.language_probability:.2f}). Result: '{result}'")
        return result
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return "Error during voice transcription. Please check backend whisper configuration."
    finally:
        # Always clean up temporary files
        try:
            os.unlink(temp_path)
        except Exception:
            pass
