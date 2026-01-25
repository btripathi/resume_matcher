from openai import OpenAI
import json
import document_utils

class AIEngine:
    def __init__(self, base_url, api_key):
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def analyze_jd(self, text):
        prompt = f"""
        You are an expert Technical Recruiter. Analyze this Job Description and extract EXTENSIVE criteria.

        JSON Format:
        {{
            "role_title": "Title",
            "must_have_skills": ["skill1", "skill2"],
            "nice_to_have_skills": ["skill3"],
            "min_years_experience": 5,
            "education_requirements": "...",
            "domain_knowledge": ["..."],
            "key_responsibilities": ["..."]
        }}
        JD: {text[:15000]}
        """
        try:
            resp = self.client.chat.completions.create(
                model="local-model", messages=[{"role": "user", "content": prompt}], temperature=0.1
            )
            return document_utils.clean_json_response(resp.choices[0].message.content)
        except Exception as e:
            return {"error": str(e)}

    def analyze_resume(self, text):
        prompt = f"""
        You are an expert HR Tech AI. Analyze this Resume and extract a RICH profile.

        JSON Format:
        {{
            "candidate_name": "Name",
            "email": "Email",
            "extracted_skills": ["Python", "AWS"],
            "years_experience": 5,
            "education_summary": "...",
            "work_history": [{{ "company": "...", "role": "...", "summary": "..." }}]
        }}
        Resume: {text[:15000]}
        """
        try:
            resp = self.client.chat.completions.create(
                model="local-model", messages=[{"role": "user", "content": prompt}], temperature=0.1
            )
            return document_utils.clean_json_response(resp.choices[0].message.content)
        except Exception as e:
            return {"candidate_name": "Error", "error_flag": True}

    def evaluate_criterion(self, resume_text, criterion_type, criterion_value):
        """
        Matches a single specific requirement against the resume.
        This ensures the AI doesn't overlook individual JD items.
        """
        system_prompt = """
        You are a strict QA Auditor for technical resumes.
        Your task is to check if a resume meets ONE specific requirement.

        Return ONLY a JSON object:
        {
            "requirement": "the requirement text",
            "status": "Met" | "Partial" | "Missing",
            "evidence": "specific text from resume or 'None found'",
            "score_impact": 0-10 (how well they meet this specific item)
        }
        """

        user_prompt = f"""
        CHECK THIS REQUIREMENT:
        Type: {criterion_type}
        Requirement: {criterion_value}

        AGAINST THIS RESUME TEXT:
        {resume_text[:20000]}
        """

        try:
            resp = self.client.chat.completions.create(
                model="local-model",
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": user_prompt}],
                temperature=0.0
            )
            data = document_utils.clean_json_response(resp.choices[0].message.content)
            return data
        except Exception as e:
            return {"requirement": str(criterion_value), "status": "Error", "evidence": str(e), "score_impact": 0}

    def generate_final_decision(self, candidate_name, match_details):
        """
        After per-criterion matching, use the results to make a final decision.
        """
        # Calculate a weighted score
        total_items = len(match_details)
        if total_items == 0: return 0, "Reject", "No criteria analyzed."

        met_count = sum(1 for d in match_details if d['status'] == 'Met')
        partial_count = sum(1 for d in match_details if d['status'] == 'Partial')

        score = int(((met_count * 1.0) + (partial_count * 0.5)) / total_items * 100)

        decision = "Reject"
        if score >= 80: decision = "Move Forward"
        elif score >= 50: decision = "Review"

        reasoning = f"Candidate met {met_count} and partially met {partial_count} out of {total_items} identified requirements."

        return score, decision, reasoning
