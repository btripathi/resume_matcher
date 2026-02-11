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
                model="local-model", messages=[{"role": "user", "content": prompt}], temperature=0.0
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
                model="local-model",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                max_tokens=1500  # Strict limit to prevent infinite generation
            )
            # If null, return a fallback object to prevent app crash
            result = document_utils.clean_json_response(resp.choices[0].message.content)
            if not result:
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
            return {"candidate_name": "Error", "error_flag": True}

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
        try:
            resp = self.client.chat.completions.create(
                model="local-model",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.1,
                max_tokens=1024
            )
            return document_utils.clean_json_response(resp.choices[0].message.content)
        except: return None

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
                model="local-model", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.0
            )
            data = document_utils.clean_json_response(resp.choices[0].message.content)
            if data: data['category'] = category
            return data
        except: return None

    def evaluate_bulk_criteria(self, resume_text, criteria_list):
        if self.use_mock:
            return [self._mock_evaluate_criterion(resume_text, cat, val) for cat, val in criteria_list]
        document_utils = self._document_utils()
        if not criteria_list: return []

        reqs_str = "\n".join([f"- [{cat}] {val}" for cat, val in criteria_list])

        system_prompt = """
        You are a Technical Auditor. Evaluate the candidate against the list of requirements provided.
        For EACH requirement, determine if it is Met, Partial, or Missing based on the resume text.

        NORMALIZATION RULES:
        - Degree equivalence: B.Tech/BTech/B.E./BE/B.S./BS/B.Sc counts as Bachelor's. M.Tech/MTech/M.E./ME/M.S./MS/M.Sc counts as Master's.
        - Cloud platforms: AWS, Azure, GCP, Google Cloud count as cloud platform experience.

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
            if isinstance(data, list): return data
            if isinstance(data, dict) and "results" in data: return data["results"]
            return []
        except: return []

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
