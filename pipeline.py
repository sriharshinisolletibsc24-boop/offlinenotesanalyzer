"""
pipeline.py - Orchestrates the full Input -> Clean -> Extract -> JSON -> SQLite
flow for every supported input type. Yields step-by-step status so the UI
can show live progress.
"""
import time
from . import ocr, pdf_extract, extractor, db

STEPS_BY_TYPE = {
    "image": ["Uploading", "Running OCR", "Cleaning text", "AI extracting", "Generating JSON", "Saving to database"],
    "pdf": ["Uploading", "Extracting pages", "Cleaning text", "AI extracting", "Generating JSON", "Saving to database"],
    "text": ["Uploading", "Cleaning text", "AI extracting", "Generating JSON", "Saving to database"],
    "audio": ["Uploading", "Transcribing (Whisper)", "Cleaning text", "AI extracting", "Generating JSON", "Saving to database"],
    "video": ["Uploading", "Extracting audio", "Transcribing (Whisper)", "Cleaning text", "AI extracting", "Generating JSON", "Saving to database"],
}


def _clean_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def file_kind(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext in ("jpg", "jpeg", "png"):
        return "image"
    if ext == "pdf":
        return "pdf"
    if ext == "txt":
        return "text"
    if ext in ("mp3", "wav", "m4a"):
        return "audio"
    if ext in ("mp4", "mov", "mkv"):
        return "video"
    return "unknown"


def process_file(filename: str, file_bytes: bytes, mode: str = "rules",
                  model_path: str = None, ocr_lang: str = "eng",
                  status_callback=None):
    """Runs the full pipeline. status_callback(step_name) is called for each
    stage if provided (used by the Streamlit UI to show live progress)."""
    start = time.time()
    kind = file_kind(filename)
    if kind == "unknown":
        raise ValueError(f"Unsupported file type: {filename}")

    def report(step):
        if status_callback:
            status_callback(step)

    steps = iter(STEPS_BY_TYPE[kind])
    report(next(steps))  # Uploading

    file_hash = db.file_hash_bytes(file_bytes)
    existing = db.find_by_hash(file_hash)
    if existing:
        return {"duplicate": True, "existing_id": existing["id"]}

    raw_text = ""
    ocr_confidence = 1.0

    if kind == "image":
        report(next(steps))
        r = ocr.ocr_image(file_bytes, lang=ocr_lang)
        raw_text, ocr_confidence = r["text"], r["confidence"]
    elif kind == "pdf":
        report(next(steps))
        r = pdf_extract.extract_pdf(file_bytes, lang=ocr_lang)
        raw_text, ocr_confidence = r["text"], r["confidence"]
    elif kind == "text":
        raw_text = file_bytes.decode("utf-8", errors="ignore")
    elif kind == "audio":
        report(next(steps))
        from . import audio as audio_mod
        r = audio_mod.transcribe_audio(file_bytes, filename_hint=filename)
        raw_text, ocr_confidence = r["text"], r["confidence"]
    elif kind == "video":
        report(next(steps))
        from . import video as video_mod
        report(next(steps))
        r = video_mod.transcribe_video(file_bytes, filename_hint=filename)
        raw_text, ocr_confidence = r["text"], r["confidence"]

    report(next(steps))  # Cleaning text
    cleaned = _clean_text(raw_text)

    report(next(steps))  # AI extracting
    doc_type = extractor.classify_document(cleaned)
    extracted = extractor.extract(cleaned, doc_type=doc_type, mode=mode, model_path=model_path)

    report(next(steps))  # Generating JSON
    confidence = round((ocr_confidence + extracted.get("confidence_score", 0.7)) / 2, 3)

    report(next(steps))  # Saving to database
    processing_time = round(time.time() - start, 3)
    doc_id = db.insert_document(
        filename=filename, file_hash=file_hash, doc_type=doc_type,
        raw_text=cleaned, extracted=extracted, confidence=confidence,
        processing_time=processing_time, pipeline_mode=mode,
    )

    return {
        "duplicate": False,
        "id": doc_id,
        "doc_type": doc_type,
        "raw_text": cleaned,
        "extracted": extracted,
        "confidence": confidence,
        "processing_time": processing_time,
    }
