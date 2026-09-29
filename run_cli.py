"""Command-line demo:  python run_cli.py sample/sample_resume.txt  (PDF/DOCX/TXT)"""
import sys

from src import database as db
from src.analyzer import analyze_resume_file


def main(path):
    db.init_db()
    db.seed_jobs_if_empty()
    with open(path, "rb") as f:
        out = analyze_resume_file(f.read(), path.split("/")[-1])

    line = "-" * 38
    print(f"{line}\n       RESUME ANALYZER\n{line}\n")
    print(f"Candidate: {out['name'] or 'Unknown'}\n")
    print("Skills Found:")
    for s in out["skills"]:
        print(f"  ✓ {s}")
    print(f"\nRecommended Category: {out['recommended_category']}\n")
    print("Recommended Jobs:")
    for i, r in enumerate(out["results"][:5], 1):
        print(f"\n{i}. {r['job_title']} @ {r['company']}\n   Match: {r['match_percentage']:.0f}%")
        if r["missing_skills"]:
            print(f"   Missing: {', '.join(r['missing_skills'])}")
    print("\nSkills to learn next:")
    for s in out["skills_to_learn"]:
        print(f"  • {s}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
