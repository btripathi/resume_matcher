import sqlite3
import json
import datetime
import pandas as pd

class DBManager:
    def __init__(self, db_path='resume_matcher.db'):
        self.db_path = db_path
        self._init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path, timeout=30)

    def _init_db(self):
        conn = self.get_connection()
        c = conn.cursor()

        # Jobs
        c.execute('''CREATE TABLE IF NOT EXISTS jobs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      filename TEXT, content TEXT, criteria TEXT, upload_date TIMESTAMP)''')

        # Resumes
        c.execute('''CREATE TABLE IF NOT EXISTS resumes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      filename TEXT, content TEXT, profile TEXT, upload_date TIMESTAMP)''')

        # Matches (Added match_details)
        try:
            c.execute("ALTER TABLE matches ADD COLUMN match_details TEXT")
        except:
            pass # Column exists

        c.execute('''CREATE TABLE IF NOT EXISTS matches
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      job_id INTEGER, resume_id INTEGER,
                      candidate_name TEXT, match_score INTEGER, decision TEXT,
                      reasoning TEXT, missing_skills TEXT, match_details TEXT,
                      FOREIGN KEY(job_id) REFERENCES jobs(id),
                      FOREIGN KEY(resume_id) REFERENCES resumes(id))''')

        # Runs
        c.execute('''CREATE TABLE IF NOT EXISTS runs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT, job_id INTEGER, created_at TIMESTAMP)''')

        # Run-Matches Link
        c.execute('''CREATE TABLE IF NOT EXISTS run_matches
                     (run_id INTEGER, match_id INTEGER,
                      PRIMARY KEY (run_id, match_id))''')

        conn.commit()
        conn.close()

    def _safe_str(self, val):
        """Ensure value is a string, handling lists/dicts gracefully."""
        if val is None:
            return ""
        if isinstance(val, list):
            return "; ".join([str(v) for v in val])
        if isinstance(val, dict):
            return json.dumps(val)
        return str(val)

    def _safe_int(self, val):
        """Ensure value is an integer."""
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return 0

    def add_job(self, filename, content, criteria):
        conn = self.get_connection()
        c = conn.cursor()
        # Check duplicate
        c.execute("SELECT id FROM jobs WHERE filename = ?", (filename,))
        if c.fetchone():
            conn.close()
            return False

        c.execute("INSERT INTO jobs (filename, content, criteria, upload_date) VALUES (?, ?, ?, ?)",
                  (filename, content, json.dumps(criteria, indent=2), datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True

    def add_resume(self, filename, content, profile):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM resumes WHERE filename = ?", (filename,))
        if c.fetchone():
            conn.close()
            return False

        c.execute("INSERT INTO resumes (filename, content, profile, upload_date) VALUES (?, ?, ?, ?)",
                  (filename, content, json.dumps(profile, indent=2), datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True

    def save_match(self, job_id, resume_id, data, match_id=None):
        conn = self.get_connection()
        c = conn.cursor()

        match_details_json = json.dumps(data.get('match_details', []))
        missing_skills_json = json.dumps(data.get('missing_skills', []))

        candidate_name = self._safe_str(data.get('candidate_name', 'Unknown'))
        match_score = self._safe_int(data.get('match_score', 0))
        decision = self._safe_str(data.get('decision', 'Review'))
        reasoning = self._safe_str(data.get('reasoning', ''))

        if match_id:
            c.execute('''UPDATE matches SET
                         candidate_name=?, match_score=?, decision=?, reasoning=?, missing_skills=?, match_details=?
                         WHERE id=?''',
                      (candidate_name, match_score, decision, reasoning, missing_skills_json, match_details_json, match_id))
            new_id = match_id
        else:
            c.execute('''INSERT INTO matches (job_id, resume_id, candidate_name, match_score, decision, reasoning, missing_skills, match_details)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (job_id, resume_id, candidate_name, match_score, decision, reasoning, missing_skills_json, match_details_json))
            new_id = c.lastrowid

        conn.commit()
        conn.close()
        return new_id

    def create_run(self, name, job_id=None):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO runs (name, job_id, created_at) VALUES (?, ?, ?)",
                  (name, job_id, datetime.datetime.now().isoformat()))
        run_id = c.lastrowid
        conn.commit()
        conn.close()
        return run_id

    def link_run_match(self, run_id, match_id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO run_matches (run_id, match_id) VALUES (?, ?)", (run_id, match_id))
        conn.commit()
        conn.close()

    def get_match_if_exists(self, job_id, resume_id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM matches WHERE job_id = ? AND resume_id = ?", (job_id, resume_id))
        res = c.fetchone()
        conn.close()
        return res[0] if res else None

    def fetch_dataframe(self, query):
        conn = self.get_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def execute_query(self, query, params=()):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        conn.close()
