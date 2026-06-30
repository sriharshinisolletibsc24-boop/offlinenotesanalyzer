"""
llm_local.py - Optional local LLM extraction via llama-cpp-python.

This module is only imported when the user enables "LLM mode" in Settings.
It is NOT required for the app to work - the default "rules" mode (see
extractor.py) needs zero extra downloads.

To enable real local-LLM extraction on your own machine (with internet
access, just for the one-time setup):
    pip install llama-cpp-python
    Download a small instruction-tuned GGUF model, e.g.:
      - TinyLlama-1.1B-Chat (~600MB)
      - Phi-3-mini-4k-instruct (Q4_K_M, ~2.3GB)
      - Qwen2.5-3B-Instruct (Q4_K_M, ~2GB)
    Place the .gguf file in models/ and set its path in the Settings page
    (or LOCAL_AI_MODEL_PATH env var).

After that one-time setup, everything still runs 100% offline / CPU-only -
no API keys, no cloud calls.
"""
import json
import re
import os

_MODEL_CACHE = {}


def _get_model(model_path: str):
    if not model_path or not os.path.exists(model_path):
        raise FileNotFoundError(
            f"No GGUF model found at '{model_path}'. Download one and set "
            f"its path in Settings (see backend/llm_local.py docstring)."
        )
    if model_path in _MODEL_CACHE:
        return _MODEL_CACHE[model_path]

    from llama_cpp import Llama  # lazy import - only needed for LLM mode
    llm = Llama(model_path=model_path, n_ctx=4096, n_threads=os.cpu_count(), verbose=False)
    _MODEL_CACHE[model_path] = llm
    return llm


def _extract_json(raw: str) -> dict:
    """Models sometimes wrap JSON in markdown fences or add stray text -
    pull out the first {...} block."""
    raw = raw.strip()
    raw = re.sub(r"^```(json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("Model did not return parseable JSON")
    return json.loads(match.group(0))


def extract_with_llm(text: str, doc_type: str, model_path: str = None) -> dict:
    from prompts.templates import build_prompt

    model_path = model_path or os.environ.get("LOCAL_AI_MODEL_PATH", "models/model.gguf")
    llm = _get_model(model_path)
    prompt = build_prompt(doc_type, text)

    output = llm(
        prompt,
        max_tokens=800,
        temperature=0.1,
        stop=["</s>", "```"],
    )
    raw_text = output["choices"][0]["text"]
    result = _extract_json(raw_text)
    result.setdefault("document_category", doc_type)
    result.setdefault("confidence_score", 0.8)
    result["_pipeline_mode"] = "llm"
    return result
