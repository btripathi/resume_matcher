import streamlit as st
import pandas as pd
import json
import time
import datetime
import logging
import urllib.request

# Import local modules
import database
import document_utils
import ai_engine
import github_sync  # <--- ADDED: Sync Module

# --- LOGGING CONFIGURATION ---
# Suppress pypdf warnings about malformed PDF structures (harmless noise)
logging.getLogger("pypdf").setLevel(logging.ERROR)

# --- CONFIGURATION ---
st.set_page_config(page_title="TalentScout AI", page_icon="🚀", layout="wide")

# --- ADDED: SYNC ON STARTUP ---
if "db_synced" not in st.session_state:
    with st.spinner("🔄 Checking GitHub for Database..."):
        if github_sync.pull_db():
            st.toast("✅ Database Restored from GitHub!", icon="☁️")
        else:
            st.toast("ℹ️ No remote DB found. Using Local.", icon="💻")
    st.session_state.db_synced = True

# Init Session State
DEFAULT_CLOUD_URL = "https://equitably-unmetalized-frieda.ngrok-free.dev/v1"
DEFAULT_LOCAL_URL = "http://127.0.0.1:1234/v1"

def _check_local_lm_available():
    url = DEFAULT_LOCAL_URL + "/models"
    try:
        with urllib.request.urlopen(url, timeout=0.5) as resp:
            return 200 <= resp.status < 400
    except Exception:
        return False

if "local_lm_available" not in st.session_state:
    st.session_state.local_lm_available = _check_local_lm_available()

if "lm_base_url" not in st.session_state:
    st.session_state.lm_base_url = DEFAULT_LOCAL_URL if st.session_state.local_lm_available else DEFAULT_CLOUD_URL
elif not st.session_state.local_lm_available and st.session_state.lm_base_url.startswith(DEFAULT_LOCAL_URL):
    st.session_state.lm_base_url = DEFAULT_CLOUD_URL
if "lm_api_key" not in st.session_state: st.session_state.lm_api_key = "lm-studio"
if "ocr_enabled" not in st.session_state: st.session_state.ocr_enabled = True
if "processed_files" not in st.session_state: st.session_state.processed_files = set()
if "write_mode" not in st.session_state: st.session_state.write_mode = False
if "write_mode_warned" not in st.session_state: st.session_state.write_mode_warned = False

# Auto-enable write mode locally if configured
try:
    auto_write = st.secrets.get("writer", {}).get("auto_write_mode", False)
    writer_name_auto = st.secrets.get("writer", {}).get("name", "")
    if auto_write and st.session_state.local_lm_available and not st.session_state.write_mode:
        lock_timeout = st.secrets.get("writer", {}).get("lock_timeout_hours", 6)
        lock_info = github_sync.get_lock(timeout_hours=lock_timeout)
        if lock_info and isinstance(lock_info, dict) and lock_info.get("owner") == (writer_name_auto or "unknown"):
            st.session_state.write_mode = True
        else:
            ok, _ = github_sync.acquire_lock(writer_name_auto or "unknown", timeout_hours=lock_timeout)
            if ok:
                st.session_state.write_mode = True
except Exception:
    pass

# Analysis Run State
if "is_running" not in st.session_state: st.session_state.is_running = False
if "stop_requested" not in st.session_state: st.session_state.stop_requested = False
if "rerun_config" not in st.session_state: st.session_state.rerun_config = None

# Upload Run State
if "is_uploading_jd" not in st.session_state: st.session_state.is_uploading_jd = False
if "stop_upload_jd" not in st.session_state: st.session_state.stop_upload_jd = False
if "is_uploading_res" not in st.session_state: st.session_state.is_uploading_res = False
if "stop_upload_res" not in st.session_state: st.session_state.stop_upload_res = False

# Initialize dynamic keys for file uploaders
if "jd_uploader_key" not in st.session_state: st.session_state.jd_uploader_key = 0
if "res_uploader_key" not in st.session_state: st.session_state.res_uploader_key = 0

# Selection State
if "selected_jd_filename" not in st.session_state: st.session_state.selected_jd_filename = None
if "selected_res_filename" not in st.session_state: st.session_state.selected_res_filename = None

db = database.DBManager()

# --- UI HELPERS ---
if not st.session_state.write_mode:
    st.info("Read-only mode: changes are local only and will NOT sync to the shared DB. Enable Write Mode to share results.", icon="🔒")

def sync_db_if_allowed():
    if st.session_state.write_mode:
        return github_sync.push_db()
    if not st.session_state.write_mode_warned:
        st.warning("Read-only mode: changes are not synced to shared DB. Enable Write Mode to push.")
        st.session_state.write_mode_warned = True
    return False

def _safe_int(val, default=0):
    try:
        if isinstance(val, (bytes, bytearray)):
            return int.from_bytes(val, byteorder="little", signed=False)
        if isinstance(val, str):
            return int(val.strip())
        return int(val)
    except Exception:
        return default

def generate_criteria_html(details):
    rows = ""
    cat_order = ["must_have_skills", "experience", "domain_knowledge", "nice_to_have_skills", "education_requirements", "soft_skills"]
    sorted_details = sorted(details, key=lambda x: cat_order.index(x.get('category')) if x.get('category') in cat_order else 99)

    for item in sorted_details:
        if not item: continue
        status = item.get('status', 'Unknown')
        cat = item.get('category', '').replace('_', ' ').upper()

        color = "color: #333; background-color: #e0e0e0;"
        if "Met" in status: color = "color: #0f5132; background-color: #d1e7dd;"
        elif "Missing" in status: color = "color: #842029; background-color: #f8d7da;"
        elif "Partial" in status: color = "color: #664d03; background-color: #fff3cd;"

        rows += f'<tr><td style="font-size:10px; font-weight:bold; color:#666;">{cat}</td><td>{item.get("requirement", "")}</td><td>{item.get("evidence", "")}</td><td><span class="status-badge" style="{color}">{status}</span></td></tr>'

    return f"""
    <style>
        .match-table {{width: 100%; border-collapse: collapse; font-family: sans-serif; margin-top: 10px;}}
        .match-table th {{background-color: #f0f2f6; padding: 12px 15px; text-align: left; border-bottom: 2px solid #e0e0e0; font-weight: 600; color: #31333F;}}
        .match-table td {{padding: 10px 15px; border-bottom: 1px solid #e0e0e0; vertical-align: top; font-size: 13px; color: #31333F;}}
        .match-table tr:hover {{background-color: #f9f9f9;}}
        .status-badge {{padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; display: inline-block;}}
    </style>
    <table class="match-table">
        <thead><tr><th>Category</th><th>Requirement</th><th>Evidence Found</th><th>Status</th></tr></thead>
        <tbody>{rows}</tbody>
    </table>
    """

def generate_candidate_list_html(df, threshold=75, is_deep=False):
    if df.empty: return "<p style='color: #666;'>No results found.</p>"
    rows = ""
    for idx, row in df.iterrows():
        score = _safe_int(row['match_score'], 0)
        job_name = row.get('job_name', 'Unknown Role')
        decision = row.get('decision', 'Reject')

        # --- DECISION LOGIC ---
        if decision == "Parsing Error" or decision == "Error":
             decision_label = "⚠️ Parsing Failed"
             badge_color = "color: #721c24; background-color: #f8d7da;" # Darker Red warning
             score_color = "#dc3545"
        elif is_deep:
            # For Deep matches, use the stored decision to stay consistent with scoring logic
            decision_label = decision
            if decision == "Move Forward":
                badge_color = "color: #0f5132; background-color: #d1e7dd;" # Green
                score_color = "#0f5132"
            elif decision == "Review":
                badge_color = "color: #664d03; background-color: #fff3cd;" # Yellow
                score_color = "#856404"
            else:
                decision_label = "Reject"
                badge_color = "color: #842029; background-color: #f8d7da;" # Red
                score_color = "#842029"
        else:
            if score < 50:
                decision_label = "Reject (Low Fit)"
                badge_color = "color: #842029; background-color: #f8d7da;" # Red
                score_color = "#842029"
            elif score < threshold:
                decision_label = "Potential (Below Threshold)"
                badge_color = "color: #555; background-color: #e2e3e5;" # Grey/Neutral
                score_color = "#555"
            else:
                decision_label = "Ready for Deep Scan"
                badge_color = "color: #084298; background-color: #cfe2ff;" # Blue
                score_color = "#084298"

        std_score_display = ""
        if 'standard_score' in row and pd.notna(row['standard_score']) and row['strategy'] == 'Deep':
            std_score_display = f"<br><span style='font-size: 10px; color: #666;'>Pass 1: {_safe_int(row['standard_score'])}%</span>"

        job_display = f"<br><span style='font-size: 11px; color: #007bff; font-weight:bold;'>Job: {job_name}</span>" if 'job_name' in df.columns and df['job_name'].nunique() > 1 else ""

        rows += f'<tr><td style="font-weight: 600;">{row["candidate_name"]}<br><span style="font-size: 11px; color: #666;">{row["res_name"]}</span>{job_display}</td><td style="color: {score_color}; font-weight: bold; font-size: 16px;">{score}%{std_score_display}</td><td><span class="status-badge" style="{badge_color}">{decision_label}</span></td><td style="font-size: 13px; color: #444;">{row["reasoning"]}</td></tr>'
    return f"""<style>.candidate-table {{width: 100%; border-collapse: collapse; margin-bottom: 20px;}}.candidate-table th {{background-color: #f8f9fa; padding: 12px; text-align: left;}}.candidate-table td {{padding: 12px; border-bottom: 1px solid #dee2e6; vertical-align: top;}}.status-badge {{padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px;}}</style><table class="candidate-table"><thead><tr><th>Candidate</th><th>Score</th><th>Decision</th><th>Reasoning</th></tr></thead><tbody>{rows}</tbody></table>"""

def generate_matrix_view(df, view_mode="All"):
    if df.empty: return

    if view_mode == "Deep Match Only":
        df_filtered = df[df['strategy'] == 'Deep']
    elif view_mode == "Standard Match Only":
        df_filtered = df[df['strategy'] != 'Deep']
    else:
        df_filtered = df

    if df_filtered.empty:
        st.info(f"No results found for '{view_mode}' filter.")
        return

    pivot_df = df_filtered.pivot_table(index='candidate_name', columns='job_name', values='match_score', aggfunc='max')
    pivot_df['Best Score'] = pivot_df.max(axis=1)
    pivot_df = pivot_df.sort_values(by='Best Score', ascending=False)

    headers = ["Candidate"] + list(pivot_df.columns[:-1]) + ["Best Score"]
    header_html = "".join([f"<th style='background-color:#f0f2f6; padding:10px; border-bottom:2px solid #ccc; text-align:center;'>{h}</th>" for h in headers])

    rows_html = ""
    for cand, row in pivot_df.iterrows():
        cells = f"<td style='padding:10px; font-weight:bold; border-bottom:1px solid #eee;'>{cand}</td>"
        for col in pivot_df.columns[:-1]:
            score = row[col]
            if pd.isna(score):
                cell_style = "color:#ccc; background-color:#f9f9f9;"
                val = "-"
            else:
                s = _safe_int(score, 0)
                if s >= 75: bg = "#d1e7dd"; color = "#0f5132"
                elif s >= 50: bg = "#fff3cd"; color = "#664d03"
                else: bg = "#f8d7da"; color = "#842029"
                cell_style = f"background-color:{bg}; color:{color}; font-weight:bold;"
                val = f"{s}%"
            cells += f"<td style='padding:10px; text-align:center; border-bottom:1px solid #eee; {cell_style}'>{val}</td>"

        best = int(row['Best Score'])
        cells += f"<td style='padding:10px; text-align:center; border-bottom:1px solid #eee; font-weight:bold; font-size:1.1em; background-color:#f8f9fa;'>{best}%</td>"
        rows_html += f"<tr>{cells}</tr>"

    st.markdown("### 📊 Cross-Job Match Matrix")
    st.markdown(f"""<div style="overflow-x:auto;"><table style="width:100%; border-collapse:collapse; font-family:sans-serif; font-size:0.9em;"><thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody></table></div>""", unsafe_allow_html=True)


# --- CORE MATCHING LOGIC ---
def run_analysis_batch(run_name, jobs, resumes, deep_match_thresh, auto_deep, force_rerun_pass1, match_by_tags=False, deep_only=False, force_rerun_deep=False, run_id=None, create_new_run=True):
    # --- SAFETY CHECK: Stop immediately if stop requested ---
    if st.session_state.stop_requested:
        st.warning("🛑 Analysis process stopped.")
        st.session_state.is_running = False
        st.session_state.stop_requested = False
        st.session_state.rerun_config = None
        time.sleep(1)
        st.rerun()
        return

    client = ai_engine.AIEngine(st.session_state.lm_base_url, st.session_state.lm_api_key)

    # Pre-calculate work to do for progress bar
    tasks = []
    if match_by_tags:
        # In tag mode, we find matching resumes for each JD
        for _, job in jobs.iterrows():
            # Prefer JD tags; fallback to filename if tags are missing
            jd_tags_raw = job.get('tags', None)
            if jd_tags_raw:
                jd_tags = [t.strip() for t in str(jd_tags_raw).split(',') if t.strip()]
            else:
                jd_tags = [str(job.get('filename', '')).strip()] if job.get('filename') else []

            if not jd_tags:
                matching_resumes = resumes.iloc[0:0]
            else:
                matching_resumes = resumes[resumes['tags'].fillna('').astype(str).apply(
                    lambda x: any(tag in [t.strip() for t in x.split(',')] for tag in jd_tags)
                )]

            if not matching_resumes.empty:
                # Create a specific run name for this JD
                specific_run_name = f"Auto: {job['filename']}"
                tasks.append({
                    "job": job,
                    "resumes": matching_resumes,
                    "run_name": specific_run_name,
                    "create_new_run": True
                })
    else:
        # Standard mode: One run, all JDs x all Resumes
        tasks.append({
            "job": None, # Will iterate all inside
            "resumes": resumes,
            "run_name": run_name,
            "create_new_run": create_new_run,
            "run_id": run_id
        })

    if not tasks and match_by_tags:
        st.error("No resumes found with tags matching the selected JDs.")
        st.session_state.is_running = False
        return

    total_ops = 0
    if match_by_tags:
        total_ops = sum([len(t['resumes']) for t in tasks])
    else:
        total_ops = len(jobs) * len(resumes)

    count = 0
    st.session_state.is_running = True

    progress_container = st.container()

    with progress_container:
        with st.status("Analyzing...", expanded=True) as status:
            master_bar = st.progress(0)
            task_display = st.empty()
            sub_bar = st.empty()
            log_placeholder = st.empty()
            log_lines = []

            def add_log(message):
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                log_lines.insert(0, f"<div style='margin-bottom:2px;'><span style='color:#888; font-size:0.8em;'>[{ts}]</span> {message}</div>")
                html_content = f"<div style='height:300px; overflow-y:auto; background-color:#f8f9fa; border:1px solid #dee2e6; padding:10px; border-radius:4px; font-family:monospace; font-size:0.9em; color:#212529;'>{''.join(log_lines)}</div>"
                log_placeholder.markdown(html_content, unsafe_allow_html=True)

            # --- PROCESS TASKS ---
            for task in tasks:
                if st.session_state.stop_requested: break

                # Create or reuse Run ID
                if task.get("create_new_run", True):
                    rid = db.create_run(task['run_name'], threshold=deep_match_thresh)
                else:
                    rid = int(task.get("run_id")) if task.get("run_id") else db.create_run(task['run_name'], threshold=deep_match_thresh)
                    # Clear old links so this run reflects the latest results
                    db.execute_query("DELETE FROM run_matches WHERE run_id = ?", (rid,))
                    # Update threshold for this run
                    db.execute_query("UPDATE runs SET threshold = ? WHERE id = ?", (deep_match_thresh, rid))

                # Determine JDs to loop over (Single specific JD or All selected JDs)
                jobs_to_process = pd.DataFrame([task['job']]) if match_by_tags else jobs
                resumes_to_process = task['resumes']

                for _, job in jobs_to_process.iterrows():
                    for _, res in resumes_to_process.iterrows():
                        # --- CHECK STOP REQUEST INSIDE LOOP ---
                        if st.session_state.stop_requested:
                            add_log("🛑 **Run stopped by user.**")
                            status.update(label="Stopped", state="error")
                            st.session_state.is_running = False
                            st.session_state.rerun_config = None
                            st.stop()
                            return # Exit completely

                        count += 1
                        current_resume_name = res['filename']
                        status.update(label=f"Match {count}/{total_ops}: {current_resume_name} vs {job['filename']}")
                        add_log(f"<b>Starting analysis for {current_resume_name}</b> vs {job['filename']}")

                        exist = db.get_match_if_exists(int(job['id']), int(res['id']))
                        mid = exist['id'] if exist else None
                        score = _safe_int(exist['match_score'], 0) if exist else 0

                        # --- PARSING ERROR CHECK ---
                        try:
                            profile_dict = json.loads(res['profile'])
                        except:
                            profile_dict = {}

                        if profile_dict.get('error_flag') or profile_dict.get('candidate_name') == "Parsing Error":
                            add_log(f"&nbsp;&nbsp;⚠️ Resume Parsing Error. Marking as Failed.")
                            data = {
                                "candidate_name": f"Error: {res['filename']}",
                                "match_score": 0,
                                "decision": "Parsing Error",
                                "reasoning": "The resume text could not be extracted or parsed correctly (e.g. Scanned PDF or corrupt file).",
                                "missing_skills": ["Unreadable Resume Content"]
                            }
                            mid = db.save_match(int(job['id']), int(res['id']), data, mid, strategy="Standard", standard_score=0, standard_reasoning="Parsing Failed")
                            if mid: db.link_run_match(rid, mid)
                            master_bar.progress(count/total_ops)
                            continue # Skip to next candidate

                        # Check if previous run was a technical failure (NEW LOGIC)
                        previous_failure = exist and (exist.get('decision') in ["Parsing Error", "Error"] or str(exist.get('match_score')) == "0")

                        should_run_standard = (not exist) or force_rerun_pass1 or previous_failure
                        if deep_only:
                            # Only run standard if we have no existing standard score to use
                            should_run_standard = not (exist and exist.get('standard_score'))

                        if should_run_standard:
                            msg_prefix = "🧠 Pass 1"
                            if previous_failure:
                                msg_prefix = "🔄 Retry (Prev Failed)"

                            task_display.info(f"{msg_prefix}: Holistic scan for **{current_resume_name}**...")
                            data = client.evaluate_standard(res['content'], job['criteria'], res['profile'])

                            # --- ERROR HANDLING FIX: Ensure 'data' is a dict ---
                            if data and isinstance(data, dict):
                                raw_reasoning = data.get('reasoning', "No reasoning provided.")
                                std_reasoning = "\n".join(raw_reasoning) if isinstance(raw_reasoning, list) else str(raw_reasoning)
                                mid = db.save_match(int(job['id']), int(res['id']), data, mid, strategy="Standard", standard_score=data['match_score'], standard_reasoning=std_reasoning)
                                score = data['match_score']
                                exist = db.get_match_if_exists(int(job['id']), int(res['id']))
                                add_log(f"&nbsp;&nbsp;🧠 Standard Score: {score}%")
                            else:
                                # Handle error case where data is None or not a dict
                                add_log(f"&nbsp;&nbsp;❌ Analysis failed or returned invalid format for {current_resume_name}. Skipping...")
                                # Mark as failed in DB to avoid re-running repeatedly
                                err_data = {
                                    "candidate_name": f"Error: {res['filename']}",
                                    "match_score": 0,
                                    "decision": "Error",
                                    "reasoning": "LLM Analysis failed or returned malformed data.",
                                    "missing_skills": []
                                }
                                mid = db.save_match(int(job['id']), int(res['id']), err_data, mid, strategy="Standard", standard_score=0, standard_reasoning="LLM Analysis Failed")
                                if mid: db.link_run_match(rid, mid) # Link failed matches too
                                master_bar.progress(count/total_ops)
                                continue # Skip this candidate
                        else:
                            if exist.get('strategy') == 'Deep' and exist.get('standard_score') is not None:
                                score = _safe_int(exist['standard_score'], 0)
                                add_log(f"&nbsp;&nbsp;ℹ️ Using existing Standard Score: {score}% (Pass 1 Skipped)")
                            else:
                                score = _safe_int(exist['match_score'], 0)
                                add_log(f"&nbsp;&nbsp;ℹ️ Using existing Match Score: {score}% (Pass 1 Skipped)")

                        is_already_deep = exist and exist['strategy'] == 'Deep'
                        qualifies_for_deep = _safe_int(score, 0) >= _safe_int(deep_match_thresh, 0)

                        if auto_deep and qualifies_for_deep:
                            if is_already_deep and not force_rerun_pass1 and not previous_failure and not force_rerun_deep:
                                mid = exist['id']
                                add_log("&nbsp;&nbsp;ℹ️ Deep match already exists. Skipping.")
                            else:
                                add_log(f"&nbsp;&nbsp;🔬 Threshold met ({score}%). Triggering Deep Scan...")
                                jd_c = json.loads(job['criteria'])

                                priority_reqs = []
                                if 'must_have_skills' in jd_c and isinstance(jd_c['must_have_skills'], list):
                                    priority_reqs.extend([('must_have_skills', v) for v in jd_c['must_have_skills']])
                                if 'domain_knowledge' in jd_c and isinstance(jd_c['domain_knowledge'], list):
                                    priority_reqs.extend([('domain_knowledge', v) for v in jd_c['domain_knowledge']])
                                if jd_c.get('min_years_experience', 0) > 0:
                                    priority_reqs.append(('experience', f"Minimum {jd_c['min_years_experience']} years relevant experience"))

                                bulk_reqs = []
                                for k in ['nice_to_have_skills', 'soft_skills', 'education_requirements', 'key_responsibilities']:
                                    if k in jd_c and isinstance(jd_c[k], list):
                                        bulk_reqs.extend([(k, v) for v in jd_c[k]])

                                details = []
                                total_criteria = len(priority_reqs) + len(bulk_reqs)
                                processed_count = 0

                                for rt, rv in priority_reqs:
                                    if st.session_state.stop_requested: break
                                    processed_count += 1
                                    add_log(f"&nbsp;&nbsp;&nbsp;&nbsp;🔎 Checking {rt.replace('_', ' ').title()}: <i>{str(rv)[:40]}...</i>")
                                    task_display.warning(f"🔬 Deep Scan: {processed_count}/{total_criteria} criteria checked (Priority)...")
                                    if total_criteria > 0:
                                        sub_bar.progress(processed_count/total_criteria)
                                    res_crit = client.evaluate_criterion(res['content'], rt, rv)
                                    if res_crit:
                                        details.append(res_crit)
                                        icon = "✅" if res_crit['status'] == 'Met' else "⚠️" if res_crit['status'] == 'Partial' else "❌"
                                        add_log(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↳ {icon} {res_crit['status']}")

                                if st.session_state.stop_requested: break

                                if bulk_reqs:
                                    task_display.info(f"⚡ Bulk Scan: Checking {len(bulk_reqs)} secondary criteria... ({processed_count}/{total_criteria})")
                                    add_log(f"&nbsp;&nbsp;&nbsp;&nbsp;⚡ Bulk checking {len(bulk_reqs)} secondary items...")
                                    if total_criteria > 0:
                                        sub_bar.progress(processed_count/total_criteria)
                                    bulk_results = client.evaluate_bulk_criteria(res['content'], bulk_reqs)
                                    if bulk_results: details.extend(bulk_results)
                                    processed_count += len(bulk_reqs)
                                    if total_criteria > 0:
                                        sub_bar.progress(min(1.0, processed_count/total_criteria))

                                sub_bar.empty()
                                if not details:
                                    add_log("&nbsp;&nbsp;⚠️ Deep scan returned no evaluated criteria. Keeping Pass 1 results.")
                                    # Keep existing standard result; do not overwrite with a Deep result.
                                    if not mid and data and isinstance(data, dict):
                                        std_reasoning = data.get('reasoning', "No reasoning provided.")
                                        std_reasoning = "\n".join(std_reasoning) if isinstance(std_reasoning, list) else str(std_reasoning)
                                        mid = db.save_match(int(job['id']), int(res['id']), data, mid, strategy="Standard", standard_score=data.get('match_score', 0), standard_reasoning=std_reasoning)
                                    continue
                                sf, df, rf = client.generate_final_decision(res['filename'], details, strategy="Deep")

                                std_score_saved = exist.get('standard_score', score)
                                std_reasoning_saved = exist.get('standard_reasoning', exist.get('reasoning'))

                                mid = db.save_match(int(job['id']), int(res['id']), {"candidate_name": res['filename'], "match_score": sf, "decision": df, "reasoning": rf, "match_details": details}, mid, strategy="Deep", standard_score=std_score_saved, standard_reasoning=std_reasoning_saved)
                                add_log(f"&nbsp;&nbsp;🏁 <b>Deep Match Final: {sf}% ({df})</b>")

                        elif auto_deep and not qualifies_for_deep:
                            add_log(f"&nbsp;&nbsp;⏭️ Score ({score}%) below threshold ({deep_match_thresh}%). Skipping Deep Match.")

                        if mid: db.link_run_match(rid, mid)
                        master_bar.progress(count/total_ops)

            status.update(label="Complete!", state="complete")

            # --- AUTO SAVE TRIGGER ---
            with st.spinner("Syncing results to GitHub..."):
                sync_db_if_allowed()

    st.session_state.is_running = False
    st.session_state.stop_requested = False
    st.session_state.rerun_config = None
    time.sleep(1)
    st.rerun()

# --- CALLBACKS ---
def start_run_callback():
    st.session_state.is_running = True
    st.session_state.stop_requested = False

def stop_run_callback():
    st.session_state.stop_requested = True

def prepare_rerun_callback(name, jobs_df, resumes_df, thresh, auto_deep, force_rerun, match_by_tags=False, deep_only=False, force_rerun_deep=False, create_new_run=False, run_id=None):
    st.session_state.rerun_config = {
        "run_name": name,
        "jobs": jobs_df,
        "resumes": resumes_df,
        "thresh": thresh,
        "auto": auto_deep,
        "force": force_rerun,
        "tags": match_by_tags,
        "deep_only": deep_only,
        "force_rerun_deep": force_rerun_deep,
        "create_new_run": create_new_run,
        "run_id": run_id
    }
    st.session_state.is_running = True
    st.session_state.stop_requested = False

def start_jd_upload():
    st.session_state.is_uploading_jd = True
    st.session_state.stop_upload_jd = False

def stop_jd_upload():
    st.session_state.stop_upload_jd = True

def start_res_upload():
    st.session_state.is_uploading_res = True
    st.session_state.stop_upload_res = False

def stop_res_upload():
    st.session_state.stop_upload_res = True

# --- HEADER & SETTINGS ---
col_head, col_set = st.columns([6, 1])
with col_head: st.title("🚀 TalentScout: Intelligent Resume Screening")
with col_set:
    with st.popover("⚙️ Settings"):
        st.write("### Configuration")
        st.text_input("LM URL", key="lm_base_url")
        st.text_input("API Key", key="lm_api_key")
        st.checkbox("Enable OCR", key="ocr_enabled")

        # --- WRITE MODE (SINGLE WRITER) ---
        st.divider()
        st.write("### Write Mode")
        lock_timeout = 6
        try:
            lock_timeout = st.secrets.get("writer", {}).get("lock_timeout_hours", 6)
        except Exception:
            lock_timeout = 6

        lock_info = github_sync.get_lock(timeout_hours=lock_timeout)
        if lock_info and isinstance(lock_info, dict):
            owner = lock_info.get("owner", "unknown")
            created = lock_info.get("created_at", "unknown time")
            if lock_info.get("expired"):
                st.caption(f"Write lock: **{owner}** since {created} (expired)")
            else:
                st.caption(f"Write lock: **{owner}** since {created}")
        else:
            st.caption("Write lock: none")

        writer_name_default = ""
        try:
            writer_name_default = st.secrets.get("writer", {}).get("name", "")
        except Exception:
            writer_name_default = ""
        writer_name = st.text_input("Writer name", value=writer_name_default, key="writer_name")
        writer_password = st.text_input("Write password", type="password", key="writer_password")

        st.caption(f"Lock auto-expires after {lock_timeout} hours. Use Release before closing if possible.")

        if st.button("Enable Write Mode"):
            expected = None
            try:
                expected = st.secrets.get("writer", {}).get("password")
            except Exception:
                expected = None
            if not expected:
                st.error("Write password not configured in secrets.")
            elif writer_password != expected:
                st.error("Incorrect write password.")
            else:
                # If lock already belongs to this writer, just resume write mode
                if lock_info and isinstance(lock_info, dict) and lock_info.get("owner") == (writer_name or "unknown"):
                    st.session_state.write_mode = True
                    st.session_state.write_mode_warned = False
                    st.success("Write mode resumed (existing lock).")
                    time.sleep(0.2)
                    st.rerun()
                else:
                    ok, msg = github_sync.acquire_lock(writer_name or "unknown", timeout_hours=lock_timeout)
                    if ok:
                        st.session_state.write_mode = True
                        st.session_state.write_mode_warned = False
                        st.success(msg)
                        time.sleep(0.2)
                        st.rerun()
                    else:
                        st.error(msg)

        if st.session_state.write_mode:
            if st.button("Disable Write Mode / Release Lock"):
                ok, msg = github_sync.release_lock(writer_name or "unknown")
                if ok:
                    st.session_state.write_mode = False
                    st.session_state.write_mode_warned = False
                    st.success(msg)
                    time.sleep(0.2)
                    st.rerun()
                else:
                    st.error(msg)

        if st.button("Force Unlock (Admin)"):
            expected = None
            try:
                expected = st.secrets.get("writer", {}).get("password")
            except Exception:
                expected = None
            if not expected:
                st.error("Write password not configured in secrets.")
            elif writer_password != expected:
                st.error("Incorrect write password.")
            else:
                ok, msg = github_sync.release_lock(writer_name or "unknown", force=True)
                if ok:
                    st.session_state.write_mode = False
                    st.session_state.write_mode_warned = False
                    st.success(msg)
                    time.sleep(0.2)
                    st.rerun()
                else:
                    st.error(msg)

        if st.button("🔌 Test Connection"):
            try:
                from openai import OpenAI
                tmp_client = OpenAI(base_url=st.session_state.lm_base_url, api_key=st.session_state.lm_api_key)
                models = tmp_client.models.list()
                st.success(f"Connected to LM Studio! Found {len(models.data)} models.")
            except Exception as e:
                st.error(f"Connection failed. Error: {e}")

        # --- SYNC BUTTONS ---
        st.divider()
        c1, c2 = st.columns(2)
        if c1.button("💾 Push to GitHub", type="primary", disabled=not st.session_state.write_mode):
            with st.spinner("Pushing database to GitHub..."):
                if sync_db_if_allowed():
                    st.success("Synced!")
                else:
                    st.error("Failed. Check logs.")

        if c2.button("📥 Force Pull"):
            with st.spinner("Pulling from GitHub..."):
                if github_sync.pull_db():
                    st.success("Pulled!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Not Found")

        if st.button("🗑️ Reset DB", type="secondary"):
            db.execute_query("DELETE FROM matches")
            db.execute_query("DELETE FROM runs")
            db.execute_query("DELETE FROM run_matches")
            db.execute_query("DELETE FROM jobs")
            db.execute_query("DELETE FROM resumes")
            st.session_state.processed_files = set()
            with st.spinner("Syncing reset to GitHub..."):
                sync_db_if_allowed()
            st.success("Reset Complete")
            time.sleep(1)
            st.rerun()

# --- TABS DEFINITION ---
tab1, tab2, tab3 = st.tabs(["1. Manage Data", "2. Run Analysis", "3. Match Results"])

# --- TAB 1: MANAGE DATA ---
with tab1:
    if not st.session_state.write_mode:
        st.info("Read-only mode: uploads/edits are saved locally only and won't sync to the shared DB.", icon="🔒")
    client = ai_engine.AIEngine(st.session_state.lm_base_url, st.session_state.lm_api_key)

    # SPLIT TAB INTO SUB-TABS
    subtab_jd, subtab_res, subtab_tags = st.tabs(["📂 Job Descriptions", "📄 Candidate Resumes", "🏷️ Tag Manager"])

    # --- JOB DESCRIPTIONS SUB-TAB ---
    with subtab_jd:
        with st.expander("📤 Upload New Job Descriptions", expanded=False):
            tag_options = sorted(set(db.list_tags()))
            jd_tag_assign = st.multiselect("Assign Tag(s) to JDs (Optional):", tag_options)
            jd_tag_val = ",".join(jd_tag_assign) if jd_tag_assign else None
            jd_up = st.file_uploader("Upload JDs (PDF/DOCX/TXT)", accept_multiple_files=True, key=f"jd_up_{st.session_state.jd_uploader_key}")
            force_reparse_jd = st.checkbox("Force Reparse Existing JDs", value=False)

            if jd_up:
                if not st.session_state.is_uploading_jd:
                    st.button("Process New JDs", type="primary", on_click=start_jd_upload)
                else:
                    st.button("🛑 STOP UPLOAD", type="primary", on_click=stop_jd_upload)

                    with st.status("Processing JDs...", expanded=True) as status:
                        total_jds = len(jd_up)
                        prog_bar = st.progress(0)

                        for i, f in enumerate(jd_up):
                            if st.session_state.stop_upload_jd:
                                status.update(label="Stopped", state="error")
                                break

                            status.update(label=f"Processing {i+1}/{total_jds}: {f.name}")
                            existing = db.get_job_by_filename(f.name)
                            if existing and not force_reparse_jd:
                                continue

                            file_bytes = f.read()
                            file_name = f.name.lower()

                            if file_name.endswith('.pdf'):
                                text = document_utils.extract_text_from_pdf(file_bytes, use_ocr=st.session_state.ocr_enabled)
                            elif file_name.endswith('.docx'):
                                text = document_utils.extract_text_from_docx(file_bytes)
                            else:
                                text = str(file_bytes, 'utf-8', errors='ignore')

                            analysis = client.analyze_jd(text)
                            if existing:
                                db.update_job_content(existing['id'], text, analysis)
                                if jd_tag_val:
                                    db.update_job_tags(existing['id'], jd_tag_val)
                            else:
                                db.add_job(f.name, text, analysis, tags=jd_tag_val)
                            if jd_tag_val:
                                for t in [t.strip() for t in jd_tag_val.split(",") if t.strip()]:
                                    db.add_tag(t)

                            prog_bar.progress((i + 1) / total_jds)

                        if not st.session_state.stop_upload_jd:
                            status.update(label="Complete!", state="complete")
                            st.session_state.jd_uploader_key += 1

                            # --- AUTO SAVE TRIGGER ---
                            with st.spinner("Syncing to GitHub..."):
                                sync_db_if_allowed()

                    st.session_state.is_uploading_jd = False
                    st.session_state.stop_upload_jd = False
                    st.rerun()

        st.subheader("Manage JDs")
        try:
            jds = db.fetch_dataframe("SELECT id, filename, criteria, content, tags, upload_date FROM jobs")
        except:
            jds = db.fetch_dataframe("SELECT id, filename, criteria, content, upload_date FROM jobs")
            jds["tags"] = None
        st.caption(f"Total Job Descriptions: {len(jds)}")

        if not jds.empty:
            # --- INTERACTIVE JD TABLE ---
            st.caption("Click on a row to edit.")
            event_jd = st.dataframe(
                jds[['filename', 'tags', 'upload_date']],
                hide_index=True,
                width="stretch",
                selection_mode="single-row",
                on_select="rerun"
            )

            selected_jd_row = None
            if len(event_jd.selection.rows) > 0:
                selected_index = event_jd.selection.rows[0]
                selected_jd_row = jds.iloc[selected_index]
                st.session_state.selected_jd_filename = selected_jd_row['filename']

            # --- SHOW EDIT PANEL IF SELECTED ---
            if "selected_jd_filename" in st.session_state and st.session_state.selected_jd_filename in jds['filename'].values:
                current_filename = st.session_state.selected_jd_filename
                selected_jd_row = jds[jds['filename'] == current_filename].iloc[0]

                st.divider()
                st.markdown(f"**Editing: `{selected_jd_row['filename']}`**")

                # Hidden ID for logic
                jd_edit_id = int(selected_jd_row['id'])

                with st.expander("🔍 Inspect Raw Extracted Text", expanded=False):
                    st.text_area("Raw Text Content", value=selected_jd_row['content'], height=300, disabled=True, key=f"raw_jd_{jd_edit_id}")

                curr_jd_tags_str = selected_jd_row['tags'] if 'tags' in selected_jd_row and selected_jd_row['tags'] else ""
                curr_jd_tags_list = [t.strip() for t in curr_jd_tags_str.split(',')] if curr_jd_tags_str else []
                all_tag_opts = sorted(set(db.list_tags() + curr_jd_tags_list))
                new_jd_tags = st.multiselect("Edit JD Tags", options=all_tag_opts, default=curr_jd_tags_list, key=f"jd_tag_ed_{jd_edit_id}")
                new_jd_tags_val = ",".join(new_jd_tags) if new_jd_tags else None

                new_crit = st.text_area("JSON Criteria", value=selected_jd_row['criteria'], height=300, key=f"jd_ed_{jd_edit_id}")

                ec1, ec2 = st.columns(2)
                if ec1.button("Save JD Changes", key=f"sav_jd_{jd_edit_id}"):
                    db.execute_query("UPDATE jobs SET criteria = ?, tags = ? WHERE id = ?", (new_crit, new_jd_tags_val, jd_edit_id))
                    if new_jd_tags:
                        for t in [t.strip() for t in new_jd_tags if t.strip()]:
                            db.add_tag(t)

                    # --- AUTO SAVE TRIGGER ---
                    with st.spinner("Syncing to GitHub..."):
                        sync_db_if_allowed()

                    st.success("Saved!")
                    time.sleep(0.5)
                    st.rerun()
                if ec2.button("Delete JD", key=f"del_jd_{jd_edit_id}", type="primary"):
                    db.execute_query("DELETE FROM matches WHERE job_id = ?", (jd_edit_id,))
                    db.execute_query("DELETE FROM jobs WHERE id = ?", (jd_edit_id,))

                    # --- AUTO SAVE TRIGGER ---
                    with st.spinner("Syncing to GitHub..."):
                        sync_db_if_allowed()

                    # Clear selection on delete
                    del st.session_state.selected_jd_filename
                    st.rerun()
        else:
            st.info("No Job Descriptions uploaded yet.")

    # --- RESUMES SUB-TAB ---
    with subtab_res:
        # Available tags for logic
        avail_jds = db.fetch_dataframe("SELECT id, filename FROM jobs")
        jd_options = {row['filename']: str(row['filename']) for idx, row in avail_jds.iterrows()}
        tag_options = sorted(set(db.list_tags() + list(jd_options.keys())))

        with st.expander("📤 Upload / Import Resumes", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.write("#### File Upload")
                selected_tags = st.multiselect("Assign Tag(s) (Optional):", tag_options)
                tag_val = ",".join(selected_tags) if selected_tags else None

                res_up = st.file_uploader("Upload Resumes (PDF/DOCX)", accept_multiple_files=True, key=f"res_up_{st.session_state.res_uploader_key}")
                force_reparse_res = st.checkbox("Force Reparse Existing Resumes", value=False)

                if res_up:
                    if not st.session_state.is_uploading_res:
                        st.button("Process New Resumes", type="primary", on_click=start_res_upload)
                    else:
                        st.button("🛑 STOP UPLOAD", type="primary", on_click=stop_res_upload)

                        with st.status("Processing Resumes...", expanded=True) as status:
                            total_res = len(res_up)
                            prog_bar = st.progress(0)

                            for i, f in enumerate(res_up):
                                if st.session_state.stop_upload_res:
                                    status.update(label="Stopped", state="error")
                                    break

                                status.update(label=f"Processing {i+1}/{total_res}: {f.name}")
                                existing = db.get_resume_by_filename(f.name)
                                if existing and not force_reparse_res:
                                    continue

                                file_bytes = f.read()
                                file_name = f.name.lower()
                                if file_name.endswith('.pdf'):
                                    text = document_utils.extract_text_from_pdf(file_bytes, use_ocr=st.session_state.ocr_enabled)
                                elif file_name.endswith('.docx'):
                                    text = document_utils.extract_text_from_docx(file_bytes)
                                else:
                                    text = str(file_bytes, 'utf-8', errors='ignore')

                                analysis = client.analyze_resume(text)

                                if existing:
                                    db.update_resume_content(existing['id'], text, analysis)
                                    if tag_val: db.update_resume_tags(existing['id'], tag_val)
                                else:
                                    db.add_resume(f.name, text, analysis, tags=tag_val)
                                if tag_val:
                                    for t in [t.strip() for t in tag_val.split(",") if t.strip()]:
                                        db.add_tag(t)

                                prog_bar.progress((i + 1) / total_res)

                            if not st.session_state.stop_upload_res:
                                status.update(label="Complete!", state="complete")
                                st.session_state.res_uploader_key += 1

                                # --- AUTO SAVE TRIGGER ---
                                with st.spinner("Syncing to GitHub..."):
                                    sync_db_if_allowed()

                        st.session_state.is_uploading_res = False
                        st.session_state.stop_upload_res = False
                        st.rerun()

            with c2:
                st.write("#### Bulk JSON Import")
                uploaded_json = st.file_uploader("Import Processed JSON", type=["json"], key="json_up")
                if uploaded_json is not None and st.button("📥 Import JSON Data"):
                    try:
                        data = json.load(uploaded_json)
                        count = 0
                        for record in data:
                            existing = db.get_resume_by_filename(record['filename'])
                            if existing:
                                db.update_resume_content(existing['id'], record['content'], record['profile'])
                            else:
                                db.add_resume(record['filename'], record['content'], record['profile'])
                            count += 1
                        st.success(f"Imported {count} resumes successfully!")

                        # --- AUTO SAVE TRIGGER ---
                        with st.spinner("Syncing to GitHub..."):
                            sync_db_if_allowed()

                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error importing JSON: {e}")

        # --- RESUME LIST ---
        st.subheader("Manage Resumes")
        try:
            ress = db.fetch_dataframe("SELECT id, filename, profile, tags, content, upload_date FROM resumes")
        except:
             ress = db.fetch_dataframe("SELECT id, filename, profile, content, upload_date FROM resumes")
             ress['tags'] = None
        def _normalize_tag_value(val):
            if val is None:
                return ""
            if isinstance(val, bytes):
                return val.decode("utf-8", errors="ignore")
            return str(val)
        ress['tags'] = ress['tags'].apply(_normalize_tag_value)
        st.caption(f"Total Resumes: {len(ress)}")

        if not ress.empty:
            # --- FILTER LIST ---
            all_tags = set()
            for t_str in ress['tags'].dropna().unique():
                for t in t_str.split(','):
                    all_tags.add(t.strip())

            list_filter = st.multiselect("Filter List by Tag:", sorted(list(all_tags)), key="list_tag_filter")

            if list_filter:
                mask = ress['tags'].apply(lambda x: any(tag in [t.strip() for t in x.split(',')] for tag in list_filter))
                filtered_ress = ress[mask]
            else:
                filtered_ress = ress
            st.caption(f"Filtered Resumes: {len(filtered_ress)}")

            st.caption("Click on a row to edit details.")
            display_ress = filtered_ress.copy()
            display_ress['tags'] = display_ress['tags'].fillna('')
            event_res = st.dataframe(
                display_ress[['filename', 'tags', 'upload_date']],
                hide_index=True,
                width="stretch",
                selection_mode="single-row",
                on_select="rerun",
                key=f"res_table_{st.session_state.get('res_table_refresh_id', 0)}"
            )

            selected_res_row = None
            if len(event_res.selection.rows) > 0:
                selected_index = event_res.selection.rows[0]
                selected_res_row = filtered_ress.iloc[selected_index]
                st.session_state.selected_res_filename = selected_res_row['filename']
                st.session_state.res_table_refresh_id = st.session_state.get("res_table_refresh_id", 0) + 1

            # --- SHOW EDIT PANEL IF SELECTED ---
            if "selected_res_filename" in st.session_state and st.session_state.selected_res_filename in ress['filename'].values:
                current_filename = st.session_state.selected_res_filename
                row = ress[ress['filename'] == current_filename].iloc[0]

                st.divider()
                st.markdown(f"**Editing: `{row['filename']}`**")

                # --- TAG EDITOR ---
                curr_tags_str = row['tags'] if 'tags' in row and row['tags'] else ""
                curr_tags_list = [t.strip() for t in curr_tags_str.split(',')] if curr_tags_str else []

                all_opts = list(tag_options)
                for t in curr_tags_list:
                    if t not in all_opts: all_opts.append(t)

                tag_key = f"tag_ed_{row['id']}"
                if st.session_state.get("selected_res_filename_prev") != current_filename:
                    st.session_state[tag_key] = list(curr_tags_list)
                    st.session_state.selected_res_filename_prev = current_filename
                elif tag_key not in st.session_state:
                    st.session_state[tag_key] = list(curr_tags_list)
                new_tags_list = st.multiselect("Edit Tags", options=all_opts, key=tag_key)
                new_tags_val = ",".join(new_tags_list) if new_tags_list else None

                with st.expander("🔍 Inspect Raw Extracted Text", expanded=False):
                    st.text_area("Raw Text Content", value=row['content'], height=300, disabled=True, key=f"raw_{row['id']}")

                new_prof = st.text_area("JSON Profile", value=row['profile'], height=300, key=f"res_ed_{row['id']}")

                ec1, ec2 = st.columns(2)
                if ec1.button("Save Profile & Tags", key=f"sav_res_{row['id']}"):
                    db.execute_query("UPDATE resumes SET profile = ?, tags = ? WHERE id = ?", (new_prof, new_tags_val, int(row['id'])))
                    if new_tags_list:
                        for t in [t.strip() for t in new_tags_list if t.strip()]:
                            db.add_tag(t)
                    st.session_state[tag_key] = list(new_tags_list)
                    st.session_state.res_table_refresh_id = st.session_state.get("res_table_refresh_id", 0) + 1

                    # --- AUTO SAVE TRIGGER ---
                    with st.spinner("Syncing to GitHub..."):
                        sync_db_if_allowed()

                    st.success("Saved!")
                    time.sleep(0.5)
                    st.rerun()
                if ec2.button("Delete Resume", key=f"del_res_{row['id']}", type="primary"):
                    db.execute_query("DELETE FROM matches WHERE resume_id = ?", (int(row['id']),))
                    db.execute_query("DELETE FROM resumes WHERE id = ?", (int(row['id']),))

                    # --- AUTO SAVE TRIGGER ---
                    with st.spinner("Syncing to GitHub..."):
                        sync_db_if_allowed()

                    del st.session_state.selected_res_filename
                    st.rerun()
        else:
            st.info("No resumes uploaded yet.")

    # --- TAG MANAGER SUB-TAB ---
    with subtab_tags:
        st.subheader("Manage Tags")
        tags = db.list_tags()
        st.caption(f"Total Tags: {len(tags)}")

        st.markdown("Add, rename, or delete tags. Renames and deletes will update JD and resume tags.")
        c1, c2, c3 = st.columns([2, 2, 2])
        with c1:
            new_tag = st.text_input("New Tag")
            if st.button("Add Tag"):
                if new_tag.strip():
                    db.add_tag(new_tag.strip())
                    with st.spinner("Syncing to GitHub..."):
                        sync_db_if_allowed()
                    st.success("Tag added.")
                    time.sleep(0.5)
                    st.rerun()
        with c2:
            if tags:
                old_tag = st.selectbox("Rename Tag", tags, key="rename_tag_old")
                new_name = st.text_input("New Name", key="rename_tag_new")
                if st.button("Rename Tag"):
                    if new_name.strip():
                        db.rename_tag(old_tag, new_name.strip())
                        db.rename_tag_in_resumes(old_tag, new_name.strip())
                        db.rename_tag_in_jobs(old_tag, new_name.strip())
                        with st.spinner("Syncing to GitHub..."):
                            sync_db_if_allowed()
                        st.success("Tag renamed.")
                        time.sleep(0.5)
                        st.rerun()
            else:
                st.info("No tags available to rename.")
        with c3:
            if tags:
                del_tag = st.selectbox("Delete Tag", tags, key="delete_tag_sel")
                if st.button("Delete Tag"):
                    db.delete_tag(del_tag)
                    db.delete_tag_from_resumes(del_tag)
                    db.delete_tag_from_jobs(del_tag)
                    with st.spinner("Syncing to GitHub..."):
                        sync_db_if_allowed()
                    st.success("Tag deleted.")
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.info("No tags available to delete.")

# --- TAB 2: RUN ANALYSIS ---
with tab2:
    if not st.session_state.write_mode:
        st.info("Read-only mode: run results are local only and won't sync to the shared DB.", icon="🔒")
    j_data = db.fetch_dataframe("SELECT * FROM jobs")
    r_data = db.fetch_dataframe("SELECT * FROM resumes")

    col_j, col_r = st.columns(2)
    with col_j:
        st.markdown("#### 1. Select Job(s)")
        all_j = st.checkbox("Select All JDs")
        sel_j = j_data if all_j else j_data[j_data['filename'].isin(st.multiselect("Choose Jobs", j_data['filename']))]

    with col_r:
        st.markdown("#### 2. Select Resumes")

        if 'tags' in r_data.columns:
            all_used_tags = set()
            for t_str in r_data['tags'].dropna().unique():
                for t in t_str.split(','):
                    all_used_tags.add(t.strip())

            filter_tag = st.selectbox("Filter by JD Tag (Optional):", ["All"] + sorted(list(all_used_tags)))

            if filter_tag != "All":
                r_data = r_data[r_data['tags'].fillna('').astype(str).apply(lambda x: filter_tag in [t.strip() for t in x.split(',')])]

        sel_r = r_data if st.checkbox("Select All Resumes", value=True) else r_data[r_data['filename'].isin(st.multiselect("Choose Resumes", r_data['filename']))]

    st.caption(f"Selected JDs: {len(sel_j)} / {len(j_data)}")
    st.caption(f"Selected Resumes: {len(sel_r)} / {len(r_data)}")

    if not sel_j.empty and not sel_r.empty:
        st.divider()
        with st.container(border=True):
            st.markdown("#### ⚙️ Smart Match Configuration")

            # --- NEW TAGS CONFIGURATION ---
            match_tags = st.checkbox("🎯 Auto-match based on JD Tags", help="When enabled, creates a separate Run for each JD, checking ONLY resumes tagged with that JD's filename.")

            c1, c2 = st.columns([2, 2])
            auto_deep = c1.checkbox("✨ Auto-Upgrade to Deep Match", value=True, help="Automatically run a Deep Scan if the Standard Match score is high enough.")

            default_run_name = f"Run {datetime.datetime.now().strftime('%H:%M')}"
            if len(sel_j) == 1:
                base_job = sel_j.iloc[0]['filename'].rsplit('.', 1)[0]
                default_run_name = f"Run: {base_job}"
            elif len(sel_j) > 1:
                default_run_name = f"Batch Run: {len(sel_j)} Jobs"

            run_name = c2.text_input("Run Batch Name", value=default_run_name)

            deep_match_thresh = 50
            if auto_deep:
                deep_match_thresh = st.slider("Deep Match Auto-Trigger Threshold (%)", 0, 100, 50, help="If Standard Match score >= this value, the system will automatically run the Deep Scan.")

            c3, c4, c5 = st.columns([1, 2, 2])
            f_rerun = c3.toggle("Force Full Re-run (Overwrite Pass 1)", help="Check this to discard previous Fast Scan results and re-analyze everything from scratch.")

            if st.session_state.is_running and st.session_state.rerun_config is None:
                c4.button("🛑 STOP ANALYSIS", type="primary", use_container_width=True, on_click=stop_run_callback)
                # Pass match_tags param
                run_analysis_batch(run_name, sel_j, sel_r, deep_match_thresh, auto_deep, force_rerun_pass1=f_rerun, match_by_tags=match_tags)
            elif not st.session_state.is_running:
                # Pass match_tags param
                c4.button("🚀 START ANALYSIS", type="primary", use_container_width=True, on_click=start_run_callback)

# --- TAB 3: MATCH RESULTS ---
with tab3:
    if not st.session_state.write_mode:
        st.info("Read-only mode: reruns/edits are local only and won't sync to the shared DB.", icon="🔒")
    runs = db.fetch_dataframe("SELECT * FROM runs ORDER BY id DESC")
    if not runs.empty:
        runs['label'] = runs['name'] + " (" + runs['created_at'] + ")"

        # Split layout for Selection and Rename
        c_sel, c_ren = st.columns([3, 1])
        with c_sel:
            sel_run_label = st.selectbox("Select Run Batch:", runs['label'])

        run_row = runs[runs['label'] == sel_run_label].iloc[0]
        run_id = int(run_row['id'])
        run_name_base = run_row['name']
        run_threshold = _safe_int(run_row['threshold'], 50) if 'threshold' in run_row and pd.notna(run_row['threshold']) else 50

        with c_ren:
            # Rename Logic
            new_run_name = st.text_input("Rename Batch:", value=run_name_base, key=f"ren_{run_id}")
            if new_run_name != run_name_base:
                db.execute_query("UPDATE runs SET name=? WHERE id=?", (new_run_name, run_id))
                with st.spinner("Syncing rename to GitHub..."):
                    sync_db_if_allowed()
                st.rerun()  # <--- CRITICAL: Refreshes the dropdown immediately

        # --- RERUN SECTION ---
        with st.expander("🔄 Rerun this Batch with New Settings", expanded=False):
            st.info(f"Re-running will process the JDs and Resumes linked to this batch using new parameters.")

            c_r1, c_r2 = st.columns(2)
            create_new_run = c_r1.checkbox("Create new run (separate history)", value=False)
            rerun_name_input = c_r1.text_input("New Batch Name", value=f"Rerun of {run_name_base}", disabled=not create_new_run)
            new_auto_deep = c_r1.checkbox("Auto-Upgrade to Deep Match", value=True, key="rerun_auto")
            new_thresh = 50
            if new_auto_deep:
                new_thresh = c_r2.slider("New Deep Match Threshold (%)", 0, 100, run_threshold, key="rerun_thresh")

            # --- RERUN TAG OPTION ---
            new_match_tags = st.checkbox("Auto-match based on JD Tags", value=False, key="rerun_tags")
            if new_match_tags and not create_new_run:
                st.caption("Tag-based reruns always create new runs.")

            deep_only = st.checkbox("Deep Scan Only (reuse existing Standard scores)", value=False, help="Only re-run Deep Scan. If a Standard score is missing, it will be computed once.")
            force_rerun_deep = st.checkbox("Force Re-run Deep Scan", value=False, help="Re-run Deep Scan even if a deep result already exists.")
            f_rerun_p1 = st.checkbox("Force Re-run Pass 1 (Standard Match)", value=False, help="If unchecked, existing standard match scores will be reused to save time.", disabled=deep_only)

            linked_data = db.fetch_dataframe(f"""
                SELECT DISTINCT m.job_id, m.resume_id
                FROM run_matches rm JOIN matches m ON rm.match_id = m.id
                WHERE rm.run_id = {run_id}
            """)

            if not linked_data.empty:
                job_ids = list(linked_data['job_id'].unique())
                res_ids = list(linked_data['resume_id'].unique())
                j_ids_str = ",".join(map(str, job_ids))
                r_ids_str = ",".join(map(str, res_ids))

                rerun_j = db.fetch_dataframe(f"SELECT * FROM jobs WHERE id IN ({j_ids_str})")
                rerun_r = db.fetch_dataframe(f"SELECT * FROM resumes WHERE id IN ({r_ids_str})")

                if st.session_state.is_running and st.session_state.rerun_config:
                    st.button("🛑 STOP RERUN", type="primary", on_click=stop_run_callback)
                    cfg = st.session_state.rerun_config
                    # Use stored config parameters
                    run_analysis_batch(cfg['run_name'], cfg['jobs'], cfg['resumes'], cfg['thresh'], cfg['auto'], cfg['force'], match_by_tags=cfg.get('tags', False), deep_only=cfg.get('deep_only', False), force_rerun_deep=cfg.get('force_rerun_deep', False), run_id=cfg.get('run_id'), create_new_run=cfg.get('create_new_run', True))
                elif not st.session_state.is_running:
                    # Pass new_match_tags here
                    name_to_use = rerun_name_input if create_new_run else run_name_base
                    create_new_run_effective = create_new_run if not new_match_tags else True
                    st.button("🚀 Rerun Batch", type="primary", on_click=prepare_rerun_callback, args=(name_to_use, rerun_j, rerun_r, new_thresh, new_auto_deep, f_rerun_p1, new_match_tags, deep_only, force_rerun_deep, create_new_run_effective, run_id))
            else:
                st.error("Could not find original JDs/Resumes for this run.")

        # --- DELETE RUN ---
        if st.button("🗑️ Delete Run History", type="secondary"):
            db.execute_query("DELETE FROM runs WHERE id=?", (run_id,))
            db.execute_query("DELETE FROM run_matches WHERE run_id=?", (run_id,))

            # --- AUTO SAVE TRIGGER ---
            with st.spinner("Syncing deletion to GitHub..."):
                sync_db_if_allowed()

            st.success("Deleted")
            st.rerun()

        results = db.fetch_dataframe(f"""
            SELECT m.*, r.filename as res_name, j.filename as job_name
            FROM matches m JOIN run_matches rm ON m.id = rm.match_id
            JOIN resumes r ON m.resume_id = r.id JOIN jobs j ON m.job_id = j.id
            WHERE rm.run_id = {run_id} ORDER BY m.match_score DESC
        """)

        if not results.empty:
            st.caption(f"Results showing against Deep Match Threshold of **{run_threshold}%** used in this run.")
            total_matches = len(results)
            deep_count = len(results[results['strategy'] == 'Deep'])
            std_count = total_matches - deep_count
            unique_candidates = results['candidate_name'].nunique()
            unique_jobs = results['job_id'].nunique()

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total Matches", total_matches)
            m2.metric("Deep Matches", deep_count)
            m3.metric("Standard Only", std_count)
            m4.metric("Unique Candidates", unique_candidates)
            m5.metric("Unique Jobs", unique_jobs)

            # --- EXPORT BUTTON ---
            col_exp, _ = st.columns([1, 4])
            with col_exp:
                csv_data = results.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Results CSV",
                    data=csv_data,
                    file_name=f"match_results_{run_id}.csv",
                    mime="text/csv"
                )

            unique_jobs = results['job_id'].nunique()
            if unique_jobs > 1:
                matrix_filter = st.radio("Matrix Data View:", ["All Scores", "Deep Match Only", "Standard Match Only"], horizontal=True)
                generate_matrix_view(results, view_mode=matrix_filter)
                st.divider()

            unique_job_names = results['job_name'].unique()
            deep_df = results[results['strategy'] == 'Deep']
            std_df = results[results['strategy'] != 'Deep']

            st.markdown(f"### ✨ Deep Matches for {run_name_base}")
            if deep_df.empty:
                st.info("No candidates qualified for Deep Match in this run.")
            else:
                if unique_jobs > 1:
                    tabs = st.tabs(list(unique_job_names))
                    for i, job in enumerate(unique_job_names):
                        with tabs[i]:
                            job_subset = deep_df[deep_df['job_name'] == job]
                            st.markdown(generate_candidate_list_html(job_subset, threshold=run_threshold, is_deep=True), unsafe_allow_html=True)
                else:
                    st.markdown(generate_candidate_list_html(deep_df, threshold=run_threshold, is_deep=True), unsafe_allow_html=True)

            st.divider()

            st.markdown(f"### 🧠 Standard Matches (Pass 1 Only)")
            if std_df.empty:
                st.info("All candidates in this run were upgraded to Deep Match.")
            else:
                if unique_jobs > 1:
                    tabs_std = st.tabs(list(unique_job_names))
                    for i, job in enumerate(unique_job_names):
                        with tabs_std[i]:
                            job_subset = std_df[std_df['job_name'] == job]
                            st.markdown(generate_candidate_list_html(job_subset, threshold=run_threshold, is_deep=False), unsafe_allow_html=True)
                else:
                    st.markdown(generate_candidate_list_html(std_df, threshold=run_threshold, is_deep=False), unsafe_allow_html=True)

            st.divider()

            st.write("### 🔎 Match Evidence Investigator")

            col_filter1, col_filter2 = st.columns(2)
            avail_jobs = results['job_name'].unique()
            sel_job_filter = col_filter1.selectbox("Filter by Job:", avail_jobs, key="inv_job_filter")

            filtered_candidates = results[results['job_name'] == sel_job_filter]
            candidate_map = {f"{row['candidate_name']} ({row['match_score']}%)": row['id'] for idx, row in filtered_candidates.iterrows()}

            sel_candidate_label = col_filter2.selectbox("Select Candidate:", list(candidate_map.keys()), key="inv_cand_filter")

            if sel_candidate_label:
                match_id = candidate_map[sel_candidate_label]
                row = results[results['id'] == match_id].iloc[0]

                c_act1, c_act2 = st.columns([1, 4])
                with c_act1:
                    if st.button("🔄 Rerun This Match", key=f"re_s_{match_id}"):
                         with st.status("Re-evaluating...", expanded=True) as status:
                            action_data = db.fetch_dataframe(f"SELECT r.content as resume_text, r.profile as resume_profile, j.criteria as job_criteria FROM matches m JOIN resumes r ON m.resume_id = r.id JOIN jobs j ON m.job_id = j.id WHERE m.id = {match_id}").iloc[0]
                            resp = client.evaluate_standard(action_data['resume_text'], action_data['job_criteria'], action_data['resume_profile'])
                            data = resp if isinstance(resp, dict) else document_utils.clean_json_response(resp)
                            if data:
                                raw_reasoning = data.get('reasoning', "No reasoning provided.")
                                std_reasoning = "\n".join(raw_reasoning) if isinstance(raw_reasoning, list) else str(raw_reasoning)
                                db.save_match(None, None, data, match_id, standard_reasoning=std_reasoning)

                                # --- AUTO SAVE TRIGGER ---
                                with st.spinner("Syncing to GitHub..."):
                                    sync_db_if_allowed()

                                status.update(label="Complete!", state="complete")
                            else:
                                status.update(label="Re-evaluation failed.", state="error")
                            time.sleep(1)
                            st.rerun()
                with c_act2:
                    if st.button("🗑️ Delete This Match", key=f"del_s_{match_id}", type="primary"):
                        db.execute_query("DELETE FROM matches WHERE id=?", (match_id,))

                        # --- AUTO SAVE TRIGGER ---
                        with st.spinner("Syncing to GitHub..."):
                            sync_db_if_allowed()

                        st.success("Deleted")
                        time.sleep(0.5)
                        st.rerun()

                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.title(row['candidate_name'])
                    c2.metric("Weighted Score", f"{_safe_int(row['match_score'], 0)}%")

                    if pd.notna(row.get('standard_score')) and row['strategy'] == 'Deep':
                         st.caption(f"Pass 1 (Standard) Score: **{_safe_int(row['standard_score'], 0)}%**")

                    if row['strategy'] == 'Deep':
                        st.caption("✨ Evaluated with High-Precision Multi-Pass Tiered Weighting")

                    st.info(f"**Final Decision:** {row['reasoning']}")

                    if pd.notna(row.get('standard_reasoning')) and row['strategy'] == 'Deep':
                         with st.expander("📄 View Pass 1 (Standard) Analysis"):
                             st.markdown(f"_{row['standard_reasoning']}_")

                    try:
                        dets = json.loads(row['match_details'])
                        if dets: st.markdown(generate_criteria_html(dets), unsafe_allow_html=True)
                    except: st.warning("Detailed requirement breakdown unavailable for this match.")
    else: st.info("No run history found. Run an analysis in Tab 2 first.")
