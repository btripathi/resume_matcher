from openai import OpenAI
import json
import document_utils

class AIEngine:
    def __init__(self, base_url, api_key):
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def analyze_jd(self, text):
        """
        STRICT TRUTH GROUNDING: Temperature 0.0.
        Only extracts information explicitly stated in the text.
        """
        prompt = f"""
        You are a high-precision Technical Recruiter. Analyze the provided Job Description text.

        STRICT RULES:
        1. GROUNDING: Extract ONLY what is explicitly written. If a degree (e.g. BS CS) or industry (e.g. HFT) is not mentioned, leave the array EMPTY.
        2. NO ASSUMPTIONS: Do not add typical requirements unless they appear in the text.
        3. CATEGORIZATION:
           - 'must_have_skills': Only explicit technical requirements.
           - 'nice_to_have_skills': Only items listed as 'Plus', 'Bonus', or 'Preferred'.

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
        prompt = f"Analyze Resume and extract profile JSON: {{ 'candidate_name': '...', 'extracted_skills': [], 'years_experience': 0, 'work_history': [] }} \n\n {text[:15000]}"
        try:
            resp = self.client.chat.completions.create(
                model="local-model", messages=[{"role": "user", "content": prompt}], temperature=0.1
            )
            return document_utils.clean_json_response(resp.choices[0].message.content)
        except Exception as e:
            return {"candidate_name": "Error", "error_flag": True}

    def evaluate_standard(self, resume_text, jd_criteria, resume_profile):
        """Pass 1: Fast Holistic Scan."""
        system_prompt = "Evaluate candidate in one pass. Return JSON: {candidate_name, match_score, decision, reasoning}"
        user_prompt = f"JD: {jd_criteria}\nResume: {resume_text[:12000]}"
        try:
            resp = self.client.chat.completions.create(
                model="local-model", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.1
            )
            return document_utils.clean_json_response(resp.choices[0].message.content)
        except: return None

    def evaluate_criterion(self, resume_text, category, value):
        """Pass 2: Granular Verification for Weighted Scoring."""
        system_prompt = f"""
        Strictly verify if the resume meets this specific {category} requirement.
        Requirement: {value}
        Return JSON: {{ "requirement": "{value}", "status": "Met" | "Partial" | "Missing", "evidence": "Quote or 'None'" }}
        """
        user_prompt = f"TEXT:\n{resume_text[:15000]}"
        try:
            resp = self.client.chat.completions.create(
                model="local-model", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.0
            )
            data = document_utils.clean_json_response(resp.choices[0].message.content)
            if data: data['category'] = category # Injected for weighting engine
            return data
        except: return None

    def generate_final_decision(self, candidate_name, match_details, strategy="Deep"):
        """
        TIERED WEIGHTING:
        Must-haves: 3.0, Experience: 3.0
        Nice-to-haves: 1.0, Soft Skills: 0.5
        """
        if not match_details: return 0, "Reject", "No data analyzed."

        weights = {
            "must_have_skills": 3.0,
            "experience": 3.0,
            "education_requirements": 1.0,
            "domain_knowledge": 1.0,
            "nice_to_have_skills": 1.0,
            "soft_skills": 0.5,
            "key_responsibilities": 0.5
        }

        total_possible_weight = 0
        earned_weight = 0

        for d in match_details:
            if not d: continue # FIX: Skip if analysis failed/returned None

            w = weights.get(d.get('category'), 1.0)
            total_possible_weight += w

            status = d.get('status', 'Missing')
            if status == 'Met':
                earned_weight += w
            elif status == 'Partial':
                earned_weight += (w * 0.5)

        score = int((earned_weight / total_possible_weight) * 100) if total_possible_weight > 0 else 0

        p_thresh = 70 if strategy == "Deep" else 80
        r_thresh = 40 if strategy == "Deep" else 50

        decision = "Reject"
        if score >= p_thresh: decision = "Move Forward"
        elif score >= r_thresh: decision = "Review"

        reasoning = f"Weighted {strategy} Scan: Candidate earned {earned_weight:.1f}/{total_possible_weight:.1f} weighted points."
        return score, decision, reasoning
