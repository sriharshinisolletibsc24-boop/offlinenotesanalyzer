"""
db.py - SQLite storage layer for Local AI.

Uses Python's built-in sqlite3 module (zero extra dependencies, fully offline).
"""
import sqlite3
import json
import os
import time
import hashlib
from contextlib import contextmanager
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "local_ai.db")


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_hash TEXT,
    doc_type TEXT,
    raw_text TEXT,
    extracted_json TEXT,
    confidence REAL,
    processing_time REAL,
    created_at REAL,
    pipeline_mode TEXT
);
CREATE INDEX IF NOT EXISTS idx_doc_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_file_hash ON documents(file_hash);
"""


@contextmanager
def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def file_hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def find_by_hash(file_hash: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM documents WHERE file_hash = ? LIMIT 1", (file_hash,))
        return cur.fetchone()


def insert_document(filename, file_hash, doc_type, raw_text, extracted: dict,
                     confidence: float, processing_time: float, pipeline_mode: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO documents
               (filename, file_hash, doc_type, raw_text, extracted_json,
                confidence, processing_time, created_at, pipeline_mode)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (filename, file_hash, doc_type, raw_text, json.dumps(extracted),
             confidence, processing_time, time.time(), pipeline_mode),
        )
        return cur.lastrowid


def list_documents(limit: int = 200):
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT * FROM documents ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        return cur.fetchall()


def get_document(doc_id: int):
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        return cur.fetchone()


def delete_document(doc_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))


def search_documents(query: str):
    q = f"%{query.lower()}%"
    with get_conn() as conn:
        cur = conn.execute(
            """SELECT * FROM documents
               WHERE lower(filename) LIKE ?
                  OR lower(raw_text) LIKE ?
                  OR lower(extracted_json) LIKE ?
               ORDER BY created_at DESC""",
            (q, q, q),
        )
        return cur.fetchall()


def stats():
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) c FROM documents").fetchone()["c"]
        avg_conf = conn.execute("SELECT AVG(confidence) c FROM documents").fetchone()["c"] or 0
        avg_time = conn.execute("SELECT AVG(processing_time) c FROM documents").fetchone()["c"] or 0
        by_type = conn.execute(
            "SELECT doc_type, COUNT(*) c FROM documents GROUP BY doc_type"
        ).fetchall()
        return {
            "total_documents": total,
            "avg_confidence": round(avg_conf, 3),
            "avg_processing_time": round(avg_time, 3),
            "by_type": {r["doc_type"]: r["c"] for r in by_type},
        }
