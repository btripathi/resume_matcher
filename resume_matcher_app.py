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

# Init Session State
if "lm_base_url" not in st.session_state: st.session_state.lm_base_url = "http://localhost:1234/v1"
if "lm_api_key" not in st.session_state: st.session_state.lm_api_key = "lm-studio"
if "ocr_enabled" not in st.session_state: st.session_state.ocr_enabled = True
if "processed_files" not in st.session_state: st.session_state.processed_files = set()

# Init DB
db = database.DBManager()

# --- UI HELPERS ---
def generate_criteria_html(details):
    rows = ""
    for item in details:
        status = item.get('status', 'Unknown')
        color_style = "color: #333; background-color: #e0e0e0;"
        if "Met" in status: color_style = "color: #0f5132; background-color: #d1e7dd;"
        elif "Missing" in status: color_style = "color: #842029; background-color: #f8d7da;"
        elif "Partial" in status: color_style = "color: #664d03; background-color: #fff3cd;"

        req = str(item.get('requirement', '')).replace('<', '&lt;')
        evi = str(item.get('evidence', '')).replace('<', '&lt;')

        rows += f'<tr><td>{req}</td><td>{evi}</td><td><span class="status-badge" style="{color_style}">{status}</span></td></tr>'

    return f"""
    <style>
        .match-table {{width: 100%; border-collapse: collapse; font-family: sans-serif; margin-top: 10px;}}
        .match-table th {{background-color: #f0f2f6; padding: 12px 15px; text-align: left; border-bottom: 2px solid #e0e0e0; font-weight: 600; color: #31333F;}}
        .match-table td {{padding: 10px 15px; border-bottom: 1px solid #e0e0e0; vertical-align: top; font-size: 14px; color: #31333F;}}
        .match-table tr:hover {{background-color: #f9f9f9;}}
        .status-badge {{padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; display: inline-block;}}
    </style>
    <table class="match-table">
        <thead><tr><th style="width: 30%">Requirement</th><th style="width: 55%">Evidence Found</th><th style="width: 15%">Status</th></tr></thead>
        <tbody>{rows}</tbody>
    </table>
    """

def generate_candidate_list_html(df):
    rows = ""
    for idx, row in df.iterrows():
        decision = row['decision']
        color_style = "color: #333; background-color: #e0e0e0;"
        if "Move Forward" in decision: color_style = "color: #0f5132; background-color: #d1e7dd;"
        elif "Reject" in decision: color_style = "color: #842029; background-color: #f8d7da;"
        elif "Review" in decision: color_style = "color: #664d03; background-color: #fff3cd;"

        score = row['match_score']
        score_color = "#0f5132" if score >= 80 else "#842029" if score < 50 else "black"

        # Strategy Badge
        strat = row.get('strategy', 'Standard')
        strategy_badge = f'<span style="background: #6366f1; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-left: 8px; font-weight: bold;">{strat.upper()} SCAN</span>'

        name = str(row['candidate_name']).replace('<', '&lt;')
        filename = str(row['res_name']).replace('<', '&lt;')
        job_name = str(row['job_name']).replace('<', '&lt;')

        rows += f'<tr><td style="font-weight: 600;">{name} {strategy_badge}<br><span style="font-size: 11px; color: #666; font-weight: normal;">Resume: {filename}</span><br><span style="font-size: 11px; color: #0056b3; font-weight: normal;">Job: {job_name}</span></td><td style="color: {score_color}; font-weight: bold; font-size: 16px;">{score}%</td><td><span class="status-badge" style="{color_style}">{decision}</span></td><td style="font-size: 13px; color: #444;">{str(row["reasoning"]).replace("<", "&lt;")}</td></tr>'

    return f"""
    <style>
        .candidate-table {{width: 100%; border-collapse: collapse; font-family: sans-serif;}}
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
        st.subheader("📂 Jobs")
        jd_up = st.file_uploader("Upload JDs", accept_multiple_files=True, key="jd")
        if jd_up and st.button(f"Process {len(jd_up)} JDs", type="primary"):
            with st.status("Processing JDs...") as status:
                for f in jd_up:
                    text = document_utils.extract_text_from_pdf(f.read()) if f.name.endswith('.pdf') else str(f.read(), 'utf-8', errors='ignore')
                    db.add_job(f.name, text, client.analyze_jd(text))
                st.rerun()
        jds = db.fetch_dataframe("SELECT id, filename FROM jobs")
        st.dataframe(jds, hide_index=True, width="stretch")

    with c2:
        st.subheader("📄 Resumes")
        res_up = st.file_uploader("Upload Resumes", accept_multiple_files=True, key="res")
        if res_up and st.button(f"Process {len(res_up)} Resumes", type="primary"):
            with st.status("Processing Resumes...") as status:
                for f in res_up:
                    text = document_utils.extract_text_from_pdf(f.read()) if f.name.endswith('.pdf') else str(f.read(), 'utf-8', errors='ignore')
                    db.add_resume(f.name, text, client.analyze_resume(text))
                st.rerun()
        ress = db.fetch_dataframe("SELECT id, filename FROM resumes")
        st.dataframe(ress, hide_index=True, width="stretch")

# --- TAB 2: ANALYSIS ---
with tab2:
    client = ai_engine.AIEngine(st.session_state.lm_base_url, st.session_state.lm_api_key)
    jds_list = db.fetch_dataframe("SELECT * FROM jobs")
    res_list = db.fetch_dataframe("SELECT * FROM resumes")

    col_j, col_r = st.columns(2)

    with col_j:
        st.markdown("#### 1. Select Job(s)")
        use_all_jds = st.checkbox("Select All JDs", value=False)
        sel_jds = jds_list if use_all_jds else jds_list[jds_list['filename'].isin(col_j.multiselect("Choose Jobs", jds_list['filename']))]

    with col_r:
        st.markdown("#### 2. Select Resumes")
        # Global threshold initialization
        score_threshold = 50

        filter_mode = st.radio("Selection Mode", ["Manual / All", "Target Candidates (From Previous Run)"], horizontal=True)

        target_res_ids = None

        if filter_mode == "Target Candidates (From Previous Run)":
            # Temporary local slider to filter the list view
            temp_threshold = st.slider("Min previous score to show in list", 0, 100, 50, key="filter_slider")
            if not sel_jds.empty:
                job_ids_raw = sel_jds['id'].tolist()
                job_ids_sql = f"({','.join(map(str, job_ids_raw))})"
                query = f"SELECT DISTINCT resume_id FROM matches WHERE match_score >= {temp_threshold} AND job_id IN {job_ids_sql}"
                matching_res_ids = db.fetch_dataframe(query)
                if not matching_res_ids.empty:
                    target_res_ids = matching_res_ids['resume_id'].tolist()
                    st.success(f"🎯 {len(target_res_ids)} candidates meet criteria.")
                else:
                    st.warning("No existing matches found above threshold.")
                    target_res_ids = []
            else:
                st.info("Select Jobs first to filter candidates.")

        if filter_mode == "Manual / All":
            use_all_res = st.checkbox("Select All Resumes", value=True)
            sel_res = res_list if use_all_res else res_list[res_list['filename'].isin(st.multiselect("Choose Resumes", res_list['filename']))]
        else:
            sel_res = res_list[res_list['id'].isin(target_res_ids)] if target_res_ids is not None else pd.DataFrame()

    if not sel_jds.empty and not sel_res.empty:
        st.divider()
        with st.container(border=True):
            st.markdown("#### ⚙️ Analysis Workflow")
            c_cfg1, c_cfg2 = st.columns([2, 2])

            strategy = c_cfg1.radio(
                "Matching Strategy",
                ["Standard (Fast)", "Deep Match (Automated 2-Pass)"],
                index=1 if filter_mode == "Target Candidates (From Previous Run)" else 0,
                help="Standard: Single pass. Deep Match: Auto-runs Fast Pass (if needed), then Deep Pass if threshold met."
            )

            run_name = c_cfg2.text_input("Run Batch Name", value=f"{strategy.split()[0]} {datetime.datetime.now().strftime('%H:%M')}")

            # Show threshold slider specifically for Deep Match configuration
            if strategy == "Deep Match (Automated 2-Pass)":
                st.info("💡 **2-Pass Logic:** If a candidate hasn't been scanned or is below the threshold, a Fast Scan runs first. The Deep Scan only executes if the Fast Scan score meets the threshold below.")
                score_threshold = st.slider("Deep Match Entry Threshold (%)", 0, 100, 50, help="Candidates must score at least this much in Pass 1 to trigger the expensive Pass 2.")

            c_cfg3, c_act1, c_act2 = st.columns([1, 2, 2])
            rerun = c_cfg3.toggle("Force Rerun", value=False)
            btn_start = c_act1.button("🚀 START WORKFLOW", type="primary", use_container_width=True)
            if c_act2.button("🛑 STOP", type="secondary", use_container_width=True):
                st.stop()

        if btn_start:
            run_id = db.create_run(run_name)
            total_pairs = len(sel_jds) * len(sel_res)
            count = 0

            with st.status(f"Executing Workflow: {strategy}...", expanded=True) as status:
                master_bar = st.progress(0)
                log_container = st.empty()
                log_lines = []

                def update_logs(msg):
                    log_lines.append(f"{datetime.datetime.now().strftime('%H:%M:%S')} - {msg}")
                    log_container.code("\n".join(log_lines[-8:]))

                for _, job in sel_jds.iterrows():
                    for _, res in sel_res.iterrows():
                        count += 1
                        status.update(label=f"Analysis {count}/{total_pairs}: {res['filename']}")

                        existing = db.get_match_if_exists(int(job['id']), int(res['id']))
                        match_id = existing['id'] if existing else None

                        if strategy == "Deep Match (Automated 2-Pass)":
                            current_score = existing['match_score'] if existing else 0

                            # Step 1: Ensure Fast Pass exists
                            if not existing or (existing['strategy'] != 'Deep' and current_score < score_threshold) or rerun:
                                update_logs(f"🕒 Pass 1 (Standard) needed for {res['filename']}...")
                                data_fast = client.evaluate_standard(res['content'], job['criteria'], res['profile'])
                                if data_fast:
                                    match_id = db.save_match(int(job['id']), int(res['id']), data_fast, match_id, strategy="Standard")
                                    current_score = data_fast['match_score']
                                    update_logs(f"  ↳ Pass 1 Result: {current_score}%")

                            # Step 2: Run Deep Pass if threshold met
                            if current_score >= score_threshold:
                                if existing and existing['strategy'] == 'Deep' and not rerun:
                                    update_logs(f"⏭️ Deep Match already exists for {res['filename']}")
                                else:
                                    update_logs(f"🔬 Pass 2 (Deep Scan) starting for {res['filename']}...")
                                    try:
                                        jd_c = json.loads(job['criteria'])
                                        reqs = []
                                        for k in ['must_have_skills', 'nice_to_have_skills', 'domain_knowledge', 'soft_skills']:
                                            if k in jd_c and isinstance(jd_c[k], list):
                                                reqs.extend([(k, v) for v in jd_c[k]])
                                        if 'min_years_experience' in jd_c:
                                            reqs.append(('experience', f"Min {jd_c['min_years_experience']} years"))
                                    except:
                                        reqs = [("raw", "JD Criteria")]

                                    details = []
                                    sub_bar = st.progress(0, text="Criterion Detail")
                                    for idx, (r_type, r_val) in enumerate(reqs):
                                        update_logs(f"  ↳ Verifying: {r_val[:30]}...")
                                        details.append(client.evaluate_criterion(res['content'], r_type, r_val))
                                        sub_bar.progress((idx+1)/len(reqs))
                                    sub_bar.empty()

                                    score_f, dec_f, reas_f = client.generate_final_decision(res['filename'], details)
                                    final_data = {
                                        "candidate_name": res['filename'], "match_score": score_f,
                                        "decision": dec_f, "reasoning": reas_f, "match_details": details
                                    }
                                    match_id = db.save_match(int(job['id']), int(res['id']), final_data, match_id, strategy="Deep")
                                    update_logs(f"✅ Deep Scan Complete: {score_f}%")
                            else:
                                update_logs(f"⏭️ Skipping Deep Scan (Below {score_threshold}%)")

                        else:
                            # Standard Strategy
                            if match_id and not rerun:
                                update_logs(f"⏭️ Skipping cached: {res['filename']}")
                            else:
                                update_logs(f"🧠 Fast Scan: {res['filename']}...")
                                data = client.evaluate_standard(res['content'], job['criteria'], res['profile'])
                                if data:
                                    match_id = db.save_match(int(job['id']), int(res['id']), data, match_id, strategy="Standard")
                                    update_logs(f"✅ Result: {data.get('match_score')}%")

                        if match_id: db.link_run_match(run_id, match_id)
                        master_bar.progress(count/total_pairs)

                status.update(label="Workflow Complete!", state="complete", expanded=False)
            st.success("Batch Finished.")

# --- TAB 3: MATCH RESULTS ---
with tab3:
    runs = db.fetch_dataframe("SELECT * FROM runs ORDER BY id DESC")
    if not runs.empty:
        runs['label'] = runs['name'] + " (" + runs['created_at'] + ")"
        sel_run_lbl = st.selectbox("Select Run", runs['label'])
        selected_run = runs[runs['label'] == sel_run_lbl].iloc[0]
        run_id = int(selected_run['id'])

        results = db.fetch_dataframe(f"""
            SELECT m.*, r.filename as res_name, j.filename as job_name
            FROM matches m JOIN run_matches rm ON m.id = rm.match_id
            JOIN resumes r ON m.resume_id = r.id JOIN jobs j ON m.job_id = j.id
            WHERE rm.run_id = {run_id}
            ORDER BY m.match_score DESC
        """)

        if not results.empty:
            st.write("### 📝 Match List")
            st.markdown(generate_candidate_list_html(results), unsafe_allow_html=True)

            st.divider()
            st.write("### 🔎 Deep Dive Investigation")
            results['display'] = results['candidate_name'] + " -> " + results['job_name'] + " (" + results['match_score'].astype(str) + "%)"
            sel_match_lbl = st.selectbox("Select Candidate to Inspect:", results['display'])

            if sel_match_lbl:
                row = results[results['display'] == sel_match_lbl].iloc[0]

                if row['strategy'] == 'Deep':
                    st.markdown("""
                        <div style="background-color: #f0f4ff; border-left: 5px solid #6366f1; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                            <span style="color: #4338ca; font-weight: bold; font-size: 1.2em;">✨ High-Precision Deep Match</span><br>
                            <span style="color: #6366f1;">This candidate was evaluated using the 2-pass criterion scan.</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("💡 Standard Match Result (Single-pass analysis).")

                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.title(row['candidate_name'])
                    c2.metric("Final Score", f"{row['match_score']}%")
                    st.info(row['reasoning'])

                    st.subheader("Requirement Validation Table")
                    try:
                        details = json.loads(row['match_details'])
                        if details:
                            st.markdown(generate_criteria_html(details), unsafe_allow_html=True)
                        else:
                            st.info("No detailed breakdown available for standard match.")
                    except:
                        st.warning("Details unavailable.")
    else:
        st.info("No runs found.")
