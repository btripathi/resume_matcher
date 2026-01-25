import streamlit as st
import pandas as pd
from openai import OpenAI
import pypdf
import docx
import pytesseract
from PIL import Image
import io
import json
import os
import sqlite3
import datetime
import re
import time
import logging

# Suppress pypdf warnings
logging.getLogger("pypdf").setLevel(logging.ERROR)

# Try to import pdf2image for OCR
try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

# --- CONFIGURATION ---
st.set_page_config(
    page_title="AI Resume Matcher (Pro)",
    page_icon="🚀",
    layout="wide"
)

# Initialize Session State Defaults
if "lm_base_url" not in st.session_state:
    st.session_state.lm_base_url = "http://localhost:1234/v1"
if "lm_api_key" not in st.session_state:
    st.session_state.lm_api_key = "lm-studio"
if "ocr_enabled" not in st.session_state:
    st.session_state.ocr_enabled = True
if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()
if "run_logs" not in st.session_state:
    st.session_state.run_logs = []

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('resume_matcher.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS jobs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT,
                  content TEXT,
                  criteria TEXT,
                  upload_date TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS resumes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT,
                  content TEXT,
                  profile TEXT,
                  upload_date TIMESTAMP)''')

    try:
        c.execute("ALTER TABLE matches ADD COLUMN match_details TEXT")
    except:
        pass

    c.execute('''CREATE TABLE IF NOT EXISTS matches
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  job_id INTEGER,
                  resume_id INTEGER,
                  candidate_name TEXT,
                  match_score INTEGER,
                  decision TEXT,
                  reasoning TEXT,
                  missing_skills TEXT,
                  match_details TEXT,
                  FOREIGN KEY(job_id) REFERENCES jobs(id),
                  FOREIGN KEY(resume_id) REFERENCES resumes(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS runs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  job_id INTEGER,
                  created_at TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS run_matches
                 (run_id INTEGER,
                  match_id INTEGER,
                  PRIMARY KEY (run_id, match_id))''')

    conn.commit()
    conn.close()

init_db()

# --- HELPER FUNCTIONS ---

def generate_criteria_html(details):
    rows = ""
    for item in details:
        status = item.get('status', 'Unknown')
        color_style = "color: #333; background-color: #e0e0e0;"
        if "Met" in status: color_style = "color: #0f5132; background-color: #d1e7dd;"
        elif "Missing" in status: color_style = "color: #842029; background-color: #f8d7da;"
        elif "Partial" in status: color_style = "color: #664d03; background-color: #fff3cd;"

        req = str(item.get('requirement', '')).replace('<', '&lt;').replace('>', '&gt;')
        evi = str(item.get('evidence', '')).replace('<', '&lt;').replace('>', '&gt;')

        rows += f'<tr><td>{req}</td><td>{evi}</td><td><span class="status-badge" style="{color_style}">{status}</span></td></tr>'

    html = f"""
<style>
    .match-table {{width: 100%; border-collapse: collapse; font-family: sans-serif; margin-top: 10px;}}
    .match-table th {{background-color: #f0f2f6; padding: 12px 15px; text-align: left; border-bottom: 2px solid #e0e0e0; font-weight: 600; color: #31333F;}}
    .match-table td {{padding: 10px 15px; border-bottom: 1px solid #e0e0e0; vertical-align: top; font-size: 14px; color: #31333F;}}
    .match-table tr:hover {{background-color: #f9f9f9;}}
    .status-badge {{padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; display: inline-block;}}
</style>
<table class="match-table">
    <thead>
        <tr>
            <th style="width: 30%">Requirement</th>
            <th style="width: 55%">Evidence Found</th>
            <th style="width: 15%">Status</th>
        </tr>
    </thead>
    <tbody>
        {rows}
    </tbody>
</table>
"""
    return html

def generate_candidate_list_html(df):
    rows = ""
    for idx, row in df.iterrows():
        decision = row['decision']
        color_style = "color: #333; background-color: #e0e0e0;"
        if "Move Forward" in decision: color_style = "color: #0f5132; background-color: #d1e7dd;"
        elif "Reject" in decision: color_style = "color: #842029; background-color: #f8d7da;"
        elif "Review" in decision: color_style = "color: #664d03; background-color: #fff3cd;"

        score = row['match_score']
        score_color = "black"
        if score >= 80: score_color = "#0f5132"
        elif score < 50: score_color = "#842029"

        name = str(row['candidate_name']).replace('<', '&lt;')
        filename = str(row['filename']).replace('<', '&lt;')
        job_name = str(row['job_name']).replace('<', '&lt;')
        reasoning = str(row['reasoning']).replace('<', '&lt;')

        rows += f'<tr><td style="font-weight: 600;">{name}<br><span style="font-size: 11px; color: #666; font-weight: normal;">Resume: {filename}</span><br><span style="font-size: 11px; color: #0056b3; font-weight: normal;">Job: {job_name}</span></td><td style="color: {score_color}; font-weight: bold; font-size: 16px;">{score}%</td><td><span class="status-badge" style="{color_style}">{decision}</span></td><td style="font-size: 13px; color: #444;">{reasoning}</td></tr>'

    html = f"""
<style>
    .candidate-table {{width: 100%; border-collapse: collapse; font-family: sans-serif;}}
    .candidate-table th {{background-color: #f8f9fa; padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6; color: #495057;}}
    .candidate-table td {{padding: 12px; border-bottom: 1px solid #dee2e6; vertical-align: top;}}
    .candidate-table tr:hover {{background-color: #f8f9fa;}}
    .status-badge {{padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; display: inline-block; white-space: nowrap;}}
</style>
<table class="candidate-table">
    <thead>
        <tr>
            <th style="width: 25%">Match Details</th>
            <th style="width: 10%">Score</th>
            <th style="width: 15%">Decision</th>
            <th style="width: 50%">Reasoning</th>
        </tr>
    </thead>
    <tbody>
        {rows}
    </tbody>
</table>
"""
    return html

def get_db_connection():
    return sqlite3.connect('resume_matcher.db', timeout=30)

def get_llm_client():
    try:
        return OpenAI(base_url=st.session_state.lm_base_url, api_key=st.session_state.lm_api_key)
    except Exception as e:
        st.error(f"Error connecting to LLM: {e}")
        return None

def extract_json_from_text(text):
    try:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end+1]
            return json.loads(json_str)
        return None
    except json.JSONDecodeError:
        return None

def extract_text_from_pdf(file_bytes, use_ocr=False, log_container=None):
    try:
        if log_container:
            with log_container:
                st.text("  - Attempting native PDF extraction...")

        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for i, page in enumerate(pdf_reader.pages):
            content = page.extract_text()
            if content:
                text += content + "\n"

        text_len = len(text.strip())
        if log_container:
            with log_container:
                st.text(f"  - Extracted {text_len} chars via native method.")

        if text_len < 50 and use_ocr:
            if log_container:
                with log_container:
                    st.text("  - Text sparse (<50 chars). Triggering OCR fallback...")

            if PDF2IMAGE_AVAILABLE:
                try:
                    images = convert_from_bytes(file_bytes)
                    if log_container:
                        with log_container:
                            st.text(f"  - Converted PDF to {len(images)} images. Running Tesseract...")

                    ocr_text = ""
                    for i, img in enumerate(images):
                        page_text = pytesseract.image_to_string(img)
                        ocr_text += page_text + "\n"
                        if log_container:
                            with log_container:
                                st.text(f"    - OCR Page {i+1} done ({len(page_text)} chars)")

                    return ocr_text if ocr_text.strip() else "[OCR Failed: No text found in images]"
                except Exception as e:
                    err = f"[OCR Error: {e}]"
                    if log_container:
                        with log_container:
                            st.error(f"  - {err}")
                    return err
            else:
                msg = "[OCR Needed but pdf2image/poppler missing]"
                if log_container:
                    with log_container:
                        st.warning(f"  - {msg}")
                return msg

        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_text_from_docx(file_bytes):
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        return f"Error reading DOCX: {e}"

def analyze_jd_criteria(client, jd_text):
    if len(jd_text) < 50:
        return {"error": "Text too short to analyze"}

    prompt = f"""
    You are an expert HR Tech AI. Analyze this Job Description and extract EXTENSIVE criteria into a JSON object.

    INSTRUCTIONS:
    1. Extract ALL technical skills mentioned, distinguishing between mandatory (must-have) and optional (nice-to-have).
    2. Extract Education requirements in detail (Degree, Field).
    3. Extract exact Years of Experience required.
    4. Extract any specific Domain Knowledge (e.g. Finance, Healthcare, Automotive).
    5. Extract Soft Skills mentioned.
    6. Extract specific tool versions if mentioned (e.g. C++14, Python 3.8).

    JSON Format:
    {{
        "role_title": "Title",
        "must_have_skills": ["skill1", "skill2", "tool3", "framework4"],
        "nice_to_have_skills": ["skill5", "skill6"],
        "min_years_experience": 5,
        "experience_description": "Description of required experience",
        "education_requirements": ["BS Computer Science", "Masters preferred"],
        "domain_knowledge": ["Finance", "High Frequency Trading"],
        "soft_skills": ["Leadership", "Communication"],
        "key_responsibilities": ["Responsibility 1", "Responsibility 2"]
    }}

    Job Description:
    {jd_text[:15000]}
    """
    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.choices[0].message.content
        return extract_json_from_text(content) or {"error": "Could not parse JSON", "raw": content}
    except Exception as e:
        return {"error": str(e)}

def analyze_resume_profile(client, resume_text):
    if len(resume_text) < 50 or "[OCR Needed" in resume_text or "[OCR Error" in resume_text:
        return {
            "candidate_name": "Extraction Failed",
            "error_flag": True
        }

    prompt = f"""
    You are an expert HR Tech AI. Analyze this Resume and extract a RICH and DETAILED profile into a JSON object.

    CRITICAL INSTRUCTIONS:
    1. Extract ACTUAL data from the resume text below. Do NOT summarize too much; keep specific technologies and versions.
    2. Extract ALL skills found (Technical, Tools, Languages, Frameworks).
    3. Extract Total Years of Experience (estimate if not explicit).
    4. Extract Education details including degree and university.
    5. Extract a list of previous roles with company names, dates, and a summary of achievements.
    6. Check for startup experience or leadership roles.
    7. If fields are missing, use "N/A".

    JSON Format:
    {{
        "candidate_name": "Name",
        "email": "Email",
        "phone": "Phone",
        "location": "Location",
        "extracted_skills": ["Python", "C++", "AWS", "Docker", "Kubernetes", "etc..."],
        "years_experience": 5,
        "education_summary": "Degree, University",
        "domain_experience": ["Fintech", "Healthcare"],
        "startup_experience": false,
        "leadership_experience": false,
        "work_history": [
            {{ "company": "Company A", "role": "Role", "duration": "2020-2022", "summary": "Key achievements..." }}
        ]
    }}

    Resume Text:
    {resume_text[:15000]}
    """
    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.choices[0].message.content
        return extract_json_from_text(content) or {"error": "Could not parse JSON", "raw": content}
    except Exception as e:
        return {"error": str(e)}

def process_and_save_files(uploaded_files, client, file_type="resume"):
    conn = get_db_connection()
    c = conn.cursor()
    count = 0

    # Use st.status for spinner + collapsible logs
    with st.status(f"Processing {len(uploaded_files)} {file_type}(s)...", expanded=True) as status:
        progress_bar = st.progress(0)
        log_expander = st.expander("📝 Processing Logs", expanded=True)

        total_files = len(uploaded_files)

        for i, file in enumerate(uploaded_files):
            status.update(label=f"Processing {i+1}/{total_files}: {file.name}")

            file_bytes = file.read()
            filename = file.name
            text = ""

            table = "resumes" if file_type == "resume" else "jobs"
            c.execute(f"SELECT id FROM {table} WHERE filename = ?", (filename,))
            if c.fetchone():
                with log_expander:
                    st.write(f"⏭️ Skipped {filename} (Already exists)")
                progress_bar.progress((i + 1) / total_files)
                continue

            with log_expander:
                st.write(f"📄 Reading: {filename}")

            ext = filename.split('.')[-1].lower()
            if ext == 'pdf':
                text = extract_text_from_pdf(file_bytes, st.session_state.ocr_enabled, log_container=log_expander)
            elif ext in ['docx', 'doc']:
                text = extract_text_from_docx(file_bytes)
            elif ext == 'txt':
                text = str(file_bytes, 'utf-8')
            elif ext in ['jpg', 'jpeg', 'png']:
                try:
                    image = Image.open(io.BytesIO(file_bytes))
                    text = pytesseract.image_to_string(image)
                except:
                    text = "[Image OCR Failed]"

            if text:
                with log_expander:
                    st.write(f"🧠 Analyzing {filename} with AI...")

                if file_type == "resume":
                    profile_json = analyze_resume_profile(client, text)
                    c.execute("INSERT INTO resumes (filename, content, profile, upload_date) VALUES (?, ?, ?, ?)",
                              (filename, text, json.dumps(profile_json, indent=2), datetime.datetime.now().isoformat()))
                else:
                    criteria_json = analyze_jd_criteria(client, text)
                    c.execute("INSERT INTO jobs (filename, content, criteria, upload_date) VALUES (?, ?, ?, ?)",
                              (filename, text, json.dumps(criteria_json, indent=2), datetime.datetime.now().isoformat()))

                with log_expander:
                    st.write(f"✅ Saved {filename}")
                count += 1
            else:
                with log_expander:
                    st.error(f"❌ Could not extract text from {filename}")

            progress_bar.progress((i + 1) / total_files)

        status.update(label=f"Processing Complete! Added {count} new {file_type}(s).", state="complete", expanded=False)

    conn.commit()
    conn.close()

    return count

def evaluate_candidate(client, resume_text, jd_criteria, resume_profile_json):
    if "[OCR Needed" in resume_text or "Extraction Failed" in resume_profile_json:
        return json.dumps({
            "candidate_name": "Extraction Failed",
            "match_score": 0,
            "decision": "Review",
            "reasoning": "Could not extract resume text (OCR missing or file corrupt).",
            "missing_skills": [],
            "match_details": []
        })

    system_prompt = """
    You are a senior technical recruiter. Evaluate the candidate.

    SCORING RULES (Strict):
    - Score 0-49: "Reject" (Missing critical mandatory skills)
    - Score 50-79: "Review" (Good match, missing some nice-to-haves or minor gaps)
    - Score 80-100: "Move Forward" (Strong match, meets all mandatory skills)

    INSTRUCTIONS:
    1. Compare the Candidate Profile and RAW Resume Text against the Job Criteria.
    2. USE THE RAW RESUME TEXT to find evidence that might be missing from the profile summary.
    3. Look for "Start-up experience" or specific domain knowledge (Fintech, etc.) in the raw text.
    4. For "match_details", create a list of objects analyzing each key requirement found in the JD.
    5. "status" in match_details must be one of: "Met", "Partial", "Missing".

    Return JSON only:
    {
        "candidate_name": "Name",
        "match_score": 0-100,
        "decision": "Move Forward" | "Review" | "Reject",
        "reasoning": "Short explanation",
        "match_details": [
            { "requirement": "5+ years Python", "evidence": "7 years found at Company X", "status": "Met" },
            { "requirement": "AWS Cert", "evidence": "Not mentioned", "status": "Missing" }
        ]
    }
    """
    user_prompt = f"""
    JOB CRITERIA (JSON):
    {jd_criteria}

    CANDIDATE PROFILE (JSON):
    {resume_profile_json}

    RAW RESUME TEXT (Truncated):
    {resume_text[:15000]}
    """
    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# --- MAIN INTERFACE ---

col_header, col_settings = st.columns([6, 1])
with col_header:
    st.title("📄 AI Recruiting Workbench")

with col_settings:
    with st.popover("⚙️ Settings"):
        st.write("### LLM Configuration")
        st.text_input("LM Studio Base URL", key="lm_base_url")
        st.text_input("API Key", key="lm_api_key")
        st.divider()
        st.write("### PDF Processing")
        st.checkbox("Enable OCR", key="ocr_enabled")
        if st.session_state.ocr_enabled and not PDF2IMAGE_AVAILABLE:
            st.warning("⚠️ pdf2image missing. OCR will fail.")
        if st.button("🗑️ Reset Database", type="primary"):
            try:
                os.remove('resume_matcher.db')
                st.session_state.processed_files = set() # Clear session state tracker
                st.success("Database cleared!")
                time.sleep(1)
                st.rerun()
            except:
                st.error("Could not delete DB. It might be in use.")

tab1, tab2, tab3 = st.tabs(["1. Manage Data", "2. Run Analysis", "3. Match Results"])

# --- TAB 1: DATA MANAGEMENT ---
with tab1:
    client = get_llm_client()
    if not client:
        st.error("Please check Settings and start LM Studio server.")
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📂 Upload Job Descriptions")
        jd_files = st.file_uploader("Upload New JDs", accept_multiple_files=True, key="jd_upload")

        # Explicit Process Button for JDs
        if jd_files:
            if st.button(f"Process {len(jd_files)} JDs", key="proc_jds_btn", type="primary"):
                num = process_and_save_files(jd_files, client, "job")
                if num > 0:
                    st.success(f"Successfully added {num} Job Descriptions.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("No new files processed (duplicates detected).")

        conn = get_db_connection()
        jds = pd.read_sql("SELECT id, filename, criteria, upload_date FROM jobs", conn)

        def is_jd_error(criteria_text):
            if not criteria_text: return True
            try:
                data = json.loads(criteria_text)
                return 'error' in data
            except:
                return True

        st.markdown("### 📚 Stored JDs")
        show_jd_errors = st.checkbox("⚠️ Show Parsing Errors Only", key="jd_filter")

        if show_jd_errors and not jds.empty:
            jds = jds[jds['criteria'].apply(is_jd_error)]
            if jds.empty: st.info("No parsing errors found in JDs! 🎉")
            else: st.error(f"Found {len(jds)} JDs with parsing issues.")

        if not jds.empty:
            st.dataframe(jds[['filename', 'upload_date']], hide_index=True, width="stretch")

            st.divider()
            st.write("#### ✏️ Edit Job Criteria")
            jd_choice = st.selectbox("Select JD to Edit", jds['filename'])
            selected_row = jds[jds['filename'] == jd_choice].iloc[0]
            new_criteria = st.text_area("Extracted Criteria (JSON)", value=selected_row['criteria'], height=300, key=f"jd_editor_{selected_row['id']}")
            if st.button("Save JD Changes"):
                c = conn.cursor()
                c.execute("UPDATE jobs SET criteria = ? WHERE id = ?", (new_criteria, int(selected_row['id'])))
                conn.commit()
                st.success("Updated JD Criteria!")
                st.rerun()

            st.divider()
            with st.expander("🗑️ Danger Zone", expanded=show_jd_errors):
                st.markdown("**Delete Specific JD**")
                jd_to_delete = st.selectbox("Select JD", jds['filename'], key="del_jd_select")
                if st.button("Confirm Delete JD", type="primary"):
                     jd_del_id = jds[jds['filename'] == jd_to_delete].iloc[0]['id']
                     c = conn.cursor()
                     c.execute("DELETE FROM matches WHERE job_id = ?", (int(jd_del_id),))
                     c.execute("DELETE FROM runs WHERE job_id = ?", (int(jd_del_id),))
                     c.execute("DELETE FROM jobs WHERE id = ?", (int(jd_del_id),))
                     conn.commit()
                     st.success(f"Deleted {jd_to_delete}")
                     st.rerun()

                if show_jd_errors:
                    st.divider()
                    if st.button("⚠️ Delete All Failed JDs", type="primary", key="del_fail_jds"):
                        c = conn.cursor()
                        ids = tuple(jds['id'].tolist())
                        if len(ids) == 1: ids = f"({ids[0]})"
                        else: ids = str(ids)
                        c.execute(f"DELETE FROM matches WHERE job_id IN {ids}")
                        c.execute(f"DELETE FROM runs WHERE job_id IN {ids}")
                        c.execute(f"DELETE FROM jobs WHERE id IN {ids}")
                        conn.commit()
                        st.success("Deleted all failed JDs.")
                        st.rerun()

                st.divider()
                if st.button("⚠️ Delete ALL Job Descriptions", type="primary", key="del_all_jds"):
                     c = conn.cursor()
                     c.execute("DELETE FROM matches")
                     c.execute("DELETE FROM runs")
                     c.execute("DELETE FROM run_matches")
                     c.execute("DELETE FROM jobs")
                     conn.commit()
                     st.success("Deleted ALL.")
                     st.rerun()
        conn.close()

    with col2:
        st.subheader("📄 Upload Resumes")
        res_files = st.file_uploader("Upload New Resumes", accept_multiple_files=True, key="res_upload")

        # Explicit Process Button for Resumes
        if res_files:
            if st.button(f"Process {len(res_files)} Resumes", key="proc_res_btn", type="primary"):
                num = process_and_save_files(res_files, client, "resume")
                if num > 0:
                    st.success(f"Successfully added {num} Resumes.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("No new files processed (duplicates detected).")

        conn = get_db_connection()
        res = pd.read_sql("SELECT id, filename, profile, upload_date FROM resumes", conn)

        def is_res_error(profile_text):
            if not profile_text: return True
            try:
                data = json.loads(profile_text)
                return data.get('error_flag') or data.get('candidate_name') in ["Extraction Failed", "Unknown"]
            except:
                return True

        st.markdown("### 📚 Stored Resumes")
        show_res_errors = st.checkbox("⚠️ Show Parsing Errors Only", key="res_filter")

        if show_res_errors and not res.empty:
            res = res[res['profile'].apply(is_res_error)]
            if res.empty: st.info("No parsing errors found in Resumes! 🎉")
            else: st.error(f"Found {len(res)} Resumes with parsing issues.")

        if not res.empty:
            st.dataframe(res[['filename', 'upload_date']], hide_index=True, width="stretch")

            st.divider()
            st.write("#### ✏️ Edit Candidate Profile")
            res_choice = st.selectbox("Select Resume to Edit", res['filename'])
            selected_row = res[res['filename'] == res_choice].iloc[0]
            new_profile = st.text_area("Extracted Profile (JSON)", value=selected_row['profile'], height=300, key=f"res_editor_{selected_row['id']}")
            if st.button("Save Profile Changes"):
                c = conn.cursor()
                c.execute("UPDATE resumes SET profile = ? WHERE id = ?", (new_profile, int(selected_row['id'])))
                conn.commit()
                st.success("Updated Candidate Profile!")
                st.rerun()

            st.divider()
            with st.expander("🗑️ Danger Zone", expanded=show_res_errors):
                st.markdown("**Delete Specific Resume**")
                res_to_delete = st.selectbox("Select Resume", res['filename'], key="del_res_select")
                if st.button("Confirm Delete Resume", type="primary"):
                     res_del_id = res[res['filename'] == res_to_delete].iloc[0]['id']
                     c = conn.cursor()
                     c.execute("DELETE FROM matches WHERE resume_id = ?", (int(res_del_id),))
                     c.execute("DELETE FROM resumes WHERE id = ?", (int(res_del_id),))
                     conn.commit()
                     st.success(f"Deleted {res_to_delete}")
                     st.rerun()

                if show_res_errors:
                    st.divider()
                    if st.button("⚠️ Delete All Failed Resumes", type="primary", key="del_fail_res"):
                        c = conn.cursor()
                        ids = tuple(res['id'].tolist())
                        if len(ids) == 1: ids = f"({ids[0]})"
                        else: ids = str(ids)
                        c.execute(f"DELETE FROM matches WHERE resume_id IN {ids}")
                        c.execute(f"DELETE FROM resumes WHERE id IN {ids}")
                        conn.commit()
                        st.success("Deleted all failed Resumes.")
                        st.rerun()

                st.divider()
                if st.button("⚠️ Delete ALL Resumes", type="primary", key="del_all_res"):
                     c = conn.cursor()
                     c.execute("DELETE FROM matches")
                     c.execute("DELETE FROM run_matches")
                     c.execute("DELETE FROM resumes")
                     conn.commit()
                     st.success("Deleted ALL Resumes.")
                     st.rerun()
        conn.close()

# --- TAB 2: RUN ANALYSIS ---
with tab2:
    client = get_llm_client()
    if 'run_logs' not in st.session_state:
        st.session_state['run_logs'] = []

    conn = get_db_connection()
    job_options = pd.read_sql("SELECT id, filename, criteria FROM jobs", conn)
    selected_job_id = None

    col_setup1, col_setup2 = st.columns([1, 1])

    with col_setup1:
        st.markdown("#### 1. Select Job Description(s)")
        target_jobs = pd.DataFrame()

        if not job_options.empty:
            use_all_jds = st.checkbox("Select All JDs", value=False)
            if use_all_jds:
                target_jobs = job_options
                st.info(f"Selected all {len(target_jobs)} Job Descriptions.")
            else:
                selected_jd_names = st.multiselect("Choose JDs:", job_options['filename'])
                target_jobs = job_options[job_options['filename'].isin(selected_jd_names)]

        if not target_jobs.empty:
            with st.expander("Preview Criteria (First Selected JD)", expanded=False):
                st.code(target_jobs.iloc[0]['criteria'], language="json")

    all_resumes = pd.read_sql("SELECT id, filename, content, profile FROM resumes", conn)
    conn.close()

    with col_setup2:
        st.markdown("#### 2. Select Resumes")
        use_all = st.checkbox("Select All Available Resumes", value=True)
        target_resumes = pd.DataFrame()
        if use_all: target_resumes = all_resumes
        else:
            resume_options = all_resumes['filename'].tolist()
            selected_filenames = st.multiselect("Choose resumes:", resume_options)
            target_resumes = all_resumes[all_resumes['filename'].isin(selected_filenames)]

    st.write("---")

    if not target_jobs.empty and not target_resumes.empty:
        st.markdown("#### 3. Run Configuration")
        c_run1, c_run2, c_run3 = st.columns([2, 1, 1])
        with c_run1:
            default_run_name = f"Run {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            run_name = st.text_input("Name this Run (for history)", value=default_run_name)
        with c_run2:
            st.write("")
            rerun_existing = st.checkbox("Overwrite existing Match data?", value=False)
        with c_run3:
            st.write("")
            total_ops = len(target_jobs) * len(target_resumes)
            start_btn = st.button(f"🚀 Analyze ({total_ops} Matches)", type="primary", use_container_width=True)

        if start_btn:
            st.session_state['run_logs'] = []
            write_conn = get_db_connection()
            c = write_conn.cursor()

            run_job_id = int(target_jobs.iloc[0]['id']) if len(target_jobs) == 1 else None

            c.execute("INSERT INTO runs (name, job_id, created_at) VALUES (?, ?, ?)",
                      (run_name, run_job_id, datetime.datetime.now().isoformat()))
            run_id = c.lastrowid

            with st.status("Starting Analysis...", expanded=True) as status:
                progress_bar = st.progress(0)
                log_expander = st.expander("📝 Execution Logs", expanded=True)

                current_op = 0

                for j_idx, job_row in target_jobs.iterrows():
                    job_id = int(job_row['id'])
                    job_criteria = job_row['criteria']

                    for r_idx, res_row in target_resumes.iterrows():
                        current_op += 1
                        resume_id = int(res_row['id'])
                        log_prefix = f"[{job_row['filename']} x {res_row['filename']}]"

                        status.update(label=f"Processing {current_op}/{total_ops}: {log_prefix}")
                        log_msg = ""

                        c.execute("SELECT id FROM matches WHERE job_id = ? AND resume_id = ?", (job_id, resume_id))
                        existing = c.fetchone()

                        should_run_ai = True
                        match_id = None

                        if existing:
                            match_id = existing[0]
                            if not rerun_existing:
                                should_run_ai = False
                                log_msg = f"⏭️ Skipped {log_prefix} (Already matched)"

                        if should_run_ai:
                            max_retries = 3
                            data = None
                            for attempt in range(max_retries):
                                try:
                                    time.sleep(0.2)
                                    llm_response = evaluate_candidate(client, res_row['content'], job_criteria, res_row['profile'])
                                    data = extract_json_from_text(llm_response)
                                    if data: break
                                except Exception as e: pass

                            if data:
                                match_details_json = json.dumps(data.get('match_details', []))
                                missing_skills_json = json.dumps(data.get('missing_skills', []))

                                if match_id:
                                    c.execute('''UPDATE matches SET
                                                 candidate_name=?, match_score=?, decision=?, reasoning=?, missing_skills=?, match_details=?
                                                 WHERE id=?''',
                                              (data.get('candidate_name', 'Unknown'),
                                               data.get('match_score', 0),
                                               data.get('decision', 'Review'),
                                               data.get('reasoning', ''),
                                               missing_skills_json,
                                               match_details_json,
                                               match_id))
                                    log_msg = f"🔄 Updated {log_prefix}"
                                else:
                                    c.execute('''INSERT INTO matches (job_id, resume_id, candidate_name, match_score, decision, reasoning, missing_skills, match_details)
                                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                              (job_id, resume_id,
                                               data.get('candidate_name', 'Unknown'),
                                               data.get('match_score', 0),
                                               data.get('decision', 'Review'),
                                               data.get('reasoning', ''),
                                               missing_skills_json,
                                               match_details_json))
                                    match_id = c.lastrowid
                                    log_msg = f"✅ Matched {log_prefix}"
                            else:
                                error_reason = f"Parse Error after {max_retries} attempts."
                                if match_id:
                                    c.execute('''UPDATE matches SET decision=?, reasoning=? WHERE id=?''', ("Error", error_reason, match_id))
                                else:
                                    c.execute('''INSERT INTO matches (job_id, resume_id, candidate_name, match_score, decision, reasoning, missing_skills, match_details)
                                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                          (job_id, resume_id, "AI Parse Error", 0, "Error", error_reason, "[]", "[]"))
                                    match_id = c.lastrowid
                                log_msg = f"⚠️ Parse Fail {log_prefix}"

                        if match_id:
                            c.execute("INSERT OR IGNORE INTO run_matches (run_id, match_id) VALUES (?, ?)", (run_id, match_id))

                        if log_msg:
                            with log_expander: st.write(log_msg)

                        write_conn.commit()
                        progress_bar.progress(current_op / total_ops)

                status.update(label="Batch Analysis Completed!", state="complete", expanded=False)

            write_conn.close()
            st.toast(f"Run '{run_name}' Finished! Go to the 'Match Results' tab to view.")

# --- TAB 3: MATCH RESULTS ---
with tab3:
    conn = get_db_connection()
    st.subheader("📊 Match Results")

    runs = pd.read_sql("SELECT id, name, created_at, job_id FROM runs ORDER BY id DESC", conn)

    if runs.empty:
        st.info("No runs found. Go to 'Run Analysis' to start one.")
    else:
        runs['label'] = runs['name'] + " (" + runs['created_at'] + ")"
        selected_run_label = st.selectbox("Select Run History:", runs['label'])

        if selected_run_label:
            selected_run_row = runs[runs['label'] == selected_run_label].iloc[0]
            run_id = int(selected_run_row['id'])

            # --- RUN-LEVEL ACTIONS ---
            c_run_act1, c_run_act2 = st.columns([1, 4])
            with c_run_act1:
                if st.button("🗑️ Delete Run", key=f"del_run_{run_id}", type="primary"):
                    c = conn.cursor()
                    c.execute("DELETE FROM runs WHERE id = ?", (run_id,))
                    c.execute("DELETE FROM run_matches WHERE run_id = ?", (run_id,))
                    conn.commit()
                    st.success("Run deleted!")
                    time.sleep(0.5)
                    st.rerun()

            # Batch Rerun Button next to Delete Run
            with c_run_act2:
                if st.button("🔄 Rerun Batch", key=f"rerun_batch_{run_id}"):
                    client = get_llm_client()
                    if client:
                        matches_in_run = pd.read_sql(f"""
                            SELECT m.id, r.content as resume_text, r.profile as resume_profile, j.criteria as job_criteria, r.filename
                            FROM matches m
                            JOIN run_matches rm ON m.id = rm.match_id
                            JOIN resumes r ON m.resume_id = r.id
                            JOIN jobs j ON m.job_id = j.id
                            WHERE rm.run_id = {run_id}
                        """, conn)

                        if not matches_in_run.empty:
                            with st.status("Re-analyzing Batch...", expanded=True) as status:
                                progress_bar = st.progress(0)
                                log_expander = st.expander("📝 Batch Rerun Logs", expanded=True)

                                total = len(matches_in_run)
                                c = conn.cursor()

                                for i, row in matches_in_run.iterrows():
                                    status.update(label=f"Re-analyzing {i+1}/{total}: {row['filename']}")

                                    try:
                                        resp = evaluate_candidate(client, row['resume_text'], row['job_criteria'], row['resume_profile'])
                                        new_data = extract_json_from_text(resp)

                                        if new_data:
                                            match_details_json = json.dumps(new_data.get('match_details', []))
                                            missing_skills_json = json.dumps(new_data.get('missing_skills', []))

                                            c.execute('''UPDATE matches SET
                                                         candidate_name=?, match_score=?, decision=?, reasoning=?, missing_skills=?, match_details=?
                                                         WHERE id=?''',
                                                      (new_data.get('candidate_name', 'Unknown'),
                                                       new_data.get('match_score', 0),
                                                       new_data.get('decision', 'Review'),
                                                       new_data.get('reasoning', ''),
                                                       missing_skills_json,
                                                       match_details_json,
                                                       row['id']))
                                            conn.commit()
                                            with log_expander: st.write(f"✅ Updated {row['filename']}")
                                        else:
                                            with log_expander: st.error(f"❌ Failed to parse {row['filename']}")
                                    except Exception as e:
                                        with log_expander: st.error(f"❌ Error {row['filename']}: {e}")

                                    progress_bar.progress((i + 1) / total)

                                status.update(label="Batch Rerun Complete!", state="complete", expanded=False)

                            st.success("Batch Rerun Complete!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("No matches found in this run to rerun.")

            results = pd.read_sql(f"""
                SELECT m.id, m.candidate_name, m.match_score, m.decision, m.reasoning, r.filename, j.filename as job_name, m.match_details
                FROM matches m
                JOIN run_matches rm ON m.id = rm.match_id
                JOIN resumes r ON m.resume_id = r.id
                JOIN jobs j ON m.job_id = j.id
                WHERE rm.run_id = {run_id}
                ORDER BY m.match_score DESC
            """, conn)

            if not results.empty:
                # 1. HEATMAP MATRIX (If multiple JDs exist)
                unique_jobs = results['job_name'].unique()
                if len(unique_jobs) > 1:
                    st.markdown("### 🌡️ Correlation Matrix")
                    st.caption("Match Scores across all selected JDs")

                    # Pivot data for heatmap
                    matrix_df = results.pivot_table(
                        index='candidate_name',
                        columns='job_name',
                        values='match_score',
                        aggfunc='max' # Handle dupes if any
                    ).fillna(0).astype(int)

                    # Display with color formatting
                    try:
                        st.dataframe(
                            matrix_df.style.background_gradient(cmap='RdYlGn', vmin=0, vmax=100),
                            width="stretch"
                        )
                    except ImportError:
                        st.error("⚠️ Matplotlib is required for the heatmap. Run `pip install matplotlib`.")
                        st.dataframe(matrix_df, width="stretch")
                    st.divider()

                # 2. DETAILED LIST VIEW
                st.markdown("### 📝 Detailed Results")
                st.markdown(generate_candidate_list_html(results), unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("### 🔎 Match Analysis Details")

                results['label'] = results['candidate_name'] + " applied to " + results['job_name'] + " (" + results['match_score'].astype(str) + "%)"
                selected_candidate_label = st.selectbox("Select Match to Inspect:", results['label'])

                # Action Buttons (Rerun / Delete) - Moved right after selection
                if selected_candidate_label:
                    match_row = results[results['label'] == selected_candidate_label].iloc[0]
                    match_id = int(match_row['id'])

                    # Fetch Data for Actions (Resume/JD content)
                    action_data = pd.read_sql(f"""
                        SELECT r.content as resume_text, r.profile as resume_profile, j.criteria as job_criteria
                        FROM matches m
                        JOIN resumes r ON m.resume_id = r.id
                        JOIN jobs j ON m.job_id = j.id
                        WHERE m.id = {match_id}
                    """, conn).iloc[0]

                    col_act1, col_act2, col_act3 = st.columns([1, 1, 3])

                    with col_act1:
                        if st.button("🔄 Rerun Match", key=f"rerun_btn_{match_id}"):
                            client = get_llm_client()
                            if client:
                                # Using st.status for single match rerun
                                with st.status(f"Re-analyzing {match_row['filename']}...", expanded=True) as status:
                                    # Logic for single rerun...
                                    resp = evaluate_candidate(client, action_data['resume_text'], action_data['job_criteria'], action_data['resume_profile'])
                                    new_data = extract_json_from_text(resp)

                                    if new_data:
                                        match_details_json = json.dumps(new_data.get('match_details', []))
                                        missing_skills_json = json.dumps(new_data.get('missing_skills', []))

                                        c = conn.cursor()
                                        c.execute('''UPDATE matches SET
                                                     candidate_name=?, match_score=?, decision=?, reasoning=?, missing_skills=?, match_details=?
                                                     WHERE id=?''',
                                                  (new_data.get('candidate_name', 'Unknown'),
                                                   new_data.get('match_score', 0),
                                                   new_data.get('decision', 'Review'),
                                                   new_data.get('reasoning', ''),
                                                   missing_skills_json,
                                                   match_details_json,
                                                   match_id))
                                        conn.commit()
                                        status.update(label="Rerun Complete!", state="complete", expanded=False)
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        status.update(label="Analysis Failed", state="error")
                                        st.error("AI Parse failed.")

                    with col_act2:
                        if st.button("🗑️ Delete Match", key=f"del_btn_{match_id}", type="primary"):
                            c = conn.cursor()
                            c.execute("DELETE FROM matches WHERE id = ?", (match_id,))
                            c.execute("DELETE FROM run_matches WHERE match_id = ?", (match_id,))
                            conn.commit()
                            st.success("Match deleted.")
                            time.sleep(0.5)
                            st.rerun()

                    with st.container(border=True):
                        c_hdr1, c_hdr2 = st.columns([3, 1])
                        with c_hdr1:
                            st.title(match_row['candidate_name'])
                            st.caption(f"Job: {match_row['job_name']}")
                            decision = match_row['decision']
                            color = "green" if decision == "Move Forward" else "red" if decision == "Reject" else "orange"
                            st.markdown(f"**Decision:** :{color}[{decision}]")
                            st.write(f"_{match_row['reasoning']}_")
                        with c_hdr2:
                            st.metric("Match Score", f"{match_row['match_score']}%")

                        st.divider()
                        st.subheader("📋 Criteria Analysis")

                        raw_details = match_row['match_details']
                        if pd.isna(raw_details) or raw_details is None:
                             st.warning("Analysis details unavailable for this match. Please Re-run Analysis.")
                        else:
                            try:
                                details = json.loads(raw_details)
                                if isinstance(details, list) and details:
                                    st.markdown(generate_criteria_html(details), unsafe_allow_html=True)
                                elif isinstance(details, list) and not details:
                                    st.info("No detailed criteria breakdown provided by AI.")
                                else:
                                    st.info("No detailed breakdown available.")
                            except Exception as e:
                                st.error(f"Could not parse match details. Error: {e}")

            else:
                st.warning("No matches found in this run.")

    conn.close()
