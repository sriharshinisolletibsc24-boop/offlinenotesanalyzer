"""
video.py - Extracts the audio track from a video file (using ffmpeg,
which must be installed locally) and transcribes it via audio.py.

Requires ffmpeg on PATH (e.g. `apt install ffmpeg` / `brew install ffmpeg`).
No video data ever leaves the machine.
"""
import subprocess
import tempfile
import os
from . import audio


def transcribe_video(video_bytes: bytes, filename_hint: str = "video.mp4", model_size: str = "base") -> dict:
    suffix = os.path.splitext(filename_hint)[1] or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as vtmp:
        vtmp.write(video_bytes)
        video_path = vtmp.name

    audio_path = video_path + ".wav"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000", audio_path],
            check=True, capture_output=True,
        )
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        return audio.transcribe_audio(audio_bytes, filename_hint="extracted.wav", model_size=model_size)
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found. Install ffmpeg to enable video processing.")
    finally:
        for p in (video_path, audio_path):
            if os.path.exists(p):
                os.unlink(p)
