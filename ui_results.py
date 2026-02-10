import json
import time
import pandas as pd
import streamlit as st


def render_results(db, client, sync_db_if_allowed, run_analysis_batch, prepare_rerun_callback, stop_run_callback, utils, document_utils, match_flow):
    if not st.session_state.write_mode:
        st.info("Read-only mode: reruns/edits are local only and won't sync to the shared DB.", icon="🔒")

    simple_tab, run_tab = st.tabs(["📌 Simple JD View", "📊 Run-Based Results"])

    with simple_tab:
        jobs_df = db.fetch_dataframe("SELECT id, filename FROM jobs ORDER BY upload_date DESC")
        if jobs_df.empty:
            st.info("No Job Descriptions available yet.")
        else:
            last_match_job = db.fetch_dataframe("""
                SELECT j.filename
                FROM matches m
                JOIN jobs j ON m.job_id = j.id
                ORDER BY m.id DESC
                LIMIT 1
            """)
            default_idx = 0
            if not last_match_job.empty:
                last_name = last_match_job.iloc[0]["filename"]
                if last_name in jobs_df["filename"].values:
                    default_idx = int(jobs_df.index[jobs_df["filename"] == last_name][0])

            jd_label = st.selectbox(
                "Select Job Description:",
                jobs_df["filename"].tolist(),
                index=default_idx,
                key="simple_jd_select",
            )
            selected_job = jobs_df[jobs_df["filename"] == jd_label].iloc[0]
            jd_id = int(selected_job["id"])

            jd_results = db.fetch_dataframe(f"""
                SELECT m.*, r.filename as res_name, j.filename as job_name
                FROM matches m
                JOIN resumes r ON m.resume_id = r.id
                JOIN jobs j ON m.job_id = j.id
                WHERE m.job_id = {jd_id}
                ORDER BY m.match_score DESC
            """)

            if jd_results.empty:
                st.info("No matches found for this JD yet.")
            else:
                threshold_rows = db.fetch_dataframe(f"""
                    SELECT rm.match_id, r.threshold
                    FROM run_matches rm
                    JOIN runs r ON r.id = rm.run_id
                    JOIN matches m ON m.id = rm.match_id
                    WHERE m.job_id = {jd_id}
                """)
                threshold_map = {}
                if not threshold_rows.empty:
                    for _, row in threshold_rows.iterrows():
                        try:
                            threshold_map[int(row["match_id"])] = int(row["threshold"])
                        except Exception:
                            continue

                c1, c2, c3 = st.columns(3)
                c1.metric("Total Matches", len(jd_results))
                c2.metric("Deep Matches", len(jd_results[jd_results["strategy"] == "Deep"]))
                c3.metric("Standard Only", len(jd_results[jd_results["strategy"] != "Deep"]))

                thresh_row = db.fetch_dataframe(f"""
                    SELECT r.threshold
                    FROM runs r
                    JOIN run_matches rm ON rm.run_id = r.id
                    JOIN matches m ON m.id = rm.match_id
                    WHERE m.job_id = {jd_id}
                    ORDER BY r.id DESC
                    LIMIT 1
                """)
                label_threshold = 50
                if not thresh_row.empty and "threshold" in thresh_row.columns and pd.notna(thresh_row.iloc[0]["threshold"]):
                    label_threshold = int(thresh_row.iloc[0]["threshold"])
                deep_df = jd_results[jd_results["strategy"] == "Deep"]
                std_df = jd_results[jd_results["strategy"] != "Deep"]

                st.markdown("#### ✨ Deep Matches")
                if deep_df.empty:
                    st.info("No Deep matches for this JD.")
                else:
                    st.markdown(
                        utils.generate_candidate_list_html(
                            deep_df, threshold=label_threshold, is_deep=True, threshold_map=threshold_map
                        ),
                        unsafe_allow_html=True,
                    )

                st.markdown("#### 🧠 Standard Matches")
                if std_df.empty:
                    st.info("No Standard matches for this JD.")
                else:
                    st.markdown(utils.generate_candidate_list_html(std_df, threshold=label_threshold, is_deep=False), unsafe_allow_html=True)

    with run_tab:
        runs = db.fetch_dataframe("SELECT * FROM runs ORDER BY id DESC")
        if runs.empty:
            st.info("No run history found. Run an analysis in Tab 2 first.")
            return

        runs["label"] = runs["name"] + " (" + runs["created_at"] + ")"
        labels = runs["label"].tolist()
        current_label = st.session_state.get("run_select_label", labels[0])
        default_idx = labels.index(current_label) if current_label in labels else 0

        # Minimal selector outside; all other controls inside rerun box
        sel_run_label = st.selectbox("Select Run Batch:", labels, index=default_idx, key="run_select_label")

        with st.expander("🔄 Rerun this Batch with New Settings", expanded=False):
            st.info("Re-running will process the JDs and Resumes linked to this batch using new parameters.")

            c_sel, c_ren = st.columns([3, 1])
            with c_sel:
                st.caption(f"Selected Batch: {sel_run_label}")

            run_row = runs[runs["label"] == sel_run_label].iloc[0]
            run_id = int(run_row["id"])
            run_name_base = run_row["name"]
            run_threshold = utils.safe_int(run_row["threshold"], 50) if "threshold" in run_row and pd.notna(run_row["threshold"]) else 50

            with c_ren:
                new_run_name = st.text_input("Rename Batch:", value=run_name_base, key=f"ren_{run_id}")
                if new_run_name != run_name_base:
                    db.execute_query("UPDATE runs SET name=? WHERE id=?", (new_run_name, run_id))
                    with st.spinner("Syncing rename to GitHub..."):
                        sync_db_if_allowed()
                    st.rerun()

            c_r1, c_r2 = st.columns(2)
            create_new_run = c_r1.checkbox("Create new run (separate history)", value=False)
            rerun_name_input = c_r1.text_input("New Batch Name", value=f"Rerun of {run_name_base}", disabled=not create_new_run)
            new_auto_deep = c_r1.checkbox("Auto-Upgrade to Deep Match", value=True, key="rerun_auto")
            new_thresh = 50
            if new_auto_deep:
                new_thresh = c_r2.slider("New Deep Match Threshold (%)", 0, 100, run_threshold, key="rerun_thresh")

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
                job_ids = list(linked_data["job_id"].unique())
                res_ids = list(linked_data["resume_id"].unique())
                j_ids_str = ",".join(map(str, job_ids))
                r_ids_str = ",".join(map(str, res_ids))

                rerun_j = db.fetch_dataframe(f"SELECT * FROM jobs WHERE id IN ({j_ids_str})")
                rerun_r = db.fetch_dataframe(f"SELECT * FROM resumes WHERE id IN ({r_ids_str})")

                if st.session_state.is_running and st.session_state.rerun_config:
                    st.button("🛑 STOP RERUN", type="primary", on_click=stop_run_callback)
                    cfg = st.session_state.rerun_config
                    run_analysis_batch(
                        cfg["run_name"],
                        cfg["jobs"],
                        cfg["resumes"],
                        cfg["thresh"],
                        cfg["auto"],
                        cfg["force"],
                        match_by_tags=cfg.get("tags", False),
                        deep_only=cfg.get("deep_only", False),
                        force_rerun_deep=cfg.get("force_rerun_deep", False),
                        run_id=cfg.get("run_id"),
                        create_new_run=cfg.get("create_new_run", True),
                    )
                elif not st.session_state.is_running:
                    name_to_use = rerun_name_input if create_new_run else run_name_base
                    create_new_run_effective = create_new_run if not new_match_tags else True
                    st.button(
                        "🚀 Rerun Batch",
                        type="primary",
                        on_click=prepare_rerun_callback,
                        args=(name_to_use, rerun_j, rerun_r, new_thresh, new_auto_deep, f_rerun_p1, new_match_tags, deep_only, force_rerun_deep, create_new_run_effective, run_id),
                    )
            else:
                st.error("Could not find original JDs/Resumes for this run.")

            if st.button("🗑️ Delete Run History", type="secondary"):
                db.execute_query("DELETE FROM runs WHERE id=?", (run_id,))
                db.execute_query("DELETE FROM run_matches WHERE run_id=?", (run_id,))
                with st.spinner("Syncing deletion to GitHub..."):
                    sync_db_if_allowed()
                st.success("Deleted")
                st.rerun()

        sel_run_label = st.session_state.get("run_select_label", labels[0])
        run_row = runs[runs["label"] == sel_run_label].iloc[0]
        run_id = int(run_row["id"])
        run_name_base = run_row["name"]
        run_threshold = utils.safe_int(run_row["threshold"], 50) if "threshold" in run_row and pd.notna(run_row["threshold"]) else 50

        results = db.fetch_dataframe(f"""
            SELECT m.*, r.filename as res_name, j.filename as job_name
            FROM matches m JOIN run_matches rm ON m.id = rm.match_id
            JOIN resumes r ON m.resume_id = r.id JOIN jobs j ON m.job_id = j.id
            WHERE rm.run_id = {run_id} ORDER BY m.match_score DESC
        """)

        if results.empty:
            st.info("No results found for this run.")
            return

        st.caption(f"Results showing against Deep Match Threshold of **{run_threshold}%** used in this run.")
        threshold_map = {int(mid): int(run_threshold) for mid in results["id"].tolist()}
        total_matches = len(results)
        deep_count = len(results[results["strategy"] == "Deep"])
        std_count = total_matches - deep_count
        unique_candidates = results["candidate_name"].nunique()
        unique_jobs = results["job_id"].nunique()

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Matches", total_matches)
        m2.metric("Deep Matches", deep_count)
        m3.metric("Standard Only", std_count)
        m4.metric("Unique Candidates", unique_candidates)
        m5.metric("Unique Jobs", unique_jobs)

        col_exp, _ = st.columns([1, 4])
        with col_exp:
            csv_data = results.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Results CSV",
                data=csv_data,
                file_name=f"match_results_{run_id}.csv",
                mime="text/csv",
            )

        if unique_jobs > 1:
            matrix_filter = st.radio("Matrix Data View:", ["All Scores", "Deep Match Only", "Standard Match Only"], horizontal=True)
            matrix_html = utils.generate_matrix_view(results, view_mode=matrix_filter)
            if matrix_html:
                st.markdown("### 📊 Cross-Job Match Matrix")
                st.markdown(matrix_html, unsafe_allow_html=True)
            st.divider()

        run_name_base = run_row["name"]
        run_threshold = utils.safe_int(run_row["threshold"], 50) if "threshold" in run_row and pd.notna(run_row["threshold"]) else 50
        unique_jobs = results["job_name"].nunique()
        unique_job_names = results["job_name"].unique()
        deep_df = results[results["strategy"] == "Deep"]
        std_df = results[results["strategy"] != "Deep"]

        st.markdown(f"### ✨ Deep Matches for {run_name_base}")
        if deep_df.empty:
            st.info("No candidates qualified for Deep Match in this run.")
        else:
            if unique_jobs > 1:
                tabs = st.tabs(list(unique_job_names))
                for i, job in enumerate(unique_job_names):
                    with tabs[i]:
                        job_subset = deep_df[deep_df["job_name"] == job]
                        st.markdown(
                            utils.generate_candidate_list_html(
                                job_subset, threshold=run_threshold, is_deep=True, threshold_map=threshold_map
                            ),
                            unsafe_allow_html=True,
                        )
            else:
                st.markdown(
                    utils.generate_candidate_list_html(deep_df, threshold=run_threshold, is_deep=True, threshold_map=threshold_map),
                    unsafe_allow_html=True,
                )

        st.divider()

        st.markdown("### 🧠 Standard Matches (Pass 1 Only)")
        if std_df.empty:
            st.info("All candidates in this run were upgraded to Deep Match.")
        else:
            if unique_jobs > 1:
                tabs_std = st.tabs(list(unique_job_names))
                for i, job in enumerate(unique_job_names):
                    with tabs_std[i]:
                        job_subset = std_df[std_df["job_name"] == job]
                        st.markdown(utils.generate_candidate_list_html(job_subset, threshold=run_threshold, is_deep=False), unsafe_allow_html=True)
            else:
                st.markdown(utils.generate_candidate_list_html(std_df, threshold=run_threshold, is_deep=False), unsafe_allow_html=True)

        st.divider()

        st.write("### 🔎 Match Evidence Investigator")
        col_filter1, col_filter2 = st.columns(2)
        avail_jobs = results["job_name"].unique()
        sel_job_filter = col_filter1.selectbox("Filter by Job:", avail_jobs, key="inv_job_filter")

        filtered_candidates = results[results["job_name"] == sel_job_filter]
        candidate_map = {f"{row['candidate_name']} ({row['match_score']}%)": row["id"] for idx, row in filtered_candidates.iterrows()}
        sel_candidate_label = col_filter2.selectbox("Select Candidate:", list(candidate_map.keys()), key="inv_cand_filter")

        if sel_candidate_label:
            match_id = candidate_map[sel_candidate_label]
            row = results[results["id"] == match_id].iloc[0]

            rerun_log_placeholder = st.empty()
            c_act1, c_act2 = st.columns([1, 4])
            with c_act1:
                if st.button("🔄 Rerun This Match", key=f"re_s_{match_id}"):
                    st.session_state.rerun_match_id = match_id
            with c_act2:
                if st.button("🗑️ Delete This Match", key=f"del_s_{match_id}", type="primary"):
                    db.execute_query("DELETE FROM matches WHERE id=?", (match_id,))
                    with st.spinner("Syncing to GitHub..."):
                        sync_db_if_allowed()
                    st.success("Deleted")
                    time.sleep(0.5)
                    st.rerun()

            if st.session_state.get("rerun_match_id") == match_id:
                with st.status("Re-evaluating...", expanded=True) as status:
                    add_log = match_flow.init_log_ui(height=320, full_width=True, placeholder=rerun_log_placeholder)
                    if row.get("strategy") == "Deep":
                        task_display = st.empty()
                        sub_bar = st.progress(0)
                        action_data = db.fetch_dataframe(
                            f"SELECT r.content as resume_text, r.profile as resume_profile, "
                            f"j.criteria as job_criteria, j.id as job_id, r.id as resume_id "
                            f"FROM matches m "
                            f"JOIN resumes r ON m.resume_id = r.id "
                            f"JOIN jobs j ON m.job_id = j.id WHERE m.id = {match_id}"
                        ).iloc[0]
                        job_df = db.fetch_dataframe(f"SELECT * FROM jobs WHERE id = {int(action_data['job_id'])}")
                        res_df = db.fetch_dataframe(f"SELECT * FROM resumes WHERE id = {int(action_data['resume_id'])}")
                        match_flow.process_match_flow(
                            job_df.iloc[0],
                            res_df.iloc[0],
                            db,
                            client,
                            run_threshold,
                            True,
                            True,
                            True,
                            False,
                            add_log,
                            safe_int_fn=utils.safe_int,
                            task_display=task_display,
                            sub_bar=sub_bar,
                        )
                        sub_bar.empty()
                        with st.spinner("Syncing to GitHub..."):
                            sync_db_if_allowed()
                        status.update(label="Complete!", state="complete")
                    else:
                        add_log("🧠 Running Pass 1 (Standard) evaluation...")
                        action_data = db.fetch_dataframe(
                            f"SELECT r.content as resume_text, r.profile as resume_profile, j.criteria as job_criteria "
                            f"FROM matches m JOIN resumes r ON m.resume_id = r.id JOIN jobs j ON m.job_id = j.id WHERE m.id = {match_id}"
                        ).iloc[0]
                        resp = client.evaluate_standard(action_data["resume_text"], action_data["job_criteria"], action_data["resume_profile"])
                        data = resp if isinstance(resp, dict) else document_utils.clean_json_response(resp)
                        if data:
                            raw_reasoning = data.get("reasoning", "No reasoning provided.")
                            std_reasoning = "\n".join(raw_reasoning) if isinstance(raw_reasoning, list) else str(raw_reasoning)
                            add_log(f"✅ Pass 1 completed. Score: {data.get('match_score', 0)}%")
                            db.save_match(None, None, data, match_id, standard_reasoning=std_reasoning)
                            with st.spinner("Syncing to GitHub..."):
                                sync_db_if_allowed()
                            status.update(label="Complete!", state="complete")
                        else:
                            add_log("❌ Pass 1 failed or returned invalid data.")
                            status.update(label="Re-evaluation failed.", state="error")
                    time.sleep(1)
                    st.session_state.rerun_match_id = None
                    st.rerun()

            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.title(row["candidate_name"])
                c2.metric("Weighted Score", f"{utils.safe_int(row['match_score'], 0)}%")

                if pd.notna(row.get("standard_score")) and row["strategy"] == "Deep":
                    st.caption(f"Pass 1 (Standard) Score: **{utils.safe_int(row['standard_score'], 0)}%**")

                if row["strategy"] == "Deep":
                    st.caption("✨ Evaluated with High-Precision Multi-Pass Tiered Weighting")

                st.info(f"**Final Decision:** {row['reasoning']}")

                if pd.notna(row.get("standard_reasoning")) and row["strategy"] == "Deep":
                    with st.expander("📄 View Pass 1 (Standard) Analysis"):
                        st.markdown(f"_{row['standard_reasoning']}_")

                try:
                    dets = json.loads(row["match_details"])
                    if dets:
                        st.markdown(utils.generate_criteria_html(dets), unsafe_allow_html=True)
                except Exception:
                    st.warning("Detailed requirement breakdown unavailable for this match.")
