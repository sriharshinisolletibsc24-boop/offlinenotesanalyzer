"""
audio.py - Offline speech-to-text via OpenAI's open-source Whisper model,
run locally on CPU (NOT the OpenAI cloud API - this is the open-weights
model running entirely on your machine).

One-time setup on your own machine (needs internet just to install):
    pip install openai-whisper
    (also requires ffmpeg installed on the system PATH)

After that, transcription runs fully offline / CPU-only.
"""
import tempfile
import os

_MODEL_CACHE = {}


def _get_model(size: str = "base"):
    if size in _MODEL_CACHE:
        return _MODEL_CACHE[size]
    try:
        import whisper  # lazy import - only needed if audio/video features are used
    except ImportError:
        raise RuntimeError(
            "Audio/video transcription needs the 'openai-whisper' package, "
            "which isn't installed.\nRun:  pip install openai-whisper\n"
            "(also requires ffmpeg installed on your system PATH)"
        )
    model = whisper.load_model(size)  # downloads once, then cached locally & used offline
    _MODEL_CACHE[size] = model
    return model


def transcribe_audio(audio_bytes: bytes, filename_hint: str = "audio.wav", model_size: str = "base") -> dict:
    suffix = os.path.splitext(filename_hint)[1] or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = _get_model(model_size)
        result = model.transcribe(tmp_path)
        text = result.get("text", "").strip()
        # Whisper doesn't give a single confidence number; approximate from
        # average per-segment no-speech probability (inverted)
        segments = result.get("segments", [])
        if segments:
            avg_conf = 1 - (sum(s.get("no_speech_prob", 0.2) for s in segments) / len(segments))
        else:
            avg_conf = 0.7
        return {"text": text, "confidence": round(max(0.0, min(1.0, avg_conf)), 3)}
    finally:
        os.unlink(tmp_path)
