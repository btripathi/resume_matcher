from openai import OpenAI
import json
import document_utils

class AIEngine:
    def __init__(self, base_url, api_key):
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def analyze_jd(self, text):
        """
        Extracts structured JSON criteria with a STRICT NO-HALLUCINATION policy.
        """
        prompt = f"""
        You are a high-precision Technical Recruiter. Analyze the provided Job Description.

        STRICT RULES:
        1. GROUNDING: Extract ONLY what is written. If 'BS Degree' or 'HFT' is not in the text, DO NOT include it.
        2. MUST-HAVES: Only include skills explicitly listed as requirements or 'What you'll need'.
        3. NICE-TO-HAVES: Include only items from 'Bonus Points' or 'Preferred'.

        JSON Format:
        {{
            "role_title": "Full title",
            "must_have_skills": ["Explicit Requirement 1", "Explicit Requirement 2"],
            "nice_to_have_skills": ["Bonus 1", "Bonus 2"],
            "min_years_experience": integer,
            "education_requirements": ["Specific degree if mentioned, else leave empty array"],
            "domain_knowledge": ["Industries mentioned"],
            "soft_skills": ["Leadership/Communication mentioned"],
            "key_responsibilities": ["Main tasks"]
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
        prompt = f"""Extract profile from Resume. JSON: {{ "candidate_name": "...", "extracted_skills": [], "years_experience": 0, "work_history": [] }} \n\n {text[:15000]}"""
        try:
            resp = self.client.chat.completions.create(
                model="local-model", messages=[{"role": "user", "content": prompt}], temperature=0.1
            )
            return document_utils.clean_json_response(resp.choices[0].message.content)
        except Exception as e:
            return {"candidate_name": "Error", "error_flag": True}

    def evaluate_standard(self, resume_text, jd_criteria, resume_profile):
        """Pass 1: Holistic single-pass."""
        system_prompt = "Evaluate candidate fit in one pass. Return JSON: {candidate_name, match_score, decision, reasoning}"
        user_prompt = f"JD: {jd_criteria}\nResume: {resume_text[:12000]}"
        try:
            resp = self.client.chat.completions.create(
                model="local-model", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.1
            )
            return document_utils.clean_json_response(resp.choices[0].message.content)
        except: return None

    def evaluate_criterion(self, resume_text, category, value):
        """Pass 2: Checks ONE specific requirement from the JD JSON."""
        system_prompt = f"""
        Check if the resume meets this specific {category} requirement.
        Return ONLY a JSON object:
        {{ "requirement": "{value}", "status": "Met" | "Partial" | "Missing", "evidence": "Resume quote or 'None'" }}
        """
        user_prompt = f"RESUME TEXT:\n{resume_text[:15000]}"
        try:
            resp = self.client.chat.completions.create(
                model="local-model",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.0
            )
            data = document_utils.clean_json_response(resp.choices[0].message.content)
            if data: data['category'] = category # Tag for weighted scoring
            return data
        except: return None

    def generate_final_decision(self, candidate_name, match_details):
        """
        Calculates a WEIGHTED score. Must-haves are the priority.
        """
        weights = {
            "must_have_skills": 1.0,
            "experience": 1.0,
            "education_requirements": 0.7,
            "domain_knowledge": 0.6,
            "nice_to_have_skills": 0.3,
            "soft_skills": 0.4,
            "key_responsibilities": 0.2
        }

        total_weight = 0
        earned_weight = 0

        for d in match_details:
            w = weights.get(d.get('category'), 0.5)
            total_weight += w
            status = d.get('status', 'Missing')
            if status == 'Met': earned_weight += w
            elif status == 'Partial': earned_weight += (w * 0.5)

        score = int((earned_weight / total_weight) * 100) if total_weight > 0 else 0

        # More lenient decision for granular deep scans
        decision = "Reject"
        if score >= 70: decision = "Move Forward"
        elif score >= 40: decision = "Review"

        reasoning = f"Weighted Deep Match: Candidate met critical requirements with high fidelity (Earned {earned_weight:.1f}/{total_weight:.1f} pts)."
        return score, decision, reasoning
