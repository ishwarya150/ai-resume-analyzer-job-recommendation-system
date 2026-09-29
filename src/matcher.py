"""Job matching: skill overlap + TF-IDF cosine similarity."""
from collections import defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILL_WEIGHT = 0.8   # share of the final score coming from skill overlap
TEXT_WEIGHT = 0.2    # share coming from resume-vs-description text similarity


def text_similarity_scores(resume_text: str, descriptions: list) -> list:
    """Cosine similarity (0-100) between the resume and each job description."""
    if not descriptions or not resume_text.strip():
        return [0.0] * len(descriptions)
    docs = [resume_text] + [d or "" for d in descriptions]
    try:
        tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        matrix = tfidf.fit_transform(docs)
    except ValueError:  # empty vocabulary
        return [0.0] * len(descriptions)
    sims = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    # Raw cosine is small for long resumes; scale x2.5 and cap so it is comparable.
    return [round(min(float(s) * 2.5, 1.0) * 100, 1) for s in sims]


def skill_overlap(candidate_skills, job_skills):
    cand = {s.lower(): s for s in candidate_skills}
    req = {s.lower(): s for s in job_skills}
    matched = sorted((req[k] for k in req if k in cand), key=str.lower)
    missing = sorted((req[k] for k in req if k not in cand), key=str.lower)
    score = 100.0 * len(matched) / len(req) if req else 0.0
    return matched, missing, round(score, 1)


def rank_jobs(resume_text, candidate_skills, jobs, min_score=0.0):
    """Score every job. `jobs` = list of dicts with job_id, job_title, company,
    category, description, skills (list). Returns list sorted by match desc."""
    text_scores = text_similarity_scores(resume_text, [j["description"] for j in jobs])
    results = []
    for job, t_score in zip(jobs, text_scores):
        matched, missing, s_score = skill_overlap(candidate_skills, job["skills"])
        if job["skills"]:
            final = SKILL_WEIGHT * s_score + TEXT_WEIGHT * t_score
        else:
            final = t_score
        results.append({
            "job_id": job["job_id"],
            "job_title": job["job_title"],
            "company": job["company"],
            "category": job["category"],
            "match_percentage": round(final, 1),
            "skill_score": s_score,
            "text_score": t_score,
            "matched_skills": matched,
            "missing_skills": missing,
        })
    results = [r for r in results if r["match_percentage"] >= min_score]
    results.sort(key=lambda r: (-r["match_percentage"], r["job_title"]))
    return results


def recommend_category(results, top_n=5):
    """Category with the highest total score among the top-N matching jobs."""
    totals = defaultdict(float)
    for r in results[:top_n]:
        if r["category"]:
            totals[r["category"]] += r["match_percentage"]
    return max(totals, key=totals.get) if totals else None


def top_missing_skills(results, top_n=5, limit=8):
    """Skills most frequently missing across the best-matching jobs."""
    counts = defaultdict(int)
    for r in results[:top_n]:
        for s in r["missing_skills"]:
            counts[s] += 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))
    return [s for s, _ in ranked[:limit]]
