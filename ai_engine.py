from openai import OpenAI
import json
import document_utils

class AIEngine:
    def __init__(self, base_url, api_key):
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def analyze_jd(self, jd_text):
        if len(jd_text) < 50: return {"error": "Text too short"}

        prompt = f"""
        You are an expert Technical Recruiter. Analyze this Job Description and extract EXTENSIVE criteria into a JSON object.

        INSTRUCTIONS:
        1. Extract ALL technical skills mentioned, distinguishing between mandatory (must-have) and optional (nice-to-have).
        2. Extract Education requirements in detail (Degree, Field).
        3. Extract exact Years of Experience required.
        4. Extract any specific Domain Knowledge (e.g. Finance, Healthcare, Automotive).
        5. Extract Soft Skills mentioned.
        6. Extract specific tool versions if mentioned (e.g. C++14, Python 3.8).

        JSON Format:
        {{
            "role_title": "Title",
            "must_have_skills": ["skill1", "skill2", "tool3", "framework4"],
            "nice_to_have_skills": ["skill5", "skill6"],
            "min_years_experience": 5,
            "experience_description": "Description of required experience",
            "education_requirements": ["BS Computer Science", "Masters preferred"],
            "domain_knowledge": ["Finance", "High Frequency Trading"],
            "soft_skills": ["Leadership", "Communication"],
            "key_responsibilities": ["Responsibility 1", "Responsibility 2"]
        }}

        Job Description:
        {jd_text[:15000]}
        """
        try:
            response = self.client.chat.completions.create(
                model="local-model", messages=[{"role": "user", "content": prompt}], temperature=0.1
            )
            return document_utils.clean_json_response(response.choices[0].message.content)
        except Exception as e:
            return {"error": str(e)}

    def analyze_resume(self, resume_text):
        if len(resume_text) < 50: return {"candidate_name": "Extraction Failed", "error_flag": True}

        prompt = f"""
        You are an expert HR Tech AI. Analyze this Resume and extract a RICH and DETAILED profile into a JSON object.

        CRITICAL INSTRUCTIONS:
        1. Extract ACTUAL data from the resume text below. Do NOT summarize too much; keep specific technologies and versions.
        2. Extract ALL skills found (Technical, Tools, Languages, Frameworks).
        3. Extract Total Years of Experience (estimate if not explicit).
        4. Extract Education details including degree and university.
        5. Extract a list of previous roles with company names, dates, and a summary of achievements.
        6. Check for startup experience or leadership roles.
        7. If fields are missing, use "N/A".

        JSON Format:
        {{
            "candidate_name": "Name",
            "email": "Email",
            "phone": "Phone",
            "location": "Location",
            "extracted_skills": ["Python", "C++", "AWS", "Docker", "Kubernetes", "etc..."],
            "years_experience": 5,
            "education_summary": "Degree, University",
            "domain_experience": ["Fintech", "Healthcare"],
            "startup_experience": false,
            "leadership_experience": false,
            "work_history": [
                {{ "company": "Company A", "role": "Role", "duration": "2020-2022", "summary": "Key achievements..." }}
            ]
        }}

        Resume Text:
        {resume_text[:15000]}
        """
        try:
            response = self.client.chat.completions.create(
                model="local-model", messages=[{"role": "user", "content": prompt}], temperature=0.1
            )
            return document_utils.clean_json_response(response.choices[0].message.content)
        except Exception as e:
            return {"candidate_name": "Error", "error_flag": True}

    def evaluate_candidate(self, resume_text, jd_criteria_json, resume_profile_json):
        # Parse JD to create a checklist
        try:
            jd = json.loads(jd_criteria_json) if isinstance(jd_criteria_json, str) else jd_criteria_json
            checklist = []
            if 'must_have_skills' in jd:
                for skill in jd['must_have_skills']: checklist.append(f"[Must Have Skill] {skill}")
            if 'min_years_experience' in jd:
                checklist.append(f"[Experience] Minimum {jd['min_years_experience']} Years")
            if 'education_requirements' in jd:
                checklist.append(f"[Education] {jd['education_requirements']}")

            checklist_str = "\n".join(checklist)
        except:
            checklist_str = "Evaluate against raw JD."

        system_prompt = """
        You are a strict QA Auditor for Recruiting.
        Your job is to verify if a candidate meets specific criteria based on their Resume.

        SCORING:
        - 0-49 (Reject): Missing must-have skills.
        - 50-79 (Review): Meets basics but has gaps.
        - 80-100 (Move Forward): Strong match.

        OUTPUT JSON:
        {
            "candidate_name": "...",
            "match_score": 85,
            "decision": "Move Forward",
            "reasoning": "...",
            "match_details": [
                { "requirement": "Must Have Python", "evidence": "7 years experience at Google", "status": "Met" },
                { "requirement": "AWS", "evidence": "Not found", "status": "Missing" }
            ],
            "missing_skills": ["AWS"]
        }
        """

        user_prompt = f"""
        I need you to check this candidate against the following SPECIFIC CRITERIA LIST.
        For EACH item in the list, determine if it is Met, Missing, or Partial based on the RAW RESUME TEXT.

        CRITERIA CHECKLIST:
        {checklist_str}

        ---

        RAW RESUME TEXT:
        {resume_text[:20000]}
        """

        try:
            response = self.client.chat.completions.create(
                model="local-model",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
