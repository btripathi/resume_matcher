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

## ⚡️ Quick Start (Web App)

1.  **Clone this repository:**
    \`\`\`bash
    git clone https://github.com/your-username/resume-matcher.git
    cd resume-matcher
    \`\`\`

2.  **Run the installer/launcher (installs deps + starts app):**
    \`\`\`bash
    chmod +x install_and_run.sh
    ./install_and_run.sh
    \`\`\`

3.  **(Optional) Start in write mode:**
    \`\`\`bash
    ./install_and_run.sh --write
    \`\`\`

4.  **Configure model API (if local server is not running):**
    * Open **Settings** in the app.
    * Set **LM URL** and **API Key** for your remote OpenAI-compatible endpoint.
    * Click **Test Connection**, then **Save Config**.

Open:
- Web app: `http://localhost:8000/`
- API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## ✅ Verify on a Clean Mac

Use the built-in smoke test to validate a fresh setup end-to-end:

\`\`\`bash
chmod +x install_and_run.sh
./install_and_run.sh --smoke-test
\`\`\`

Expected result:
- Script auto-installs Homebrew if missing.
- Script installs `tesseract`, `poppler`, and Python packages.
- Temporary server starts and `/health` check passes.
- Script exits with success after verification.

## 🧱 Architecture

This project runs as a backend service with a rich browser UI served at the root path.

### Deploy to Render (Free)

This repo includes a Render blueprint at `render.yaml`.

1. Push latest `main` to GitHub.
2. In Render, choose **New +** -> **Blueprint** and select this repo.
3. Render will create the `resume-matcher` web service and deploy automatically.
4. In Render service settings, set required secret env vars:
   - `RESUME_MATCHER_LM_BASE_URL` (your model API base URL, e.g. `https://.../v1`)
   - `RESUME_MATCHER_LM_API_KEY`
   - `RESUME_MATCHER_GITHUB_TOKEN`
   - `RESUME_MATCHER_GITHUB_REPO` (format: `owner/repo`)
   - Optional writer auth from env:
     - `RESUME_MATCHER_WRITER_NAME`
     - `RESUME_MATCHER_WRITER_PASSWORD`
     - `RESUME_MATCHER_WRITER_USERS_JSON` (JSON list like `[{"name":"admin","password":"..."}]`)

Defaults in blueprint:
- `RESUME_MATCHER_READ_ONLY=true` for safe public mode.
- Health check path: `/health`

### Available endpoints (v0.1)

- `GET /health`
- `GET /v1/jobs`
- `POST /v1/jobs`
- `GET /v1/resumes`
- `POST /v1/resumes`
- `POST /v1/matches/score`
- `GET /v1/matches`
- `POST /v1/runs` (durable background queue)
- `GET /v1/runs`
- `GET /v1/runs/{id}`
- `GET /v1/runs/{id}/logs`

See migration details in `docs/migration_to_mature_architecture.md`.

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
This application uses a local SQLite database (`resume_matcher.db`) stored in the root folder. **Do not commit this file to GitHub** if it contains real candidate data (it is already added to `.gitignore`).

## 📤 How to Push to GitHub

If you are setting this up for the first time:

1.  **Initialize Git:**
    \`\`\`bash
    git init
    git add .
    git commit -m "Initial commit"
    \`\`\`

2.  **Connect & Push:**
    \`\`\`bash
    git branch -M main
    git remote add origin https://github.com/<username>/<repo>.git
    git push -u origin main
    \`\`\`

**Troubleshooting: "Updates were rejected" Error**
If you created the repo with a default README/License, you might get an error. You can force overwrite the remote files using:
\`\`\`bash
git push -f origin main
\`\`\`
