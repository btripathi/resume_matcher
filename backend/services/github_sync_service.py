import base64
import datetime as dt
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import time
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

def _env_bool(name: str, default: bool = False) -> bool:
    value = str(os.getenv(name, "")).strip().lower()
    if not value:
        return default
    return value in ("1", "true", "yes", "on")


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
        env_default_name = str(os.getenv("RESUME_MATCHER_WRITER_NAME", "")).strip()
        env_default_password = str(os.getenv("RESUME_MATCHER_WRITER_PASSWORD", "")).strip()
        env_users_raw = str(os.getenv("RESUME_MATCHER_WRITER_USERS_JSON", "")).strip()
        env_lock_timeout = str(os.getenv("RESUME_MATCHER_LOCK_TIMEOUT_HOURS", "")).strip()
        env_auto_write_mode = _env_bool("RESUME_MATCHER_AUTO_WRITE_MODE", False)
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
        if env_users_raw:
            try:
                env_users = json.loads(env_users_raw)
                if isinstance(env_users, dict):
                    env_users = [{"name": k, "password": v} for k, v in env_users.items()]
                if isinstance(env_users, list):
                    users = []
                    for row in env_users:
                        if not isinstance(row, dict):
                            continue
                        n = str(row.get("name") or "").strip()
                        p = str(row.get("password") or "")
                        if n and p:
                            users.append({"name": n, "password": p})
            except Exception:
                pass
        lock_timeout = int(writer.get("lock_timeout_hours", 6) or 6)
        if env_lock_timeout:
            try:
                lock_timeout = int(env_lock_timeout)
            except Exception:
                pass
        return {
            "default_name": env_default_name or writer.get("name", ""),
            "password": env_default_password or writer.get("password", ""),
            "users": users,
            "lock_timeout_hours": lock_timeout,
            "auto_write_mode": env_auto_write_mode if str(os.getenv("RESUME_MATCHER_AUTO_WRITE_MODE", "")).strip() else bool(writer.get("auto_write_mode", False)),
        }

    def pull_db(self) -> tuple[bool, str]:
        _, repo, err = self._client()
        if not repo:
            return False, err or "GitHub repo not accessible."
        try:
            local_path = Path(self.db_path)
            local_runtime = self._snapshot_runtime_tables(local_path)
            contents = repo.get_contents(self.remote_db_filename)
            file_data: bytes | None = None
            if contents.content:
                file_data = base64.b64decode(contents.content)
            else:
                blob = repo.get_git_blob(contents.sha)
                file_data = base64.b64decode(blob.content)
            if not file_data:
                return False, "Downloaded DB content was empty."
            local_path.write_bytes(file_data)
            self._restore_runtime_tables(local_path, local_runtime)
            return True, "Database pulled from GitHub (local runtime queue history preserved)."
        except GithubException as exc:
            if exc.status == 404:
                return False, "Remote DB not found in repository."
            return False, f"Error pulling DB: {exc}"
        except Exception as exc:
            return False, f"Error pulling DB: {exc}"

    def _snapshot_runtime_tables(self, db_file: Path) -> tuple[list[tuple], list[tuple]]:
        if not db_file.exists():
            return [], []
        try:
            conn = sqlite3.connect(str(db_file), timeout=30)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, job_type, payload_json, status, progress, current_step, error, result_json, created_at, started_at, finished_at
                FROM job_runs
                ORDER BY id ASC
                """
            )
            runs = cur.fetchall()
            cur.execute(
                """
                SELECT id, run_id, level, message, created_at
                FROM job_run_logs
                ORDER BY id ASC
                """
            )
            logs = cur.fetchall()
            conn.close()
            return runs, logs
        except Exception:
            return [], []

    def _restore_runtime_tables(self, db_file: Path, snapshot: tuple[list[tuple], list[tuple]]) -> None:
        runs, logs = snapshot
        if not runs and not logs:
            return
        try:
            conn = sqlite3.connect(str(db_file), timeout=30)
            cur = conn.cursor()
            # Keep local machine queue state/history intact across pulls.
            cur.execute("DELETE FROM job_run_logs")
            cur.execute("DELETE FROM job_runs")
            if runs:
                cur.executemany(
                    """
                    INSERT INTO job_runs
                    (id, job_type, payload_json, status, progress, current_step, error, result_json, created_at, started_at, finished_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    runs,
                )
            if logs:
                cur.executemany(
                    """
                    INSERT INTO job_run_logs
                    (id, run_id, level, message, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    logs,
                )
            conn.commit()
            conn.close()
        except Exception:
            # Runtime queue tables are optional in older DB snapshots; do not fail sync on restore.
            return

    def _prune_runtime_tables_for_push(self, db_file: Path) -> None:
        try:
            conn = sqlite3.connect(str(db_file), timeout=30)
            cur = conn.cursor()
            # Push only terminal queue history requested by user.
            cur.execute("DELETE FROM job_runs WHERE status NOT IN ('completed', 'failed')")
            cur.execute(
                """
                DELETE FROM job_run_logs
                WHERE run_id NOT IN (SELECT id FROM job_runs)
                """
            )
            conn.commit()
            conn.close()
        except Exception:
            return

    def _build_sanitized_db_bytes_for_push(self) -> bytes:
        local_db = Path(self.db_path)
        if not local_db.exists():
            raise FileNotFoundError(f"Local database not found at {self.db_path}")

        with tempfile.TemporaryDirectory(prefix="resume_matcher_sync_") as td:
            temp_db = Path(td) / local_db.name
            shutil.copy2(local_db, temp_db)
            self._prune_runtime_tables_for_push(temp_db)
            return temp_db.read_bytes()

    def _local_blob_sha(self) -> str | None:
        local_db = Path(self.db_path)
        if not local_db.exists():
            return None
        try:
            content = local_db.read_bytes()
        except Exception:
            return None
        header = f"blob {len(content)}\0".encode("utf-8")
        return hashlib.sha1(header + content).hexdigest()

    def _blob_sha_from_bytes(self, content: bytes) -> str:
        header = f"blob {len(content)}\0".encode("utf-8")
        return hashlib.sha1(header + content).hexdigest()

    def remote_db_sha(self) -> tuple[str | None, str | None]:
        _, repo, err = self._client()
        if not repo:
            return None, err or "GitHub repo not accessible."
        try:
            contents = repo.get_contents(self.remote_db_filename)
            return str(contents.sha), None
        except GithubException as exc:
            if exc.status == 404:
                return None, "Remote DB not found in repository."
            return None, f"Error reading remote DB metadata: {exc}"
        except Exception as exc:
            return None, f"Error reading remote DB metadata: {exc}"

    def pull_if_behind(self) -> tuple[bool, str, bool]:
        remote_sha, err = self.remote_db_sha()
        if err:
            return False, err, False
        local_sha = self._local_blob_sha()
        if local_sha and remote_sha and local_sha == remote_sha:
            return True, "Local DB already up-to-date with remote.", False
        ok, msg = self.pull_db()
        return ok, msg, bool(ok)

    def push_db(self) -> tuple[bool, str]:
        local_db = Path(self.db_path)
        if not local_db.exists():
            return False, f"Local database not found at {self.db_path}"
        _, repo, err = self._client()
        if not repo:
            return False, err or "GitHub repo not accessible."

        try:
            content = self._build_sanitized_db_bytes_for_push()
        except Exception as exc:
            return False, f"Error preparing DB for push: {exc}"
        local_blob_sha = self._blob_sha_from_bytes(content)
        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            try:
                try:
                    existing = repo.get_contents(self.remote_db_filename)
                    if str(existing.sha) == local_blob_sha:
                        return True, "Database already up-to-date on GitHub."
                    repo.update_file(
                        existing.path,
                        f"Update DB: {dt.datetime.now().isoformat()}",
                        content,
                        existing.sha,
                    )
                except GithubException as exc:
                    if exc.status == 404:
                        repo.create_file(self.remote_db_filename, "Initial DB Commit", content)
                    elif exc.status == 409 and attempt < max_attempts:
                        time.sleep(0.2 * attempt)
                        continue
                    else:
                        raise
                return True, "Database pushed to GitHub (queue history includes completed/failed runs only)."
            except GithubException as exc:
                if exc.status == 409 and attempt < max_attempts:
                    time.sleep(0.2 * attempt)
                    continue
                return False, f"Error pushing DB: {exc}"
            except Exception as exc:
                return False, f"Error pushing DB: {exc}"
        return False, "Error pushing DB: retries exhausted after concurrent update conflicts."

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
