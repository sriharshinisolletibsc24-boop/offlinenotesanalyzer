"""
pdf_extract.py - Extract text from PDFs (offline).

Strategy:
  1. Try pdfplumber for native text extraction (fast, accurate for text PDFs).
  2. If a page has no extractable text (scanned/image PDF), rasterize it
     and run it through Tesseract OCR.
"""
import io
import pdfplumber
from PIL import Image
from . import ocr


def extract_pdf(pdf_bytes: bytes, lang: str = "eng") -> dict:
    pages_text = []
    ocr_used = False
    confidences = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = (page.extract_text() or "").strip()
            if text:
                pages_text.append(text)
                confidences.append(0.95)  # native text is high-confidence
            else:
                # Scanned page -> rasterize + OCR
                try:
                    im = page.to_image(resolution=200).original
                    buf = io.BytesIO()
                    im.save(buf, format="PNG")
                    result = ocr.ocr_image(buf.getvalue(), lang=lang)
                    pages_text.append(result["text"])
                    confidences.append(result["confidence"])
                    ocr_used = True
                except Exception as e:
                    pages_text.append("")
                    confidences.append(0.0)

    full_text = "\n\n".join(p for p in pages_text if p)
    avg_conf = (sum(confidences) / len(confidences)) if confidences else 0.0

    return {
        "text": full_text.strip(),
        "page_count": len(pages_text),
        "ocr_used": ocr_used,
        "confidence": round(avg_conf, 3),
    }
