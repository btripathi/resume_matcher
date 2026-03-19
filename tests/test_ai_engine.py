"""Tests for ai_engine.py — mock mode."""

from ai_engine import AIEngine
from document_utils import clean_json_response


def _engine():
    return AIEngine(base_url="mock://test", api_key="test-key")


def test_mock_analyze_jd_returns_criteria():
    engine = _engine()
    result = engine.analyze_jd("Software Engineer\nmust have: Python, FastAPI\npreferred: Docker")
    assert isinstance(result, dict)
    assert "must_have_skills" in result
    assert "Python" in result["must_have_skills"]
    assert result["role_title"] == "Software Engineer"


def test_mock_analyze_resume_returns_profile():
    engine = _engine()
    text = "Alice Smith\nalice@example.com\n+1 555-1234\nSkills: Python, SQL\n5 years experience"
    result = engine.analyze_resume(text)
    assert isinstance(result, dict)
    assert result["candidate_name"] == "Alice Smith"
    assert "Python" in result["extracted_skills"]
    assert result["years_experience"] == 5


def test_mock_evaluate_standard_high_score():
    engine = _engine()
    criteria = {"must_have_skills": ["Python", "SQL"]}
    resume_text = "I know Python and SQL well."
    result = engine.evaluate_standard(resume_text, criteria, {})
    assert isinstance(result, dict)
    assert result["match_score"] == 85
    assert result["decision"] == "Move Forward"
    assert result["missing_skills"] == []


def test_mock_evaluate_standard_low_score():
    engine = _engine()
    criteria = {"must_have_skills": ["Rust", "Go"]}
    resume_text = "I know Python."
    result = engine.evaluate_standard(resume_text, criteria, {})
    assert result["match_score"] == 40
    assert result["decision"] == "Reject"
    assert len(result["missing_skills"]) == 2


def test_mock_evaluate_criterion_met():
    engine = _engine()
    result = engine.evaluate_criterion("I know Python well.", "must_have_skills", "Python")
    assert result["status"] == "Met"
    assert result["evidence"] == "Python"


def test_mock_evaluate_criterion_missing():
    engine = _engine()
    result = engine.evaluate_criterion("I know Java.", "must_have_skills", "Rust")
    assert result["status"] == "Missing"
    assert result["evidence"] == "None"


def test_clean_json_response_valid():
    raw = '{"name": "Alice", "score": 90}'
    result = clean_json_response(raw)
    assert result == {"name": "Alice", "score": 90}


def test_clean_json_response_fenced():
    raw = '```json\n{"name": "Bob"}\n```'
    result = clean_json_response(raw)
    assert result == {"name": "Bob"}


def test_clean_json_response_malformed():
    assert clean_json_response("not json at all") is None
    assert clean_json_response("") is None
    assert clean_json_response(None) is None
