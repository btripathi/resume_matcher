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
                      filename TEXT, content TEXT, criteria TEXT, tags TEXT, upload_date TIMESTAMP)''')

        # Added 'tags' column to resumes
        c.execute('''CREATE TABLE IF NOT EXISTS resumes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      filename TEXT, content TEXT, profile TEXT, tags TEXT, upload_date TIMESTAMP)''')

        c.execute('''CREATE TABLE IF NOT EXISTS tags
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT UNIQUE)''')

        # Migration for existing dbs
        try:
            c.execute("ALTER TABLE resumes ADD COLUMN tags TEXT")
        except:
            pass
        try:
            c.execute("ALTER TABLE jobs ADD COLUMN tags TEXT")
        except:
            pass

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

        # NEW: threshold column for runs
        try:
            c.execute("ALTER TABLE runs ADD COLUMN threshold INTEGER DEFAULT 50")
        except:
            pass

        c.execute('''CREATE TABLE IF NOT EXISTS runs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT, job_id INTEGER, threshold INTEGER, created_at TIMESTAMP)''')

        c.execute('''CREATE TABLE IF NOT EXISTS run_matches
                     (run_id INTEGER, match_id INTEGER,
                      PRIMARY KEY (run_id, match_id))''')

        c.execute('''CREATE TABLE IF NOT EXISTS job_runs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      job_type TEXT NOT NULL,
                      payload_json TEXT,
                      status TEXT NOT NULL DEFAULT 'queued',
                      progress INTEGER DEFAULT 0,
                      current_step TEXT,
                      error TEXT,
                      result_json TEXT,
                      created_at TIMESTAMP,
                      started_at TIMESTAMP,
                      finished_at TIMESTAMP)''')

        c.execute('''CREATE TABLE IF NOT EXISTS job_run_logs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      run_id INTEGER NOT NULL,
                      level TEXT NOT NULL,
                      message TEXT NOT NULL,
                      created_at TIMESTAMP,
                      FOREIGN KEY(run_id) REFERENCES job_runs(id))''')

        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_job_runs_status_created_at ON job_runs(status, created_at)"
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_job_run_logs_run_id_id ON job_run_logs(run_id, id)"
        )

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

    def add_job(self, filename, content, criteria, tags=None):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO jobs (filename, content, criteria, tags, upload_date) VALUES (?, ?, ?, ?, ?)",
                  (filename, content, json.dumps(criteria, indent=2), tags, datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def update_job_content(self, job_id, content, criteria):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("UPDATE jobs SET content = ?, criteria = ?, upload_date = ? WHERE id = ?",
                  (content, json.dumps(criteria, indent=2), datetime.datetime.now().isoformat(), job_id))
        conn.commit()
        conn.close()

    def update_job_tags(self, job_id, tags):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("UPDATE jobs SET tags = ? WHERE id = ?", (tags, job_id))
        conn.commit()
        conn.close()

    def add_resume(self, filename, content, profile, tags=None):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO resumes (filename, content, profile, tags, upload_date) VALUES (?, ?, ?, ?, ?)",
                  (filename, content, json.dumps(profile, indent=2), tags, datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def update_resume_content(self, resume_id, content, profile):
        conn = self.get_connection()
        c = conn.cursor()
        # Preserve existing tags if not passed? For now just content update.
        c.execute("UPDATE resumes SET content = ?, profile = ?, upload_date = ? WHERE id = ?",
                  (content, json.dumps(profile, indent=2), datetime.datetime.now().isoformat(), resume_id))
        conn.commit()
        conn.close()

    def update_resume_tags(self, resume_id, tags):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("UPDATE resumes SET tags = ? WHERE id = ?", (tags, resume_id))
        conn.commit()
        conn.close()

    def list_tags(self):
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute("SELECT name FROM tags ORDER BY name COLLATE NOCASE")
            rows = [row[0] for row in c.fetchall()]
        except:
            rows = []
        conn.close()
        return rows

    def add_tag(self, name):
        if not name or not name.strip():
            return
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name.strip(),))
        conn.commit()
        conn.close()

    def delete_tag(self, name):
        if not name or not name.strip():
            return
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM tags WHERE name = ?", (name.strip(),))
        conn.commit()
        conn.close()

    def rename_tag(self, old, new):
        if not old or not new:
            return
        old_name = old.strip()
        new_name = new.strip()
        if not old_name or not new_name or old_name == new_name:
            return
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (new_name,))
        c.execute("DELETE FROM tags WHERE name = ?", (old_name,))
        conn.commit()
        conn.close()

    def rename_tag_in_resumes(self, old, new):
        if not old or not new:
            return
        old_name = old.strip()
        new_name = new.strip()
        if not old_name or not new_name or old_name == new_name:
            return
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT id, tags FROM resumes WHERE tags IS NOT NULL AND tags != ''")
        rows = c.fetchall()
        for resume_id, tags_str in rows:
            tags = self._split_tags(tags_str)
            updated = False
            new_tags = []
            for tag in tags:
                if tag == old_name:
                    new_tags.append(new_name)
                    updated = True
                else:
                    new_tags.append(tag)
            if updated:
                new_tags_val = self._join_tags(new_tags)
                c.execute("UPDATE resumes SET tags = ? WHERE id = ?", (new_tags_val, resume_id))
        conn.commit()
        conn.close()

    def rename_tag_in_jobs(self, old, new):
        if not old or not new:
            return
        old_name = old.strip()
        new_name = new.strip()
        if not old_name or not new_name or old_name == new_name:
            return
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT id, tags FROM jobs WHERE tags IS NOT NULL AND tags != ''")
        rows = c.fetchall()
        for job_id, tags_str in rows:
            tags = self._split_tags(tags_str)
            updated = False
            new_tags = []
            for tag in tags:
                if tag == old_name:
                    new_tags.append(new_name)
                    updated = True
                else:
                    new_tags.append(tag)
            if updated:
                new_tags_val = self._join_tags(new_tags)
                c.execute("UPDATE jobs SET tags = ? WHERE id = ?", (new_tags_val, job_id))
        conn.commit()
        conn.close()

    def delete_tag_from_resumes(self, name):
        if not name or not name.strip():
            return
        tag_name = name.strip()
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT id, tags FROM resumes WHERE tags IS NOT NULL AND tags != ''")
        rows = c.fetchall()
        for resume_id, tags_str in rows:
            tags = self._split_tags(tags_str)
            if tag_name not in tags:
                continue
            new_tags = [t for t in tags if t != tag_name]
            new_tags_val = self._join_tags(new_tags) if new_tags else None
            c.execute("UPDATE resumes SET tags = ? WHERE id = ?", (new_tags_val, resume_id))
        conn.commit()
        conn.close()

    def delete_tag_from_jobs(self, name):
        if not name or not name.strip():
            return
        tag_name = name.strip()
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT id, tags FROM jobs WHERE tags IS NOT NULL AND tags != ''")
        rows = c.fetchall()
        for job_id, tags_str in rows:
            tags = self._split_tags(tags_str)
            if tag_name not in tags:
                continue
            new_tags = [t for t in tags if t != tag_name]
            new_tags_val = self._join_tags(new_tags) if new_tags else None
            c.execute("UPDATE jobs SET tags = ? WHERE id = ?", (new_tags_val, job_id))
        conn.commit()
        conn.close()

    def _split_tags(self, tags_str):
        if not tags_str:
            return []
        return [t.strip() for t in str(tags_str).split(",") if t.strip()]

    def _join_tags(self, tags_list):
        if not tags_list:
            return None
        seen = set()
        out = []
        for tag in tags_list:
            if not tag:
                continue
            t = tag.strip()
            if not t:
                continue
            key = t.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(t)
        return ",".join(out)

    def save_match(self, job_id, resume_id, data, match_id=None, strategy="Standard", standard_score=None, standard_reasoning=None):
        conn = self.get_connection()
        c = conn.cursor()

        details = json.dumps(data.get('match_details', []))
        missing = json.dumps(data.get('missing_skills', []))

        # --- FIX: Sanitize reasoning to ensure it's a string, not a list ---
        reasoning_val = data.get('reasoning', "No reasoning provided.")
        if isinstance(reasoning_val, list):
            reasoning_val = "\n".join([str(item) for item in reasoning_val])
        else:
            reasoning_val = str(reasoning_val)

        # Check if job_id or resume_id are None (case when re-running existing match)
        if match_id:
            # Update
            if standard_score is not None:
                c.execute('''UPDATE matches SET
                            candidate_name=?, match_score=?, standard_score=?, decision=?, reasoning=?, standard_reasoning=?, missing_skills=?, match_details=?, strategy=?
                            WHERE id=?''',
                        (data['candidate_name'], data['match_score'], standard_score, data['decision'], reasoning_val, standard_reasoning, missing, details, strategy, match_id))
            else:
                 c.execute('''UPDATE matches SET
                            candidate_name=?, match_score=?, decision=?, reasoning=?, missing_skills=?, match_details=?, strategy=?
                            WHERE id=?''',
                        (data['candidate_name'], data['match_score'], data['decision'], reasoning_val, missing, details, strategy, match_id))
            new_id = match_id
        else:
            c.execute('''INSERT INTO matches (job_id, resume_id, candidate_name, match_score, standard_score, decision, reasoning, standard_reasoning, missing_skills, match_details, strategy)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (job_id, resume_id, data['candidate_name'], data['match_score'], standard_score, data['decision'], reasoning_val, standard_reasoning, missing, details, strategy))
            new_id = c.lastrowid

        conn.commit()
        conn.close()
        return new_id

    def create_run(self, name, job_id=None, threshold=50):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO runs (name, job_id, threshold, created_at) VALUES (?, ?, ?, ?)",
                  (name, job_id, threshold, datetime.datetime.now().isoformat()))
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
        c.execute(
            "SELECT id, match_score, strategy, standard_score, reasoning, standard_reasoning "
            "FROM matches WHERE job_id = ? AND resume_id = ? ORDER BY id DESC LIMIT 1",
            (job_id, resume_id),
        )
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

    # --- Background run queue methods ---
    def enqueue_job_run(self, job_type, payload):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            '''INSERT INTO job_runs (job_type, payload_json, status, progress, created_at)
               VALUES (?, ?, 'queued', 0, ?)''',
            (job_type, json.dumps(payload or {}), datetime.datetime.now().isoformat()),
        )
        run_id = c.lastrowid
        conn.commit()
        conn.close()
        return run_id

    def list_job_runs(self, limit=100):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            '''SELECT jr.id, jr.job_type, jr.payload_json, jr.status, jr.progress, jr.current_step, jr.error,
                      jr.result_json, jr.created_at, jr.started_at, jr.finished_at,
                      (SELECT MAX(l.created_at) FROM job_run_logs l WHERE l.run_id = jr.id) AS last_log_at
               FROM job_runs jr
               ORDER BY id DESC
               LIMIT ?''',
            (int(limit),),
        )
        rows = c.fetchall()
        conn.close()
        out = []
        for row in rows:
            out.append({
                "id": row[0],
                "job_type": row[1],
                "payload": json.loads(row[2]) if row[2] else {},
                "status": row[3],
                "progress": int(row[4] or 0),
                "current_step": row[5],
                "error": row[6],
                "result": json.loads(row[7]) if row[7] else {},
                "created_at": row[8],
                "started_at": row[9],
                "finished_at": row[10],
                "last_log_at": row[11],
            })
        return out

    def get_job_run(self, run_id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            '''SELECT jr.id, jr.job_type, jr.payload_json, jr.status, jr.progress, jr.current_step, jr.error,
                      jr.result_json, jr.created_at, jr.started_at, jr.finished_at,
                      (SELECT MAX(l.created_at) FROM job_run_logs l WHERE l.run_id = jr.id) AS last_log_at
               FROM job_runs jr
               WHERE jr.id = ?
               LIMIT 1''',
            (int(run_id),),
        )
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row[0],
            "job_type": row[1],
            "payload": json.loads(row[2]) if row[2] else {},
            "status": row[3],
            "progress": int(row[4] or 0),
            "current_step": row[5],
            "error": row[6],
            "result": json.loads(row[7]) if row[7] else {},
            "created_at": row[8],
            "started_at": row[9],
            "finished_at": row[10],
            "last_log_at": row[11],
        }

    def claim_next_job_run(self):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT id FROM job_runs WHERE status = 'queued' ORDER BY id ASC LIMIT 1"
        )
        row = c.fetchone()
        if not row:
            conn.close()
            return None

        run_id = int(row[0])
        c.execute(
            '''UPDATE job_runs
               SET status = 'running', started_at = ?, current_step = ?, progress = 1
               WHERE id = ? AND status = 'queued' ''',
            (datetime.datetime.now().isoformat(), "started", run_id),
        )
        changed = c.rowcount
        conn.commit()
        conn.close()
        if changed != 1:
            return None
        return self.get_job_run(run_id)

    def update_job_run_progress(self, run_id, progress=0, current_step=None):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            "UPDATE job_runs SET progress = ?, current_step = ? WHERE id = ?",
            (int(progress), current_step, int(run_id)),
        )
        conn.commit()
        conn.close()

    def update_job_run_payload(self, run_id, payload):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            "UPDATE job_runs SET payload_json = ? WHERE id = ?",
            (json.dumps(payload or {}), int(run_id)),
        )
        conn.commit()
        conn.close()

    def update_job_run_result(self, run_id, result):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            "UPDATE job_runs SET result_json = ? WHERE id = ?",
            (json.dumps(result or {}), int(run_id)),
        )
        conn.commit()
        conn.close()

    def complete_job_run(self, run_id, result=None):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            '''UPDATE job_runs
               SET status = 'completed', progress = 100, current_step = ?, result_json = ?, finished_at = ?
               WHERE id = ?''',
            ("completed", json.dumps(result or {}), datetime.datetime.now().isoformat(), int(run_id)),
        )
        conn.commit()
        conn.close()

    def fail_job_run(self, run_id, error_message):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            '''UPDATE job_runs
               SET status = 'failed', current_step = ?, error = ?, finished_at = ?
               WHERE id = ?''',
            ("failed", str(error_message), datetime.datetime.now().isoformat(), int(run_id)),
        )
        conn.commit()
        conn.close()

    def requeue_job_run(self, run_id, payload=None, current_step="requeued"):
        conn = self.get_connection()
        c = conn.cursor()
        if payload is None:
            c.execute(
                '''UPDATE job_runs
                   SET status = 'queued', error = NULL, current_step = ?, started_at = NULL, finished_at = NULL
                   WHERE id = ?''',
                (str(current_step), int(run_id)),
            )
        else:
            c.execute(
                '''UPDATE job_runs
                   SET status = 'queued', payload_json = ?, error = NULL, current_step = ?, started_at = NULL, finished_at = NULL
                   WHERE id = ?''',
                (json.dumps(payload or {}), str(current_step), int(run_id)),
            )
        changed = c.rowcount
        conn.commit()
        conn.close()
        return changed == 1

    def append_job_run_log(self, run_id, level, message):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            '''INSERT INTO job_run_logs (run_id, level, message, created_at)
               VALUES (?, ?, ?, ?)''',
            (int(run_id), str(level), str(message), datetime.datetime.now().isoformat()),
        )
        log_id = c.lastrowid
        conn.commit()
        conn.close()
        return int(log_id)

    def list_job_run_logs(self, run_id, limit=500):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            '''SELECT id, run_id, level, message, created_at
               FROM job_run_logs
               WHERE run_id = ?
               ORDER BY id DESC
               LIMIT ?''',
            (int(run_id), int(limit)),
        )
        rows = c.fetchall()
        conn.close()
        return [
            {
                "id": int(row[0]),
                "run_id": int(row[1]),
                "level": row[2],
                "message": row[3],
                "created_at": row[4],
            }
            for row in rows
        ]
