import os
import shutil
import logging
import whisper
import threading

logger = logging.getLogger(__name__)

# ---------------- GLOBAL STATE ----------------
_whisper_model = None
_model_lock = threading.Lock()
_model_loading = False
_model_error = None


# ---------------- DEPENDENCY CHECK ----------------
def _ensure_ffmpeg():
    if shutil.which("ffmpeg") is None:
        raise EnvironmentError(
            "FFmpeg is not installed or not found in PATH. "
            "Install it and restart the server."
        )


# ---------------- MODEL LOADER ----------------
def _load_model(model_name: str):
    """
    Actually loads the Whisper model (blocking).
    Only called inside a lock.
    """
    global _whisper_model, _model_error, _model_loading

    try:
        logger.info(f"Loading Whisper model '{model_name}' (first time only)...")

        _ensure_ffmpeg()

        # FIXED: Added device="cpu" to bypass the CUDA/GPU version mismatch
        _whisper_model = whisper.load_model(model_name, device="cpu")

        logger.info("Whisper model loaded successfully.")

    except Exception as e:
        _model_error = str(e)
        logger.exception("Whisper model failed to load!")

    finally:
        _model_loading = False


# MODIFIED: Changed default model_name from "tiny" to "base" so it loads a multilingual-capable model
def _get_whisper_model(model_name: str = "base"):
    """
    Thread-safe lazy loader.

    Behavior:
    - First request waits until model loads
    - Other requests queue safely
    - Never loads twice
    - Properly reports permanent failures
    """
    global _whisper_model, _model_loading, _model_error

    # If model previously failed
    if _model_error:
        raise RuntimeError(f"Speech model failed to load: {_model_error}")

    # Fast path
    if _whisper_model is not None:
        return _whisper_model

    # Only ONE thread loads model
    with _model_lock:
        if _whisper_model is None and not _model_loading:
            _model_loading = True
            _load_model(model_name)

    # After lock release
    if _model_error:
        raise RuntimeError(f"Speech model failed to load: {_model_error}")

    if _whisper_model is None:
        raise RuntimeError("Model failed to initialize for unknown reason.")

    return _whisper_model


# ---------------- TRANSCRIPTION ----------------
# MODIFIED: Added task="transcribe" parameter and changed default model_name to "base"
def convert_to_text(file_path: str, model_name: str = "base", task: str = "transcribe") -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    model = _get_whisper_model(model_name)

    logger.info("Transcribing/Translating (%s): %s", task, file_path)

    # MODIFIED: Passing the task parameter directly to whisper's transcribe method
    result = model.transcribe(file_path, task=task)

    text = result.get("text", "")
    if isinstance(text, list):
        text = " ".join(str(item) for item in text)

    return (text or "").strip()