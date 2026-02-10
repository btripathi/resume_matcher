import json
import time
import re
import pandas as pd
import streamlit as st


def render_manage_data(db, client, document_utils, sync_db_if_allowed, start_jd_upload, stop_jd_upload, start_res_upload, stop_res_upload):
    if not st.session_state.write_mode:
        st.info("Read-only mode: uploads/edits are saved locally only and won't sync to the shared DB.", icon="🔒")

    subtab_jd, subtab_res, subtab_tags, subtab_verify = st.tabs([
        "📂 Job Descriptions", "📄 Candidate Resumes", "🏷️ Tag Manager", "✅ Data Verification"
    ])

    # --- JOB DESCRIPTIONS SUB-TAB ---
    with subtab_jd:
        with st.expander("📤 Upload New Job Descriptions", expanded=False):
            tag_options = sorted(set(db.list_tags()))
            create_tag_option = "➕ Create new tag…"
            jd_tag_assign = st.multiselect(
                "Assign Tag(s) to JDs (Optional):",
                tag_options + [create_tag_option]
            )
            new_jd_tag = ""
            if create_tag_option in jd_tag_assign:
                new_jd_tag = st.text_input("New Tag Name", key="new_jd_tag")
                jd_tag_assign = [t for t in jd_tag_assign if t != create_tag_option]
            new_jd_tag = new_jd_tag.strip()
            entered_new_tag = st.session_state.get("new_jd_tag", "").strip()
            if new_jd_tag:
                db.add_tag(new_jd_tag)
                if new_jd_tag not in jd_tag_assign:
                    jd_tag_assign.append(new_jd_tag)
                tag_options = sorted(set(db.list_tags()))
            jd_tag_assign = [t.strip() for t in jd_tag_assign if t.strip()]
            effective_jd_tags = list(jd_tag_assign)
            for tag_val in [new_jd_tag, entered_new_tag]:
                if tag_val and tag_val not in effective_jd_tags:
                    effective_jd_tags.append(tag_val)
            jd_tag_val = ",".join(effective_jd_tags) if effective_jd_tags else None

            jd_up = st.file_uploader(
                "Upload JDs (PDF/DOCX/TXT)",
                accept_multiple_files=True,
                key=f"jd_up_{st.session_state.jd_uploader_key}"
            )
            force_reparse_jd = st.checkbox("Force Reparse Existing JDs", value=False)

            if jd_up:
                has_jd_tag = bool(effective_jd_tags)
                if not st.session_state.is_uploading_jd:
                    st.button("Process New JDs", type="primary", on_click=start_jd_upload, disabled=not has_jd_tag)
                    if not has_jd_tag:
                        st.error("Please select an existing tag or create a new tag before uploading JDs.")
                else:
                    if not has_jd_tag:
                        st.error("Please select an existing tag or create a new tag before uploading JDs.")
                        st.session_state.is_uploading_jd = False
                        st.session_state.stop_upload_jd = False
                        st.rerun()
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

                            with st.spinner("Syncing to GitHub..."):
                                sync_db_if_allowed()

                    st.session_state.is_uploading_jd = False
                    st.session_state.stop_upload_jd = False
                    st.rerun()

        st.subheader("Manage JDs")
        try:
            jds = db.fetch_dataframe("SELECT id, filename, criteria, content, tags, upload_date FROM jobs")
        except Exception:
            jds = db.fetch_dataframe("SELECT id, filename, criteria, content, upload_date FROM jobs")
            jds["tags"] = None
        st.caption(f"Total Job Descriptions: {len(jds)}")

        if not jds.empty:
            st.caption("Click on a row to edit.")
            event_jd = st.dataframe(
                jds[['filename', 'tags', 'upload_date']],
                hide_index=True,
                width="stretch",
                selection_mode="single-row",
                on_select="rerun"
            )

            if len(event_jd.selection.rows) > 0:
                selected_index = event_jd.selection.rows[0]
                selected_jd_row = jds.iloc[selected_index]
                st.session_state.selected_jd_filename = selected_jd_row['filename']

            if "selected_jd_filename" in st.session_state and st.session_state.selected_jd_filename in jds['filename'].values:
                current_filename = st.session_state.selected_jd_filename
                selected_jd_row = jds[jds['filename'] == current_filename].iloc[0]

                st.divider()
                st.markdown(f"**Editing: `{selected_jd_row['filename']}`**")

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

                    with st.spinner("Syncing to GitHub..."):
                        sync_db_if_allowed()

                    st.success("Saved!")
                    time.sleep(0.5)
                    st.rerun()
                if ec2.button("Delete JD", key=f"del_jd_{jd_edit_id}", type="primary"):
                    db.execute_query("DELETE FROM matches WHERE job_id = ?", (jd_edit_id,))
                    db.execute_query("DELETE FROM jobs WHERE id = ?", (jd_edit_id,))

                    with st.spinner("Syncing to GitHub..."):
                        sync_db_if_allowed()

                    del st.session_state.selected_jd_filename
                    st.rerun()
        else:
            st.info("No Job Descriptions uploaded yet.")

    # --- RESUMES SUB-TAB ---
    with subtab_res:
        avail_jds = db.fetch_dataframe("SELECT id, filename, tags FROM jobs")
        tag_options = sorted(set(db.list_tags()))

        with st.expander("📤 Upload / Import Resumes", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.write("#### File Upload")
                create_tag_option = "➕ Create new tag…"
                selected_tags = st.multiselect(
                    "Assign Tag(s) (Optional):",
                    tag_options + [create_tag_option]
                )
                new_res_tag = ""
                if create_tag_option in selected_tags:
                    new_res_tag = st.text_input("New Tag Name", key="new_res_tag")
                    selected_tags = [t for t in selected_tags if t != create_tag_option]
                if new_res_tag.strip():
                    db.add_tag(new_res_tag.strip())
                    if new_res_tag.strip() not in selected_tags:
                        selected_tags.append(new_res_tag.strip())
                    tag_options = sorted(set(db.list_tags()))
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
                                    if tag_val:
                                        db.update_resume_tags(existing['id'], tag_val)
                                else:
                                    db.add_resume(f.name, text, analysis, tags=tag_val)
                                if tag_val:
                                    for t in [t.strip() for t in tag_val.split(",") if t.strip()]:
                                        db.add_tag(t)

                                prog_bar.progress((i + 1) / total_res)

                            if not st.session_state.stop_upload_res:
                                status.update(label="Complete!", state="complete")
                                st.session_state.res_uploader_key += 1

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

                        with st.spinner("Syncing to GitHub..."):
                            sync_db_if_allowed()

                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error importing JSON: {e}")

        st.subheader("Manage Resumes")
        try:
            ress = db.fetch_dataframe("SELECT id, filename, profile, tags, content, upload_date FROM resumes")
        except Exception:
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
            list_filter = st.multiselect("Filter List by Tag:", tag_options, key="list_tag_filter")

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

            if len(event_res.selection.rows) > 0:
                selected_index = event_res.selection.rows[0]
                selected_res_row = filtered_ress.iloc[selected_index]
                st.session_state.selected_res_filename = selected_res_row['filename']
                st.session_state.res_table_refresh_id = st.session_state.get("res_table_refresh_id", 0) + 1

            if "selected_res_filename" in st.session_state and st.session_state.selected_res_filename in ress['filename'].values:
                current_filename = st.session_state.selected_res_filename
                row = ress[ress['filename'] == current_filename].iloc[0]

                st.divider()
                st.markdown(f"**Editing: `{row['filename']}`**")

                curr_tags_str = row['tags'] if 'tags' in row and row['tags'] else ""
                curr_tags_list = [t.strip() for t in curr_tags_str.split(',')] if curr_tags_str else []

                all_opts = list(tag_options)
                for t in curr_tags_list:
                    if t not in all_opts:
                        all_opts.append(t)

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
                    st.session_state.res_table_refresh_id = st.session_state.get("res_table_refresh_id", 0) + 1

                    with st.spinner("Syncing to GitHub..."):
                        sync_db_if_allowed()

                    st.success("Saved!")
                    time.sleep(0.5)
                    st.rerun()
                if ec2.button("Delete Resume", key=f"del_res_{row['id']}", type="primary"):
                    db.execute_query("DELETE FROM matches WHERE resume_id = ?", (int(row['id']),))
                    db.execute_query("DELETE FROM resumes WHERE id = ?", (int(row['id']),))

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

    # --- DATA VERIFICATION SUB-TAB ---
    with subtab_verify:
        st.subheader("Data Verification")
        st.caption("Compare extracted text with JSON to verify accuracy.")

        verify_mode = st.radio("Verify", ["Job Description", "Resume"], horizontal=True)

        def _find_evidence(text, query, window=80):
            if not text or not query:
                return ""
            def _normalize(s):
                if not s:
                    return ""
                s = str(s)
                try:
                    s = unicodedata.normalize("NFKC", s)
                except Exception:
                    pass
                s = s.replace("\u2022", " ")
                s = re.sub(r"(?:\b\w\s+){2,}\w\b", lambda m: m.group(0).replace(" ", ""), s)
                s = s.replace("\u2010", "-").replace("\u2011", "-").replace("\u2012", "-").replace("\u2013", "-").replace("\u2014", "-")
                s = re.sub(r"(?<=\w)\s+(?=\w)", " ", s)
                s = re.sub(r"\s+", " ", s)
                s = re.sub(r"\s*-\s*", "-", s)
                s = re.sub(r"\s*,\s*", ", ", s)
                s = re.sub(r"\(\s*", "(", s)
                s = re.sub(r"\s*\)", ")", s)
                return s.lower().strip()

            norm_text = _normalize(text)
            norm_query = _normalize(query)
            idx = norm_text.find(norm_query)
            if idx == -1:
                compact_text = re.sub(r"[^a-z0-9]", "", norm_text)
                compact_query = re.sub(r"[^a-z0-9]", "", norm_query)
                idx = compact_text.find(compact_query)
                if idx == -1:
                    tokens = [t for t in re.split(r"\W+", norm_query) if len(t) > 3]
                    text_tokens = [t for t in re.split(r"\W+", norm_text) if len(t) > 3]
                    if tokens and text_tokens:
                        def _token_match(qt, tt):
                            if qt == tt:
                                return True
                            if qt.startswith(tt[:4]) or tt.startswith(qt[:4]):
                                return True
                            return False
                        matched = 0
                        for qt in tokens:
                            if any(_token_match(qt, tt) for tt in text_tokens):
                                matched += 1
                        coverage = matched / max(1, len(tokens))
                        if coverage >= 0.6:
                            return norm_query
                    return ""
                return norm_query
            start = max(0, idx - window)
            end = min(len(norm_text), idx + len(norm_query) + window)
            snippet = norm_text[start:end]
            return snippet

        def _highlight_text(text, query):
            if not text or not query:
                return text or ""
            pattern = re.escape(query)
            return re.sub(pattern, lambda m: f"<mark>{m.group(0)}</mark>", text, flags=re.IGNORECASE)

        def _rank_json_items_by_query(items, query):
            if not query:
                return []
            q = query.lower()
            results = []
            for item in items:
                if not isinstance(item, str):
                    continue
                score = 0
                if q in item.lower():
                    score += 3
                score += sum(1 for token in q.split() if token in item.lower())
                if score > 0:
                    results.append((score, item))
            return [item for score, item in sorted(results, key=lambda x: -x[0])]

        if verify_mode == "Job Description":
            jds_v = db.fetch_dataframe("SELECT id, filename, criteria, content, tags, upload_date FROM jobs")
            if jds_v.empty:
                st.info("No Job Descriptions available.")
            else:
                tag_options = ["All"] + sorted(db.list_tags())
                tag_filter = st.selectbox("Filter by Tag", tag_options, key="verify_jd_tag")
                if tag_filter != "All":
                    jds_v = jds_v[jds_v['tags'].fillna('').astype(str).apply(lambda x: tag_filter in [t.strip() for t in x.split(',')])]

                jd_choice = st.selectbox("Select JD", jds_v['filename'].tolist())
                jd_row = jds_v[jds_v['filename'] == jd_choice].iloc[0]
                jd_text = jd_row['content'] or ""
                jd_criteria_raw = jd_row['criteria'] or "{}"
                try:
                    jd_criteria = json.loads(jd_criteria_raw)
                except Exception:
                    jd_criteria = {}

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Extracted Text**")
                    st.markdown(
                        "<div style='border:1px solid #eee; padding:8px; height:400px; overflow:auto; white-space:pre-wrap;'>"
                        f"{jd_text}</div>",
                        unsafe_allow_html=True
                    )
                with c2:
                    st.markdown("**Parsed JSON**")
                    st.text_area("JD JSON", value=jd_criteria_raw, height=400, disabled=True)

                st.divider()
                st.markdown("**Evidence Check**")
                rows = []
                all_items = []
                for section in ["must_have_skills", "nice_to_have_skills", "education_requirements", "domain_knowledge", "soft_skills", "key_responsibilities"]:
                    items = jd_criteria.get(section, [])
                    if not isinstance(items, list):
                        continue
                    for item in items:
                        if isinstance(item, str):
                            all_items.append((section, item))
                            evidence = _find_evidence(jd_text, item)
                            status = "Found" if evidence else "Not Found"
                            rows.append({
                                "section": section,
                                "item": item,
                                "status": status,
                                "evidence": evidence[:200]
                            })

                if all_items:
                    item_labels = [f"{sec}: {val}" for sec, val in all_items]
                    selected_item = st.selectbox("Find JSON item in raw text", item_labels, key="jd_find_item")
                    selected_text = selected_item.split(": ", 1)[1] if ": " in selected_item else selected_item
                    evidence = _find_evidence(jd_text, selected_text)
                    if evidence:
                        st.markdown("**Evidence Snippet**")
                        st.markdown(_highlight_text(evidence, selected_text), unsafe_allow_html=True)
                    else:
                        st.warning("No exact evidence found in raw text.")

                    st.markdown("**Paste sentence to find matching JSON items**")
                    query = st.text_input("Sentence or phrase", key="jd_query")
                    if query.strip():
                        ranked = _rank_json_items_by_query([v for _, v in all_items], query.strip())
                        if ranked:
                            st.write("Closest JSON items:")
                            for item in ranked[:10]:
                                st.write(f"- {item}")
                        else:
                            st.info("No similar JSON items found.")
                if rows:
                    st.dataframe(pd.DataFrame(rows), width="stretch")
                else:
                    st.info("No criteria items found to verify.")

        else:
            ress_v = db.fetch_dataframe("SELECT id, filename, profile, content, tags, upload_date FROM resumes")
            if ress_v.empty:
                st.info("No Resumes available.")
            else:
                tag_options = ["All"] + sorted(db.list_tags())
                tag_filter = st.selectbox("Filter by Tag", tag_options, key="verify_res_tag")
                if tag_filter != "All":
                    ress_v = ress_v[ress_v['tags'].fillna('').astype(str).apply(lambda x: tag_filter in [t.strip() for t in x.split(',')])]

                res_choice = st.selectbox("Select Resume", ress_v['filename'].tolist())
                res_row = ress_v[ress_v['filename'] == res_choice].iloc[0]
                res_text = res_row['content'] or ""
                res_profile_raw = res_row['profile'] or "{}"
                try:
                    res_profile = json.loads(res_profile_raw)
                except Exception:
                    res_profile = {}

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Extracted Text**")
                    st.markdown(
                        "<div style='border:1px solid #eee; padding:8px; height:400px; overflow:auto; white-space:pre-wrap;'>"
                        f"{res_text}</div>",
                        unsafe_allow_html=True
                    )
                with c2:
                    st.markdown("**Parsed JSON**")
                    st.text_area("Resume JSON", value=res_profile_raw, height=400, disabled=True)

                st.divider()
                st.markdown("**Evidence Check**")
                rows = []
                skills = res_profile.get("extracted_skills", [])
                skill_items = [s for s in skills if isinstance(s, str)]
                if skill_items:
                    selected_skill = st.selectbox("Find skill in raw text", skill_items, key="res_find_skill")
                    evidence = _find_evidence(res_text, selected_skill)
                    if evidence:
                        st.markdown("**Evidence Snippet**")
                        st.markdown(_highlight_text(evidence, selected_skill), unsafe_allow_html=True)
                    else:
                        st.warning("No exact evidence found in raw text.")

                    st.markdown("**Paste sentence to find matching skills**")
                    query = st.text_input("Sentence or phrase", key="res_query")
                    if query.strip():
                        ranked = _rank_json_items_by_query(skill_items, query.strip())
                        if ranked:
                            st.write("Closest skills:")
                            for item in ranked[:10]:
                                st.write(f"- {item}")
                        else:
                            st.info("No similar skills found.")
                if isinstance(skills, list):
                    for item in skills:
                        if not isinstance(item, str):
                            continue
                        evidence = _find_evidence(res_text, item)
                        status = "Found" if evidence else "Not Found"
                        rows.append({
                            "section": "extracted_skills",
                            "item": item,
                            "status": status,
                            "evidence": evidence[:200]
                        })
                if rows:
                    st.dataframe(pd.DataFrame(rows), width="stretch")
                else:
                    st.info("No skills found to verify.")
