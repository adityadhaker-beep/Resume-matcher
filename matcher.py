
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from skills import extract_skills


def clean_text(text):
    """Normalize whitespace without deleting useful technical terms."""
    return re.sub(r"\s+", " ", text).strip()


def compare_resume_to_job(resume_text, job_text):
    resume_text = clean_text(resume_text)
    job_text = clean_text(job_text)

    if not resume_text or not job_text:
        raise ValueError(
            "Both the resume and job description must contain text."
        )

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True
    )

    vectors = vectorizer.fit_transform([resume_text, job_text])

    similarity = float(
        cosine_similarity(vectors[0], vectors[1])[0, 0]
    )

    resume_skills = set(extract_skills(resume_text))
    job_skills = set(extract_skills(job_text))

    matched_skills = sorted(resume_skills & job_skills)
    missing_skills = sorted(job_skills - resume_skills)
    extra_skills = sorted(resume_skills - job_skills)

    if job_skills:
        skill_coverage = len(matched_skills) / len(job_skills)
    else:
        skill_coverage = None

    return {
        "similarity": similarity,
        "skill_coverage": skill_coverage,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "extra_skills": extra_skills,
        "resume_skills": sorted(resume_skills),
        "job_skills": sorted(job_skills),
    }
