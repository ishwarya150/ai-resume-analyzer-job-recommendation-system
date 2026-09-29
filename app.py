"""AI Resume Analyzer & Job Recommendation System - Streamlit UI.
Run:  streamlit run app.py
"""
import pandas as pd
import streamlit as st

from src import database as db
from src.analyzer import analyze_resume_file
from src.resume_parser import extract_email, extract_text, guess_name
from src.skills import extract_skills

st.set_page_config(page_title="AI Resume Analyzer", page_icon="🤖", layout="wide")
db.init_db()
db.seed_jobs_if_empty()

st.sidebar.title("🤖 Resume Analyzer")
page = st.sidebar.radio("Navigate", ["Analyze Resume", "Job Board", "History"])
st.sidebar.caption("Python · NLP · SQL · Streamlit")


def score_color(p):
    return "🟢" if p >= 70 else "🟡" if p >= 45 else "🔴"


# ------------------------------------------------------------------ Analyze
if page == "Analyze Resume":
    st.title("Resume Analyzer & Job Recommendations")
    st.write("Upload a resume (PDF, DOCX or TXT). Optionally paste a job description to compare against.")

    file = st.file_uploader("Resume", type=["pdf", "docx", "txt"])
    col1, col2 = st.columns(2)
    with st.expander("➕ Compare against a specific job description (optional)"):
        jt = st.text_input("Job title", placeholder="e.g. Reporting Analyst")
        jc = st.text_input("Company", placeholder="e.g. Acme Corp")
        jd = st.text_area("Job description", height=180)

    if file is not None:
        raw = file.getvalue()
        try:
            preview_text = extract_text(raw, file.name)
        except Exception as e:  # corrupt / encrypted PDF etc.
            st.error(f"Could not read this file: {e}")
            st.stop()
        if len(preview_text) < 30:
            st.warning("Very little text was extracted. If this is a scanned PDF, use a text-based one.")
        name = col1.text_input("Candidate name", value=guess_name(preview_text))
        email = col2.text_input("Email", value=extract_email(preview_text))
        top_n = st.slider("Jobs to show", 3, 15, 5)

        if st.button("🔍 Analyze", type="primary"):
            custom = {"title": jt, "company": jc, "description": jd} if jd.strip() else None
            with st.spinner("Analyzing..."):
                out = analyze_resume_file(raw, file.name, name=name, email=email, custom_job=custom)
            st.session_state["out"] = out
            st.session_state["top_n"] = top_n

    out = st.session_state.get("out")
    if out:
        st.divider()
        st.subheader(f"Candidate: {out['name'] or 'Unknown'}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Skills found", len(out["skills"]))
        m2.metric("Best match", f"{out['results'][0]['match_percentage']:.0f}%" if out["results"] else "-")
        m3.metric("Recommended category", out["recommended_category"] or "-")

        st.markdown("**Skills found**")
        st.write("  ".join(f"`✓ {s}`" for s in out["skills"]) or "No known skills detected.")

        if out["custom_result"]:
            r = out["custom_result"]
            st.markdown(f"### 🎯 Your pasted job: {r['job_title']} — {score_color(r['match_percentage'])} {r['match_percentage']:.0f}%")
            st.progress(min(r["match_percentage"] / 100, 1.0))
            c1, c2 = st.columns(2)
            c1.success("Matched: " + (", ".join(r["matched_skills"]) or "none"))
            c2.error("Missing: " + (", ".join(r["missing_skills"]) or "none 🎉"))

        st.markdown("### Recommended jobs")
        for i, r in enumerate(out["results"][: st.session_state.get("top_n", 5)], 1):
            with st.expander(f"{i}. {r['job_title']} @ {r['company']} — {score_color(r['match_percentage'])} {r['match_percentage']:.0f}%", expanded=i == 1):
                st.progress(min(r["match_percentage"] / 100, 1.0))
                st.caption(f"Category: {r['category']} · Skill score {r['skill_score']:.0f}% · Text similarity {r['text_score']:.0f}%")
                c1, c2 = st.columns(2)
                c1.success("Matched: " + (", ".join(r["matched_skills"]) or "none"))
                c2.error("Missing: " + (", ".join(r["missing_skills"]) or "none 🎉"))

        if out["skills_to_learn"]:
            st.markdown("### 📚 Skills to learn next")
            st.write("Most often missing across your best-matching jobs:")
            st.write("  ".join(f"`{s}`" for s in out["skills_to_learn"]))

        st.download_button("⬇️ Download results (CSV)",
                           pd.DataFrame(out["results"]).assign(
                               matched_skills=lambda d: d.matched_skills.apply(", ".join),
                               missing_skills=lambda d: d.missing_skills.apply(", ".join)).to_csv(index=False),
                           file_name="job_matches.csv", mime="text/csv")

# ---------------------------------------------------------------- Job board
elif page == "Job Board":
    st.title("Job Board")
    jobs = db.get_jobs(exclude_category="Custom")
    df = pd.DataFrame([{**j, "skills": ", ".join(j["skills"]), "description": j["description"][:90] + "…"} for j in jobs])
    st.dataframe(df.drop(columns=[]), use_container_width=True, hide_index=True)

    st.subheader("Add a job")
    with st.form("add_job", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        title = c1.text_input("Job title")
        company = c2.text_input("Company")
        category = c3.text_input("Category", value="General")
        desc = st.text_area("Job description", height=150)
        manual = st.text_input("Required skills (comma separated) — leave empty to auto-extract from description")
        if st.form_submit_button("Add job"):
            if not title or not desc:
                st.error("Title and description are required.")
            else:
                skills = [s.strip() for s in manual.split(",") if s.strip()] or extract_skills(desc)
                db.add_job(title, company, category, desc, skills)
                st.success(f"Added '{title}' with skills: {', '.join(skills) or 'none detected'}")
                st.rerun()

    st.subheader("Remove a job")
    if jobs:
        choice = st.selectbox("Job", jobs, format_func=lambda j: f"{j['job_title']} @ {j['company']}")
        if st.button("🗑️ Delete selected job"):
            db.delete_job(choice["job_id"])
            st.rerun()

# ------------------------------------------------------------------ History
else:
    st.title("Analysis History")
    cands = db.get_candidates()
    if not cands:
        st.info("No analyses yet. Upload a resume on the first page.")
    else:
        st.dataframe(pd.DataFrame(cands), use_container_width=True, hide_index=True)
        pick = st.selectbox("View matches for", [None] + cands,
                            format_func=lambda c: "All candidates" if c is None else
                            f"#{c['candidate_id']} {c['name'] or 'Unknown'} — {c['created_at']}")
        hist = db.get_history(pick["candidate_id"] if pick else None)
        if hist:
            h = pd.DataFrame(hist)
            st.dataframe(h.drop(columns=["match_id", "candidate_id"]), use_container_width=True, hide_index=True)
            st.markdown("**Top matches**")
            st.bar_chart(h.sort_values("match_percentage", ascending=False).head(10).set_index("job_title")["match_percentage"])
        if pick and st.button("🗑️ Delete this candidate and their matches"):
            db.delete_candidate(pick["candidate_id"])
            st.rerun()
