from dataclasses import dataclass
import json

from ai_engine import AIEngine

from .repository import Repository


@dataclass
class AnalysisService:
    repo: Repository
    llm: AIEngine

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
        force_rerun_pass1: bool = False,
        force_rerun_deep: bool = False,
        log_fn=None,
        deep_resume_from: int = 0,
        deep_partial_details: list[dict] | None = None,
        progress_fn=None,
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
        if existing and not force_any:
            existing_strategy = str(existing.get("strategy") or "Standard")
            can_reuse = (not wants_deep) or (wants_deep and existing_strategy == "Deep")
            if can_reuse:
                row = self.repo.get_match(existing_match_id)
                if row:
                    return row

        standard = self.llm.evaluate_standard(resume["content"], job["criteria"], resume["profile"])
        if not isinstance(standard, dict):
            raise RuntimeError("Standard evaluation failed.")

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

        should_run_deep = (auto_deep and standard_score >= threshold) or force_rerun_deep
        if should_run_deep:
            strategy = "Deep"
            deep_details = list(deep_partial_details or [])
            if callable(log_fn):
                log_fn("Starting Deep Scan requirement checks")
            criteria = job.get("criteria") or {}
            if isinstance(criteria, str):
                import json

                try:
                    criteria = json.loads(criteria)
                except Exception:
                    criteria = {}

            criteria_items: list[tuple[str, str]] = []
            if isinstance(criteria, dict):
                sections = [
                    "must_have_skills",
                    "experience",
                    "education_requirements",
                    "domain_knowledge",
                    "nice_to_have_skills",
                    "soft_skills",
                    "key_responsibilities",
                ]
                for section in sections:
                    raw = criteria.get(section, [])
                    values = raw if isinstance(raw, list) else [raw]
                    for value in values:
                        if isinstance(value, str) and value.strip():
                            criteria_items.append((section, value.strip()))

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

            for idx, (category, value) in enumerate(criteria_items[resume_from:], start=resume_from + 1):
                if callable(log_fn):
                    log_fn(f"Deep Scan {idx}/{total_reqs}: [{category}] {value}")
                evaluation = self.llm.evaluate_criterion(resume["content"], category, value)
                if not isinstance(evaluation, dict):
                    evaluation = {
                        "requirement": value,
                        "category": category,
                        "status": "Missing",
                        "evidence": "Evaluation timed out or failed",
                    }
                else:
                    evaluation["category"] = evaluation.get("category") or category
                    evaluation["requirement"] = evaluation.get("requirement") or value
                    evaluation["status"] = evaluation.get("status") or "Missing"
                    evaluation["evidence"] = evaluation.get("evidence") or "None"
                deep_details.append(evaluation)
                if callable(progress_fn):
                    progress_fn(idx, total_reqs, deep_details)

                if callable(log_fn):
                    status = str(evaluation.get("status") or "Missing")
                    icon = "✅" if status == "Met" else "⚠️" if status == "Partial" else "❌"
                    log_fn(f"  ↳ {icon} {status} — {evaluation.get('requirement')}")

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

        if run_name:
            run_id = self.repo.create_run(run_name=run_name, threshold=threshold)
            self.repo.link_run_match(run_id=run_id, match_id=match_id)

        match_row = self.repo.get_match(match_id)
        if not match_row:
            raise RuntimeError(f"Match {match_id} was not persisted.")
        return match_row
