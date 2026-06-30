"""
app.py - Offline Notes Analyser
Streamlit front-end. Run with:  streamlit run app.py
"""
import sys
import os
import json
import time
import logging

logging.getLogger("pdfminer").setLevel(logging.ERROR)

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd

from backend import db, pipeline, exporters

st.set_page_config(
    page_title="Offline Notes Analyser",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()

# Fixed settings - kept simple, no settings page.
PIPELINE_MODE = "rules"          # switch to "llm" in code if you set up a local model
MODEL_PATH = "models/model.gguf"
OCR_LANG = "eng"

if "page" not in st.session_state:
    st.session_state.page = "Analyze"

# ------------------------------------------------------------------ style --
st.markdown("""
<style>
.metric-card {
    border:1px solid #2a2a2a22; border-radius:12px; padding:16px;
    background:linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------- sidebar --
with st.sidebar:
    st.markdown("## 🧠 Offline Notes Analyser")
    st.caption("Upload a file, get structured notes, search them later.")
    st.session_state.page = st.radio(
        "Navigate",
        ["Analyze", "History"],
        index=["Analyze", "History"].index(st.session_state.page),
        label_visibility="collapsed",
    )
    st.divider()
    s = db.stats()
    st.metric("Notes analyzed", s["total_documents"])
    st.success("🟢 100% Offline")


# ===================================================== ANALYZE (UPLOAD) ===
def render_analyze():
    st.title("📤 Analyze")
    st.caption("Drop a file below. Everything happens locally on this machine.")

    uploaded = st.file_uploader(
        "Choose a file",
        type=["jpg", "jpeg", "png", "pdf", "txt", "mp3", "wav", "m4a", "mp4", "mov", "mkv"],
        accept_multiple_files=True,
    )

    if not uploaded:
        st.info("Upload an image, PDF, text file, audio, or video to begin.")
        return

    for f in uploaded:
        filename, file_bytes = f.name, f.read()
        with st.container(border=True):
            st.markdown(f"**{filename}**")
            status_box = st.empty()
            progress = st.progress(0)
            steps_seen = []

            def on_step(step_name, _seen=steps_seen, _box=status_box, _prog=progress):
                _seen.append(step_name)
                _box.write(" → ".join(_seen))
                _prog.progress(min(0.95, len(_seen) * 0.15))

            try:
                result = pipeline.process_file(
                    filename, file_bytes,
                    mode=PIPELINE_MODE, model_path=MODEL_PATH, ocr_lang=OCR_LANG,
                    status_callback=on_step,
                )
                progress.progress(1.0)
            except Exception as e:
                st.error(f"Processing failed: {e}")
                continue

            if result.get("duplicate"):
                st.warning(f"⚠️ Already analyzed before — see document #{result['existing_id']} in History.")
                continue

            c1, c2, c3 = st.columns(3)
            c1.metric("Type", result["doc_type"])
            c2.metric("Confidence", f"{result['confidence']*100:.0f}%")
            c3.metric("Time", f"{result['processing_time']}s")

            tab1, tab2 = st.tabs(["📋 Structured result", "📝 Raw text"])
            with tab1:
                st.json(result["extracted"])
                st.download_button(
                    "⬇️ Download JSON",
                    data=json.dumps(result["extracted"], indent=2),
                    file_name=f"{filename}.json",
                    mime="application/json",
                    key=f"dl_{filename}_{result['id']}",
                )
                st.caption("Want CSV or Excel instead? Open this document in the **History** tab to download it in any format.")
            with tab2:
                st.text_area("Raw extracted text", result["raw_text"], height=200, key=f"raw_{result['id']}")

    st.success("Done — find this anytime in History.")


# ================================================ HISTORY (+ SEARCH) ======
def render_history():
    st.title("🗂️ History")

    query = st.text_input("🔍 Search by name, email, company, invoice number, keyword…")
    rows = db.search_documents(query) if query else db.list_documents(limit=500)

    if not rows:
        st.info("Nothing here yet — analyze a file first." if not query else "No matches.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        try:
            st.download_button("⬇️ Export all (JSON)", exporters.to_json_bytes(rows), "notes.json", "application/json")
        except Exception as e:
            st.error(f"JSON export failed: {e}")
    with col2:
        try:
            st.download_button("⬇️ Export all (CSV)", exporters.to_csv_bytes(rows), "notes.csv", "text/csv")
        except Exception as e:
            st.error(f"CSV export failed: {e}")
    with col3:
        try:
            st.download_button("⬇️ Export all (Excel)", exporters.to_excel_bytes(rows), "notes.xlsx",
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            st.error(f"Excel export failed: {e}")

    st.divider()
    for r in rows:
        with st.expander(f"#{r['id']} · {r['filename']} · {r['doc_type']} · {r['confidence']*100:.0f}% confidence"):
            st.caption(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r["created_at"])))
            extracted = json.loads(r["extracted_json"])
            st.json(extracted)
            c_json, c_csv, c_xlsx, c_del = st.columns(4)
            with c_json:
                st.download_button("⬇️ JSON", json.dumps(extracted, indent=2),
                                    f"{r['filename']}.json", key=f"hist_json_{r['id']}")
            with c_csv:
                st.download_button("⬇️ CSV", exporters.to_csv_bytes([r]),
                                    f"{r['filename']}.csv", "text/csv", key=f"hist_csv_{r['id']}")
            with c_xlsx:
                st.download_button("⬇️ Excel", exporters.to_excel_bytes([r]),
                                    f"{r['filename']}.xlsx",
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"hist_xlsx_{r['id']}")
            with c_del:
                if st.button("🗑️ Delete", key=f"hist_del_{r['id']}"):
                    db.delete_document(r["id"])
                    st.rerun()


PAGES = {"Analyze": render_analyze, "History": render_history}
PAGES[st.session_state.page]()
