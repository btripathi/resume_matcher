import streamlit as st
import pandas as pd
import json
import time
import datetime
import logging

# Import local modules
import database
import document_utils
import ai_engine

# --- CONFIGURATION ---
st.set_page_config(page_title="AI Recruiting Workbench (Pro)", page_icon="🚀", layout="wide")

# Init Session State
if "lm_base_url" not in st.session_state: st.session_state.lm_base_url = "http://localhost:1234/v1"
if "lm_api_key" not in st.session_state: st.session_state.lm_api_key = "lm-studio"
if "ocr_enabled" not in st.session_state: st.session_state.ocr_enabled = True
if "processed_files" not in st.session_state: st.session_state.processed_files = set()

# Initialize dynamic keys for file uploaders to allow clearing them
if "jd_uploader_key" not in st.session_state: st.session_state.jd_uploader_key = 0
if "res_uploader_key" not in st.session_state: st.session_state.res_uploader_key = 0

db = database.DBManager()

# --- UI HELPERS ---
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

def generate_candidate_list_html(df, threshold=75):
    if df.empty: return "<p style='color: #666;'>No results found.</p>"
    rows = ""

    # Calculate review threshold (20 points below success threshold)
    review_thresh = max(0, threshold - 20)

    for idx, row in df.iterrows():
        # --- UI DECISION LOGIC (OVERRIDES AI TEXT) ---
        score = row['match_score']

        if score >= threshold:
            decision_label = "Move Forward"
            badge_color = "color: #0f5132; background-color: #d1e7dd;" # Green
            score_color = "#0f5132"
        elif score >= review_thresh:
            decision_label = "Review"
            badge_color = "color: #664d03; background-color: #fff3cd;" # Yellow
            score_color = "#856404"
        else:
            decision_label = "Reject"
            badge_color = "color: #842029; background-color: #f8d7da;" # Red
            score_color = "#842029"

        # Display Standard Score if it differs significantly or is available
        std_score_display = ""
        if 'standard_score' in row and pd.notna(row['standard_score']) and row['strategy'] == 'Deep':
            std_score_display = f"<br><span style='font-size: 10px; color: #666;'>Pass 1: {int(row['standard_score'])}%</span>"

        rows += f'<tr><td style="font-weight: 600;">{row["candidate_name"]}<br><span style="font-size: 11px; color: #666;">{row["res_name"]}</span></td><td style="color: {score_color}; font-weight: bold; font-size: 16px;">{score}%{std_score_display}</td><td><span class="status-badge" style="{badge_color}">{decision_label}</span></td><td style="font-size: 13px; color: #444;">{row["reasoning"]}</td></tr>'
    return f"""<style>.candidate-table {{width: 100%; border-collapse: collapse; margin-bottom: 20px;}}.candidate-table th {{background-color: #f8f9fa; padding: 12px; text-align: left;}}.candidate-table td {{padding: 12px; border-bottom: 1px solid #dee2e6; vertical-align: top;}}.status-badge {{padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px;}}</style><table class="candidate-table"><thead><tr><th>Candidate</th><th>Score</th><th>Decision</th><th>Reasoning</th></tr></thead><tbody>{rows}</tbody></table>"""

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

    # Jobs Column
    with c1:
        st.subheader("📂 Upload Job Descriptions")
        # Use dynamic key based on session state
        jd_up = st.file_uploader("Upload JDs", accept_multiple_files=True, key=f"jd_up_{st.session_state.jd_uploader_key}")
        force_reparse_jd = st.checkbox("Force Reparse Existing JDs", value=False)

        if jd_up and st.button("Process New JDs", type="primary"):
            with st.status("Processing JDs...") as status:
                for f in jd_up:
                    # Check duplication
                    existing = db.get_job_by_filename(f.name)
                    if existing and not force_reparse_jd:
                        st.warning(f"Skipped {f.name} (Duplicate). Check 'Force Reparse' to overwrite.")
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
                        st.info(f"Updated {f.name}")
                    else:
                        db.add_job(f.name, text, analysis)

                # Increment key to clear uploader
                st.session_state.jd_uploader_key += 1
                st.rerun()

        jds = db.fetch_dataframe("SELECT id, filename, criteria, content, upload_date FROM jobs")
        if not jds.empty:
            st.dataframe(jds[['filename', 'upload_date']], hide_index=True, width="stretch")

            st.divider()
            jd_choice = st.selectbox("Select JD to Edit:", jds['filename'])
            row = jds[jds['filename'] == jd_choice].iloc[0]

            # --- RAW TEXT INSPECTOR FOR JD ---
            with st.expander("🔍 Inspect Raw Extracted Text", expanded=False):
                st.info("This is the exact text extracted from the file.")
                st.text_area("Raw Text Content", value=row['content'], height=400, disabled=True, key=f"raw_jd_{row['id']}")
            # ---------------------------------

            new_crit = st.text_area("JSON Criteria", value=row['criteria'], height=300, key=f"jd_ed_{row['id']}")

            c_sav, c_del = st.columns(2)
            if c_sav.button("Save JD", key=f"sav_jd_{row['id']}"):
                db.execute_query("UPDATE jobs SET criteria = ? WHERE id = ?", (new_crit, int(row['id'])))
                st.success("Saved!")
                st.rerun()
            if c_del.button("Delete JD", key=f"del_jd_{row['id']}", type="primary"):
                db.execute_query("DELETE FROM matches WHERE job_id = ?", (int(row['id']),))
                db.execute_query("DELETE FROM jobs WHERE id = ?", (int(row['id']),))
                st.rerun()

    # Resumes Column
    with c2:
        st.subheader("📄 Upload Resumes")
        # Use dynamic key based on session state
        res_up = st.file_uploader("Upload Resumes", accept_multiple_files=True, key=f"res_up_{st.session_state.res_uploader_key}")
        force_reparse_res = st.checkbox("Force Reparse Existing Resumes", value=False)

        if res_up and st.button("Process New Resumes", type="primary"):
            with st.status("Processing Resumes...") as status:
                for f in res_up:
                    # Check duplication
                    existing = db.get_resume_by_filename(f.name)
                    if existing and not force_reparse_res:
                        st.warning(f"Skipped {f.name} (Duplicate). Check 'Force Reparse' to overwrite.")
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
                        st.info(f"Updated {f.name}")
                    else:
                        db.add_resume(f.name, text, analysis)

                # Increment key to clear uploader
                st.session_state.res_uploader_key += 1
                st.rerun()

        ress = db.fetch_dataframe("SELECT id, filename, profile, content, upload_date FROM resumes")
        if not ress.empty:
            st.dataframe(ress[['filename', 'upload_date']], hide_index=True, width="stretch")

            st.divider()
            res_choice = st.selectbox("Select Resume to Edit:", ress['filename'])
            row = ress[ress['filename'] == res_choice].iloc[0]

            # --- RAW TEXT INSPECTOR ---
            with st.expander("🔍 Inspect Raw Extracted Text", expanded=False):
                st.info("This is the exact text extracted from the file. If this is empty or gibberish, OCR failed or the file is unreadable.")
                st.text_area("Raw Text Content", value=row['content'], height=400, disabled=True, key=f"raw_{row['id']}")
            # ---------------------------

            new_prof = st.text_area("JSON Profile", value=row['profile'], height=300, key=f"res_ed_{row['id']}")

            c_sav, c_del = st.columns(2)
            if c_sav.button("Save Profile", key=f"sav_res_{row['id']}"):
                db.execute_query("UPDATE resumes SET profile = ? WHERE id = ?", (new_prof, int(row['id'])))
                st.success("Saved!")
                st.rerun()
            if c_del.button("Delete Resume", key=f"del_res_{row['id']}", type="primary"):
                db.execute_query("DELETE FROM matches WHERE resume_id = ?", (int(row['id']),))
                db.execute_query("DELETE FROM resumes WHERE id = ?", (int(row['id']),))
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
        # Removed "Selection Mode" radio button.
        # Simplified logic: User manually selects OR selects all.
        # This removes the redundant slider confusion.
        sel_r = r_data if st.checkbox("Select All Resumes", value=True) else r_data[r_data['filename'].isin(st.multiselect("Choose Resumes", r_data['filename']))]

    if not sel_j.empty and not sel_r.empty:
        st.divider()
        with st.container(border=True):
            st.markdown("#### ⚙️ Smart Match Configuration")

            c1, c2 = st.columns([2, 2])

            # Simplified Strategy Selection
            auto_deep = c1.checkbox("✨ Auto-Upgrade to Deep Match", value=True, help="Automatically run a Deep Scan if the Standard Match score is high enough.")

            run_name = c2.text_input("Run Batch Name", value=f"Run {datetime.datetime.now().strftime('%H:%M')}")

            deep_match_thresh = 50
            if auto_deep:
                deep_match_thresh = st.slider("Deep Match Auto-Trigger Threshold (%)", 0, 100, 50, help="If Standard Match score >= this value, the system will automatically run the Deep Scan.")

            c3, c4, c5 = st.columns([1, 2, 2])
            f_rerun = c3.toggle("Force Full Re-run", help="Ignore existing matches and re-analyze everything.")

            if c4.button("🚀 START ANALYSIS", type="primary", use_container_width=True):
                rid = db.create_run(run_name)
                total = len(sel_j) * len(sel_r)
                count = 0

                with st.status("Analyzing...", expanded=True) as status:
                    master_bar = st.progress(0)
                    task_display = st.empty()
                    sub_bar = st.empty()

                    # --- SCROLLABLE LOG CONSOLE ---
                    log_placeholder = st.empty()
                    log_lines = []

                    def add_log(message):
                        ts = datetime.datetime.now().strftime("%H:%M:%S")
                        log_lines.insert(0, f"<div style='margin-bottom:2px;'><span style='color:#888; font-size:0.8em;'>[{ts}]</span> {message}</div>")

                        html_content = f"""
                        <div style="height:300px; overflow-y:auto; background-color:#f8f9fa; border:1px solid #dee2e6; padding:10px; border-radius:4px; font-family:monospace; font-size:0.9em; color:#212529;">
                            {''.join(log_lines)}
                        </div>
                        """
                        log_placeholder.markdown(html_content, unsafe_allow_html=True)
                    # ------------------------------

                    for _, job in sel_j.iterrows():
                        for _, res in sel_r.iterrows():
                            count += 1
                            current_resume_name = res['filename']

                            # Update Status Bar with X/Y
                            status.update(label=f"Match {count}/{total}: {current_resume_name} vs {job['filename']}")
                            add_log(f"<b>Starting analysis for {current_resume_name}</b> vs {job['filename']}")

                            exist = db.get_match_if_exists(int(job['id']), int(res['id']))
                            mid = exist['id'] if exist else None
                            score = exist['match_score'] if exist else 0

                            # Logic:
                            # 1. Always ensure we have at least a Standard Match (Pass 1).
                            # 2. If Auto-Deep is ON and Score >= Thresh, ensure we have a Deep Match.

                            # Step 1: Standard Pass (Fast Scan)
                            # Run if: No match exists OR we are forcing a rerun
                            should_run_standard = (not exist) or f_rerun

                            if should_run_standard:
                                task_display.info(f"🧠 Pass 1: Holistic scan for **{current_resume_name}**...")
                                data = client.evaluate_standard(res['content'], job['criteria'], res['profile'])
                                if data:
                                    # Preserve reasoning if updating
                                    std_reasoning = data.get('reasoning', "No reasoning provided.")

                                    # Save Pass 1
                                    mid = db.save_match(int(job['id']), int(res['id']), data, mid, strategy="Standard", standard_score=data['match_score'], standard_reasoning=std_reasoning)
                                    score = data['match_score']

                                    # Update 'exist' so Deep Match logic knows the latest state
                                    exist = db.get_match_if_exists(int(job['id']), int(res['id']))
                                    add_log(f"&nbsp;&nbsp;🧠 Standard Score: {score}%")
                            else:
                                add_log(f"&nbsp;&nbsp;ℹ️ Using existing Standard Score: {score}%")

                            # Step 2: Deep Match (Pass 2)
                            # Run if: Auto-Deep is enabled AND Score >= Threshold
                            # Skip if: We already have a Deep Match (unless forced rerun)

                            is_already_deep = exist and exist['strategy'] == 'Deep'
                            qualifies_for_deep = score >= deep_match_thresh

                            if auto_deep and qualifies_for_deep:
                                if is_already_deep and not f_rerun:
                                    add_log("&nbsp;&nbsp;ℹ️ Deep match already exists. Skipping.")
                                else:
                                    add_log(f"&nbsp;&nbsp;🔬 Threshold met ({score}%). Triggering Deep Scan...")
                                    jd_c = json.loads(job['criteria'])

                                    # OPTIMIZATION: SPLIT CRITERIA
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

                                    # Process High Priority
                                    num_reqs = len(priority_reqs) + (1 if bulk_reqs else 0)
                                    processed_count = 0

                                    for rt, rv in priority_reqs:
                                        processed_count += 1
                                        # Log the specific check
                                        add_log(f"&nbsp;&nbsp;&nbsp;&nbsp;🔎 Checking {rt.replace('_', ' ').title()}: <i>{str(rv)[:40]}...</i>")

                                        task_display.warning(f"🔬 Deep Scan: Checking {rt.upper()} (Priority)...")
                                        sub_bar.progress(processed_count/num_reqs)

                                        res_crit = client.evaluate_criterion(res['content'], rt, rv)
                                        if res_crit:
                                            details.append(res_crit)
                                            # Log result
                                            icon = "✅" if res_crit['status'] == 'Met' else "⚠️" if res_crit['status'] == 'Partial' else "❌"
                                            add_log(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↳ {icon} {res_crit['status']}")

                                    # Process Low Priority (Bulk)
                                    if bulk_reqs:
                                        processed_count += 1
                                        task_display.info(f"⚡ Bulk Scan: Checking {len(bulk_reqs)} secondary criteria...")
                                        add_log(f"&nbsp;&nbsp;&nbsp;&nbsp;⚡ Bulk checking {len(bulk_reqs)} secondary items...")
                                        sub_bar.progress(processed_count/num_reqs)
                                        bulk_results = client.evaluate_bulk_criteria(res['content'], bulk_reqs)
                                        if bulk_results: details.extend(bulk_results)

                                    sub_bar.empty()
                                    sf, df, rf = client.generate_final_decision(res['filename'], details, strategy="Deep")

                                    # Important: Carry over the Standard Reasoning/Score from 'exist' record
                                    std_score_saved = exist.get('standard_score', score)
                                    std_reasoning_saved = exist.get('standard_reasoning', exist.get('reasoning'))

                                    mid = db.save_match(int(job['id']), int(res['id']), {"candidate_name": res['filename'], "match_score": sf, "decision": df, "reasoning": rf, "match_details": details}, mid, strategy="Deep", standard_score=std_score_saved, standard_reasoning=std_reasoning_saved)
                                    add_log(f"&nbsp;&nbsp;🏁 <b>Deep Match Final: {sf}% ({df})</b>")

                            elif auto_deep and not qualifies_for_deep:
                                add_log(f"&nbsp;&nbsp;⏭️ Score ({score}%) below threshold ({deep_match_thresh}%). Skipping Deep Match.")

                            if mid: db.link_run_match(rid, mid)
                            master_bar.progress(count/total)

                    status.update(label="Complete!", state="complete")
                st.rerun()

            if c5.button("🛑 STOP", type="secondary", use_container_width=True):
                st.stop()

# --- TAB 3: MATCH RESULTS ---
with tab3:
    runs = db.fetch_dataframe("SELECT * FROM runs ORDER BY id DESC")
    if not runs.empty:
        runs['label'] = runs['name'] + " (" + runs['created_at'] + ")"
        sel_run = st.selectbox("Select Run Batch:", runs['label'])
        run_id = int(runs[runs['label'] == sel_run].iloc[0]['id'])

        # --- RUN-LEVEL ACTIONS ---
        c_act1, c_act2, _ = st.columns([1, 1, 3])
        with c_act1:
            if st.button("🔄 Rerun Batch"):
                # Placeholder for batch rerun if needed, or user can just use Tab 2
                st.info("Please use Tab 2 to rerun full batches with new settings.")
        with c_act2:
            if st.button("🗑️ Delete Run", type="primary"):
                db.execute_query("DELETE FROM runs WHERE id=?", (run_id,))
                db.execute_query("DELETE FROM run_matches WHERE run_id=?", (run_id,))
                st.success("Deleted")
                st.rerun()

        results = db.fetch_dataframe(f"""
            SELECT m.*, r.filename as res_name, j.filename as job_name
            FROM matches m JOIN run_matches rm ON m.id = rm.match_id
            JOIN resumes r ON m.resume_id = r.id JOIN jobs j ON m.job_id = j.id
            WHERE rm.run_id = {run_id} ORDER BY m.match_score DESC
        """)

        if not results.empty:
            # --- Dynamic Threshold Slider ---
            c_thresh, _ = st.columns([2, 4])
            with c_thresh:
                display_thresh = st.slider("Decision Threshold (%)", 0, 100, 75, help="Scores above this are 'Move Forward'. Scores within 20% below are 'Review'.")

            # --- SPLIT TABLES: DEEP vs STANDARD ---
            deep_df = results[results['strategy'] == 'Deep']
            std_df = results[results['strategy'] != 'Deep']

            st.markdown("### ✨ Deep Matches (Passed Pass 1)")
            st.markdown(generate_candidate_list_html(deep_df, threshold=display_thresh), unsafe_allow_html=True)

            st.divider()
            st.markdown("### 🧠 Standard Matches (Did not qualify for Deep Scan)")
            st.markdown(generate_candidate_list_html(std_df, threshold=display_thresh), unsafe_allow_html=True)

            st.divider()
            st.write("### 🔎 Match Evidence Investigator")
            results['d'] = results['candidate_name'] + " -> " + results['job_name'] + " (" + results['match_score'].astype(str) + "%)"
            s_match = st.selectbox("Select Candidate to Inspect Details:", results['d'])

            if s_match:
                row = results[results['d'] == s_match].iloc[0]

                # Single Match Actions
                c_act1, c_act2 = st.columns([1, 4])
                match_id = int(row['id'])
                with c_act1:
                    if st.button("🔄 Rerun This Match", key=f"re_s_{match_id}"):
                         with st.status("Re-evaluating...", expanded=True) as status:
                            action_data = db.fetch_dataframe(f"SELECT r.content as resume_text, r.profile as resume_profile, j.criteria as job_criteria FROM matches m JOIN resumes r ON m.resume_id = r.id JOIN jobs j ON m.job_id = j.id WHERE m.id = {match_id}").iloc[0]
                            # Corrected method call below from evaluate_candidate to evaluate_standard
                            resp = client.evaluate_standard(action_data['resume_text'], action_data['job_criteria'], action_data['resume_profile'])
                            data = document_utils.clean_json_response(resp)
                            if data:
                                db.save_match(None, None, data, match_id)
                                status.update(label="Complete!", state="complete")
                                time.sleep(1)
                                st.rerun()
                with c_act2:
                    if st.button("🗑️ Delete This Match", key=f"del_s_{match_id}", type="primary"):
                        db.execute_query("DELETE FROM matches WHERE id=?", (match_id,))
                        st.success("Deleted")
                        time.sleep(0.5)
                        st.rerun()

                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.title(row['candidate_name'])
                    c2.metric("Weighted Score", f"{row['match_score']}%")

                    if pd.notna(row.get('standard_score')) and row['strategy'] == 'Deep':
                         st.caption(f"Pass 1 (Standard) Score: **{int(row['standard_score'])}%**")

                    if row['strategy'] == 'Deep':
                        st.caption("✨ Evaluated with High-Precision Multi-Pass Tiered Weighting")

                    # Display reasoning
                    st.info(f"**Final Decision:** {row['reasoning']}")

                    # Display saved Standard Reasoning if available and different
                    if pd.notna(row.get('standard_reasoning')) and row['strategy'] == 'Deep':
                         with st.expander("📄 View Pass 1 (Standard) Analysis"):
                             st.markdown(f"_{row['standard_reasoning']}_")

                    try:
                        dets = json.loads(row['match_details'])
                        if dets: st.markdown(generate_criteria_html(dets), unsafe_allow_html=True)
                    except: st.warning("Detailed requirement breakdown unavailable for this match.")
    else: st.info("No run history found. Run an analysis in Tab 2 first.")
