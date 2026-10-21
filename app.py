
from io import BytesIO

import streamlit as st
from pypdf import PdfReader

from matcher import compare_resume_to_job


st.set_page_config(
    page_title="HireLens | Resume Matcher",
    page_icon="🎯",
    layout="wide"
)


def extract_pdf_text(uploaded_file):
    """Extract text from an uploaded PDF resume."""
    reader = PdfReader(BytesIO(uploaded_file.getvalue()))

    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")

    text = "\n".join(pages).strip()

    if not text:
        raise ValueError(
            "No readable text was found. "
            "This may be a scanned PDF requiring OCR."
        )

    return text


st.title("🎯 HireLens")
st.subheader("Understand how your resume matches a job description")
st.write(
    "Compare relevant skills and textual similarity using "
    "transparent NLP techniques."
)

st.info(
    "This tool provides an indicative comparison, not a hiring "
    "decision or a prediction of interview success."
)

left, right = st.columns(2)

with left:
    st.markdown("### 1. Your resume")
    input_method = st.radio(
        "Resume input method",
        ["Upload PDF", "Paste text"],
        horizontal=True
    )

    resume_text = ""

    if input_method == "Upload PDF":
        resume_file = st.file_uploader(
            "Upload a text-based PDF resume",
            type=["pdf"]
        )

        if resume_file is not None:
            try:
                resume_text = extract_pdf_text(resume_file)
                st.success("Resume text extracted successfully.")
                with st.expander("Preview extracted text"):
                    st.text(resume_text[:5000])
            except Exception as error:
                st.error(f"Could not read the PDF: {error}")
    else:
        resume_text = st.text_area(
            "Paste your resume",
            height=300,
            placeholder=(
                "Paste your education, skills, projects, "
                "and experience here..."
            )
        )

with right:
    st.markdown("### 2. Job description")

    job_text = st.text_area(
        "Paste the complete job description",
        height=300,
        placeholder=(
            "Paste the responsibilities, qualifications, "
            "and required skills from the job posting..."
        )
    )

analyze = st.button(
    "Analyze Match",
    type="primary",
    use_container_width=True
)

if analyze:
    if not resume_text.strip() or not job_text.strip():
        st.warning(
            "Please provide both a resume and a job description."
        )
    else:
        try:
            result = compare_resume_to_job(resume_text, job_text)

            st.divider()
            st.header("Analysis results")

            col1, col2 = st.columns(2)

            col1.metric(
                "Text similarity",
                f"{result['similarity']:.1%}"
            )

            coverage = result["skill_coverage"]

            if coverage is not None:
                col2.metric(
                    "Detected skill coverage",
                    f"{coverage:.1%}"
                )
            else:
                col2.metric("Detected skill coverage", "N/A")

            st.caption(
                "Text similarity compares TF-IDF representations. "
                "Skill coverage compares detected skills only. "
                "Neither score measures employability."
            )

            st.subheader("Skill comparison")

            matched_col, missing_col = st.columns(2)

            with matched_col:
                st.markdown("#### ✅ Matched skills")
                if result["matched_skills"]:
                    for skill in result["matched_skills"]:
                        st.write(f"• {skill}")
                else:
                    st.write("No matching skills detected.")

            with missing_col:
                st.markdown("#### 📌 Skills not detected")
                if result["missing_skills"]:
                    for skill in result["missing_skills"]:
                        st.write(f"• {skill}")
                else:
                    st.write(
                        "No missing skills detected from "
                        "the current dictionary."
                    )

            with st.expander("View all detected skills"):
                st.write("**Resume:**")
                st.write(", ".join(result["resume_skills"]) or "None")
                st.write("**Job description:**")
                st.write(", ".join(result["job_skills"]) or "None")
                st.write("**Additional resume skills:**")
                st.write(", ".join(result["extra_skills"]) or "None")

        except ValueError as error:
            st.warning(str(error))
        except Exception as error:
            st.error(f"Analysis failed: {error}")

st.divider()
st.caption(
    "HireLens | Educational NLP portfolio project | "
    "TF-IDF + cosine similarity + rule-based skill extraction"
)
