# 📄 AI Resume Matcher (Local & Privacy-Focused)

A powerful recruiting tool that runs on your Mac (M1/M2/M3/M4) and can use either a local model server or a remote OpenAI-compatible API to match resumes against Job Descriptions.

## 🚀 Features

* **Universal File Support:** Upload PDFs (native & scanned/OCR), DOCX, and Text files.
* **Flexible Model Backends:** Use local models (LM Studio) or a remote OpenAI-compatible API.
* **Batch Processing:** Match hundreds of resumes against multiple JDs in one go ("All x All" matrix).
* **Intelligent Scoring:**
    * **0-49 (Reject):** Missing mandatory skills.
    * **50-79 (Review):** Good fit with minor gaps.
    * **80-100 (Move Forward):** Strong match.
* **Deep Dive Analysis:** Visual heatmap matrix and detailed criterion-by-criterion breakdown.

## 🛠️ Prerequisites

1.  **Mac with Apple Silicon** (M1/M2/M3/M4 recommended for speed).
2.  **Python 3.10+** installed.
3.  **Internet access** (script auto-installs Homebrew + dependencies if needed).

## ⚡️ Quick Start

1.  **Clone this repository:**
    ```bash
    git clone https://github.com/btripathi/resume_matcher.git
    cd resume_matcher
    ```

2.  **Run the installer/launcher (installs deps + starts app):**
    ```bash
    chmod +x install_and_run.sh
    ./install_and_run.sh
    ```

3.  **Configure model API (if local server is not running):**
    * Open **Settings** in the app.
    * Set **LM URL** and **API Key** for your remote OpenAI-compatible endpoint.
    * Click **Test Connection**, then **Save Config**.

Open:
- Web app: `http://localhost:8000/`
- API docs: `http://localhost:8000/docs`

## 🔄 Write Mode & Shared DB Sync

By default the app runs in **read-only mode** — all changes are saved to your local SQLite database only. To sync changes to a shared GitHub-hosted database:

1.  Get a `secrets.toml` file from the admin (contains GitHub token + writer credentials).
2.  Place it in the project root (it is gitignored).
3.  Open **Settings** in the app → enter your writer name and password → click **Enable Write Mode**.

Once enabled, local changes automatically push to the shared DB after each operation.

Alternatively, start with write mode on from the command line (skips auth, useful for the admin):
```bash
./install_and_run.sh --write
```

## ✅ Verify on a Clean Mac

```bash
./install_and_run.sh --smoke-test
```

Expected: auto-installs dependencies, starts a temporary server, verifies `/health`, then exits.

## 🧱 Architecture

FastAPI backend with a rich browser UI served at the root path.

### Available endpoints (v0.1)

- `GET /health`
- `GET /v1/jobs` / `POST /v1/jobs`
- `GET /v1/resumes` / `POST /v1/resumes`
- `POST /v1/matches/score` / `GET /v1/matches`
- `POST /v1/runs` (durable background queue)
- `GET /v1/runs` / `GET /v1/runs/{id}` / `GET /v1/runs/{id}/logs`

### Background jobs (survive browser refresh)

Queue long tasks as run objects:

```bash
curl -X POST http://localhost:8000/v1/runs \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "score_match",
    "payload": {"job_id": 1, "resume_id": 2, "auto_deep": true, "threshold": 50}
  }'
```

Then poll:

```bash
curl http://localhost:8000/v1/runs
curl http://localhost:8000/v1/runs/<run_id>/logs
```

## 📖 How to Use

### 1. Manage Data
* Go to the **Manage Data** tab.
* Drag & Drop your Job Descriptions (JDs) and Resumes.
* The system acts as a "Database" — files are processed once and saved. You can re-run matches anytime without re-uploading.

### 2. Run Analysis
* Go to the **Run Analysis** tab.
* Select one (or all) Job Descriptions.
* Select the Resumes you want to screen.
* Click **🚀 Analyze**.
* *Tip: Use the "Run Name" field to tag batch runs (e.g., "Senior Dev Q1 Hiring").*

### 3. Match Results
* View the **Correlation Matrix** heatmap to spot top candidates across multiple roles.
* Select a specific match to see the **Deep Dive**:
    * Match Score & Decision.
    * **Missing Skills** list.
    * **Criteria Table:** See exactly which resume text matched which JD requirement.
* Use the **Rerun** or **Delete** buttons to fix specific entries.

## 🔒 Data Privacy Note
This application uses a local SQLite database (`resume_matcher.db`) stored in the root folder. It is already in `.gitignore` — do not commit it if it contains real candidate data.
