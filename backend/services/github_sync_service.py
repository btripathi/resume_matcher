import base64
import datetime as dt
import json
import os
from dataclasses import dataclass
from pathlib import Path

from github import Github, GithubException


def _load_secrets() -> dict:
    secrets_path = Path(".streamlit") / "secrets.toml"
    if not secrets_path.exists():
        return {}
    try:
        import tomllib

        return tomllib.loads(secrets_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _parse_lock_time(ts: str | None) -> dt.datetime | None:
    if not ts:
        return None
    try:
        return dt.datetime.fromisoformat(ts)
    except Exception:
        return None


@dataclass
class GitHubSyncService:
    db_path: str
    remote_db_filename: str = "resume_matcher.db"
    lock_filename: str = "WRITE_LOCK.json"

    def _credentials(self) -> tuple[str | None, str | None]:
        secrets = _load_secrets()
        token = os.getenv("RESUME_MATCHER_GITHUB_TOKEN") or secrets.get("github", {}).get("token")
        repo_name = os.getenv("RESUME_MATCHER_GITHUB_REPO") or secrets.get("github", {}).get("repo_name")
        return token, repo_name

    def _client(self):
        token, repo_name = self._credentials()
        if not token or not repo_name:
            return None, None, "GitHub credentials not configured."
        try:
            g = Github(token)
            repo = g.get_repo(repo_name)
            return g, repo, None
        except Exception as exc:
            return None, None, f"Could not access repo '{repo_name}': {exc}"

    def writer_config(self) -> dict:
        secrets = _load_secrets()
        writer = secrets.get("writer", {})
        users_raw = writer.get("users", {})
        users: list[dict] = []
        if isinstance(users_raw, dict):
            for name, pwd in users_raw.items():
                n = str(name or "").strip()
                p = str(pwd or "")
                if n and p:
                    users.append({"name": n, "password": p})
        elif isinstance(users_raw, list):
            for row in users_raw:
                if not isinstance(row, dict):
                    continue
                n = str(row.get("name") or "").strip()
                p = str(row.get("password") or "")
                if n and p:
                    users.append({"name": n, "password": p})
        return {
            "default_name": writer.get("name", ""),
            "password": writer.get("password", ""),
            "users": users,
            "lock_timeout_hours": int(writer.get("lock_timeout_hours", 6) or 6),
            "auto_write_mode": bool(writer.get("auto_write_mode", False)),
        }

    def pull_db(self) -> tuple[bool, str]:
        _, repo, err = self._client()
        if not repo:
            return False, err or "GitHub repo not accessible."
        try:
            contents = repo.get_contents(self.remote_db_filename)
            file_data: bytes | None = None
            if contents.content:
                file_data = base64.b64decode(contents.content)
            else:
                blob = repo.get_git_blob(contents.sha)
                file_data = base64.b64decode(blob.content)
            if not file_data:
                return False, "Downloaded DB content was empty."
            Path(self.db_path).write_bytes(file_data)
            return True, "Database pulled from GitHub."
        except GithubException as exc:
            if exc.status == 404:
                return False, "Remote DB not found in repository."
            return False, f"Error pulling DB: {exc}"
        except Exception as exc:
            return False, f"Error pulling DB: {exc}"

    def push_db(self) -> tuple[bool, str]:
        local_db = Path(self.db_path)
        if not local_db.exists():
            return False, f"Local database not found at {self.db_path}"
        _, repo, err = self._client()
        if not repo:
            return False, err or "GitHub repo not accessible."

        content = local_db.read_bytes()
        try:
            try:
                existing = repo.get_contents(self.remote_db_filename)
                repo.update_file(
                    existing.path,
                    f"Update DB: {dt.datetime.now().isoformat()}",
                    content,
                    existing.sha,
                )
            except GithubException as exc:
                if exc.status != 404:
                    raise
                repo.create_file(self.remote_db_filename, "Initial DB Commit", content)
            return True, "Database pushed to GitHub."
        except Exception as exc:
            return False, f"Error pushing DB: {exc}"

    def get_lock(self, timeout_hours: int | None = None) -> dict | None:
        _, repo, _ = self._client()
        if not repo:
            return None
        try:
            contents = repo.get_contents(self.lock_filename)
            if not contents.content:
                return None
            data = base64.b64decode(contents.content).decode("utf-8", errors="ignore")
            lock = json.loads(data)
            if timeout_hours is not None:
                created = _parse_lock_time(lock.get("created_at"))
                if created:
                    age = (dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - created).total_seconds() / 3600
                    lock["age_hours"] = round(age, 2)
                    lock["expired"] = age >= float(timeout_hours)
            return lock
        except GithubException as exc:
            if exc.status == 404:
                return None
            return {"error": f"Error reading lock: {exc}"}
        except Exception as exc:
            return {"error": f"Error reading lock: {exc}"}

    def acquire_lock(self, owner: str, timeout_hours: int | None = None) -> tuple[bool, str]:
        _, repo, err = self._client()
        if not repo:
            return False, err or "GitHub repo not accessible."
        try:
            repo.get_contents(self.lock_filename)
            if timeout_hours is not None:
                lock = self.get_lock(timeout_hours=timeout_hours)
                if lock and lock.get("expired"):
                    try:
                        lock_contents = repo.get_contents(self.lock_filename)
                        repo.delete_file(lock_contents.path, "Release expired write lock", lock_contents.sha)
                    except Exception:
                        return False, "Lock expired but could not be released."
                else:
                    return False, "Write lock already exists."
            else:
                return False, "Write lock already exists."
        except GithubException as exc:
            if exc.status != 404:
                return False, f"Error checking lock: {exc}"

        payload = json.dumps(
            {
                "owner": owner,
                "created_at": dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(),
            },
            indent=2,
        )
        try:
            repo.create_file(self.lock_filename, "Acquire write lock", payload)
            return True, "Write lock acquired."
        except Exception as exc:
            return False, f"Error creating lock: {exc}"

    def release_lock(self, owner: str, force: bool = False) -> tuple[bool, str]:
        _, repo, err = self._client()
        if not repo:
            return False, err or "GitHub repo not accessible."
        try:
            contents = repo.get_contents(self.lock_filename)
            lock = None
            if contents.content:
                data = base64.b64decode(contents.content).decode("utf-8", errors="ignore")
                try:
                    lock = json.loads(data)
                except Exception:
                    lock = {}
            if not force and lock and lock.get("owner") and lock.get("owner") != owner:
                return False, f"Lock owned by {lock.get('owner')}"
            repo.delete_file(contents.path, "Release write lock", contents.sha)
            return True, "Write lock released."
        except GithubException as exc:
            if exc.status == 404:
                return True, "No lock to release."
            return False, f"Error releasing lock: {exc}"
        except Exception as exc:
            return False, f"Error releasing lock: {exc}"
