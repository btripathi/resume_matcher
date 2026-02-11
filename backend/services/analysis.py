from dataclasses import dataclass

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
    ) -> dict:
        job = self.repo.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        resume = self.repo.get_resume(resume_id)
        if not resume:
            raise ValueError(f"Resume {resume_id} not found.")

        existing = self.repo.get_existing_match(job_id, resume_id)
        existing_match_id = int(existing["id"]) if existing else None
        if existing and not force_rerun_pass1:
            if not auto_deep:
                row = self.repo.get_match(existing_match_id)
                if row:
                    return row
            if auto_deep and existing.get("strategy") == "Deep" and not force_rerun_deep:
                row = self.repo.get_match(existing_match_id)
                if row:
                    return row

        standard = self.llm.evaluate_standard(resume["content"], job["criteria"], resume["profile"])
        if not isinstance(standard, dict):
            raise RuntimeError("Standard evaluation failed.")

        raw_reasoning = standard.get("reasoning", "")
        standard_reasoning = "\n".join(raw_reasoning) if isinstance(raw_reasoning, list) else str(raw_reasoning)
        standard_score = int(standard.get("match_score", 0) or 0)

        strategy = "Standard"
        result = standard

        if auto_deep and standard_score >= threshold:
            strategy = "Deep"
            deep_details = []
            # MVP deep path: evaluate must-have skills as atomic criteria.
            # This provides a backend-compatible result while we decouple the full Streamlit deep flow.
            criteria = job.get("criteria") or {}
            if isinstance(criteria, str):
                import json

                criteria = json.loads(criteria)
            must_have = criteria.get("must_have_skills", []) if isinstance(criteria, dict) else []
            for skill in must_have:
                evaluation = self.llm.evaluate_criterion(resume["content"], "must_have_skills", skill)
                if evaluation:
                    deep_details.append(evaluation)

            final_score, final_decision, final_reasoning = self.llm.generate_final_decision(
                resume["filename"], deep_details, strategy="Deep"
            )
            result = {
                "candidate_name": resume["filename"],
                "match_score": final_score,
                "decision": final_decision,
                "reasoning": final_reasoning,
                "missing_skills": standard.get("missing_skills", []),
                "match_details": deep_details,
            }

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
