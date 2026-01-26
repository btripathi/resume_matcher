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

        c.execute('''CREATE TABLE IF NOT EXISTS jobs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      filename TEXT, content TEXT, criteria TEXT, upload_date TIMESTAMP)''')

        c.execute('''CREATE TABLE IF NOT EXISTS resumes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      filename TEXT, content TEXT, profile TEXT, upload_date TIMESTAMP)''')

        # Ensure strategy column exists (migration for existing dbs)
        try:
            c.execute("ALTER TABLE matches ADD COLUMN strategy TEXT DEFAULT 'Standard'")
        except:
            pass

        try:
            c.execute("ALTER TABLE matches ADD COLUMN match_details TEXT")
        except:
            pass

        # Ensure standard_score column exists for history
        try:
            c.execute("ALTER TABLE matches ADD COLUMN standard_score INTEGER")
        except:
            pass

        # Ensure standard_reasoning column exists for history
        try:
            c.execute("ALTER TABLE matches ADD COLUMN standard_reasoning TEXT")
        except:
            pass

        c.execute('''CREATE TABLE IF NOT EXISTS matches
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      job_id INTEGER, resume_id INTEGER,
                      candidate_name TEXT, match_score INTEGER, standard_score INTEGER, decision TEXT,
                      reasoning TEXT, standard_reasoning TEXT, missing_skills TEXT, match_details TEXT,
                      strategy TEXT,
                      FOREIGN KEY(job_id) REFERENCES jobs(id),
                      FOREIGN KEY(resume_id) REFERENCES resumes(id))''')

        c.execute('''CREATE TABLE IF NOT EXISTS runs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT, job_id INTEGER, created_at TIMESTAMP)''')

        c.execute('''CREATE TABLE IF NOT EXISTS run_matches
                     (run_id INTEGER, match_id INTEGER,
                      PRIMARY KEY (run_id, match_id))''')

        conn.commit()
        conn.close()

    def get_job_by_filename(self, filename):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM jobs WHERE filename = ?", (filename,))
        res = c.fetchone()
        conn.close()
        return {'id': res[0]} if res else None

    def get_resume_by_filename(self, filename):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM resumes WHERE filename = ?", (filename,))
        res = c.fetchone()
        conn.close()
        return {'id': res[0]} if res else None

    def add_job(self, filename, content, criteria):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO jobs (filename, content, criteria, upload_date) VALUES (?, ?, ?, ?)",
                  (filename, content, json.dumps(criteria, indent=2), datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def update_job_content(self, job_id, content, criteria):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("UPDATE jobs SET content = ?, criteria = ?, upload_date = ? WHERE id = ?",
                  (content, json.dumps(criteria, indent=2), datetime.datetime.now().isoformat(), job_id))
        conn.commit()
        conn.close()

    def add_resume(self, filename, content, profile):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO resumes (filename, content, profile, upload_date) VALUES (?, ?, ?, ?)",
                  (filename, content, json.dumps(profile, indent=2), datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def update_resume_content(self, resume_id, content, profile):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("UPDATE resumes SET content = ?, profile = ?, upload_date = ? WHERE id = ?",
                  (content, json.dumps(profile, indent=2), datetime.datetime.now().isoformat(), resume_id))
        conn.commit()
        conn.close()

    def save_match(self, job_id, resume_id, data, match_id=None, strategy="Standard", standard_score=None, standard_reasoning=None):
        conn = self.get_connection()
        c = conn.cursor()

        details = json.dumps(data.get('match_details', []))
        missing = json.dumps(data.get('missing_skills', []))

        # Check if job_id or resume_id are None (case when re-running existing match)
        if match_id:
            # Update
            if standard_score is not None:
                c.execute('''UPDATE matches SET
                            candidate_name=?, match_score=?, standard_score=?, decision=?, reasoning=?, standard_reasoning=?, missing_skills=?, match_details=?, strategy=?
                            WHERE id=?''',
                        (data['candidate_name'], data['match_score'], standard_score, data['decision'], data['reasoning'], standard_reasoning, missing, details, strategy, match_id))
            else:
                 c.execute('''UPDATE matches SET
                            candidate_name=?, match_score=?, decision=?, reasoning=?, missing_skills=?, match_details=?, strategy=?
                            WHERE id=?''',
                        (data['candidate_name'], data['match_score'], data['decision'], data['reasoning'], missing, details, strategy, match_id))
            new_id = match_id
        else:
            c.execute('''INSERT INTO matches (job_id, resume_id, candidate_name, match_score, standard_score, decision, reasoning, standard_reasoning, missing_skills, match_details, strategy)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (job_id, resume_id, data['candidate_name'], data['match_score'], standard_score, data['decision'], data['reasoning'], standard_reasoning, missing, details, strategy))
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
        c.execute("SELECT id, match_score, strategy, standard_score, reasoning, standard_reasoning FROM matches WHERE job_id = ? AND resume_id = ?", (job_id, resume_id))
        res = c.fetchone()
        conn.close()
        if res:
            return {
                "id": res[0],
                "match_score": res[1],
                "strategy": res[2],
                "standard_score": res[3],
                "reasoning": res[4],
                "standard_reasoning": res[5]
            }
        return None

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
