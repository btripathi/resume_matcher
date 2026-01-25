import streamlit as st
import pandas as pd
import json
import time
import logging
import datetime

# Import local modules
import database
import document_utils
import ai_engine

# --- CONFIGURATION ---
st.set_page_config(
    page_title="AI Recruiting Workbench (Pro)",
    page_icon="🚀",
    layout="wide"
)

# Init Session State FIRST to prevent AttributeErrors
if "lm_base_url" not in st.session_state: st.session_state.lm_base_url = "http://localhost:1234/v1"
if "lm_api_key" not in st.session_state: st.session_state.lm_api_key = "lm-studio"
if "ocr_enabled" not in st.session_state: st.session_state.ocr_enabled = True
if "processed_files" not in st.session_state: st.session_state.processed_files = set()

db = database.DBManager()

# --- UI HELPERS ---
def generate_criteria_html(details):
    rows = ""
    # Sort details by category weight (Must-haves first)
    cat_order = ["must_have_skills", "experience", "education_requirements", "domain_knowledge", "soft_skills", "nice_to_have_skills"]
    sorted_details = sorted(details, key=lambda x: cat_order.index(x.get('category')) if x.get('category') in cat_order else 99)

    for item in sorted_details:
        status = item.get('status', 'Unknown')
        cat = item.get('category', '').replace('_', ' ').upper()
        color_style = "color: #0f5132; background-color: #d1e7dd;" if "Met" in status else "color: #842029; background-color: #f8d7da;" if "Missing" in status else "color: #664d03; background-color: #fff3cd;"

        req = str(item.get('requirement', '')).replace('<', '&lt;')
        evi = str(item.get('evidence', '')).replace('<', '&lt;')

        rows += f'<tr><td style="font-size:10px; font-weight:bold; color:#666;">{cat}</td><td>{req}</td><td>{evi}</td><td><span class="status-badge" style="{color_style}">{status}</span></td></tr>'

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

def generate_candidate_list_html(df):
    if df.empty:
        return "<p style='color: #666; font-style: italic;'>No results found in this category.</p>"
    rows = ""
    for idx, row in df.iterrows():
        decision = row['decision']
        color_style = "color: #0f5132; background-color: #d1e7dd;" if "Move Forward" in decision else "color: #842029; background-color: #f8d7da;" if "Reject" in decision else "color: #664d03; background-color: #fff3cd;"

        score = row['match_score']
        score_color = "#0f5132" if score >= 70 else "#842029" if score < 40 else "black"

        name = str(row['candidate_name']).replace('<', '&lt;')
        filename = str(row['res_name']).replace('<', '&lt;')
        job_name = str(row['job_name']).replace('<', '&lt;')

        rows += f'<tr><td style="font-weight: 600;">{name}<br><span style="font-size: 11px; color: #666; font-weight: normal;">Resume: {filename}</span><br><span style="font-size: 11px; color: #0056b3; font-weight: normal;">Job: {job_name}</span></td><td style="color: {score_color}; font-weight: bold; font-size: 16px;">{score}%</td><td><span class="status-badge" style="{color_style}">{decision}</span></td><td style="font-size: 13px; color: #444;">{str(row["reasoning"]).replace("<", "&lt;")}</td></tr>'

    return f"""
    <style>
        .candidate-table {{width: 100%; border-collapse: collapse; font-family: sans-serif; margin-bottom: 20px;}}
        .candidate-table th {{background-color: #f8f9fa; padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6; color: #495057;}}
        .candidate-table td {{padding: 12px; border-bottom: 1px solid #dee2e6; vertical-align: top;}}
        .candidate-table tr:hover {{background-color: #f8f9fa;}}
        .status-badge {{padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; display: inline-block; white-space: nowrap;}}
    </style>
    <table class="candidate-table">
        <thead><tr><th style="width: 25%">Match Details</th><th style="width: 10%">Score</th><th style="width: 15%">Decision</th><th style="width: 50%">Reasoning</th></tr></thead>
        <tbody>{rows}</tbody>
    </table>
    """

# --- HEADER ---
st.title("📄 AI Recruiting Workbench")

tab1, tab2, tab3 = st.tabs(["1. Manage Data", "2. Run Analysis", "3. Match Results"])

# --- TAB 1: MANAGE DATA ---
with tab1:
    client = ai_engine.AIEngine(st.session_state.lm_base_url, st.session_state.lm_api_key)
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📂 Job Descriptions")
        jd_up = st.file_uploader("Upload JDs", accept_multiple_files=True, key="jd_up")
        if jd_up and st.button(f"Process {len(jd_up)} JDs", type="primary"):
            with st.status("Processing JDs...") as status:
                for f in jd_up:
                    text = document_utils.extract_text_from_pdf(f.read()) if f.name.endswith('.pdf') else str(f.read(), 'utf-8', errors='ignore')
                    db.add_job(f.name, text, client.analyze_jd(text))
                st.rerun()

        jds_m = db.fetch_dataframe("SELECT id, filename, criteria FROM jobs")
        if not jds_m.empty:
            st.dataframe(jds_m[['filename']], hide_index=True, width="stretch")
            st.divider()
            jd_sel = st.selectbox("Select JD to Edit:", jds_m['filename'])
            row = jds_m[jds_m['filename'] == jd_sel].iloc[0]
            new_crit = st.text_area("JSON Criteria", row['criteria'], height=300, key=f"jd_ed_{row['id']}")
            c_s, c_d = st.columns(2)
            if c_s.button("Save JD"):
                db.execute_query("UPDATE jobs SET criteria=? WHERE id=?", (new_crit, int(row['id'])))
                st.success("Saved!")
                st.rerun()
            if c_d.button("Delete JD", type="primary"):
                db.execute_query("DELETE FROM jobs WHERE id=?", (int(row['id']),))
                st.rerun()

    with c2:
        st.subheader("📄 Resumes")
        res_up = st.file_uploader("Upload Resumes", accept_multiple_files=True, key="res_up")
        if res_up and st.button(f"Process {len(res_up)} Resumes", type="primary"):
            with st.status("Processing Resumes...") as status:
                for f in res_up:
                    text = document_utils.extract_text_from_pdf(f.read()) if f.name.endswith('.pdf') else str(f.read(), 'utf-8', errors='ignore')
                    db.add_resume(f.name, text, client.analyze_resume(text))
                st.rerun()

        res_m = db.fetch_dataframe("SELECT id, filename, profile FROM resumes")
        if not res_m.empty:
            st.dataframe(res_m[['filename']], hide_index=True, width="stretch")
            st.divider()
            res_sel = st.selectbox("Select Resume to Edit:", res_m['filename'])
            row = res_m[res_m['filename'] == res_sel].iloc[0]
            new_prof = st.text_area("Candidate Profile (JSON)", row['profile'], height=300, key=f"res_ed_{row['id']}")
            c_s, c_d = st.columns(2)
            if c_s.button("Save Profile"):
                db.execute_query("UPDATE resumes SET profile=? WHERE id=?", (new_prof, int(row['id'])))
                st.success("Saved!")
                st.rerun()
            if c_d.button("Delete Resume", type="primary"):
                db.execute_query("DELETE FROM resumes WHERE id=?", (int(row['id']),))
                st.rerun()

# --- TAB 2: RUN ANALYSIS ---
with tab2:
    client = ai_engine.AIEngine(st.session_state.lm_base_url, st.session_state.lm_api_key)
    j_data = db.fetch_dataframe("SELECT * FROM jobs")
    r_data = db.fetch_dataframe("SELECT * FROM resumes")

    col_j, col_r = st.columns(2)
    with col_j:
        st.markdown("#### 1. Select Job(s)")
        all_j = st.checkbox("Select All JDs")
        sel_j = j_data if all_j else j_data[j_data['filename'].isin(st.multiselect("Choose Jobs", j_data['filename']))]

    with col_r:
        st.markdown("#### 2. Select Resumes")
        f_mode = st.radio("Selection Mode", ["Manual / All", "Target High-Scorers (Pass 2)"], horizontal=True)

        target_ids = None
        pass1_thresh = 50

        if f_mode == "Target High-Scorers (Pass 2)":
            pass1_thresh = st.slider("Min score from previous standard run", 0, 100, 50, key="pass1_slider")
            if not sel_j.empty:
                j_ids = f"({','.join(map(str, sel_j['id'].tolist()))})"
                matches = db.fetch_dataframe(f"SELECT DISTINCT resume_id FROM matches WHERE match_score >= {pass1_thresh} AND job_id IN {j_ids}")
                target_ids = matches['resume_id'].tolist() if not matches.empty else []
                st.success(f"🎯 {len(target_ids)} candidates meet threshold.")
            else: st.info("Select Jobs first.")

        if f_mode == "Manual / All":
            all_r = st.checkbox("Select All Resumes", value=True)
            sel_r = r_data if all_r else r_data[r_data['filename'].isin(st.multiselect("Choose Resumes", r_data['filename']))]
        else:
            sel_r = r_data[r_data['id'].isin(target_ids)] if target_ids is not None else pd.DataFrame()

    if not sel_j.empty and not sel_r.empty:
        st.divider()
        with st.container(border=True):
            st.markdown("#### ⚙️ Workflow Configuration")
            c1, c2 = st.columns([2, 2])
            strategy = c1.radio("Matching Strategy", ["Standard (Fast)", "Deep Match (Automated 2-Pass)"], index=1 if f_mode == "Target High-Scorers (Pass 2)" else 0)
            run_name = c2.text_input("Run Name", value=f"{strategy.split()[0]} {datetime.datetime.now().strftime('%H:%M')}")

            if strategy == "Deep Match (Automated 2-Pass)":
                st.info("💡 **2-Pass Logic:** If a Fast scan hasn't run, it runs first. Deep scan follows only for those meeting the threshold below.")
                pass1_thresh = st.slider("Deep Match Entry Threshold (%)", 0, 100, 50, key="deep_thresh_slider")

            c3, c4, c5 = st.columns([1, 2, 2])
            f_rerun = c3.toggle("Rerun All")

            if c4.button("🚀 START ANALYSIS", type="primary", use_container_width=True):
                rid = db.create_run(run_name)
                total = len(sel_j) * len(sel_r)
                count = 0

                with st.status(f"Executing {strategy}...", expanded=True) as status:
                    master_bar = st.progress(0)
                    task_display = st.empty()
                    sub_bar = st.empty()
                    log_history = st.expander("Detailed Activity Log", expanded=True)

                    def add_log(msg, bold=False):
                        ts = datetime.datetime.now().strftime("%H:%M:%S")
                        with log_history:
                            if bold: st.markdown(f"**[{ts}] {msg}**")
                            else: st.text(f"[{ts}] {msg}")

                    for _, job in sel_j.iterrows():
                        for _, res in sel_r.iterrows():
                            count += 1
                            current_resume_name = res['filename']
                            status.update(label=f"Analysis {count}/{total}: {current_resume_name}")
                            add_log(f"Starting analysis for {current_resume_name}", bold=True)

                            exist = db.get_match_if_exists(int(job['id']), int(res['id']))
                            mid = exist['id'] if exist else None
                            score = exist['match_score'] if exist else 0

                            # 1. Standard Pass (Fast holistic pass)
                            if not exist or (exist['strategy'] != 'Deep' and score < pass1_thresh) or f_rerun:
                                task_display.info(f"🧠 Pass 1: Holistic scan for **{current_resume_name}**...")
                                data = client.evaluate_standard(res['content'], job['criteria'], res['profile'])
                                if data:
                                    mid = db.save_match(int(job['id']), int(res['id']), data, mid, strategy="Standard")
                                    score = data['match_score']
                                    add_log(f"Standard Match Score: {score}%")

                            # 2. Deep Weighted Pass (STRICT JSON ALIGNMENT)
                            if strategy == "Deep Match (Automated 2-Pass)" and score >= pass1_thresh:
                                if exist and exist['strategy'] == 'Deep' and not f_rerun:
                                    add_log("Deep match already exists. Skipping.")
                                else:
                                    add_log(f"Threshold met ({score}%). Triggering Deep Scan...")
                                    jd_c = json.loads(job['criteria'])
                                    reqs = []
                                    # Collect all requirements from structured JSON categories
                                    for k in ['must_have_skills', 'nice_to_have_skills', 'domain_knowledge', 'soft_skills', 'education_requirements']:
                                        if k in jd_c and isinstance(jd_c[k], list): reqs.extend([(k, v) for v in jd_c[k]])
                                    if jd_c.get('min_years_experience', 0) > 0:
                                        reqs.append(('experience', f"Minimum {jd_c['min_years_experience']} years relevant experience"))

                                    details = []
                                    num_reqs = len(reqs)

                                    for idx, (rt, rv) in enumerate(reqs):
                                        task_display.warning(f"🔬 Deep Scan: Checking criterion {idx+1}/{num_reqs}\n\n**[{rt.upper()}]** {rv[:100]}...")
                                        sub_bar.progress((idx+1)/num_reqs)
                                        details.append(client.evaluate_criterion(res['content'], rt, rv))

                                    sub_bar.empty()
                                    sf, df, rf = client.generate_final_decision(res['filename'], details, strategy="Deep")
                                    mid = db.save_match(int(job['id']), int(res['id']), {"candidate_name": res['filename'], "match_score": sf, "decision": df, "reasoning": rf, "match_details": details}, mid, strategy="Deep")
                                    add_log(f"Deep Match Final Score: {sf}% ({df})", bold=True)

                            if mid: db.link_run_match(rid, mid)
                            master_bar.progress(count/total)

                    task_display.success("✅ All selected resumes processed successfully.")
                    status.update(label="Analysis Complete!", state="complete")
                st.rerun()

            if c5.button("🛑 STOP", type="secondary", use_container_width=True):
                st.stop()

# --- TAB 3: MATCH RESULTS ---
with tab3:
    runs = db.fetch_dataframe("SELECT * FROM runs ORDER BY id DESC")
    if not runs.empty:
        runs['label'] = runs['name'] + " (" + runs['created_at'] + ")"
        sel_run = st.selectbox("Select Run Batch", runs['label'])
        run_id = int(runs[runs['label'] == sel_run].iloc[0]['id'])

        results = db.fetch_dataframe(f"""
            SELECT m.*, r.filename as res_name, j.filename as job_name
            FROM matches m JOIN run_matches rm ON m.id = rm.match_id
            JOIN resumes r ON m.resume_id = r.id JOIN jobs j ON m.job_id = j.id
            WHERE rm.run_id = {run_id} ORDER BY m.match_score DESC
        """)

        if not results.empty:
            # --- SPLIT TABLES: DEEP vs STANDARD ---
            deep_df = results[results['strategy'] == 'Deep']
            standard_df = results[results['strategy'] != 'Deep']

            st.markdown("### ✨ High-Precision Deep Scans")
            st.markdown(generate_candidate_list_html(deep_df), unsafe_allow_html=True)

            st.divider()
            st.markdown("### 🧠 Standard Fast Scans")
            st.markdown(generate_candidate_list_html(standard_df), unsafe_allow_html=True)

            st.divider()
            st.write("### 🔎 Match Evidence Investigator")
            results['d'] = results['candidate_name'] + " -> " + results['job_name'] + " (" + results['match_score'].astype(str) + "%)"
            s_match = st.selectbox("Select Candidate to Inspect Details:", results['d'])

            if s_match:
                row = results[results['d'] == s_match].iloc[0]
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.title(row['candidate_name'])
                    c2.metric("Weighted Score", f"{row['match_score']}%")

                    if row['strategy'] == 'Deep':
                        st.caption("✨ Evaluated with High-Precision Multi-Pass Tiered Weighting")

                    st.info(row['reasoning'])
                    try:
                        dets = json.loads(row['match_details'])
                        if dets: st.markdown(generate_criteria_html(dets), unsafe_allow_html=True)
                    except: st.warning("Detailed requirement breakdown unavailable for this match.")
    else: st.info("No run history found. Run an analysis in Tab 2 first.")
