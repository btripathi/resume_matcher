import streamlit as st
import pandas as pd
import json
import re
import unicodedata
import os
import time
import datetime
import logging
import urllib.request

# Import local modules
import database
import document_utils
import ai_engine
import github_sync  # <--- ADDED: Sync Module
import ui_manage_data
import ui_run_analysis
import ui_results
import match_flow
import db_sync
import utils

# --- LOGGING CONFIGURATION ---
# Suppress pypdf warnings about malformed PDF structures (harmless noise)
logging.getLogger("pypdf").setLevel(logging.ERROR)

# --- CONFIGURATION ---
st.set_page_config(page_title="TalentScout AI", page_icon="🚀", layout="wide")

# --- ADDED: SYNC ON STARTUP ---
db_sync.ensure_db_synced_on_startup(github_sync)

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
if "write_mode_locked" not in st.session_state: st.session_state.write_mode_locked = False

db_sync.init_write_mode_state(st.session_state.local_lm_available, github_sync)

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
    return db_sync.sync_db_if_allowed(github_sync)

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
            log_placeholder = st.container()
            add_log = match_flow.init_log_ui(height=300)

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
                        score = utils.safe_int(exist['match_score'], 0) if exist else 0

                        mid = match_flow.process_match_flow(
                            job,
                            res,
                            db,
                            client,
                            deep_match_thresh,
                            auto_deep,
                            force_rerun_pass1,
                            force_rerun_deep,
                            deep_only,
                            add_log,
                            task_display=task_display,
                            sub_bar=sub_bar,
                            safe_int_fn=utils.safe_int
                        )

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
        db_sync.render_write_mode_controls(github_sync)

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
tab_results, tab_manage, tab_run = st.tabs(["Match Results", "Manage Data", "Run Analysis"])

client = ai_engine.AIEngine(st.session_state.lm_base_url, st.session_state.lm_api_key)

with tab_results:
    ui_results.render_results(
        db,
        client,
        sync_db_if_allowed,
        run_analysis_batch,
        prepare_rerun_callback,
        stop_run_callback,
        utils,
        document_utils,
        match_flow,
    )

with tab_manage:
    ui_manage_data.render_manage_data(
        db,
        client,
        document_utils,
        sync_db_if_allowed,
        start_jd_upload,
        stop_jd_upload,
        start_res_upload,
        stop_res_upload,
    )

with tab_run:
    ui_run_analysis.render_run_analysis(
        db,
        run_analysis_batch,
        start_run_callback,
        stop_run_callback,
    )
