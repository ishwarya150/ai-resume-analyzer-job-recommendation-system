# 🤖 AI Resume Analyzer & Job Recommendation System

Upload a resume → extract text → detect skills with NLP → match against job descriptions →
get match %, missing skills, a recommended category and ranked jobs. Everything is stored in SQLite.

```
Resume (PDF/DOCX/TXT) → Text Extraction → Cleaning → Skill Extraction → Job Matching → Recommendations → SQL history
```

## Features
- Resume upload: PDF, DOCX, TXT (pypdf / python-docx)
- Automatic name + email detection
- Skill extraction: ~150-skill catalog with aliases (`sklearn`→scikit-learn, `postgres`→PostgreSQL, `c++`, `c#`, `node.js`) and boundary-safe regex (no "Java" inside "JavaScript")
- Job description input: paste any JD, skills are auto-extracted and matched
- Match score = **80% skill overlap + 20% TF-IDF cosine similarity** (resume vs job description)
- Matched / missing skills per job, plus "skills to learn next" across your top matches
- Recommended job category
- Job board: 15 seeded jobs, add / delete your own
- SQL database (SQLite, 6 tables) and history page with charts
- Streamlit web UI + CLI demo + unit tests

## Run it
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py                                    # web app
python run_cli.py sample/sample_resume.txt              # CLI demo
python -m pytest tests                                  # tests (pip install -r requirements-dev.txt)
```
The database is created automatically at `data/resume_analyzer.db`
(override with the `RESUME_DB` environment variable).

## Project structure
```
app.py                Streamlit UI (Analyze / Job Board / History)
run_cli.py            Terminal demo
schema.sql            Database schema
src/skills.py         Skill catalog + extraction
src/resume_parser.py  PDF/DOCX/TXT text extraction, email & name detection
src/matcher.py        Skill overlap, TF-IDF similarity, ranking, category, missing skills
src/database.py       SQLite access layer
src/analyzer.py       End-to-end pipeline
data/sample_jobs.csv  Seed jobs (edit freely)
sample/               Sample resume
tests/test_core.py    Unit tests
```

## Database schema
`candidates`, `skills`, `candidate_skills`, `jobs`, `job_skills`, `job_matches`
(see `schema.sql`; `job_matches` also stores skill score, text score, matched/missing skills and timestamp).

## How matching works
For each job: `skill_score = matched required skills / required skills × 100`;
`text_score = TF-IDF cosine(resume, description)` (scaled and capped at 100);
`match % = 0.8 × skill_score + 0.2 × text_score`. Tune the weights in `src/matcher.py`.

## Extending it (ideas for your portfolio write-up)
- Add skills to `SKILLS` in `src/skills.py`, or replace it with spaCy `PhraseMatcher` / a trained NER model
- Swap TF-IDF for sentence embeddings (`sentence-transformers`) for semantic matching
- Weight skills (must-have vs nice-to-have), add experience-years parsing
- Scrape/import real job postings, deploy on Streamlit Community Cloud
- OCR for scanned PDFs (`pytesseract`)

## Limitations
Scanned image-only PDFs have no extractable text; skill detection is catalog-based, so unlisted skills aren't detected.
