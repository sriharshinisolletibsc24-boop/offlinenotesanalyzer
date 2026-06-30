<<<<<<< HEAD
# Local AI — Offline Multi-Modal Document Intelligence System

Turn images, PDFs, plain text, audio, and video into structured JSON — **100% offline, CPU-only.**
No cloud APIs, no API keys, no telemetry, no internet dependency after setup.

Built with **Streamlit** (not React/FastAPI — swapped per project requirements for a single-process,
easy-to-run app), Tesseract OCR, and a lightweight rule-based local extraction engine, with an
optional upgrade path to a real local LLM via `llama-cpp-python`.

---

## ✅ What's fully working out of the box (zero extra downloads)

- **Images → OCR → JSON** (Tesseract, native)
- **PDFs → text/OCR → JSON** (`pdfplumber`, with automatic OCR fallback for scanned pages)
- **Plain text → JSON**
- Automatic **document type classification** (invoice, resume, receipt, meeting notes, contract,
  medical report, letter, research paper, certificate, general)
- Rule-based **entity extraction**: people, emails, phones, dates, amounts, organizations,
  invoice numbers, keywords, tags, summary, confidence score
- **SQLite storage**, full **History** view, **Search**, **Dashboard** with charts
- **Export** to JSON / CSV / Excel
- **Duplicate detection** via SHA-256 file hashing
- **Demo Mode** (one click, no upload needed)

This mode (`rules` in Settings) is what the app uses by default and what was tested end-to-end
while building this — see "What was tested" below.

## 🔌 Optional upgrades (require one-time internet access on *your* machine)

| Feature | Install | Notes |
|---|---|---|
| Real local LLM extraction | `pip install llama-cpp-python` + a `.gguf` model in `models/` | Switch to "llm" mode in Settings. See `backend/llm_local.py` for model recommendations (TinyLlama, Phi-3-mini, Qwen2.5-3B). |
| Audio transcription | `pip install openai-whisper` + `ffmpeg` on PATH | Powers `.mp3/.wav/.m4a` uploads |
| Video transcription | same as above | Extracts audio via ffmpeg, then transcribes |

Once installed, these still run **entirely locally / CPU-only** — the "offline" install step is a
one-time download of the model file, not a runtime API call.

---

## Quickstart

```bash
git clone <this-repo>
cd local-ai
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt

# Tesseract binary (required for OCR):
#   Ubuntu/Debian:  sudo apt install tesseract-ocr
#   macOS:          brew install tesseract
#   Windows:        https://github.com/UB-Mannheim/tesseract/wiki

streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501). Try **Home → Run Demo Mode**, or
upload a file from `sample_docs/`.

---

## Architecture

```
Input (image/pdf/text/audio/video)
        │
        ▼
   OCR / Transcription      (Tesseract / pdfplumber / Whisper)
        │
        ▼
   Text Cleaning
        │
        ▼
   Local AI Extraction      (rule-based engine, or local LLM via llama.cpp)
        │
        ▼
   Structured JSON
        │
        ▼
   SQLite Storage  ──►  Dashboard / History / Search / Export
```

## Folder structure

```
local-ai/
├── app.py                # Streamlit UI (Home, Upload, Dashboard, History, Search, Settings)
├── backend/
│   ├── ocr.py             # Tesseract image OCR
│   ├── pdf_extract.py     # PDF text extraction + OCR fallback for scans
│   ├── extractor.py       # Document classification + rule-based JSON extraction
│   ├── llm_local.py       # Optional llama-cpp-python local LLM extraction
│   ├── audio.py           # Optional Whisper transcription
│   ├── video.py           # Optional ffmpeg audio extraction + Whisper
│   ├── pipeline.py         # Orchestrates the full flow + status updates
│   ├── db.py               # SQLite storage (stdlib sqlite3, no ORM dependency)
│   └── exporters.py        # JSON / CSV / Excel export
├── prompts/
│   └── templates.py        # Prompt templates per document type (used in LLM mode)
├── sample_docs/            # Sample files for quick testing / Demo Mode
├── models/                 # Drop a .gguf model here to enable LLM mode
├── data/                   # SQLite database lives here (created at runtime)
├── requirements.txt
├── LICENSE                 # GPLv3
└── README.md
```

## API surface (internal, called by the Streamlit UI)

These are plain Python functions, not HTTP endpoints (no separate backend server is
needed since Streamlit handles both UI and processing in one process):

- `pipeline.process_file(filename, bytes, mode, model_path, ocr_lang, status_callback)`
- `db.list_documents()`, `db.search_documents(query)`, `db.get_document(id)`, `db.delete_document(id)`, `db.stats()`
- `exporters.to_json_bytes(rows)`, `to_csv_bytes(rows)`, `to_excel_bytes(rows)`

If you specifically need a separate REST API (e.g. to call from another app), the same
`backend/` modules can be wrapped in FastAPI with a thin `main.py` — they have no
Streamlit dependency themselves.

## What was tested while building this (in a sandboxed, no-internet environment)

- Image OCR on a generated test image ✅
- PDF native-text extraction on a generated test PDF ✅
- Document classification across invoice/resume/meeting-notes samples ✅
- Full entity extraction (emails, phones, dates, amounts, orgs, names) ✅
- SQLite insert/list/search/stats/delete ✅
- Duplicate detection via hashing ✅
- JSON/CSV/Excel export ✅

Not testable in that environment (no internet to install/download): the Streamlit UI render
itself, `llama-cpp-python` LLM mode, and Whisper audio/video transcription. The code for all
three is complete and follows each library's standard, stable API — install the optional
dependencies above to light them up.

## Security & privacy

No cloud calls, no telemetry, no analytics, no external API keys anywhere in this codebase.
All processing and storage stays on the machine running `streamlit run app.py`.

## License

GPLv3 — see [LICENSE](LICENSE).

## Future improvements

- Folder-watch mode for auto-processing new files
- Custom JSON schema builder in Settings
- Batch processing queue with pause/resume/retry
- Side-by-side original-document + JSON viewer with click-to-highlight
- Multi-user auth if deployed beyond a single local user
=======
# offline notes analyser



## Getting started

To make it easy for you to get started with GitLab, here's a list of recommended next steps.

Already a pro? Just edit this README.md and make it your own. Want to make it easy? [Use the template at the bottom](#editing-this-readme)!

## Add your files

* [Create](https://docs.gitlab.com/user/project/repository/web_editor/#create-a-file) or [upload](https://docs.gitlab.com/user/project/repository/web_editor/#upload-a-file) files
* [Add files using the command line](https://docs.gitlab.com/topics/git/add_files/#add-files-to-a-git-repository) or push an existing Git repository with the following command:

```
cd existing_repo
git remote add origin https://code.swecha.org/sriharshini2901/offline-notes-analyser.git
git branch -M main
git push -uf origin main
```

## Integrate with your tools

* [Set up project integrations](https://code.swecha.org/sriharshini2901/offline-notes-analyser/-/settings/integrations)

## Collaborate with your team

* [Invite team members and collaborators](https://docs.gitlab.com/user/project/members/)
* [Create a new merge request](https://docs.gitlab.com/user/project/merge_requests/creating_merge_requests/)
* [Automatically close issues from merge requests](https://docs.gitlab.com/user/project/issues/managing_issues/#closing-issues-automatically)
* [Enable merge request approvals](https://docs.gitlab.com/user/project/merge_requests/approvals/)
* [Set auto-merge](https://docs.gitlab.com/user/project/merge_requests/auto_merge/)

## Test and Deploy

Use the built-in continuous integration in GitLab.

* [Get started with GitLab CI/CD](https://docs.gitlab.com/ci/quick_start/)
* [Analyze your code for known vulnerabilities with Static Application Security Testing (SAST)](https://docs.gitlab.com/user/application_security/sast/)
* [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/topics/autodevops/requirements/)
* [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/user/clusters/agent/)
* [Set up protected environments](https://docs.gitlab.com/ci/environments/protected_environments/)

***

# Editing this README

When you're ready to make this README your own, just edit this file and use the handy template below (or feel free to structure it however you want - this is just a starting point!). Thanks to [makeareadme.com](https://www.makeareadme.com/) for this template.

## Suggestions for a good README

Every project is different, so consider which of these sections apply to yours. The sections used in the template are suggestions for most open source projects. Also keep in mind that while a README can be too long and detailed, too long is better than too short. If you think your README is too long, consider utilizing another form of documentation rather than cutting out information.

## Name
Choose a self-explaining name for your project.

## Description
Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

## Badges
On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Visuals
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Installation
Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support
Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
>>>>>>> 5198c728ba5184d464aecc5842b792739ae0ed27
