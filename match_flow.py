import datetime
import json
import streamlit as st


def init_log_ui(height=300, full_width=False, placeholder=None):
    log_lines = []
    log_placeholder = placeholder or st.empty()

    def add_log(message):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        log_lines.append(f"<div style='margin-bottom:2px;'><span style='color:#888; font-size:0.8em;'>[{ts}]</span> {message}</div>")
        html_content = (
            f"<div style='width:100%; height:{height}px; overflow-y:auto; background-color:#f8f9fa; border:1px solid #dee2e6; "
            f"padding:10px; border-radius:4px; font-family:monospace; font-size:0.9em; color:#212529;'>"
            f"{''.join(log_lines)}</div>"
        )
        if full_width:
            log_placeholder.markdown(f"<div style='width:100%;'>{html_content}</div>", unsafe_allow_html=True)
        else:
            log_placeholder.markdown(html_content, unsafe_allow_html=True)

    return add_log


def process_match_flow(job, res, db, client, deep_match_thresh, auto_deep, force_rerun_pass1, force_rerun_deep, deep_only, add_log, task_display=None, sub_bar=None, safe_int_fn=None):
    current_resume_name = res['filename']
    mid = None
    exist = db.get_match_if_exists(int(job['id']), int(res['id']))
    if exist:
        mid = exist['id']

    # --- PARSING ERROR CHECK ---
    try:
        profile_dict = json.loads(res['profile'])
    except Exception:
        profile_dict = {}

    if profile_dict.get('error_flag') or profile_dict.get('candidate_name') == "Parsing Error":
        add_log(f"&nbsp;&nbsp;⚠️ Resume Parsing Error. Marking as Failed.")
        data = {
            "candidate_name": f"Error: {res['filename']}",
            "match_score": 0,
            "decision": "Parsing Error",
            "reasoning": "The resume text could not be extracted or parsed correctly (e.g. Scanned PDF or corrupt file).",
            "missing_skills": ["Unreadable Resume Content"],
        }
        mid = db.save_match(int(job['id']), int(res['id']), data, mid, strategy="Standard", standard_score=0, standard_reasoning="Parsing Failed")
        return mid

    previous_failure = exist and (exist.get('decision') in ["Parsing Error", "Error"] or str(exist.get('match_score')) == "0")

    should_run_standard = (not exist) or force_rerun_pass1 or previous_failure
    if deep_only:
        should_run_standard = not (exist and exist.get('standard_score'))

    score = 0
    if should_run_standard:
        msg_prefix = "🧠 Pass 1"
        if previous_failure:
            msg_prefix = "🔄 Retry (Prev Failed)"
        if task_display:
            task_display.info(f"{msg_prefix}: Holistic scan for **{current_resume_name}**...")
        add_log(f"&nbsp;&nbsp;{msg_prefix}: evaluating standard match")
        data = client.evaluate_standard(res['content'], job['criteria'], res['profile'])
        if data and isinstance(data, dict):
            raw_reasoning = data.get('reasoning', "No reasoning provided.")
            std_reasoning = "\n".join(raw_reasoning) if isinstance(raw_reasoning, list) else str(raw_reasoning)
            mid = db.save_match(int(job['id']), int(res['id']), data, mid, strategy="Standard", standard_score=data['match_score'], standard_reasoning=std_reasoning)
            score = data['match_score']
            exist = db.get_match_if_exists(int(job['id']), int(res['id']))
            add_log(f"&nbsp;&nbsp;✅ Standard Score: {score}%")
        else:
            add_log(f"&nbsp;&nbsp;❌ Analysis failed or returned invalid format for {current_resume_name}.")
            err_data = {
                "candidate_name": f"Error: {res['filename']}",
                "match_score": 0,
                "decision": "Error",
                "reasoning": "LLM Analysis failed or returned malformed data.",
                "missing_skills": [],
            }
            mid = db.save_match(int(job['id']), int(res['id']), err_data, mid, strategy="Standard", standard_score=0, standard_reasoning="LLM Analysis Failed")
            return mid
    else:
        if exist.get('strategy') == 'Deep' and exist.get('standard_score') is not None:
            score = safe_int_fn(exist['standard_score'], 0) if safe_int_fn else int(exist['standard_score'])
            add_log(f"&nbsp;&nbsp;ℹ️ Using existing Standard Score: {score}% (Pass 1 Skipped)")
        else:
            score = safe_int_fn(exist['match_score'], 0) if safe_int_fn else int(exist['match_score'])
            add_log(f"&nbsp;&nbsp;ℹ️ Using existing Match Score: {score}% (Pass 1 Skipped)")

    is_already_deep = exist and exist['strategy'] == 'Deep'
    qualifies_for_deep = (safe_int_fn(score, 0) if safe_int_fn else score) >= (safe_int_fn(deep_match_thresh, 0) if safe_int_fn else deep_match_thresh)

    if auto_deep and qualifies_for_deep:
        if is_already_deep and not force_rerun_pass1 and not previous_failure and not force_rerun_deep:
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
            for k in ['nice_to_have_skills', 'soft_skills', 'education_requirements']:
                if k in jd_c and isinstance(jd_c[k], list):
                    bulk_reqs.extend([(k, v) for v in jd_c[k]])

            details = []
            expected = []
            for rt, rv in priority_reqs:
                expected.append((rt, str(rv)))
            for rt, rv in bulk_reqs:
                expected.append((rt, str(rv)))
            total_criteria = len(expected)
            processed_count = 0

            for rt, rv in priority_reqs:
                if st.session_state.stop_requested:
                    break
                processed_count += 1
                add_log(f"&nbsp;&nbsp;&nbsp;&nbsp;🔎 Checking {rt.replace('_', ' ').title()}: <i>{str(rv)[:60]}...</i>")
                if task_display:
                    task_display.warning(f"🔬 Deep Scan: {processed_count}/{total_criteria} criteria checked (Priority)...")
                if sub_bar and total_criteria > 0:
                    sub_bar.progress(processed_count / total_criteria)
                res_crit = client.evaluate_criterion(res['content'], rt, rv)
                if res_crit:
                    details.append(res_crit)
                    icon = "✅" if res_crit['status'] == 'Met' else "⚠️" if res_crit['status'] == 'Partial' else "❌"
                    add_log(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↳ {icon} {res_crit['status']} — {rv}")

            if st.session_state.stop_requested:
                return mid

            if bulk_reqs:
                if task_display:
                    task_display.info(f"⚡ Bulk Scan: Checking {len(bulk_reqs)} secondary criteria... ({processed_count}/{total_criteria})")
                add_log(f"&nbsp;&nbsp;&nbsp;&nbsp;⚡ Bulk checking {len(bulk_reqs)} secondary items...")
                if sub_bar and total_criteria > 0:
                    sub_bar.progress(processed_count / total_criteria)
                bulk_results = client.evaluate_bulk_criteria(res['content'], bulk_reqs)
                if bulk_results:
                    details.extend(bulk_results)
                    for br in bulk_results:
                        if isinstance(br, dict):
                            add_log(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↳ {br.get('status','n/a')} — {br.get('requirement','')}")
                processed_count += len(bulk_reqs)
                if sub_bar and total_criteria > 0:
                    sub_bar.progress(min(1.0, processed_count / total_criteria))

            # Ensure deterministic criteria list per JD: backfill missing items
            def _norm(s):
                return " ".join(str(s).strip().lower().split())

            def _rank(status):
                if status == "Met":
                    return 2
                if status == "Partial":
                    return 1
                return 0

            by_req = {}
            for d in details:
                if not isinstance(d, dict):
                    continue
                req = d.get("requirement") or d.get("criteria") or ""
                if not req:
                    continue
                key = _norm(req)
                cur = by_req.get(key)
                if not cur or _rank(d.get("status", "Missing")) > _rank(cur.get("status", "Missing")):
                    by_req[key] = d

            normalized_expected = []
            for cat, req in expected:
                normalized_expected.append((_norm(req), cat, req))

            deterministic = []
            for nreq, cat, req in normalized_expected:
                found = by_req.get(nreq)
                if found:
                    deterministic.append({
                        "category": cat,
                        "requirement": req,
                        "status": found.get("status", "Missing"),
                        "evidence": found.get("evidence", "")
                    })
                else:
                    deterministic.append({
                        "category": cat,
                        "requirement": req,
                        "status": "Missing",
                        "evidence": ""
                    })

            details = deterministic

            if sub_bar:
                sub_bar.empty()
            if not details:
                add_log("&nbsp;&nbsp;⚠️ Deep scan returned no evaluated criteria. Keeping Pass 1 results.")
                return mid

            sf, df, rf = client.generate_final_decision(res['filename'], details, strategy="Deep")
            std_score_saved = exist.get('standard_score', score)
            std_reasoning_saved = exist.get('standard_reasoning', exist.get('reasoning'))
            mid = db.save_match(int(job['id']), int(res['id']), {
                "candidate_name": res['filename'],
                "match_score": sf,
                "decision": df,
                "reasoning": rf,
                "match_details": details
            }, mid, strategy="Deep", standard_score=std_score_saved, standard_reasoning=std_reasoning_saved)
            add_log(f"&nbsp;&nbsp;🏁 Deep Match Final: {sf}% ({df})")
    elif auto_deep and not qualifies_for_deep:
        add_log(f"&nbsp;&nbsp;⏭️ Score ({score}%) below threshold ({deep_match_thresh}%). Skipping Deep Match.")

    return mid
