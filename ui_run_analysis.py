import datetime
import streamlit as st


def render_run_analysis(db, run_analysis_batch, _safe_int, start_run_callback, stop_run_callback):
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
            filter_tag_options = ["All"] + sorted(db.list_tags())
            filter_tag = st.selectbox("Filter by JD Tag (Optional):", filter_tag_options)
            if filter_tag != "All":
                r_data = r_data[r_data['tags'].fillna('').astype(str).apply(lambda x: filter_tag in [t.strip() for t in x.split(',')])]

        sel_r = r_data if st.checkbox("Select All Resumes", value=True) else r_data[r_data['filename'].isin(st.multiselect("Choose Resumes", r_data['filename']))]

    st.caption(f"Selected JDs: {len(sel_j)} / {len(j_data)}")
    st.caption(f"Selected Resumes: {len(sel_r)} / {len(r_data)}")

    if not sel_j.empty and not sel_r.empty:
        st.divider()
        with st.container(border=True):
            st.markdown("#### ⚙️ Smart Match Configuration")

            match_tags = st.checkbox("🎯 Auto-match based on JD Tags", help="When enabled, creates a separate Run for each JD, checking ONLY resumes tagged with that JD's filename.")

            c1, c2 = st.columns([2, 2])
            auto_deep = c1.checkbox("✨ Auto-Upgrade to Deep Match", value=True, help="Automatically run a Deep Scan if the Standard Match score is high enough.")

            default_run_name = f"Run {datetime.datetime.now().strftime('%H:%M')}"
            if len(sel_j) == 1:
                base_job = sel_j.iloc[0]['filename'].rsplit('.', 1)[0]
                default_run_name = f"Run: {base_job}"
            elif len(sel_j) > 1:
                default_run_name = f"Batch Run: {len(sel_j)} Jobs"

            deep_match_thresh = c2.slider("Deep Match Threshold (%)", 0, 100, 50, key="deep_match_threshold")
            run_name = st.text_input("Run Name", value=default_run_name)

            f_rerun = st.checkbox("Force Re-run Pass 1 (Standard Match)", value=False)

            c3, c4 = st.columns([1, 3])
            if st.session_state.is_running and st.session_state.rerun_config is None:
                c4.button("🛑 STOP ANALYSIS", type="primary", use_container_width=True, on_click=stop_run_callback)
                run_analysis_batch(run_name, sel_j, sel_r, deep_match_thresh, auto_deep, force_rerun_pass1=f_rerun, match_by_tags=match_tags)
            elif not st.session_state.is_running:
                c4.button("🚀 START ANALYSIS", type="primary", use_container_width=True, on_click=start_run_callback)
