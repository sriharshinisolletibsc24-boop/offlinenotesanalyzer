"""
ocr.py - Image OCR using Tesseract (offline, CPU-only).

Tesseract is a mature, fully offline OCR engine - no internet or cloud
calls are made. Requires the `tesseract` binary + `pytesseract` package.
"""
from PIL import Image
import pytesseract
import io


def ocr_image(image_bytes: bytes, lang: str = "eng") -> dict:
    """Run OCR on raw image bytes. Returns text + a rough confidence score."""
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")

    try:
        text = pytesseract.image_to_string(img, lang=lang)
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract OCR engine is not installed on this machine.\n"
            "Install it, then restart the app:\n"
            "  Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "  macOS:   brew install tesseract\n"
            "  Linux:   sudo apt install tesseract-ocr"
        )

    # image_to_data gives per-word confidence; average the valid ones
    try:
        data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
        confs = [int(c) for c in data["conf"] if c not in ("-1", -1)]
        avg_conf = (sum(confs) / len(confs) / 100.0) if confs else 0.5
    except Exception:
        avg_conf = 0.5

    return {"text": text.strip(), "confidence": round(avg_conf, 3)}


def available_languages() -> list:
    try:
        return pytesseract.get_languages(config="")
    except Exception:
        return ["eng"]
