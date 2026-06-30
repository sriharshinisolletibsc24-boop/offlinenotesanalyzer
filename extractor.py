"""
extractor.py - Turns cleaned text into structured JSON, 100% offline.

Two modes (selectable in Settings):
  - "rules"  : fast regex/heuristic extraction. No model download needed,
               works immediately, zero extra dependencies. This is the
               default and is what powers the app out of the box.
  - "llm"    : routes through backend/llm_local.py, which calls a local
               quantized GGUF model via llama-cpp-python (CPU only).
               Requires the user to `pip install llama-cpp-python` and
               place a .gguf model in models/ (see README) - both need
               internet/disk access on the user's own machine.

Both modes return the same JSON shape so the rest of the app doesn't care
which one produced it.
"""
import re
from collections import Counter

STOPWORDS = set("""
a an the and or but if of in on at to for with from by is are was were be
been being this that these those it its as not no yes you your we our
they their he she his her i me my mine us them than then so such can will
would should could may might must do does did have has had
""".split())

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(?<!\w)(\+?\d{1,3}[\s.-])?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\w)")
DATE_RE = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)
AMOUNT_RE = re.compile(r"(?:[$₹€£]\s?\d[\d,]*\.?\d{0,2}|\b\d[\d,]*\.\d{2}\b)")
INVOICE_NO_RE = re.compile(r"\b(?:invoice|inv|receipt|order)[\s#:no.]*([A-Z0-9-]{4,})\b", re.IGNORECASE)
NAME_LINE_RE = re.compile(r"\b([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+){1,2})\b")
NAME_BLOCKLIST = {
    "bill to", "amount due", "invoice no", "ship to", "pay to", "total due",
    "due date", "order no", "purchase order", "account number", "sold to",
    "action items", "meeting notes", "product roadmap",
}
ORG_HINT_RE = re.compile(
    r"\b([A-Z][\w&]*(?:\s+[A-Z][\w&]*)*\s+(?:Inc\.?|LLC|Ltd\.?|Corp\.?|Company|Co\.|Technologies|Solutions|Group))\b"
)

DOC_TYPE_KEYWORDS = {
    "invoice": ["invoice", "bill to", "subtotal", "tax", "amount due", "po number"],
    "receipt": ["receipt", "total", "cash", "change due", "thank you for your purchase"],
    "resume": ["experience", "education", "skills", "resume", "curriculum vitae", "objective"],
    "medical_report": ["diagnosis", "patient", "physician", "prescribed", "symptoms", "treatment"],
    "meeting_notes": ["agenda", "attendees", "action items", "minutes of meeting", "next steps"],
    "contract": ["agreement", "party", "parties", "hereby", "terms and conditions", "termination"],
    "letter": ["dear", "sincerely", "regards", "yours truly"],
    "research_paper": ["abstract", "references", "introduction", "methodology", "conclusion"],
    "certificate": ["certificate", "certify", "awarded", "completion"],
}


def classify_document(text: str) -> str:
    lower = text.lower()
    scores = {}
    for doc_type, keywords in DOC_TYPE_KEYWORDS.items():
        scores[doc_type] = sum(lower.count(k) for k in keywords)
    best_type, best_score = max(scores.items(), key=lambda kv: kv[1])
    return best_type if best_score > 0 else "general"


def _top_keywords(text: str, n: int = 10) -> list:
    words = re.findall(r"[A-Za-z]{4,}", text.lower())
    words = [w for w in words if w not in STOPWORDS]
    return [w for w, _ in Counter(words).most_common(n)]


def _summary(text: str, max_sentences: int = 2) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(sentences[:max_sentences])[:400]


def extract_entities(text: str) -> dict:
    """Common entities every document type shares."""
    emails = sorted(set(EMAIL_RE.findall(text)))
    phones = sorted(set(m.group(0).strip() for m in PHONE_RE.finditer(text)))
    dates = sorted(set(DATE_RE.findall(text)))
    amounts = sorted(set(AMOUNT_RE.findall(text)))
    orgs = sorted(set(ORG_HINT_RE.findall(text)))
    invoice_match = INVOICE_NO_RE.search(text)
    names_raw = set(NAME_LINE_RE.findall(text))
    names = sorted(n for n in names_raw if n.lower() not in NAME_BLOCKLIST and n not in orgs)[:10]

    return {
        "people": names,
        "emails": emails,
        "phones": phones,
        "dates": dates,
        "amounts": amounts,
        "organizations": orgs,
        "invoice_number": invoice_match.group(1) if invoice_match else None,
    }


def rule_based_extract(text: str, doc_type: str) -> dict:
    entities = extract_entities(text)
    result = {
        "document_category": doc_type,
        "summary": _summary(text),
        "tags": _top_keywords(text, 8),
        "keywords": _top_keywords(text, 15),
        **entities,
    }

    # Type-specific shaping so the JSON looks purpose-built, not generic
    if doc_type == "resume":
        result["full_name"] = entities["people"][0] if entities["people"] else None
        result["email"] = entities["emails"][0] if entities["emails"] else None
        result["phone"] = entities["phones"][0] if entities["phones"] else None
        skill_kw = ["python", "java", "sql", "react", "fastapi", "excel", "design",
                    "leadership", "communication", "javascript", "aws", "docker"]
        result["skills"] = [k for k in skill_kw if k in text.lower()]
    elif doc_type in ("invoice", "receipt"):
        result["total_amount"] = entities["amounts"][-1] if entities["amounts"] else None
        result["vendor"] = entities["organizations"][0] if entities["organizations"] else None
        result["date"] = entities["dates"][0] if entities["dates"] else None

    # crude confidence: more populated fields = higher confidence
    populated = sum(1 for v in result.values() if v)
    result["confidence_score"] = round(min(0.95, 0.35 + populated * 0.05), 2)
    return result


def extract(text: str, doc_type: str = None, mode: str = "rules", model_path: str = None) -> dict:
    """Main entry point. `mode` is 'rules' (default, always works offline)
    or 'llm' (requires llama-cpp-python + a local GGUF model)."""
    if not doc_type:
        doc_type = classify_document(text)

    if mode == "llm":
        from . import llm_local
        try:
            return llm_local.extract_with_llm(text, doc_type, model_path)
        except Exception as e:
            # Always fall back to rule-based so the pipeline never hard-fails
            result = rule_based_extract(text, doc_type)
            result["_llm_error"] = str(e)
            result["_fallback_used"] = "rules"
            return result

    return rule_based_extract(text, doc_type)
