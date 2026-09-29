PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS candidates (
    candidate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT,
    email        TEXT,
    resume_file  TEXT,
    resume_text  TEXT,
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS candidate_skills (
    candidate_id INTEGER NOT NULL,
    skill_id     INTEGER NOT NULL,
    PRIMARY KEY (candidate_id, skill_id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id)     REFERENCES skills(skill_id)
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    job_title   TEXT NOT NULL,
    company     TEXT,
    category    TEXT,
    description TEXT,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id   INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    PRIMARY KEY (job_id, skill_id),
    FOREIGN KEY (job_id)   REFERENCES jobs(job_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
);

CREATE TABLE IF NOT EXISTS job_matches (
    match_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id     INTEGER NOT NULL,
    job_id           INTEGER NOT NULL,
    match_percentage REAL NOT NULL,
    skill_score      REAL,
    text_score       REAL,
    matched_skills   TEXT,
    missing_skills   TEXT,
    matched_at       TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    FOREIGN KEY (job_id)       REFERENCES jobs(job_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_matches_candidate ON job_matches(candidate_id);
CREATE INDEX IF NOT EXISTS idx_matches_job       ON job_matches(job_id);
