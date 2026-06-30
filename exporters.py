"""
exporters.py - Export stored documents as JSON, CSV, or Excel.
"""
import json
import io
import pandas as pd


def to_json_bytes(rows) -> bytes:
    docs = []
    for r in rows:
        docs.append({
            "id": r["id"], "filename": r["filename"], "doc_type": r["doc_type"],
            "confidence": r["confidence"], "processing_time": r["processing_time"],
            "extracted": json.loads(r["extracted_json"]),
        })
    return json.dumps(docs, indent=2).encode("utf-8")


def _flatten_rows(rows):
    flat = []
    for r in rows:
        extracted = json.loads(r["extracted_json"])
        row = {
            "id": r["id"], "filename": r["filename"], "doc_type": r["doc_type"],
            "confidence": r["confidence"], "processing_time": r["processing_time"],
        }
        for k, v in extracted.items():
            row[k] = json.dumps(v) if isinstance(v, (list, dict)) else v
        flat.append(row)
    return flat


def to_csv_bytes(rows) -> bytes:
    df = pd.DataFrame(_flatten_rows(rows))
    return df.to_csv(index=False).encode("utf-8")


def to_excel_bytes(rows) -> bytes:
    df = pd.DataFrame(_flatten_rows(rows))
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Documents")
    return buf.getvalue()
