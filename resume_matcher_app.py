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
    page_title="AI Resume Matcher (Pro)",
    page_icon="🚀",
    layout="wide"
)

# Init Session State
if "lm_base_url" not in st.session_state: st.session_state.lm_base_url = "http://localhost:1234/v1"
if "lm_api_key" not in st.session_state: st.session_state.lm_api_key = "lm-studio"
if "ocr_enabled" not in st.session_state: st.session_state.ocr_enabled = True
if "processed_files" not in st.session_state: st.session_state.processed_files = set()
if "is_running" not in st.session_state: st.session_state.is_running = False

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

        name = str(row['candidate_name']).replace('<', '&lt;')
        filename = str(row['res_name']).replace('<', '&lt;')
        job_name = str(row['job_name']).replace('<', '&lt;')

        rows += f'<tr><td style="font-weight: 600;">{name}<br><span style="font-size: 11px; color: #666; font-weight: normal;">Resume: {filename}</span><br><span style="font-size: 11px; color: #0056b3; font-weight: normal;">Job: {job_name}</span></td><td style="color: {score_color}; font-weight: bold; font-size: 16px;">{score}%</td><td><span class="status-badge" style="{color_style}">{decision}</span></td><td style="font-size: 13px; color: #444;">{str(row["reasoning"]).replace("<", "&lt;")}</td></tr>'

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

# --- HEADER & SETTINGS ---
col_head, col_set = st.columns([6, 1])
with col_head: st.title("📄 AI Recruiting Workbench")
with col_set:
    with st.popover("⚙️ Settings"):
        st.write("### Configuration")
        st.text_input("LM URL", key="lm_base_url")
        st.text_input("API Key", key="lm_api_key")
        st.checkbox("Enable OCR", key="ocr_enabled")
        if st.button("🗑️ Reset DB", type="primary"):
            db.execute_query("DELETE FROM matches")
            db.execute_query("DELETE FROM runs")
            db.execute_query("DELETE FROM run_matches")
            db.execute_query("DELETE FROM jobs")
            db.execute_query("DELETE FROM resumes")
            st.session_state.processed_files = set()
            st.success("Reset Complete")
            time.sleep(1)
            st.rerun()

# --- TABS ---
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
                bar = st.progress(0)
                log_box = st.expander("Logs", expanded=True)
                for i, f in enumerate(jd_up):
                    if f.name in st.session_state.processed_files: continue
                    text = document_utils.extract_text_from_pdf(f.read(), st.session_state.ocr_enabled, log_box.write) if f.name.endswith('.pdf') else str(f.read(), 'utf-8', errors='ignore')
                    if text:
                        data = client.analyze_jd(text)
                        db.add_job(f.name, text, data)
                        st.session_state.processed_files.add(f.name)
                        log_box.write(f"✅ Saved {f.name}")
                    bar.progress((i+1)/len(jd_up))
                status.update(label="Complete!", state="complete", expanded=False)
                time.sleep(1)
                st.rerun()

        jds = db.fetch_dataframe("SELECT id, filename, criteria, upload_date FROM jobs")
        if not jds.empty:
            st.dataframe(jds[['filename', 'upload_date']], hide_index=True, width="stretch")
            st.divider()
            jd_choice = st.selectbox("Edit Criteria:", jds['filename'])
            row = jds[jds['filename'] == jd_choice].iloc[0]
            new_crit = st.text_area("JSON", value=row['criteria'], height=300, key=f"jd_ed_{row['id']}")
            c_sav, c_del = st.columns(2)
            if c_sav.button("Save JD", key=f"sav_jd_{row['id']}"):
                db.execute_query("UPDATE jobs SET criteria = ? WHERE id = ?", (new_crit, int(row['id'])))
                st.success("Saved!")
                st.rerun()
            if c_del.button("Delete JD", key=f"del_jd_{row['id']}", type="primary"):
                db.execute_query("DELETE FROM jobs WHERE id = ?", (int(row['id']),))
                st.rerun()

    with c2:
        st.subheader("📄 Resumes")
        res_up = st.file_uploader("Upload Resumes", accept_multiple_files=True, key="res")
        if res_up and st.button(f"Process {len(res_up)} Resumes", type="primary"):
            with st.status("Processing Resumes...") as status:
                bar = st.progress(0)
                log_box = st.expander("Logs", expanded=True)
                for i, f in enumerate(res_up):
                    if f.name in st.session_state.processed_files: continue
                    text = document_utils.extract_text_from_pdf(f.read(), st.session_state.ocr_enabled, log_callback=log_box.write) if f.name.endswith('.pdf') else str(f.read(), 'utf-8', errors='ignore')
                    if text:
                        data = client.analyze_resume(text)
                        db.add_resume(f.name, text, data)
                        st.session_state.processed_files.add(f.name)
                        log_box.write(f"✅ Saved {f.name}")
                    bar.progress((i+1)/len(res_up))
                status.update(label="Complete!", state="complete", expanded=False)
                time.sleep(1)
                st.rerun()

        ress = db.fetch_dataframe("SELECT id, filename, profile, upload_date FROM resumes")
        if not ress.empty:
            st.dataframe(ress[['filename', 'upload_date']], hide_index=True, width="stretch")
            st.divider()
            res_choice = st.selectbox("Edit Profile:", ress['filename'])
            row = ress[ress['filename'] == res_choice].iloc[0]
            new_prof = st.text_area("JSON", value=row['profile'], height=300, key=f"res_ed_{row['id']}")
            c_sav, c_del = st.columns(2)
            if c_sav.button("Save Profile", key=f"sav_res_{row['id']}"):
                db.execute_query("UPDATE resumes SET profile = ? WHERE id = ?", (new_prof, int(row['id'])))
                st.success("Saved!")
                st.rerun()
            if c_del.button("Delete Resume", key=f"del_res_{row['id']}", type="primary"):
                db.execute_query("DELETE FROM resumes WHERE id = ?", (int(row['id']),))
                st.rerun()

# --- TAB 2: RUN ANALYSIS ---
with tab2:
    client = ai_engine.AIEngine(st.session_state.lm_base_url, st.session_state.lm_api_key)

    jds_data = db.fetch_dataframe("SELECT id, filename, criteria FROM jobs")
    ress_data = db.fetch_dataframe("SELECT id, filename, content, profile FROM resumes")

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        st.markdown("#### Select Job Descriptions")
        use_all_jds = st.checkbox("All JDs", value=False)
        sel_jds = jds_data if use_all_jds else jds_data[jds_data['filename'].isin(st.multiselect("Choose Jobs", jds_data['filename']))]

    with col_sel2:
        st.markdown("#### Select Resumes")
        use_all_res = st.checkbox("All Resumes", value=True)
        sel_res = ress_data if use_all_res else ress_data[ress_data['filename'].isin(st.multiselect("Choose Resumes", ress_data['filename']))]

    st.divider()

    if not sel_jds.empty and not sel_res.empty:
        with st.container(border=True):
            st.markdown("#### Run Configuration")
            c_p1, c_p2 = st.columns([3, 1])
            run_name_input = c_p1.text_input("Batch Name", value=f"Batch {datetime.datetime.now().strftime('%H:%M')}")
            rerun_toggle = c_p2.toggle("Overwrite existing?", value=False)

            c_act1, c_act2 = st.columns([1, 1])
            btn_analyze = c_act1.button("🚀 START ANALYSIS", type="primary", use_container_width=True)
            btn_stop = c_act2.button("🛑 STOP RUN", type="secondary", use_container_width=True)

        # Handle explicit stop
        if btn_stop:
            st.session_state.is_running = False
            st.warning("Run interrupted. Standing by.")
            st.stop()

        if btn_analyze:
            st.session_state.is_running = True
            run_id = db.create_run(run_name_input)
            total_ops = len(sel_jds) * len(sel_res)
            count = 0

            with st.status("Analyzing matches...", expanded=True) as status:
                bar = st.progress(0)
                log_box = st.expander("Live Progress", expanded=True)

                for _, job in sel_jds.iterrows():
                    for _, res in sel_res.iterrows():
                        # Streamlit reruns on any interaction, btn_analyze will remain True
                        # during this loop until complete or interrupted by a new rerun.
                        count += 1
                        status.update(label=f"Matching {count}/{total_ops}: {res['filename']}")

                        match_id = db.get_match_if_exists(int(job['id']), int(res['id']))
                        if not match_id or rerun_toggle:
                            resp = client.evaluate_candidate(res['content'], job['criteria'], res['profile'])
                            data = document_utils.clean_json_response(resp)
                            if data:
                                match_id = db.save_match(int(job['id']), int(res['id']), data, match_id)
                                with log_box: st.write(f"✅ Matched **{res['filename']}**")
                        else:
                            with log_box: st.write(f"⏭️ Skipping cached: {res['filename']}")

                        if match_id:
                            db.link_run_match(run_id, match_id)

                        bar.progress(count/total_ops)

                st.session_state.is_running = False
                status.update(label="Analysis Complete!", state="complete", expanded=False)
                st.success("Batch Finished! View results in the Match Results tab.")

# --- TAB 3: RESULTS ---
with tab3:
    runs = db.fetch_dataframe("SELECT * FROM runs ORDER BY id DESC")
    if not runs.empty:
        runs['label'] = runs['name'] + " (" + runs['created_at'] + ")"
        c_sel, c_btn1, c_btn2 = st.columns([3, 1, 1])
        sel_run_lbl = c_sel.selectbox("Select Run", runs['label'])
        run_id = int(runs[runs['label'] == sel_run_lbl].iloc[0]['id'])

        if c_btn1.button("🔄 Rerun Batch"):
            matches_in_run = db.fetch_dataframe(f"""
                SELECT m.id, r.content as resume_text, r.profile as resume_profile, j.criteria as job_criteria, r.filename, j.id as job_id, r.id as resume_id
                FROM matches m
                JOIN run_matches rm ON m.id = rm.match_id
                JOIN resumes r ON m.resume_id = r.id
                JOIN jobs j ON m.job_id = j.id
                WHERE rm.run_id = {run_id}
            """)
            if not matches_in_run.empty:
                with st.status("Re-analyzing...") as status:
                    bar = st.progress(0)
                    for i, row in matches_in_run.iterrows():
                        resp = client.evaluate_candidate(row['resume_text'], row['job_criteria'], row['resume_profile'])
                        data = document_utils.clean_json_response(resp)
                        if data:
                            db.save_match(row['job_id'], row['resume_id'], data, int(row['id']))
                        bar.progress((i+1)/len(matches_in_run))
                st.rerun()

        if c_btn2.button("🗑️ Delete Run", type="primary"):
            db.execute_query("DELETE FROM runs WHERE id=?", (run_id,))
            db.execute_query("DELETE FROM run_matches WHERE run_id=?", (run_id,))
            st.rerun()

        st.divider()
        results = db.fetch_dataframe(f"""
            SELECT m.*, r.filename as res_name, j.filename as job_name, r.content as res_text, j.criteria as job_crit, r.profile as res_prof
            FROM matches m
            JOIN run_matches rm ON m.id = rm.match_id
            JOIN resumes r ON m.resume_id = r.id
            JOIN jobs j ON m.job_id = j.id
            WHERE rm.run_id = {run_id}
            ORDER BY m.match_score DESC
        """)

        if not results.empty:
            if len(results['job_name'].unique()) > 1:
                st.write("### 🌡️ Heatmap")
                matrix = results.pivot_table(index='res_name', columns='job_name', values='match_score', aggfunc='max').fillna(0).astype(int)
                try:
                    st.dataframe(matrix.style.background_gradient(cmap='RdYlGn'), width="stretch")
                except:
                    st.dataframe(matrix, width="stretch")

            st.write("### 📝 Match List")
            st.markdown(generate_candidate_list_html(results), unsafe_allow_html=True)

            st.divider()
            st.write("### 🔎 Deep Dive")
            results['display'] = results['candidate_name'] + " -> " + results['job_name'] + " (" + results['match_score'].astype(str) + "%)"
            sel_match_lbl = st.selectbox("Inspect Match:", results['display'])

            if sel_match_lbl:
                row = results[results['display'] == sel_match_lbl].iloc[0]
                ac1, ac2 = st.columns([1, 4])
                if ac1.button("🔄 Rerun", key=f"re_s_{row['id']}"):
                    resp = client.evaluate_candidate(row['res_text'], row['job_crit'], row['res_prof'])
                    data = document_utils.clean_json_response(resp)
                    if data:
                        db.save_match(row['job_id'], row['resume_id'], data, row['id'])
                        st.rerun()
                if ac2.button("🗑️ Delete", key=f"del_s_{row['id']}", type="primary"):
                    db.execute_query("DELETE FROM matches WHERE id=?", (int(row['id']),))
                    st.rerun()

                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.title(row['candidate_name'])
                    c2.metric("Score", f"{row['match_score']}%")
                    st.info(row['reasoning'])
                    try:
                        details = json.loads(row['match_details'])
                        if details:
                            st.markdown(generate_criteria_html(details), unsafe_allow_html=True)
                    except:
                        st.warning("Details unavailable.")
    else:
        st.info("No runs found.")
