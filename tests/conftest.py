import os
import sys
import tempfile

import pytest

# Ensure project root is on sys.path so imports resolve correctly.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import DBManager
from ai_engine import AIEngine
from backend.services.repository import Repository
from backend.services.analysis import AnalysisService


@pytest.fixture()
def tmp_db(tmp_path):
    """Yield a temporary SQLite DB path and clean up after."""
    db_path = str(tmp_path / "test.db")
    yield db_path
    # cleanup is automatic via tmp_path


@pytest.fixture()
def db(tmp_db):
    """Create a fresh DBManager backed by a temp DB."""
    return DBManager(db_path=tmp_db)


@pytest.fixture()
def repo(db):
    """Create a Repository wrapping the temp DB."""
    return Repository(db=db)


@pytest.fixture()
def mock_llm():
    """Create an AIEngine in mock mode."""
    return AIEngine(base_url="mock://test", api_key="test-key")


@pytest.fixture()
def analysis(repo, mock_llm):
    """Create an AnalysisService with repo + mock LLM."""
    return AnalysisService(repo=repo, llm=mock_llm)


@pytest.fixture()
def client(tmp_path):
    """Create a FastAPI TestClient with temp DB, mock LLM, and GitHub sync disabled."""
    db_path = str(tmp_path / "api_test.db")
    os.environ["RESUME_MATCHER_DB_PATH"] = db_path
    os.environ["RESUME_MATCHER_LM_BASE_URL"] = "mock://test"
    os.environ["RESUME_MATCHER_LM_API_KEY"] = "test-key"
    os.environ["RESUME_MATCHER_AUTO_PULL_DB_ON_START"] = "off"
    os.environ["RESUME_MATCHER_GITHUB_TOKEN"] = ""
    os.environ["RESUME_MATCHER_GITHUB_REPO"] = ""

    # Reload settings so the dataclass picks up the new env vars.
    import importlib
    import backend.config as config_mod
    importlib.reload(config_mod)

    # Re-import create_app after config reload so it uses the fresh settings.
    import backend.app as app_mod
    importlib.reload(app_mod)
    from backend.app import create_app

    app = create_app()
    from starlette.testclient import TestClient
    with TestClient(app, raise_server_exceptions=False) as tc:
        yield tc
