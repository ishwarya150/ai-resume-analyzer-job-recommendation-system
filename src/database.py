"""SQLite persistence layer."""
import csv
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .skills import canonical, extract_skills

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("RESUME_DB", ROOT / "data" / "resume_analyzer.db"))
SCHEMA_PATH = ROOT / "schema.sql"
JOBS_CSV = ROOT / "data" / "sample_jobs.csv"


@contextmanager
def connect(db_path=None):
    conn = sqlite3.connect(str(db_path or DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path=None):
    with connect(db_path) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def _skill_id(conn, name):
    name = canonical(name)
    conn.execute("INSERT OR IGNORE INTO skills (skill_name) VALUES (?)", (name,))
    return conn.execute("SELECT skill_id FROM skills WHERE skill_name = ?", (name,)).fetchone()[0]


# ---------- jobs ----------
def add_job(title, company, category, description, skills=None, db_path=None):
    """Insert a job. If `skills` is None the skills are extracted from the description."""
    if skills is None:
        skills = extract_skills(description)
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO jobs (job_title, company, category, description) VALUES (?,?,?,?)",
            (title, company, category, description),
        )
        job_id = cur.lastrowid
        for s in skills:
            conn.execute("INSERT OR IGNORE INTO job_skills VALUES (?,?)", (job_id, _skill_id(conn, s)))
    return job_id


def seed_jobs_if_empty(db_path=None):
    with connect(db_path) as conn:
        if conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] > 0:
            return 0
    if not JOBS_CSV.exists():
        return 0
    n = 0
    with open(JOBS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            skills = [s.strip() for s in row["required_skills"].split(";") if s.strip()]
            add_job(row["job_title"], row["company"], row["category"], row["description"], skills, db_path)
            n += 1
    return n


def get_jobs(exclude_category=None, db_path=None):
    """All jobs with their skills as a list. Optionally hide one category (e.g. 'Custom')."""
    where, params = "", ()
    if exclude_category:
        where, params = "WHERE COALESCE(j.category,'') != ?", (exclude_category,)
    q = f"""SELECT j.job_id, j.job_title, j.company, j.category, j.description,
                   COALESCE(GROUP_CONCAT(s.skill_name, '||'), '') AS skills
            FROM jobs j
            LEFT JOIN job_skills js ON js.job_id = j.job_id
            LEFT JOIN skills s ON s.skill_id = js.skill_id
            {where}
            GROUP BY j.job_id ORDER BY j.job_id"""
    with connect(db_path) as conn:
        rows = conn.execute(q, params).fetchall()
    return [{**dict(r), "skills": [x for x in r["skills"].split("||") if x]} for r in rows]


def delete_job(job_id, db_path=None):
    with connect(db_path) as conn:
        conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))


# ---------- candidates ----------
def save_candidate(name, email, resume_file, resume_text, skills, db_path=None):
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO candidates (name, email, resume_file, resume_text) VALUES (?,?,?,?)",
            (name, email, resume_file, resume_text),
        )
        cid = cur.lastrowid
        for s in skills:
            conn.execute("INSERT OR IGNORE INTO candidate_skills VALUES (?,?)", (cid, _skill_id(conn, s)))
    return cid


def save_matches(candidate_id, results, db_path=None):
    with connect(db_path) as conn:
        conn.executemany(
            """INSERT INTO job_matches
               (candidate_id, job_id, match_percentage, skill_score, text_score, matched_skills, missing_skills)
               VALUES (?,?,?,?,?,?,?)""",
            [
                (candidate_id, r["job_id"], r["match_percentage"], r["skill_score"], r["text_score"],
                 ", ".join(r["matched_skills"]), ", ".join(r["missing_skills"]))
                for r in results
            ],
        )


def get_candidates(db_path=None):
    with connect(db_path) as conn:
        return [dict(r) for r in conn.execute(
            """SELECT c.candidate_id, c.name, c.email, c.resume_file, c.created_at,
                      COUNT(cs.skill_id) AS skill_count
               FROM candidates c LEFT JOIN candidate_skills cs ON cs.candidate_id = c.candidate_id
               GROUP BY c.candidate_id ORDER BY c.candidate_id DESC""")]


def get_history(candidate_id=None, db_path=None):
    where, params = "", ()
    if candidate_id:
        where, params = "WHERE m.candidate_id = ?", (candidate_id,)
    q = f"""SELECT m.match_id, m.candidate_id, c.name AS candidate, j.job_title, j.company, j.category,
                   m.match_percentage, m.skill_score, m.text_score, m.matched_skills, m.missing_skills,
                   m.matched_at
            FROM job_matches m
            JOIN candidates c ON c.candidate_id = m.candidate_id
            JOIN jobs j ON j.job_id = m.job_id
            {where} ORDER BY m.matched_at DESC, m.match_percentage DESC"""
    with connect(db_path) as conn:
        return [dict(r) for r in conn.execute(q, params).fetchall()]


def delete_candidate(candidate_id, db_path=None):
    with connect(db_path) as conn:
        conn.execute("DELETE FROM candidates WHERE candidate_id = ?", (candidate_id,))
