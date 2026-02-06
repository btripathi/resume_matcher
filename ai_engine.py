import importlib
import importlib.util
import json
import re

class AIEngine:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.use_mock = base_url.startswith("mock://")

        if not self.use_mock:
            if importlib.util.find_spec("openai") is None:
                raise RuntimeError(
                    "openai is not installed. Install it or use base_url='mock://local' for the mock API."
                )
            openai_module = importlib.import_module("openai")
            self.client = openai_module.OpenAI(base_url=base_url, api_key=api_key)

    def analyze_jd(self, text):
        if self.use_mock:
            return self._mock_analyze_jd(text)
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
                model="local-model", messages=[{"role": "user", "content": prompt}], temperature=0.0
            )
            parsed = document_utils.clean_json_response(resp.choices[0].message.content)
            ok, _ = document_utils.validate_jd_schema(parsed)
            if ok:
                return parsed

            # Retry once with a fix prompt
            fix_prompt = f"""
            Your previous response was invalid JSON or missing required keys.
            Return ONLY valid JSON using this exact schema and double quotes:
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
            resp2 = self.client.chat.completions.create(
                model="local-model", messages=[{"role": "user", "content": fix_prompt}], temperature=0.0
            )
            parsed2 = document_utils.clean_json_response(resp2.choices[0].message.content)
            ok2, _ = document_utils.validate_jd_schema(parsed2)
            return parsed2 if ok2 else {"error": "Invalid JD JSON schema"}
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
                model="local-model",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                max_tokens=1500  # Strict limit to prevent infinite generation
            )
            result = document_utils.clean_json_response(resp.choices[0].message.content)
            ok, _ = document_utils.validate_resume_profile_schema(result)
            if ok:
                return result

            # Retry once with a fix prompt
            fix_prompt = """
            Your previous response was invalid JSON or missing required keys.
            Return ONLY valid JSON using this schema and double quotes:
            {
                "candidate_name": "Name",
                "email": "Email",
                "phone": "Phone",
                "extracted_skills": ["Skill A", "Skill B"],
                "years_experience": 10,
                "education_summary": "Degree, University",
                "domain_experience": ["Domain A", "Domain B"],
                "work_history": [
                    { "company": "Company A", "role": "Title", "summary": "Concise summary of work" }
                ]
            }
            """
            resp2 = self.client.chat.completions.create(
                model="local-model",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": fix_prompt + "\n\nRESUME CONTENT:\n" + text[:15000]}
                ],
                temperature=0.0,
                max_tokens=1500
            )
            result2 = document_utils.clean_json_response(resp2.choices[0].message.content)
            ok2, _ = document_utils.validate_resume_profile_schema(result2)
            if ok2:
                return result2
            return {
                "candidate_name": "Parsing Error",
                "extracted_skills": [],
                "years_experience": 0,
                "error_flag": True
            }
        except Exception:
            return {"candidate_name": "Error", "error_flag": True}

    def evaluate_standard(self, resume_text, jd_criteria, resume_profile):
        if self.use_mock:
            return self._mock_evaluate_standard(resume_text, jd_criteria)
        document_utils = self._document_utils()
        jd = self._parse_criteria(jd_criteria)

        # Build a deterministic evaluation list
        criteria_list = []
        for k in ["must_have_skills", "domain_knowledge", "nice_to_have_skills", "soft_skills", "education_requirements", "key_responsibilities"]:
            if k in jd and isinstance(jd[k], list):
                criteria_list.extend([(k, v) for v in jd[k]])

        if jd.get("min_years_experience", 0) and int(jd.get("min_years_experience", 0)) > 0:
            criteria_list.append(("experience", f"Minimum {jd['min_years_experience']} years relevant experience"))

        details = self.evaluate_bulk_criteria(resume_text, criteria_list)
        details = self._enforce_evidence(details)

        score, decision, reasoning = self.generate_final_decision("Candidate", details, strategy="Standard")
        confidence, needs_review, low_evidence = self._compute_confidence(details)

        missing_skills = [
            d.get("requirement")
            for d in details
            if d.get("category") == "must_have_skills" and d.get("status") in ["Missing", "Partial"]
        ]

        candidate_name = "Unknown"
        profile_obj = resume_profile
        if isinstance(resume_profile, str):
            try:
                profile_obj = json.loads(resume_profile)
            except json.JSONDecodeError:
                profile_obj = None
        if isinstance(profile_obj, dict):
            candidate_name = profile_obj.get("candidate_name", "Unknown")

        result = {
            "candidate_name": candidate_name,
            "match_score": score,
            "decision": decision,
            "reasoning": reasoning,
            "missing_skills": missing_skills,
            "match_details": details,
            "confidence": confidence,
            "needs_review": int(needs_review),
            "low_evidence": int(low_evidence)
        }
        ok, _ = document_utils.validate_standard_output_schema(result)
        return result if ok else None

    def evaluate_criterion(self, resume_text, category, value):
        if self.use_mock:
            return self._mock_evaluate_criterion(resume_text, category, value)
        document_utils = self._document_utils()
        system_prompt = f"""
        Verify if resume meets this {category} requirement: "{value}".
        Return JSON: {{ "requirement": "{value}", "status": "Met" | "Partial" | "Missing", "evidence": "Short quote or 'None'" }}
        Evidence rule: If status is Met or Partial, evidence MUST be a short exact quote from the resume.
        """
        user_prompt = f"TEXT:\n{resume_text[:15000]}"
        try:
            resp = self.client.chat.completions.create(
                model="local-model", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.0
            )
            data = document_utils.clean_json_response(resp.choices[0].message.content)
            ok, _ = document_utils.validate_criterion_schema(data)
            if not ok:
                fix_prompt = f"""
                Fix your previous response to valid JSON with keys: requirement, status, evidence.
                Status must be one of: Met, Partial, Missing.
                Evidence rule: If status is Met or Partial, evidence MUST be a short exact quote from the resume.
                Requirement: "{value}"
                """
                resp2 = self.client.chat.completions.create(
                    model="local-model", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": fix_prompt}], temperature=0.0
                )
                data = document_utils.clean_json_response(resp2.choices[0].message.content)

            if data:
                data["category"] = category
                data = self._enforce_evidence([data])[0]
            return data
        except:
            return None

    def evaluate_bulk_criteria(self, resume_text, criteria_list):
        if self.use_mock:
            return [self._mock_evaluate_criterion(resume_text, cat, val) for cat, val in criteria_list]
        document_utils = self._document_utils()
        if not criteria_list: return []

        reqs_str = "\n".join([f"- [{cat}] {val}" for cat, val in criteria_list])

        system_prompt = """
        You are a Technical Auditor. Evaluate the candidate against the list of requirements provided.
        For EACH requirement, determine if it is Met, Partial, or Missing based on the resume text.
        Evidence rule: If status is Met or Partial, evidence MUST be a short exact quote from the resume.

        RETURN ONLY A JSON ARRAY of objects:
        [
            { "requirement": "text from list", "category": "category from list", "status": "Met/Partial/Missing", "evidence": "brief quote" },
            ...
        ]
        """
        user_prompt = f"REQUIREMENTS:\n{reqs_str}\n\nRESUME TEXT:\n{resume_text[:15000]}"

        try:
            resp = self.client.chat.completions.create(
                model="local-model", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.0
            )
            data = document_utils.clean_json_response(resp.choices[0].message.content)
            if isinstance(data, dict) and "results" in data:
                data = data["results"]

            ok, _ = document_utils.validate_bulk_criteria_schema(data)
            if not ok:
                fix_prompt = f"""
                Fix your previous response to ONLY a valid JSON array.
                Each item must have: requirement, category, status (Met/Partial/Missing), evidence.
                Evidence rule: If status is Met or Partial, evidence MUST be a short exact quote from the resume.
                REQUIREMENTS:
                {reqs_str}
                """
                resp2 = self.client.chat.completions.create(
                    model="local-model", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": fix_prompt}], temperature=0.0
                )
                data = document_utils.clean_json_response(resp2.choices[0].message.content)
                if isinstance(data, dict) and "results" in data:
                    data = data["results"]

            if isinstance(data, list):
                return self._enforce_evidence(data)
            return []
        except:
            return []

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

    def _document_utils(self):
        if importlib.util.find_spec("document_utils") is None:
            raise RuntimeError("document_utils is unavailable; install project dependencies.")
        return importlib.import_module("document_utils")

    def _estimate_years(self, text):
        match = re.search(r"(\d+)\+?\s*years", text, re.IGNORECASE)
        return int(match.group(1)) if match else 0

    def _enforce_evidence(self, details):
        if not isinstance(details, list):
            return []
        cleaned = []
        for d in details:
            if not isinstance(d, dict):
                continue
            status = d.get("status", "Missing")
            evidence = d.get("evidence", "")
            if status in ["Met", "Partial"]:
                if not evidence or str(evidence).strip().lower() == "none":
                    d["status"] = "Missing" if status == "Partial" else "Partial"
            cleaned.append(d)
        return cleaned

    def _compute_confidence(self, details):
        if not isinstance(details, list) or len(details) == 0:
            return 0.0, True, True

        total = 0
        met = 0
        partial = 0
        missing = 0
        evidence_missing = 0
        must_missing = 0

        for d in details:
            if not isinstance(d, dict):
                continue
            total += 1
            status = d.get("status", "Missing")
            evidence = str(d.get("evidence", "") or "").strip()

            if status == "Met":
                met += 1
            elif status == "Partial":
                partial += 1
            else:
                missing += 1

            if d.get("category") == "must_have_skills" and status in ["Missing", "Partial"]:
                must_missing += 1

            if status in ["Met", "Partial"] and (not evidence or evidence.lower() == "none"):
                evidence_missing += 1

        coverage = (met + 0.5 * partial) / total if total > 0 else 0.0
        evidence_ratio = 1.0 - (evidence_missing / max(1, (met + partial)))
        confidence = max(0.05, min(1.0, coverage * (0.6 + 0.4 * evidence_ratio)))

        low_evidence = evidence_ratio < 0.6
        needs_review = must_missing > 0 or confidence < 0.6 or low_evidence

        return round(confidence, 2), bool(needs_review), bool(low_evidence)
