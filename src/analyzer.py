"""High-level pipeline tying parsing, extraction, matching and storage together."""
from . import database as db
from .matcher import rank_jobs, recommend_category, top_missing_skills
from .resume_parser import extract_email, extract_text, guess_name
from .skills import extract_skills


def analyze_resume_text(resume_text, name="", email="", resume_file="", save=True,
                        custom_job=None, min_score=0.0, db_path=None):
    """Run the full pipeline on already-extracted text.

    custom_job: optional dict(title, company, description) - a pasted job description
    that is stored (category 'Custom') and matched alongside the job board.
    """
    skills = extract_skills(resume_text)
    jobs = db.get_jobs(exclude_category="Custom", db_path=db_path)

    custom_id = None
    if custom_job and custom_job.get("description", "").strip():
        custom_id = db.add_job(custom_job.get("title") or "Custom Job",
                               custom_job.get("company") or "-", "Custom",
                               custom_job["description"], db_path=db_path)
        jobs = jobs + [j for j in db.get_jobs(db_path=db_path) if j["job_id"] == custom_id]

    results = rank_jobs(resume_text, skills, jobs, min_score=min_score)
    custom_result = next((r for r in results if r["job_id"] == custom_id), None) if custom_id else None
    board_results = [r for r in results if r["job_id"] != custom_id]

    candidate_id = None
    if save:
        candidate_id = db.save_candidate(name, email, resume_file, resume_text, skills, db_path)
        db.save_matches(candidate_id, results, db_path)

    return {
        "candidate_id": candidate_id,
        "name": name,
        "email": email,
        "skills": skills,
        "recommended_category": recommend_category(board_results),
        "results": board_results,
        "custom_result": custom_result,
        "skills_to_learn": top_missing_skills(board_results),
    }


def analyze_resume_file(file_bytes, filename, **kwargs):
    text = extract_text(file_bytes, filename)
    kwargs.setdefault("name", guess_name(text))
    kwargs.setdefault("email", extract_email(text))
    return analyze_resume_text(text, resume_file=filename, **kwargs)
