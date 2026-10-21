
from matcher import compare_resume_to_job, clean_text


def test_clean_text():
    assert clean_text("Python   and\nSQL") == "Python and SQL"


def test_matching_skills():
    resume = "Python, pandas, and machine learning"
    job = "Python, machine learning, and PyTorch"

    result = compare_resume_to_job(resume, job)

    assert "python" in result["matched_skills"]
    assert "machine learning" in result["matched_skills"]
    assert "pytorch" in result["missing_skills"]


def test_identical_documents():
    text = "Python machine learning data analysis"

    result = compare_resume_to_job(text, text)

    assert abs(result["similarity"] - 1.0) < 1e-9


def test_empty_input():
    try:
        compare_resume_to_job("", "Python developer")
        assert False, "Expected ValueError"
    except ValueError:
        pass
