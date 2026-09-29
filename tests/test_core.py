import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import database as db  # noqa: E402
from src.analyzer import analyze_resume_text  # noqa: E402
from src.matcher import skill_overlap  # noqa: E402
from src.resume_parser import extract_email, guess_name  # noqa: E402
from src.skills import extract_skills  # noqa: E402

SAMPLE = (Path(__file__).resolve().parent.parent / "sample" / "sample_resume.txt").read_text()


def test_skill_extraction_basics():
    s = extract_skills("Worked with Python, SQL, C++, C#, Node.js and Power BI. Studied R programming.")
    for expected in ["Python", "SQL", "C++", "C#", "Node.js", "Power BI", "R"]:
        assert expected in s
    assert "Java" not in extract_skills("I love JavaScript")     # no substring false-positive
    assert "Go" not in extract_skills("Ready to go the extra mile")
    assert "C" not in extract_skills("C++ and C# only")


def test_skill_overlap_percentage():
    matched, missing, score = skill_overlap(["Python", "SQL", "Excel", "Power BI"],
                                            ["Python", "SQL", "Power BI", "Tableau"])
    assert matched == ["Power BI", "Python", "SQL"]
    assert missing == ["Tableau"]
    assert score == 75.0


def test_parser_helpers():
    assert extract_email(SAMPLE) == "ishwarya.raman@example.com"
    assert guess_name(SAMPLE) == "Ishwarya Raman"


def test_full_pipeline_and_history():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "t.db")
        db.init_db(path)
        assert db.seed_jobs_if_empty(path) >= 10
        out = analyze_resume_text(SAMPLE, "Ishwarya", "i@x.com", "r.txt", db_path=path,
                                  custom_job={"title": "Reporting Analyst", "company": "Acme",
                                              "description": "Needs SQL, Tableau and Excel."})
        assert out["results"][0]["match_percentage"] >= out["results"][-1]["match_percentage"]
        assert out["recommended_category"] in {"Data Analyst", "Business Intelligence", "Database"}
        assert out["custom_result"]["missing_skills"] == ["Tableau"]
        hist = db.get_history(out["candidate_id"], db_path=path)
        assert len(hist) == len(out["results"]) + 1
        db.delete_candidate(out["candidate_id"], db_path=path)
        assert db.get_history(db_path=path) == []
