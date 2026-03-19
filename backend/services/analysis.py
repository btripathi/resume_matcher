from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import json
import re

from ai_engine import AIEngine

from .repository import Repository


@dataclass
class AnalysisService:
    repo: Repository
    llm: AIEngine

    # ── Deep-scan helper sections ──────────────────────────────────────────

    _CRITERIA_SECTIONS = [
        "must_have_skills",
        "experience",
        "education_requirements",
        "domain_knowledge",
        "nice_to_have_skills",
        "soft_skills",
        "key_responsibilities",
    ]

    @staticmethod
    def _extract_criteria_items(criteria: dict | str | None) -> list[tuple[str, str]]:
        """Parse a criteria dict (or JSON string) into (category, value) pairs."""
        if isinstance(criteria, str):
            try:
                criteria = json.loads(criteria)
            except Exception:
                criteria = {}
        if not isinstance(criteria, dict):
            return []
        items: list[tuple[str, str]] = []
        for section in AnalysisService._CRITERIA_SECTIONS:
            raw = criteria.get(section, [])
            values = raw if isinstance(raw, list) else [raw]
            for value in values:
                if isinstance(value, str) and value.strip():
                    items.append((section, value.strip()))
        return items

    @staticmethod
    def _normalize_deep_eval(raw: dict | None, category: str, value: str) -> dict:
        """Normalize a single deep-evaluation result into a canonical dict."""
        evaluation = raw if isinstance(raw, dict) else {}
        if not evaluation:
            return {
                "requirement": value,
                "category": category,
                "status": "Missing",
                "evidence": "Evaluation timed out or failed",
            }
        evaluation["category"] = evaluation.get("category") or category
        evaluation["requirement"] = evaluation.get("requirement") or value
        evaluation["status"] = evaluation.get("status") or "Missing"
        evaluation["evidence"] = evaluation.get("evidence") or "None"
        return evaluation

    # ── Bulk matching helpers (static) ─────────────────────────────────────

    @staticmethod
    def _norm_eval(raw_item, default_category: str, default_requirement: str) -> dict:
        raw = raw_item if isinstance(raw_item, dict) else {}
        status = str(raw.get("status") or "Missing")
        if status not in ("Met", "Partial", "Missing"):
            status = "Missing"
        return {
            "requirement": str(default_requirement),
            "category": str(default_category),
            "status": status,
            "evidence": str(raw.get("evidence") or "None"),
        }

    @staticmethod
    def _norm_key(category: str, requirement: str) -> tuple[str, str]:
        return (str(category or "").strip().lower(), str(requirement or "").strip().lower())

    @staticmethod
    def _norm_cat(category: str) -> str:
        return str(category or "").strip().lower().replace(" ", "_")

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        stop = {
            "the", "and", "for", "with", "from", "that", "this", "have", "has", "had",
            "are", "was", "were", "will", "can", "may", "into", "onto", "over", "under",
            "your", "their", "our", "you", "they", "them", "its", "etc", "or", "of", "to",
            "in", "on", "at", "by", "as", "is", "be", "an", "a",
        }
        toks = re.findall(r"[a-z0-9][a-z0-9+#./-]{2,}", str(text or "").lower())
        return {t for t in toks if t not in stop}

    @staticmethod
    def _row_usable_for_req(row: dict, req_category: str, req_text: str) -> bool:
        if not isinstance(row, dict):
            return False
        status = str(row.get("status") or "Missing")
        evidence = str(row.get("evidence") or "").strip()
        if status not in ("Met", "Partial", "Missing"):
            status = "Missing"
        if status == "Missing":
            return True
        if not evidence or evidence.lower() == "none":
            return False

        req_tokens = AnalysisService._tokenize(req_text)
        ev_tokens = AnalysisService._tokenize(evidence)
        if not req_tokens:
            return True
        overlap = len(req_tokens & ev_tokens)
        ratio = overlap / max(1, len(req_tokens))
        if status == "Met":
            return overlap >= 2 or ratio >= 0.22
        return overlap >= 1 or ratio >= 0.12

    # ── Bulk deep-scan orchestration ───────────────────────────────────────

    def _run_bulk_deep_scan(
        self,
        resume_content: str,
        remaining_items: list[tuple[str, str]],
        resume_from: int,
        total_reqs: int,
        deep_details: list[dict],
        deep_ai_concurrency: int,
        deep_single_prompt: bool,
        debug_bulk_log: bool,
        debug_run_id: int | None,
        job_id: int,
        resume_id: int,
        log_fn,
        progress_fn,
    ) -> list[dict]:
        """Run bulk evaluation and return ordered evaluations for *remaining_items*."""
        bulk_resolved: dict[int, dict] = {}

        def _bulk_fill_missing(missing_rel_indices: list[int], attempt_no: int) -> int:
            if not missing_rel_indices:
                return 0
            subset = [remaining_items[i] for i in missing_rel_indices]
            if callable(log_fn):
                log_fn(
                    f"Deep Scan bulk request #{attempt_no} for {len(subset)} missing requirement(s)"
                )
            raw_bulk = self.llm.evaluate_bulk_criteria(
                resume_content,
                subset,
                debug_context={
                    "run_id": int(debug_run_id) if debug_run_id is not None else "",
                    "attempt": attempt_no,
                    "job_id": int(job_id),
                    "resume_id": int(resume_id),
                    "total_requirements": int(total_reqs),
                    "subset_size": len(subset),
                    "debug_bulk_log": bool(debug_bulk_log),
                },
            )
            rows = raw_bulk if isinstance(raw_bulk, list) else []
            if callable(log_fn):
                log_fn(
                    f"Deep Scan bulk response #{attempt_no}: {len(rows)} row(s) for {len(subset)} request(s)"
                )

            assigned = 0
            by_key: dict[tuple[str, str], int] = {}
            by_id: dict[int, int] = {}
            for rel_idx in missing_rel_indices:
                cat, req = remaining_items[rel_idx]
                by_key[self._norm_key(cat, req)] = rel_idx
                by_id[rel_idx + 1] = rel_idx

            unmatched_rows: list[dict] = []
            unmatched_rel = set(missing_rel_indices)

            # ── Pass 0: strict requirement_id match ──
            for row in rows:
                if not isinstance(row, dict):
                    continue
                rel_idx = None
                try:
                    rid = int(row.get("requirement_id"))
                    rel_idx = by_id.get(rid)
                except Exception:
                    rel_idx = None
                if rel_idx is not None and rel_idx in unmatched_rel and rel_idx not in bulk_resolved:
                    cat, req = remaining_items[rel_idx]
                    if self._row_usable_for_req(row, cat, req):
                        bulk_resolved[rel_idx] = self._norm_eval(row, cat, req)
                        unmatched_rel.discard(rel_idx)
                        assigned += 1
                    else:
                        unmatched_rows.append(row if isinstance(row, dict) else {})
                else:
                    unmatched_rows.append(row if isinstance(row, dict) else {})

            # ── Pass 1: strict key match (category + requirement) ──
            still_unmatched_rows: list[dict] = []
            for row in unmatched_rows:
                row_key = self._norm_key(row.get("category"), row.get("requirement"))
                rel_idx = by_key.get(row_key)
                if rel_idx is not None and rel_idx in unmatched_rel and rel_idx not in bulk_resolved:
                    cat, req = remaining_items[rel_idx]
                    if self._row_usable_for_req(row, cat, req):
                        bulk_resolved[rel_idx] = self._norm_eval(row, cat, req)
                        unmatched_rel.discard(rel_idx)
                        assigned += 1
                    else:
                        still_unmatched_rows.append(row if isinstance(row, dict) else {})
                else:
                    still_unmatched_rows.append(row if isinstance(row, dict) else {})
            unmatched_rows = still_unmatched_rows

            # ── Pass 1.5: category + ordinal placeholder match ──
            if unmatched_rows and unmatched_rel:
                cat_positions: dict[str, list[int]] = {}
                for rel_idx in sorted(unmatched_rel):
                    cat, _ = remaining_items[rel_idx]
                    cat_positions.setdefault(self._norm_cat(cat), []).append(rel_idx)

                still_unmatched_rows = []
                for row in unmatched_rows:
                    req_raw = str(row.get("requirement") or "").strip()
                    row_cat = self._norm_cat(str(row.get("category") or ""))
                    m = re.match(r"^([a-zA-Z_ ]+?)\s+(\d+)$", req_raw)
                    mapped = False
                    if m:
                        req_cat = self._norm_cat(m.group(1))
                        ordinal = int(m.group(2))
                        target_cat = row_cat or req_cat
                        if target_cat in cat_positions and ordinal >= 1:
                            rel_list = cat_positions.get(target_cat) or []
                            if ordinal <= len(rel_list):
                                rel_idx = rel_list[ordinal - 1]
                                if rel_idx in unmatched_rel and rel_idx not in bulk_resolved:
                                    cat, req = remaining_items[rel_idx]
                                    if self._row_usable_for_req(row, cat, req):
                                        bulk_resolved[rel_idx] = self._norm_eval(row, cat, req)
                                        unmatched_rel.discard(rel_idx)
                                        assigned += 1
                                        mapped = True
                    if not mapped:
                        still_unmatched_rows.append(row)
                unmatched_rows = still_unmatched_rows

            # ── Pass 2: requirement-only unique match ──
            if unmatched_rows and unmatched_rel:
                req_to_idx: dict[str, int] = {}
                for rel_idx in list(unmatched_rel):
                    _, req = remaining_items[rel_idx]
                    req_to_idx[str(req).strip().lower()] = rel_idx
                still_unmatched_rows_2: list[dict] = []
                for row in unmatched_rows:
                    req_key = str(row.get("requirement") or "").strip().lower()
                    rel_idx = req_to_idx.get(req_key)
                    if rel_idx is not None and rel_idx in unmatched_rel and rel_idx not in bulk_resolved:
                        cat, req = remaining_items[rel_idx]
                        if self._row_usable_for_req(row, cat, req):
                            bulk_resolved[rel_idx] = self._norm_eval(row, cat, req)
                            unmatched_rel.discard(rel_idx)
                            assigned += 1
                        else:
                            still_unmatched_rows_2.append(row)
                    else:
                        still_unmatched_rows_2.append(row)
                unmatched_rows = still_unmatched_rows_2

            # NOTE: Intentionally NO positional fill here.
            return assigned

        # ── Bulk fill passes ──
        missing_rel = list(range(len(remaining_items)))
        assigned_1 = _bulk_fill_missing(missing_rel, 1)
        missing_rel = [i for i in range(len(remaining_items)) if i not in bulk_resolved]

        if missing_rel and assigned_1 > 0:
            assigned_2 = _bulk_fill_missing(missing_rel, 2)
            missing_rel = [i for i in range(len(remaining_items)) if i not in bulk_resolved]
            if callable(log_fn):
                log_fn(
                    f"Deep Scan bulk fill summary: pass1={assigned_1}, pass2={assigned_2}, remaining={len(missing_rel)}"
                )
        elif missing_rel and callable(log_fn):
            log_fn(
                "Deep Scan bulk pass #1 returned no usable rows. "
                "Skipping bulk pass #2 and falling back to per-requirement checks."
            )

        # ── Fallback: per-requirement for anything still missing ──
        fallback_logged_rel: set[int] = set()
        if deep_ai_concurrency > 1 and len(missing_rel) > 1:
            if callable(log_fn):
                log_fn(
                    f"Deep Scan fallback running concurrently with {min(deep_ai_concurrency, len(missing_rel))} worker(s)."
                )
            with ThreadPoolExecutor(max_workers=min(deep_ai_concurrency, len(missing_rel))) as pool:
                futures = {}
                for rel_idx in missing_rel:
                    idx = resume_from + rel_idx + 1
                    category, value = remaining_items[rel_idx]
                    if callable(log_fn):
                        log_fn(f"Deep Scan fallback {idx}/{total_reqs}: [{category}] {value}")
                    fut = pool.submit(self.llm.evaluate_criterion, resume_content, category, value)
                    futures[fut] = (rel_idx, idx, category, value)
                for fut in as_completed(futures):
                    rel_idx, idx, category, value = futures[fut]
                    try:
                        raw_eval = fut.result()
                    except Exception:
                        raw_eval = None
                    evaluation = self._normalize_deep_eval(raw_eval, category, value)
                    bulk_resolved[rel_idx] = evaluation
                    fallback_logged_rel.add(rel_idx)
                    if callable(log_fn):
                        status = str(evaluation.get("status") or "Missing")
                        icon = "✅" if status == "Met" else "⚠️" if status == "Partial" else "❌"
                        log_fn(f"  ↳ {icon} {status} — {evaluation.get('requirement')}")
                    if callable(progress_fn):
                        ordered_partial = []
                        for i in range(len(remaining_items)):
                            if i in bulk_resolved:
                                ordered_partial.append(bulk_resolved[i])
                        progress_fn(idx, total_reqs, deep_details + ordered_partial)
        else:
            for rel_idx in missing_rel:
                idx = resume_from + rel_idx + 1
                category, value = remaining_items[rel_idx]
                if callable(log_fn):
                    log_fn(f"Deep Scan fallback {idx}/{total_reqs}: [{category}] {value}")
                raw_eval = self.llm.evaluate_criterion(resume_content, category, value)
                evaluation = self._normalize_deep_eval(raw_eval, category, value)
                bulk_resolved[rel_idx] = evaluation
                fallback_logged_rel.add(rel_idx)
                if callable(log_fn):
                    status = str(evaluation.get("status") or "Missing")
                    icon = "✅" if status == "Met" else "⚠️" if status == "Partial" else "❌"
                    log_fn(f"  ↳ {icon} {status} — {evaluation.get('requirement')}")
                if callable(progress_fn):
                    ordered_partial = []
                    for i in range(len(remaining_items)):
                        if i in bulk_resolved:
                            ordered_partial.append(bulk_resolved[i])
                    progress_fn(idx, total_reqs, deep_details + ordered_partial)

        # ── Append in original requirement order ──
        new_details: list[dict] = []
        for rel_idx, (category, value) in enumerate(remaining_items):
            idx = resume_from + rel_idx + 1
            evaluation = bulk_resolved.get(rel_idx)
            if not evaluation:
                evaluation = {
                    "requirement": value,
                    "category": category,
                    "status": "Missing",
                    "evidence": "None",
                }
            new_details.append(evaluation)
            if callable(progress_fn):
                progress_fn(idx, total_reqs, deep_details + new_details)
            if callable(log_fn) and rel_idx not in fallback_logged_rel:
                status = str(evaluation.get("status") or "Missing")
                icon = "✅" if status == "Met" else "⚠️" if status == "Partial" else "❌"
                log_fn(f"Deep Scan {idx}/{total_reqs}: [{evaluation.get('category')}] {evaluation.get('requirement')}")
                log_fn(f"  ↳ {icon} {status} — {evaluation.get('requirement')}")
        return new_details

    # ── Per-requirement deep-scan orchestration ────────────────────────────

    def _run_per_requirement_deep_scan(
        self,
        resume_content: str,
        remaining_items: list[tuple[str, str]],
        resume_from: int,
        total_reqs: int,
        deep_details: list[dict],
        deep_ai_concurrency: int,
        log_fn,
        progress_fn,
    ) -> list[dict]:
        """Run per-requirement evaluation and return ordered evaluations for *remaining_items*."""
        new_details: list[dict] = []
        if deep_ai_concurrency > 1 and len(remaining_items) > 1:
            if callable(log_fn):
                log_fn(
                    f"Deep Scan per-requirement mode running concurrently with {min(deep_ai_concurrency, len(remaining_items))} worker(s)."
                )
            results_by_rel: dict[int, dict] = {}
            with ThreadPoolExecutor(max_workers=min(deep_ai_concurrency, len(remaining_items))) as pool:
                futures = {}
                for rel_idx, (category, value) in enumerate(remaining_items):
                    idx = resume_from + rel_idx + 1
                    if callable(log_fn):
                        log_fn(f"Deep Scan {idx}/{total_reqs}: [{category}] {value}")
                    fut = pool.submit(self.llm.evaluate_criterion, resume_content, category, value)
                    futures[fut] = (rel_idx, idx, category, value)
                for fut in as_completed(futures):
                    rel_idx, idx, category, value = futures[fut]
                    try:
                        raw_eval = fut.result()
                    except Exception:
                        raw_eval = None
                    evaluation = self._normalize_deep_eval(raw_eval, category, value)
                    results_by_rel[rel_idx] = evaluation
                    if callable(log_fn):
                        status = str(evaluation.get("status") or "Missing")
                        icon = "✅" if status == "Met" else "⚠️" if status == "Partial" else "❌"
                        log_fn(f"  ↳ {icon} {status} — {evaluation.get('requirement')}")
                    if callable(progress_fn):
                        ordered_partial = [results_by_rel[i] for i in sorted(results_by_rel.keys())]
                        progress_fn(idx, total_reqs, deep_details + ordered_partial)
            for rel_idx in range(len(remaining_items)):
                new_details.append(
                    results_by_rel.get(rel_idx)
                    or self._normalize_deep_eval(None, remaining_items[rel_idx][0], remaining_items[rel_idx][1])
                )
        else:
            for idx, (category, value) in enumerate(remaining_items, start=resume_from + 1):
                if callable(log_fn):
                    log_fn(f"Deep Scan {idx}/{total_reqs}: [{category}] {value}")
                raw_eval = self.llm.evaluate_criterion(resume_content, category, value)
                evaluation = self._normalize_deep_eval(raw_eval, category, value)
                new_details.append(evaluation)
                if callable(progress_fn):
                    progress_fn(idx, total_reqs, deep_details + new_details)
                if callable(log_fn):
                    status = str(evaluation.get("status") or "Missing")
                    icon = "✅" if status == "Met" else "⚠️" if status == "Partial" else "❌"
                    log_fn(f"  ↳ {icon} {status} — {evaluation.get('requirement')}")
        return new_details

    def ingest_job(self, filename: str, content: str, tags: list[str]) -> dict:
        criteria = self.llm.analyze_jd(content)
        if not isinstance(criteria, dict) or criteria.get("error"):
            raise RuntimeError(f"JD analysis failed: {criteria}")
        return self.repo.add_job(filename=filename, content=content, criteria=criteria, tags=tags)

    def ingest_resume(self, filename: str, content: str, tags: list[str]) -> dict:
        profile = self.llm.analyze_resume(content)
        if not isinstance(profile, dict):
            raise RuntimeError("Resume analysis failed.")
        return self.repo.add_resume(filename=filename, content=content, profile=profile, tags=tags)

    def score_match(
        self,
        job_id: int,
        resume_id: int,
        threshold: int = 50,
        auto_deep: bool = False,
        run_name: str | None = None,
        legacy_run_id: int | None = None,
        force_rerun_pass1: bool = False,
        force_rerun_deep: bool = False,
        max_deep_scans_per_jd: int = 0,
        deep_single_prompt: bool = False,
        ai_concurrency: int = 1,
        debug_bulk_log: bool = False,
        log_fn=None,
        deep_resume_from: int = 0,
        deep_partial_details: list[dict] | None = None,
        progress_fn=None,
        debug_run_id: int | None = None,
    ) -> dict:
        job = self.repo.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        resume = self.repo.get_resume(resume_id)
        if not resume:
            raise ValueError(f"Resume {resume_id} not found.")

        existing = self.repo.get_existing_match(job_id, resume_id)
        existing_match_id = int(existing["id"]) if existing else None
        force_any = bool(force_rerun_pass1 or force_rerun_deep)
        wants_deep = bool(auto_deep or force_rerun_deep)
        existing_strategy = str((existing or {}).get("strategy") or "")
        if existing and not force_any:
            existing_strategy = str(existing.get("strategy") or "Standard")
            can_reuse = (not wants_deep) or (wants_deep and existing_strategy == "Deep")
            if can_reuse:
                row = self.repo.get_match(existing_match_id)
                if row:
                    # Even on cache reuse, link the match into the requested legacy run context.
                    if legacy_run_id:
                        self.repo.link_run_match(run_id=int(legacy_run_id), match_id=int(row["id"]))
                    elif run_name:
                        run_id = self.repo.create_run(run_name=run_name, threshold=threshold)
                        self.repo.link_run_match(run_id=run_id, match_id=int(row["id"]))
                    return row

        standard = None
        if existing and wants_deep and (not force_rerun_pass1) and existing_strategy == "Standard":
            # In deep-cap second-wave reruns, reuse cached Pass 1 output and only run Deep Scan.
            standard = {
                "candidate_name": str(existing.get("candidate_name") or (resume or {}).get("filename") or "Unknown Candidate"),
                "match_score": int(existing.get("standard_score") if existing.get("standard_score") is not None else existing.get("match_score") or 0),
                "decision": str(existing.get("decision") or "Review"),
                "reasoning": str(existing.get("standard_reasoning") or existing.get("reasoning") or ""),
                "missing_skills": [],
            }
            if callable(log_fn):
                log_fn("Pass 1 reused from existing Standard match (force_rerun_pass1=false).")
        else:
            standard = self.llm.evaluate_standard(resume["content"], job["criteria"], resume["profile"])
            if not isinstance(standard, dict):
                if callable(log_fn):
                    log_fn("Standard evaluation failed or malformed; using fallback standard result.")
                standard = {
                    "candidate_name": str((resume or {}).get("filename") or "Unknown Candidate"),
                    "match_score": 0,
                    "decision": "Review",
                    "reasoning": "Standard evaluation failed; fallback result applied.",
                    "missing_skills": [],
                }

        def _preferred_candidate_name() -> str:
            profile = resume.get("profile")
            parsed = {}
            if isinstance(profile, dict):
                parsed = profile
            elif isinstance(profile, str):
                try:
                    parsed = json.loads(profile)
                except Exception:
                    parsed = {}
            name = str(parsed.get("candidate_name", "") or "").strip() if isinstance(parsed, dict) else ""
            if name:
                return name
            name = str(standard.get("candidate_name", "") or "").strip()
            if name:
                return name
            return str(resume.get("filename", "") or "").strip()

        candidate_name = _preferred_candidate_name()
        standard["candidate_name"] = candidate_name

        raw_reasoning = standard.get("reasoning", "")
        standard_reasoning = "\n".join(raw_reasoning) if isinstance(raw_reasoning, list) else str(raw_reasoning)
        standard_score = int(standard.get("match_score", 0) or 0)
        if callable(log_fn):
            log_fn(f"Pass 1 (Standard) score={standard_score}%, threshold={threshold}%")

        strategy = "Standard"
        result = standard

        existing_deep_row = None
        if existing_match_id and existing_strategy == "Deep":
            existing_deep_row = self.repo.get_match(existing_match_id)

        # If deep rerun is not explicitly forced, reuse previously computed deep output.
        # This preserves deep evidence and avoids expensive deep recomputation.
        if wants_deep and not force_rerun_deep and existing_deep_row:
            strategy = "Deep"
            result = {
                "candidate_name": str(existing_deep_row.get("candidate_name") or candidate_name),
                "match_score": int(existing_deep_row.get("match_score") or 0),
                "decision": str(existing_deep_row.get("decision") or ""),
                "reasoning": str(existing_deep_row.get("reasoning") or ""),
                "missing_skills": standard.get("missing_skills", []),
                "match_details": list(existing_deep_row.get("match_details") or []),
            }
            if callable(log_fn):
                log_fn(
                    "Deep Scan reused from existing deep result (force_rerun_deep=false). "
                    "Pass 1 was updated without rerunning deep."
                )
            should_run_deep = False
        else:
            should_run_deep = (auto_deep and standard_score >= threshold) or force_rerun_deep

        # Optional per-JD deep-scan cap scoped to current legacy run batch.
        # 0 means unlimited.
        deep_cap = max(0, int(max_deep_scans_per_jd or 0))
        if should_run_deep and deep_cap > 0 and legacy_run_id:
            deep_used = self.repo.count_legacy_run_deep_matches_for_job(run_id=int(legacy_run_id), job_id=int(job_id))
            if deep_used >= deep_cap:
                should_run_deep = False
                if callable(log_fn):
                    log_fn(
                        f"Deep Scan skipped: reached max deep scans for JD in this batch "
                        f"({deep_used}/{deep_cap})."
                    )
        if should_run_deep:
            strategy = "Deep"
            deep_details = list(deep_partial_details or [])
            deep_ai_concurrency = max(1, int(ai_concurrency or 1))
            if callable(log_fn):
                mode_text = "single prompt" if deep_single_prompt else "per requirement"
                log_fn(f"Starting Deep Scan requirement checks ({mode_text}, concurrency={deep_ai_concurrency})")

            criteria_items = self._extract_criteria_items(job.get("criteria"))

            total_reqs = len(criteria_items)
            resume_from = max(0, min(int(deep_resume_from or 0), total_reqs))
            if callable(log_fn):
                if total_reqs:
                    log_fn(f"Deep Scan requirements: {total_reqs}")
                    if resume_from > 0:
                        log_fn(f"Resuming Deep Scan from requirement {resume_from + 1}/{total_reqs}")
                else:
                    log_fn("Deep Scan requirements: 0 (no criteria items found)")

            if resume_from > 0 and len(deep_details) > resume_from:
                deep_details = deep_details[:resume_from]

            remaining_items = criteria_items[resume_from:]

            if deep_single_prompt and remaining_items:
                new_details = self._run_bulk_deep_scan(
                    resume_content=resume["content"],
                    remaining_items=remaining_items,
                    resume_from=resume_from,
                    total_reqs=total_reqs,
                    deep_details=deep_details,
                    deep_ai_concurrency=deep_ai_concurrency,
                    deep_single_prompt=deep_single_prompt,
                    debug_bulk_log=debug_bulk_log,
                    debug_run_id=debug_run_id,
                    job_id=job_id,
                    resume_id=resume_id,
                    log_fn=log_fn,
                    progress_fn=progress_fn,
                )
            else:
                new_details = self._run_per_requirement_deep_scan(
                    resume_content=resume["content"],
                    remaining_items=remaining_items,
                    resume_from=resume_from,
                    total_reqs=total_reqs,
                    deep_details=deep_details,
                    deep_ai_concurrency=deep_ai_concurrency,
                    log_fn=log_fn,
                    progress_fn=progress_fn,
                )
            deep_details.extend(new_details)

            final_score, final_decision, final_reasoning = self.llm.generate_final_decision(
                candidate_name, deep_details, strategy="Deep"
            )
            if callable(log_fn):
                log_fn(f"Deep Scan complete: score={final_score}%, decision={final_decision}")
            result = {
                "candidate_name": candidate_name,
                "match_score": final_score,
                "decision": final_decision,
                "reasoning": final_reasoning,
                "missing_skills": standard.get("missing_skills", []),
                "match_details": deep_details,
            }
        elif callable(log_fn) and auto_deep:
            log_fn(
                f"Deep Scan skipped: standard score {standard_score}% is below threshold {threshold}%."
            )
        elif callable(log_fn):
            log_fn(
                f"Deep Scan not requested: auto_deep={auto_deep}, force_rerun_deep={force_rerun_deep}. "
                f"Standard score {standard_score}% (threshold {threshold}%)."
            )

        match_id = self.repo.save_match(
            job_id=job_id,
            resume_id=resume_id,
            result=result,
            match_id=existing_match_id,
            strategy=strategy,
            standard_score=standard_score,
            standard_reasoning=standard_reasoning,
        )

        if legacy_run_id:
            self.repo.link_run_match(run_id=int(legacy_run_id), match_id=match_id)
        elif run_name:
            run_id = self.repo.create_run(run_name=run_name, threshold=threshold)
            self.repo.link_run_match(run_id=run_id, match_id=match_id)

        match_row = self.repo.get_match(match_id)
        if not match_row:
            raise RuntimeError(f"Match {match_id} was not persisted.")
        return match_row
