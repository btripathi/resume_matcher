from openai import OpenAI
import json
import document_utils

class AIEngine:
    def __init__(self, base_url, api_key):
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def analyze_jd(self, text):
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
            return document_utils.clean_json_response(resp.choices[0].message.content)
        except Exception as e:
            return {"error": str(e)}

    def analyze_resume(self, text):
        """
        Extracts structured profile from Resume.
        Enforces strict JSON formatting (Double Quotes).
        """
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

        prompt = f"""
        You are an expert Technical Recruiter. Parse the resume text below into a structured JSON profile.

        INSTRUCTIONS:
        1. Extract the candidate's name, email, and phone.
        2. "extracted_skills": List ALL technical skills, tools, languages, and frameworks found.
        3. "work_history": Create a list of previous roles with company name, job title, and a short summary of duties.
        4. "years_experience": Estimate total years of professional experience based on the timeline.
        5. "domain_experience": List any specific industries (e.g. Fintech, Healthcare, E-commerce) mentioned.

        CRITICAL: Return ONLY valid JSON. Use DOUBLE QUOTES for all keys and strings. Do not use single quotes.

        JSON Format:
        {{
            "candidate_name": "Name",
            "email": "Email",
            "phone": "Phone",
            "extracted_skills": ["Skill A", "Skill B"],
            "years_experience": 10,
            "education_summary": "Degree, University",
            "domain_experience": ["Domain A", "Domain B"],
            "work_history": [
                {{ "company": "Company A", "role": "Title", "summary": "Summary of work" }}
            ]
        }}

        RESUME TEXT:
        {text[:20000]}
        """
        try:
            resp = self.client.chat.completions.create(
                model="local-model", messages=[{"role": "user", "content": prompt}], temperature=0.1
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
            return result
        except Exception as e:
            return {"candidate_name": "Error", "error_flag": True}

    def evaluate_standard(self, resume_text, jd_criteria, resume_profile):
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

        Return JSON: {candidate_name, match_score, decision, reasoning, missing_skills}
        """
        user_prompt = f"JD CRITERIA:\n{jd_criteria}\n\nRESUME PROFILE:\n{resume_profile}\n\nRESUME TEXT:\n{resume_text[:12000]}"
        try:
            resp = self.client.chat.completions.create(
                model="local-model", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.1
            )
            return document_utils.clean_json_response(resp.choices[0].message.content)
        except: return None

    def evaluate_criterion(self, resume_text, category, value):
        system_prompt = f"""
        Verify if resume meets this {category} requirement: "{value}".
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
        if not criteria_list: return []

        reqs_str = "\n".join([f"- [{cat}] {val}" for cat, val in criteria_list])

        system_prompt = """
        You are a Technical Auditor. Evaluate the candidate against the list of requirements provided.
        For EACH requirement, determine if it is Met, Partial, or Missing based on the resume text.

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
