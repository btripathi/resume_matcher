import importlib
import importlib.util
import json
import re
import os
import time
from pathlib import Path

class AIEngine:
    def __init__(
        self,
        base_url,
        api_key,
        request_timeout_sec=None,
        bulk_timeout_sec=None,
        bulk_resume_chars=None,
        preferred_model=None,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.use_mock = base_url.startswith("mock://")
        self.request_timeout_sec = int(
            request_timeout_sec
            if request_timeout_sec is not None
            else (os.getenv("RESUME_MATCHER_LLM_TIMEOUT_SEC", "600") or 600)
        )
        self.bulk_timeout_sec = int(
            bulk_timeout_sec
            if bulk_timeout_sec is not None
            else (os.getenv("RESUME_MATCHER_LLM_BULK_TIMEOUT_SEC", "600") or 600)
        )
        self.bulk_resume_chars = int(
            bulk_resume_chars
            if bulk_resume_chars is not None
            else (os.getenv("RESUME_MATCHER_LLM_BULK_RESUME_CHARS", "10000") or 10000)
        )
        self.preferred_model = str(
            preferred_model
            if preferred_model is not None
            else (os.getenv("RESUME_MATCHER_LM_MODEL", "") or "")
        ).strip()
        self.debug_bulk_log = str(os.getenv("RESUME_MATCHER_DEBUG_BULK_LOG", "")).strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        self._resolved_chat_model = None

        if not self.use_mock:
            if importlib.util.find_spec("openai") is None:
                raise RuntimeError(
                    "openai is not installed. Install it or use base_url='mock://local' for the mock API."
                )
            openai_module = importlib.import_module("openai")
            self.client = openai_module.OpenAI(base_url=base_url, api_key=api_key)

    def _chat_model(self):
        if self.use_mock:
            return "local-model"
        if self.preferred_model:
            return self.preferred_model
        if self._resolved_chat_model:
            return self._resolved_chat_model

        try:
            models = self.client.models.list()
            data = list(getattr(models, "data", []) or [])
            ids = [str(getattr(m, "id", "") or "").strip() for m in data]
            ids = [m for m in ids if m]
            non_embedding = [m for m in ids if "embed" not in m.lower()]
            ranked = non_embedding or ids
            preferred = [
                "qwen2.5-7b-instruct",
                "qwen2.5-3b-instruct",
                "gpt",
                "llama",
                "instruct",
                "chat",
            ]
            for token in preferred:
                hit = next((m for m in ranked if token in m.lower()), None)
                if hit:
                    self._resolved_chat_model = hit
                    return hit
            if ranked:
                self._resolved_chat_model = ranked[0]
                return ranked[0]
        except Exception:
            pass

        # Last fallback for OpenAI-compatible local gateways.
        return "local-model"

    def analyze_jd(self, text):
        if self.use_mock:
            return self._normalize_jd_schema(self._mock_analyze_jd(text), text)
        document_utils = self._document_utils()
        prompt = f"""
        You are a high-precision Technical Recruiter. Analyze the provided Job Description text.

        STRICT RULES:
        1. GROUNDING: Extract ONLY what is explicitly written.
        2. CATEGORIZATION:
           - 'must_have_skills': Only explicit technical requirements.
           - 'nice_to_have_skills': Only items listed as 'Plus', 'Bonus', or 'Preferred'.
        3. FORMAT: Output valid JSON with DOUBLE QUOTES.

        JSON Format:
        {{
            "role_title": "Full title",
            "must_have_skills": [],
            "nice_to_have_skills": [],
            "min_years_experience": integer,
            "education_requirements": [],
            "domain_knowledge": [],
            "soft_skills": [],
            "key_responsibilities": []
        }}
        JD TEXT:
        {text[:15000]}
        """
        try:
            resp = self.client.chat.completions.create(
                model=self._chat_model(),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                timeout=self.request_timeout_sec,
            )
            raw = document_utils.clean_json_response(resp.choices[0].message.content)
            return self._normalize_jd_schema(raw, text)
        except Exception as e:
            return {"error": str(e)}

    def analyze_resume(self, text):
        """
        Extracts structured profile from Resume.
        Enforces strict JSON formatting (Double Quotes).
        """
        if self.use_mock:
            return self._mock_analyze_resume(text)
        document_utils = self._document_utils()
        # --- SAFETY GUARD ---
        # Prevent hallucination (John Doe) if OCR failed or text is empty
        if not text or len(text.strip()) < 50 or text.startswith("[OCR Error") or text.startswith("Error"):
            return {
                "candidate_name": "Error: Unreadable Resume",
                "email": "",
                "phone": "",
                "extracted_skills": [],
                "years_experience": 0,
                "education_summary": "Could not extract text. PDF might be an image without OCR support.",
                "work_history": [],
                "error_flag": True
            }

        system_prompt = """
        You are an expert Technical Recruiter.
        Task: Parse the resume text into a structured JSON profile.
        Output: Return ONLY valid JSON. Use DOUBLE QUOTES for all keys and strings.
        """

        user_prompt = f"""
        INSTRUCTIONS:
        1. Extract candidate_name, email, phone.
        2. "extracted_skills": List ALL technical skills, tools, languages.
        3. "work_history": List previous roles. IMPORTANT: Summarize duties concisely (max 3 sentences per role) to save space.
        4. "years_experience": Estimate total years of professional experience.
        5. "domain_experience": List specific industries (e.g. Fintech, Healthcare, AI).

        JSON Structure:
        {{
            "candidate_name": "Name",
            "email": "Email",
            "phone": "Phone",
            "extracted_skills": ["Skill A", "Skill B"],
            "years_experience": 10,
            "education_summary": "Degree, University",
            "domain_experience": ["Domain A", "Domain B"],
            "work_history": [
                {{ "company": "Company A", "role": "Title", "summary": "Concise summary of work" }}
            ]
        }}

        RESUME CONTENT:
        {text[:15000]}
        """
        try:
            resp = self.client.chat.completions.create(
                model=self._chat_model(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                max_tokens=1500,  # Strict limit to prevent infinite generation
                timeout=self.request_timeout_sec,
            )
            # If null, return a fallback object to prevent app crash
            raw_content = resp.choices[0].message.content
            result = document_utils.clean_json_response(raw_content)
            if not result:
                 self._log_parse_failure(raw_content, reason="clean_json_response returned None")
                 return {
                    "candidate_name": "Parsing Error",
                    "extracted_skills": [],
                    "years_experience": 0,
                    "error_flag": True
                }
            # Post-process to ground years_experience and enrich skills from explicit text
            try:
                lowered = text.lower()
                # Extract explicit years statements
                yrs = [int(m.group(1)) for m in re.finditer(r"\b(\d{1,2})\s+years?\b", lowered)]
                # Handle "X years ... alongside Y years" style
                alongside = re.search(r"\b(\d{1,2})\s+years?\b.*\balongside\b.*\b(\d{1,2})\s+years?\b", lowered)
                explicit_years = None
                if alongside:
                    explicit_years = int(alongside.group(1)) + int(alongside.group(2))
                elif yrs:
                    explicit_years = max(yrs)

                if explicit_years is not None:
                    # Use explicit years from text when available
                    result["years_experience"] = explicit_years

                # Enrich extracted_skills with explicit HR/ops keywords found in text
                skill_keywords = [
                    "payroll", "compensation", "benefits", "hr policies", "employee relations",
                    "people operations", "onboarding", "offboarding", "attendance", "leave management",
                    "performance management", "confidential", "compliance", "statutory compliance"
                ]
                found = []
                for kw in skill_keywords:
                    if kw in lowered:
                        found.append(kw.title() if kw.islower() else kw)
                existing = result.get("extracted_skills") or []
                if isinstance(existing, str):
                    existing = [existing]
                merged = list(dict.fromkeys([*existing, *found]))
                result["extracted_skills"] = merged
            except Exception:
                pass
            return result
        except Exception as e:
            self._log_parse_failure(f"[EXCEPTION] {e}", reason="exception during analyze_resume")
            return {"candidate_name": "Error", "error_flag": True}

    def _log_parse_failure(self, raw_content, reason="unknown"):
        try:
            log_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "ai_parse_errors.log")
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] PARSE_FAILURE reason={reason}\n")
                f.write("----- RAW START -----\n")
                f.write(str(raw_content))
                f.write("\n----- RAW END -----\n\n")
        except Exception:
            pass

    def evaluate_standard(self, resume_text, jd_criteria, resume_profile):
        if self.use_mock:
            return self._mock_evaluate_standard(resume_text, jd_criteria)
        document_utils = self._document_utils()
        system_prompt = """
        You are a very strict Technical Recruiter. Your job is to filter out candidates who do not strongly match the requirements.

        STRICT SCORING RULES (0-100):
        1. CRITICAL: If the candidate lacks "Must Have" skills, the score MUST be below 50.
        2. EXPERIENCE: If the candidate has significantly fewer years of experience than required, deduct 20 points immediately.
        3. DEPTH: Mentioning a keyword is not enough. Look for evidence of usage in Work History.

        SCORING TIERS:
        - 0-59: Reject. Missing key skills or experience.
        - 60-79: Review. Has most skills, but maybe lacks depth or specific domain knowledge.
        - 80-100: Strong Match. Exceeds requirements.

        OUTPUT RULES:
        - Return ONLY a single JSON object.
        - Do NOT include explanations, markdown, or multiple JSON blocks.
        - Do NOT include <think>...</think> reasoning blocks.
        - Do NOT include chain-of-thought.
        - Use double quotes for all keys and strings.

        NORMALIZATION RULES:
        - Degree equivalence: B.Tech/BTech/B.E./BE/B.S./BS/B.Sc counts as Bachelor's. M.Tech/MTech/M.E./ME/M.S./MS/M.Sc counts as Master's.
        - Cloud platforms: AWS, Azure, GCP, Google Cloud count as cloud platform experience.

        Return JSON: {candidate_name, match_score, decision, reasoning, missing_skills}
        """
        jd_str = jd_criteria if isinstance(jd_criteria, str) else json.dumps(jd_criteria, indent=2)
        profile_str = resume_profile if isinstance(resume_profile, str) else json.dumps(resume_profile, indent=2)
        max_total = 12000
        max_jd = 3500
        max_profile = 3500
        max_resume = 4000
        jd_str = jd_str[:max_jd]
        profile_str = profile_str[:max_profile]
        resume_str = resume_text[:max_resume] if isinstance(resume_text, str) else str(resume_text)[:max_resume]
        user_prompt = f"JD CRITERIA:\n{jd_str}\n\nRESUME PROFILE:\n{profile_str}\n\nRESUME TEXT:\n{resume_str}"
        if len(user_prompt) > max_total:
            overflow = len(user_prompt) - max_total
            if len(resume_str) > overflow:
                resume_str = resume_str[:max_resume - overflow]
            user_prompt = f"JD CRITERIA:\n{jd_str}\n\nRESUME PROFILE:\n{profile_str}\n\nRESUME TEXT:\n{resume_str}"
        def _fallback(reason: str) -> dict:
            name = "Unknown Candidate"
            try:
                parsed = resume_profile if isinstance(resume_profile, dict) else json.loads(str(resume_profile or "{}"))
                if isinstance(parsed, dict):
                    profile_name = str(parsed.get("candidate_name") or "").strip()
                    if profile_name:
                        name = profile_name
            except Exception:
                pass
            return {
                "candidate_name": name,
                "match_score": 0,
                "decision": "Review",
                "reasoning": f"Standard evaluation fallback used ({reason}).",
                "missing_skills": [],
            }

        def _normalize(data):
            if not isinstance(data, dict):
                return None
            try:
                score = int(data.get("match_score", 0) or 0)
            except Exception:
                score = 0
            score = max(0, min(100, score))
            decision = str(data.get("decision") or "").strip() or ("Reject" if score < 60 else "Review")
            reasoning = data.get("reasoning", "")
            if isinstance(reasoning, list):
                reasoning = "\n".join([str(x) for x in reasoning if str(x).strip()])
            reasoning = str(reasoning or "").strip() or "No reasoning returned by model."
            missing = data.get("missing_skills", [])
            if isinstance(missing, str):
                missing = [x.strip() for x in missing.split(",") if x.strip()]
            if not isinstance(missing, list):
                missing = []
            candidate = str(data.get("candidate_name") or "").strip() or "Unknown Candidate"
            return {
                "candidate_name": candidate,
                "match_score": score,
                "decision": decision,
                "reasoning": reasoning,
                "missing_skills": [str(x) for x in missing],
            }

        def _recover_from_text(raw_text: str):
            txt = str(raw_text or "").strip()
            if not txt:
                return None
            # Strip DeepSeek-style thinking block if present.
            txt = re.sub(r"<think>.*?</think>", "", txt, flags=re.IGNORECASE | re.DOTALL).strip()
            if not txt:
                return None

            # Try JSON extraction again after stripping think block.
            recovered_json = document_utils.clean_json_response(txt)
            norm = _normalize(recovered_json)
            if norm is not None:
                return norm

            lowered = txt.lower()
            score = None
            m = re.search(r'"match_score"\s*:\s*(\d{1,3})', txt, flags=re.IGNORECASE)
            if not m:
                m = re.search(r"\bmatch[_\s-]*score\b[^0-9]{0,20}(\d{1,3})", txt, flags=re.IGNORECASE)
            if not m:
                m = re.search(r"\bscore\b[^0-9]{0,20}(\d{1,3})", txt, flags=re.IGNORECASE)
            if m:
                try:
                    score = max(0, min(100, int(m.group(1))))
                except Exception:
                    score = None

            decision = None
            if re.search(r"\bmove\s*forward\b", lowered):
                decision = "Move Forward"
            elif re.search(r"\breview\b", lowered):
                decision = "Review"
            elif re.search(r"\breject\b", lowered):
                decision = "Reject"

            if score is None and decision is None:
                return None

            if score is None:
                score = 30 if decision == "Reject" else 70 if decision == "Review" else 85
            if decision is None:
                decision = "Reject" if score < 60 else "Review" if score < 80 else "Move Forward"

            reasoning = ""
            for line in txt.splitlines():
                line = line.strip()
                if not line:
                    continue
                # skip obvious JSON scaffolding lines
                if line in ("{", "}", "[", "]"):
                    continue
                if line.startswith('"') and ":" in line:
                    continue
                reasoning = line
                break
            if not reasoning:
                reasoning = "Recovered standard evaluation from non-JSON model output."

            return _normalize(
                {
                    "candidate_name": "Unknown Candidate",
                    "match_score": score,
                    "decision": decision,
                    "reasoning": reasoning,
                    "missing_skills": [],
                }
            )

        last_error = "unknown"
        for attempt in range(2):
            try:
                resp = self.client.chat.completions.create(
                    model=self._chat_model(),
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                    temperature=0.0 if attempt else 0.1,
                    max_tokens=1024,
                    timeout=self.request_timeout_sec,
                )
                raw = resp.choices[0].message.content
                data = document_utils.clean_json_response(raw)
                norm = _normalize(data)
                if norm is not None:
                    return norm
                recovered = _recover_from_text(raw)
                if recovered is not None:
                    return recovered
                last_error = "malformed JSON output"
                self._log_parse_failure(raw, reason=f"evaluate_standard attempt={attempt + 1} malformed")
            except Exception as e:
                last_error = str(e)
                self._log_parse_failure(f"[EXCEPTION] {e}", reason=f"evaluate_standard attempt={attempt + 1} exception")
        return _fallback(last_error)

    def evaluate_criterion(self, resume_text, category, value):
        if self.use_mock:
            return self._mock_evaluate_criterion(resume_text, category, value)
        document_utils = self._document_utils()
        # Heuristic: allow partial match for India HR ops/statutory compliance when resume shows payroll/HR policies
        try:
            cat = str(category or "").lower()
            req = str(value or "").lower()
            resume_l = str(resume_text or "").lower()
            # Deterministic gate for stack-specific MUST-HAVE requirements:
            # do not infer from adjacent tools; require explicit token overlap.
            if cat == "must_have_skills":
                tech_terms = [
                    "react", "python", "fastapi", "pydantic", "sqlmodel", "async",
                    "vite", "bun", "react-query", "react query", "react-table", "react table",
                    "grpc", "protobuf", "kubernetes", "docker"
                ]
                req_terms = [t for t in tech_terms if t in req]
                if len(req_terms) >= 2:
                    matched = []
                    for t in req_terms:
                        # normalize dashed/spaced variants for react-query/react-table
                        variants = {t, t.replace("-", " "), t.replace(" ", "-")}
                        if any(v in resume_l for v in variants):
                            matched.append(t)
                    if not matched:
                        return {"requirement": value, "status": "Missing", "evidence": "None"}
                    if len(matched) < len(set(req_terms)):
                        return {
                            "requirement": value,
                            "status": "Partial",
                            "evidence": f"Explicitly matched: {', '.join(sorted(set(matched)))}"
                        }
                    return {
                        "requirement": value,
                        "status": "Met",
                        "evidence": f"Explicitly matched: {', '.join(sorted(set(matched)))}"
                    }
            # Heuristic: experience requirement like "Minimum X years"
            if cat == "experience" and ("minimum" in req and "years" in req):
                m = re.search(r"(\\d{1,2})\\s*\\+?\\s*years?", req)
                if m:
                    required = int(m.group(1))
                    # Find explicit years in resume text (e.g., "11 years", "10+ years", "10 yrs")
                    years = [int(x) for x in re.findall(r"\\b(\\d{1,2})\\s*\\+?\\s*(?:years?|yrs?)\\b", resume_l)]
                    # If we included RESUME_PROFILE, use years_experience as a signal too
                    if "years_experience" in resume_l and not years:
                        m2 = re.search(r"years_experience[^0-9]*(\\d{1,2})", resume_l)
                        if m2:
                            years = [int(m2.group(1))]
                    if years:
                        if max(years) >= required:
                            return {"requirement": value, "status": "Met", "evidence": f"Explicit years in resume: {max(years)}"}
                        return {"requirement": value, "status": "Partial", "evidence": f"Explicit years in resume: {max(years)} (below {required})"}
            if cat == "domain_knowledge" and ("statutory compliance" in req or "india hr operations" in req or "labor laws" in req):
                signals = []
                for kw in ["payroll", "hr policies", "employee relations", "compensation", "benefits"]:
                    if kw in resume_l:
                        signals.append(kw)
                if signals:
                    return {
                        "requirement": value,
                        "status": "Partial",
                        "evidence": f"Matched keywords in resume: {', '.join(signals[:4])}"
                    }
        except Exception:
            pass
        system_prompt = f"""
        Verify if resume meets this {category} requirement: "{value}".
        NORMALIZATION RULES:
        - Degree equivalence: B.Tech/BTech/B.E./BE/B.S./BS/B.Sc counts as Bachelor's. M.Tech/MTech/M.E./ME/M.S./MS/M.Sc counts as Master's.
        - Cloud platforms: AWS, Azure, GCP, Google Cloud count as cloud platform experience.
        Return JSON: {{ "requirement": "{value}", "status": "Met" | "Partial" | "Missing", "evidence": "Quote or 'None'" }}
        """
        user_prompt = f"TEXT:\n{resume_text[:15000]}"
        try:
            resp = self.client.chat.completions.create(
                model=self._chat_model(),
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.0,
                timeout=self.request_timeout_sec,
            )
            data = document_utils.clean_json_response(resp.choices[0].message.content)
            if data: data['category'] = category
            return data
        except: return None

    def evaluate_bulk_criteria(self, resume_text, criteria_list, debug_context=None):
        if self.use_mock:
            return [self._mock_evaluate_criterion(resume_text, cat, val) for cat, val in criteria_list]
        document_utils = self._document_utils()
        if not criteria_list: return []

        expected_len = len(criteria_list)
        debug_context = debug_context if isinstance(debug_context, dict) else {}
        req_objects = [
            {
                "requirement_id": idx,
                "category": str(cat),
                "requirement": str(val),
            }
            for idx, (cat, val) in enumerate(criteria_list, start=1)
        ]
        reqs_json = json.dumps(req_objects, ensure_ascii=False, indent=2)

        system_prompt = """
        You are a Technical Auditor. Evaluate the candidate against the list of requirements provided.
        For EACH requirement, determine if it is Met, Partial, or Missing based on the resume text.

        NORMALIZATION RULES:
        - Degree equivalence: B.Tech/BTech/B.E./BE/B.S./BS/B.Sc counts as Bachelor's. M.Tech/MTech/M.E./ME/M.S./MS/M.Sc counts as Master's.
        - Cloud platforms: AWS, Azure, GCP, Google Cloud count as cloud platform experience.

        CRITICAL OUTPUT REQUIREMENTS (STRICT):
        - Return EXACTLY one JSON object per input requirement.
        - Output ARRAY length MUST equal number of requirements provided.
        - Preserve input order exactly (1..N).
        - Echo the exact requirement_id for each row.
        - Echo requirement text exactly as provided for that requirement_id.
        - Do not skip or merge requirements.
        - If evidence is weak/unclear, still return the row with status "Missing" or "Partial" and evidence "None" if needed.
        - Return ONLY JSON (no markdown, no explanations).

        RETURN ONLY A JSON ARRAY of objects:
        [
            { "requirement_id": 1, "requirement": "exact text from list", "category": "category from list", "status": "Met/Partial/Missing", "evidence": "brief quote or None" },
            ...
        ]
        """
        resume_snippet = str(resume_text or "")[: max(1000, int(self.bulk_resume_chars))]
        user_prompt = (
            f"REQUIREMENTS COUNT: {expected_len}\n"
            f"REQUIREMENTS (ordered JSON):\n{reqs_json}\n\n"
            f"RESUME TEXT:\n{resume_snippet}"
        )

        try:
            # Attempt 1: full bulk window with longer timeout.
            resp = self.client.chat.completions.create(
                model=self._chat_model(),
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.0,
                max_tokens=3500,
                timeout=max(self.request_timeout_sec, self.bulk_timeout_sec),
            )
            raw_content = resp.choices[0].message.content
            self._debug_bulk_dump(
                stage="attempt1_raw",
                raw_content=raw_content,
                expected_len=expected_len,
                criteria_list=criteria_list,
                resume_snippet=resume_snippet,
                extra=debug_context,
            )
            data = document_utils.clean_json_response(raw_content)
            if isinstance(data, dict) and "results" in data:
                data = data["results"]
            if not isinstance(data, list):
                self._debug_bulk_dump(
                    stage="attempt1_non_list",
                    raw_content=raw_content,
                    expected_len=expected_len,
                    criteria_list=criteria_list,
                    resume_snippet=resume_snippet,
                    extra={"parsed_type": type(data).__name__ if data is not None else "None", **debug_context},
                )
                self._log_parse_failure(
                    f"[bulk] expected={expected_len} parsed_type={type(data).__name__ if data is not None else 'None'}\n{raw_content}",
                    reason="evaluate_bulk_criteria non-list output",
                )
                return []

            # Preserve partial bulk output so caller can recover missing rows in staged fallbacks.
            normalized = []
            for idx, raw in enumerate(data):
                if not isinstance(raw, dict):
                    continue
                default_category = criteria_list[idx][0] if idx < len(criteria_list) else ""
                default_requirement = criteria_list[idx][1] if idx < len(criteria_list) else ""
                status = str(raw.get("status") or "Missing")
                if status not in ("Met", "Partial", "Missing"):
                    status = "Missing"
                normalized.append({
                    "requirement_id": int(raw.get("requirement_id") or (idx + 1)),
                    "requirement": str(raw.get("requirement") or default_requirement),
                    "category": str(raw.get("category") or default_category),
                    "status": status,
                    "evidence": str(raw.get("evidence") or "None"),
                })
            if len(normalized) < expected_len:
                self._log_parse_failure(
                    f"[bulk] expected={expected_len} parsed_rows={len(normalized)} raw_rows={len(data)}\n{raw_content}",
                    reason="evaluate_bulk_criteria incomplete rows",
                )
            self._debug_bulk_dump(
                stage="attempt1_parsed",
                raw_content=raw_content,
                expected_len=expected_len,
                criteria_list=criteria_list,
                resume_snippet=resume_snippet,
                extra={
                    "parsed_rows": len(normalized),
                    "raw_rows": len(data),
                    **debug_context,
                },
            )
            return normalized
        except Exception as e:
            self._log_parse_failure(f"[EXCEPTION] {e}", reason="evaluate_bulk_criteria exception")
            self._debug_bulk_dump(
                stage="attempt1_exception",
                raw_content=f"[EXCEPTION] {e}",
                expected_len=expected_len,
                criteria_list=criteria_list,
                resume_snippet=resume_snippet,
                extra=debug_context,
            )
            # Attempt 2: shorter resume context to reduce model latency.
            try:
                reduced_resume = str(resume_snippet)[: max(1500, int(len(resume_snippet) * 0.55))]
                retry_prompt = (
                    f"REQUIREMENTS COUNT: {expected_len}\n"
                    f"REQUIREMENTS (ordered JSON):\n{reqs_json}\n\n"
                    f"RESUME TEXT:\n{reduced_resume}"
                )
                resp = self.client.chat.completions.create(
                    model=self._chat_model(),
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": retry_prompt}],
                    temperature=0.0,
                    max_tokens=2500,
                    timeout=max(self.request_timeout_sec, int(self.bulk_timeout_sec * 0.75)),
                )
                raw_content = resp.choices[0].message.content
                self._debug_bulk_dump(
                    stage="attempt2_raw",
                    raw_content=raw_content,
                    expected_len=expected_len,
                    criteria_list=criteria_list,
                    resume_snippet=reduced_resume,
                    extra=debug_context,
                )
                data = document_utils.clean_json_response(raw_content)
                if isinstance(data, dict) and "results" in data:
                    data = data["results"]
                if not isinstance(data, list):
                    self._debug_bulk_dump(
                        stage="attempt2_non_list",
                        raw_content=raw_content,
                        expected_len=expected_len,
                        criteria_list=criteria_list,
                        resume_snippet=reduced_resume,
                        extra={"parsed_type": type(data).__name__ if data is not None else "None", **debug_context},
                    )
                    self._log_parse_failure(
                        f"[bulk-retry] expected={expected_len} parsed_type={type(data).__name__ if data is not None else 'None'}\n{raw_content}",
                        reason="evaluate_bulk_criteria retry non-list output",
                    )
                    return []
                normalized = []
                for idx, raw in enumerate(data):
                    if not isinstance(raw, dict):
                        continue
                    default_category = criteria_list[idx][0] if idx < len(criteria_list) else ""
                    default_requirement = criteria_list[idx][1] if idx < len(criteria_list) else ""
                    status = str(raw.get("status") or "Missing")
                    if status not in ("Met", "Partial", "Missing"):
                        status = "Missing"
                    normalized.append({
                        "requirement_id": int(raw.get("requirement_id") or (idx + 1)),
                        "requirement": str(raw.get("requirement") or default_requirement),
                        "category": str(raw.get("category") or default_category),
                        "status": status,
                        "evidence": str(raw.get("evidence") or "None"),
                    })
                if len(normalized) < expected_len:
                    self._log_parse_failure(
                        f"[bulk-retry] expected={expected_len} parsed_rows={len(normalized)} raw_rows={len(data)}\n{raw_content}",
                        reason="evaluate_bulk_criteria retry incomplete rows",
                    )
                self._debug_bulk_dump(
                    stage="attempt2_parsed",
                    raw_content=raw_content,
                    expected_len=expected_len,
                    criteria_list=criteria_list,
                    resume_snippet=reduced_resume,
                    extra={
                        "parsed_rows": len(normalized),
                        "raw_rows": len(data),
                        **debug_context,
                    },
                )
                return normalized
            except Exception as e2:
                self._log_parse_failure(f"[EXCEPTION] {e2}", reason="evaluate_bulk_criteria retry exception")
                self._debug_bulk_dump(
                    stage="attempt2_exception",
                    raw_content=f"[EXCEPTION] {e2}",
                    expected_len=expected_len,
                    criteria_list=criteria_list,
                    resume_snippet=reduced_resume if "reduced_resume" in locals() else resume_snippet,
                    extra=debug_context,
                )
                return []

    def _debug_bulk_dump(self, stage, raw_content, expected_len, criteria_list, resume_snippet, extra=None):
        extra = extra if isinstance(extra, dict) else {}
        per_call_enabled = bool(extra.get("debug_bulk_log"))
        if not self.debug_bulk_log and not per_call_enabled:
            return
        try:
            safe_stage = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(stage or "bulk"))
            run_id = ""
            attempt = ""
            run_id = str(extra.get("run_id") or "")
            attempt = str(extra.get("attempt") or "")
            safe_run = re.sub(r"[^a-zA-Z0-9_.-]+", "_", run_id) if run_id else "adhoc"
            safe_attempt = re.sub(r"[^a-zA-Z0-9_.-]+", "_", attempt) if attempt else "na"
            ts = time.strftime("%Y%m%d-%H%M%S")
            out_dir = Path("logs") / "bulk_debug"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{ts}_{safe_run}_{safe_attempt}_{safe_stage}.json"
            payload = {
                "stage": stage,
                "run_id": run_id or None,
                "attempt": attempt or None,
                "expected_len": int(expected_len or 0),
                "criteria_list": [
                    {"category": str(c), "requirement": str(r)}
                    for c, r in (criteria_list or [])
                ],
                "resume_snippet": str(resume_snippet or ""),
                "raw_content": str(raw_content or ""),
                "extra": extra or {},
            }
            out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            # Debug dump must never break scoring path.
            return

    def generate_final_decision(self, candidate_name, match_details, strategy="Deep"):
        if not match_details: return 0, "Reject", "No data analyzed."

        weights = {
            "must_have_skills": 3.0,
            "experience": 3.0,
            "education_requirements": 1.0,
            "domain_knowledge": 3.0, # Elevated
            "nice_to_have_skills": 1.0,
            "soft_skills": 0.5,
            "key_responsibilities": 0.5
        }

        total_weight = 0
        earned_weight = 0

        for d in match_details:
            if not d or not isinstance(d, dict): continue

            cat = d.get('category', 'nice_to_have_skills')
            w = weights.get(cat, 1.0)

            total_weight += w
            status = d.get('status', 'Missing')

            if status == 'Met': earned_weight += w
            elif status == 'Partial': earned_weight += (w * 0.5)

        score = int((earned_weight / total_weight) * 100) if total_weight > 0 else 0

        p_thresh = 70 if strategy == "Deep" else 80
        r_thresh = 40 if strategy == "Deep" else 50

        decision = "Reject"
        if score >= p_thresh: decision = "Move Forward"
        elif score >= r_thresh: decision = "Review"

        reasoning = f"Weighted {strategy} Scan: Candidate met {earned_weight:.1f}/{total_weight:.1f} weighted points."
        return score, decision, reasoning

    def _mock_analyze_jd(self, text):
        must_have = []
        nice_to_have = []
        min_years = 0

        must_match = re.search(r"must have:(.*)", text, re.IGNORECASE)
        pref_match = re.search(r"(preferred|plus|bonus):(.*)", text, re.IGNORECASE)
        years_match = re.search(r"(\d+)\+?\s*years", text, re.IGNORECASE)

        if must_match:
            must_have = [s.strip() for s in must_match.group(1).split(",") if s.strip()]
        if pref_match:
            nice_to_have = [s.strip() for s in pref_match.group(2).split(",") if s.strip()]
        if years_match:
            min_years = int(years_match.group(1))

        return {
            "role_title": text.strip().splitlines()[0] if text.strip() else "Unknown Role",
            "must_have_skills": must_have,
            "nice_to_have_skills": nice_to_have,
            "min_years_experience": min_years,
            "education_requirements": [],
            "domain_knowledge": [],
            "soft_skills": [],
            "key_responsibilities": []
        }

    def _mock_analyze_resume(self, text):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        name = lines[0] if lines else "Unknown"
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        email = email_match.group(0) if email_match else ""
        phone_match = re.search(r"\+?\d[\d\s\-]{7,}\d", text)
        phone = phone_match.group(0) if phone_match else ""

        skills = []
        tools_match = re.search(r"(tools|skills):(.+)", text, re.IGNORECASE)
        if tools_match:
            skills = [s.strip() for s in tools_match.group(2).split(",") if s.strip()]

        return {
            "candidate_name": name,
            "email": email,
            "phone": phone,
            "extracted_skills": skills,
            "years_experience": self._estimate_years(text),
            "education_summary": "",
            "domain_experience": [],
            "work_history": []
        }

    def _mock_evaluate_standard(self, resume_text, jd_criteria):
        criteria = self._parse_criteria(jd_criteria)
        must_have = criteria.get("must_have_skills", [])
        missing = [skill for skill in must_have if skill.lower() not in resume_text.lower()]
        score = 85 if not missing else 40
        decision = "Move Forward" if score >= 80 else "Reject"
        reasoning = "Mock evaluation based on keyword presence."
        return {
            "candidate_name": "Mock Candidate",
            "match_score": score,
            "decision": decision,
            "reasoning": reasoning,
            "missing_skills": missing
        }

    def _mock_evaluate_criterion(self, resume_text, category, value):
        status = "Met" if value.lower() in resume_text.lower() else "Missing"
        evidence = value if status == "Met" else "None"
        return {
            "requirement": value,
            "category": category,
            "status": status,
            "evidence": evidence
        }

    def _parse_criteria(self, jd_criteria):
        if isinstance(jd_criteria, dict):
            return jd_criteria
        if isinstance(jd_criteria, str):
            try:
                return json.loads(jd_criteria)
            except json.JSONDecodeError:
                return {}
        return {}

    def _normalize_jd_schema(self, jd_data, jd_text):
        if not isinstance(jd_data, dict):
            jd_data = {}

        def norm_list(value):
            if value is None:
                return []
            if isinstance(value, str):
                return [value.strip()] if value.strip() else []
            if not isinstance(value, list):
                return []
            out = []
            for item in value:
                if item is None:
                    continue
                if isinstance(item, str):
                    if item.strip():
                        out.append(item.strip())
                    continue
                if isinstance(item, dict):
                    for key in ("name", "skill", "requirement", "text", "value"):
                        if key in item and isinstance(item[key], str) and item[key].strip():
                            out.append(item[key].strip())
                            break
                    continue
            return out

        def norm_int(value):
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                match = re.search(r"(\d+)", value)
                return int(match.group(1)) if match else 0
            return 0

        role_title = jd_data.get("role_title")
        if not isinstance(role_title, str) or not role_title.strip():
            role_title = self._first_nonempty_line(jd_text) or "Unknown Role"

        must_have = norm_list(jd_data.get("must_have_skills"))
        nice_to_have = norm_list(jd_data.get("nice_to_have_skills"))
        education = norm_list(jd_data.get("education_requirements"))
        domain = norm_list(jd_data.get("domain_knowledge"))
        soft = norm_list(jd_data.get("soft_skills"))
        responsibilities = norm_list(jd_data.get("key_responsibilities"))
        min_years = norm_int(jd_data.get("min_years_experience"))

        if not must_have:
            extracted = self._extract_must_haves_from_text(jd_text)
            if extracted:
                must_have = extracted

        must_have = self._dedupe_list(must_have)
        nice_to_have = self._dedupe_list(nice_to_have)
        education = self._dedupe_list(education)
        domain = self._dedupe_list(domain)
        soft = self._dedupe_list(soft)
        responsibilities = self._dedupe_list(responsibilities)

        # Cross-category dedupe: keep highest-priority category for identical requirements
        def norm_key(s):
            return " ".join(str(s).strip().lower().split())

        category_order = [
            ("must_have_skills", must_have),
            ("experience", [f"Minimum {min_years} years relevant experience"] if min_years > 0 else []),
            ("domain_knowledge", domain),
            ("nice_to_have_skills", nice_to_have),
            ("education_requirements", education),
            ("soft_skills", soft),
            ("key_responsibilities", responsibilities),
        ]

        seen = set()
        deduped = {k: [] for k, _ in category_order}
        for cat, items in category_order:
            for item in items:
                k = norm_key(item)
                if not k or k in seen:
                    continue
                seen.add(k)
                if cat in deduped:
                    deduped[cat].append(item)

        must_have = deduped["must_have_skills"]
        domain = deduped["domain_knowledge"]
        nice_to_have = deduped["nice_to_have_skills"]
        education = deduped["education_requirements"]
        soft = deduped["soft_skills"]
        responsibilities = deduped["key_responsibilities"]

        return {
            "role_title": role_title.strip(),
            "must_have_skills": must_have,
            "nice_to_have_skills": nice_to_have,
            "min_years_experience": min_years,
            "education_requirements": education,
            "domain_knowledge": domain,
            "soft_skills": soft,
            "key_responsibilities": responsibilities,
        }

    def _extract_must_haves_from_text(self, text):
        sections = [
            "requirements",
            "required",
            "qualifications",
            "what we are looking for",
            "what we're looking for",
            "must have",
            "must-have",
            "experience",
        ]
        lines = self._extract_section_lines(text, sections, max_lines=30)
        if not lines:
            return []
        candidates = []
        for line in lines:
            cleaned = self._clean_bullet_line(line)
            if not cleaned:
                continue
            if len(cleaned) < 3:
                continue
            candidates.append(cleaned)
        return self._dedupe_list(candidates)[:15]

    def _extract_section_lines(self, text, headings, max_lines=25):
        if not text:
            return []
        lines = [l.strip() for l in text.splitlines()]
        lowered = [l.lower() for l in lines]
        start_idx = None
        for i, line in enumerate(lowered):
            for h in headings:
                if h in line:
                    start_idx = i + 1
                    break
            if start_idx is not None:
                break
        if start_idx is None:
            return []

        results = []
        for line in lines[start_idx:]:
            if not line:
                if results:
                    break
                continue
            lower = line.lower()
            if any(h in lower for h in headings) and results:
                break
            if re.match(r"^[A-Z][A-Za-z\s/&-]{3,}$", line) and results:
                break
            results.append(line)
            if len(results) >= max_lines:
                break
        return results

    def _clean_bullet_line(self, line):
        cleaned = re.sub(r"^[\-\*]+\s*", "", line).strip()
        cleaned = re.sub(r"^\d+\.\s*", "", cleaned).strip()
        return cleaned

    def _dedupe_list(self, items):
        seen = set()
        out = []
        for item in items:
            if not isinstance(item, str):
                continue
            key = item.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(item.strip())
        return out

    def _first_nonempty_line(self, text):
        if not text:
            return None
        for line in text.splitlines():
            if line.strip():
                return line.strip()
        return None

    def _document_utils(self):
        if importlib.util.find_spec("document_utils") is None:
            raise RuntimeError("document_utils is unavailable; install project dependencies.")
        return importlib.import_module("document_utils")

    def _estimate_years(self, text):
        match = re.search(r"(\d+)\+?\s*years", text, re.IGNORECASE)
        return int(match.group(1)) if match else 0
