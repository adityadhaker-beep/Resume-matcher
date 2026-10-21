import re
from io import BytesIO

import streamlit as st
from pypdf import PdfReader

from matcher import compare_resume_to_job
from skills import SKILLS


st.set_page_config(
    page_title="HireLens — Intelligent Resume Matcher",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Custom Styling (CSS)
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Hero Banner */
    .hero-container {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #2563eb 100%);
        padding: 2.2rem 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.25);
    }
    .hero-pill {
        display: inline-block;
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(8px);
        padding: 0.35rem 0.85rem;
        border-radius: 50px;
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 0.75rem;
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.2;
        color: #ffffff;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: rgba(255, 255, 255, 0.9);
        margin-top: 0.5rem;
        max-width: 780px;
    }

    /* Input & Section Cards */
    .panel-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.5rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        margin-bottom: 1.2rem;
    }
    .panel-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .panel-caption {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 1rem;
    }

    /* Metric Cards */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.4rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
    }
    .kpi-value {
        font-size: 2.3rem;
        font-weight: 800;
        line-height: 1.1;
        margin: 0.3rem 0;
    }
    .kpi-label {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
    }
    .kpi-subtext {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-top: 0.3rem;
    }

    /* Skill Badge Chips */
    .chip-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0.75rem 0 1.25rem 0;
    }
    .chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.35rem 0.8rem;
        border-radius: 9999px;
        font-size: 0.84rem;
        font-weight: 600;
        line-height: 1;
        transition: transform 0.15s ease;
    }
    .chip:hover {
        transform: scale(1.04);
    }
    .chip-matched {
        background-color: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }
    .chip-missing {
        background-color: #fff1f2;
        color: #9f1239;
        border: 1px solid #fecdd3;
    }
    .chip-extra {
        background-color: #f5f3ff;
        color: #5b21b6;
        border: 1px solid #ddd6fe;
    }

    /* Verdict Alert Banner */
    .verdict-banner {
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin: 1.5rem 0;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .verdict-high {
        background-color: #ecfdf5;
        border: 1px solid #10b981;
        color: #064e3b;
    }
    .verdict-medium {
        background-color: #fffbeb;
        border: 1px solid #f59e0b;
        color: #78350f;
    }
    .verdict-low {
        background-color: #fef2f2;
        border: 1px solid #ef4444;
        color: #7f1d1d;
    }

    /* Quick stat counters */
    .word-badge {
        display: inline-block;
        font-size: 0.75rem;
        background: #f1f5f9;
        color: #475569;
        padding: 0.2rem 0.55rem;
        border-radius: 6px;
        font-weight: 500;
    }

    /* Button Enhancements */
    div.stButton > button:first-child {
        border-radius: 10px;
        font-weight: 600;
        font-size: 1.05rem;
        padding: 0.65rem 1.2rem;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Helper Functions & Sample Demos
# ---------------------------------------------------------
def extract_pdf_text(uploaded_file):
    """Extract text from an uploaded PDF resume."""
    reader = PdfReader(BytesIO(uploaded_file.getvalue()))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    text = "\n".join(pages).strip()
    if not text:
        raise ValueError(
            "No readable text was found. This may be a scanned image PDF requiring OCR."
        )
    return text


SAMPLE_RESUMES = {
    "ML Engineer": """Alex Mercer
alex.mercer@email.com | github.com/alexmercer | linkedin.com/in/alexmercer

SUMMARY
Machine Learning Engineer with 4+ years of experience designing, training, and deploying end-to-end deep learning and NLP models. Proficient in Python, PyTorch, Scikit-learn, and cloud deployments.

TECHNICAL SKILLS
Languages & Core: Python, SQL, C++, Git, Docker
Frameworks & ML: PyTorch, TensorFlow, Scikit-learn, Pandas, NumPy, Hugging Face Transformers, NLTK, Spacy
Domains: Machine Learning, Deep Learning, Natural Language Processing, Computer Vision, Data Analysis, Statistics
Deployment & Cloud: FastAPI, Docker, AWS, REST API, Streamlit

EXPERIENCE
Machine Learning Engineer | AI Solutions Corp (2022 - Present)
- Built NLP summarization and classification pipelines using Transformers and PyTorch, improving document processing latency by 35%.
- Fine-tuned Scikit-learn and LightGBM models for tabular predictive classification, achieving 92% ROC-AUC.
- Implemented automated REST APIs using FastAPI and deployed on AWS ECS with Docker.
- Orchestrated SQL queries and PostgreSQL database pipelines for data preprocessing and analysis.

Data Scientist | FinTech Labs (2020 - 2022)
- Built regression and classification models in Python using Pandas, NumPy, and Scikit-learn to detect financial anomalies.
- Designed interactive analytics dashboards with Streamlit for executive stakeholders.
- Collaborated using Git for version control and continuous integration.

EDUCATION
B.S. in Computer Science | University of Technology (2016 - 2020)
""",
    "Full-Stack Developer": """Samantha Lee
samantha.lee@email.com | github.com/samlee | linkedin.com/in/samlee

SUMMARY
Full-Stack Software Engineer with 3 years experience building scalable web applications, microservices, and databases.

TECHNICAL SKILLS
Programming: Python, Java, SQL, C++
Web & APIs: FastAPI, Flask, REST API, Streamlit
Databases & Cloud: PostgreSQL, MySQL, MongoDB, Docker, Git, AWS
Fundamentals: Data Analysis, Object-Oriented Programming, Unit Testing

EXPERIENCE
Software Engineer | CloudScale Inc. (2023 - Present)
- Developed secure REST APIs with FastAPI and Python, handling 20,000 requests/minute.
- Optimized relational database queries in PostgreSQL and MySQL, reducing latency by 40%.
- Containerized microservices using Docker and deployed on AWS.
- Managed version control workflows through Git and GitHub Actions.

Junior Web Developer | Innovate Soft (2021 - 2023)
- Built back-end services with Flask and MongoDB.
- Created internal data visualization tools using Python and Streamlit.
"""
}

SAMPLE_JOBS = {
    "ML Engineer": """Senior Machine Learning Engineer
Location: Remote / Hybrid

About the Role:
We are seeking an experienced Machine Learning Engineer to drive next-generation AI and NLP capabilities across our enterprise platform.

Key Responsibilities:
- Design, build, and deploy production-grade Machine Learning and Deep Learning models.
- Develop NLP pipelines utilizing Transformers, Spacy, and PyTorch.
- Conduct statistical data analysis, regression, and classification modeling.
- Build resilient REST APIs with FastAPI and containerize services with Docker.
- Write clean, maintainable Python code and collaborate using Git.
- Work closely with AWS cloud infrastructure and SQL databases.

Required Qualifications:
- 3+ years experience with Python, PyTorch, and Scikit-learn.
- Strong background in Natural Language Processing (NLP), Deep Learning, and Machine Learning.
- Hands-on experience with Pandas, NumPy, and SQL databases (PostgreSQL / MySQL).
- Proficiency with Docker, FastAPI, and AWS deployments.
- Bachelor's or Master's degree in Computer Science, Data Science, or related field.
""",
    "Full-Stack Developer": """Full Stack Python & Cloud Developer
Location: San Francisco, CA (or Remote)

Responsibilities:
- Build high-concurrency microservices and REST APIs using Python, FastAPI, or Flask.
- Manage relational and NoSQL databases including PostgreSQL and MongoDB.
- Containerize applications using Docker and deploy to AWS infrastructure.
- Implement automated testing and collaborate using Git and CI/CD pipelines.

Requirements:
- 2+ years of professional backend development with Python.
- Proven experience with REST API architecture, FastAPI or Flask.
- Strong proficiency in SQL, MongoDB, and Docker.
- Experience with AWS cloud services.
"""
}


# Initialize Session State
if "resume_input" not in st.session_state:
    st.session_state.resume_input = ""
if "job_input" not in st.session_state:
    st.session_state.job_input = ""


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------
with st.sidebar:
    st.image(
        "https://api.iconify.design/lucide:target.svg?color=%234f46e5&width=48",
        width=48
    )
    st.markdown("## **HireLens Studio**")
    st.markdown(
        "AI-assisted resume and job description alignment evaluator."
    )
    st.divider()

    st.markdown("### ⚡ Quick-Load Demo")
    st.caption("Try pre-loaded industry samples with one click:")

    col_demo1, col_demo2 = st.columns(2)
    with col_demo1:
        if st.button("🤖 ML Engineer", use_container_width=True):
            st.session_state.resume_input = SAMPLE_RESUMES["ML Engineer"]
            st.session_state.job_input = SAMPLE_JOBS["ML Engineer"]
            st.rerun()

    with col_demo2:
        if st.button("🌐 Full Stack", use_container_width=True):
            st.session_state.resume_input = SAMPLE_RESUMES["Full-Stack Developer"]
            st.session_state.job_input = SAMPLE_JOBS["Full-Stack Developer"]
            st.rerun()

    if st.button("🔄 Clear Inputs", use_container_width=True):
        st.session_state.resume_input = ""
        st.session_state.job_input = ""
        st.rerun()

    st.divider()

    st.markdown("### 📊 Skill Taxonomy")
    total_tax_skills = len(SKILLS)
    st.markdown(
        f"Tracks **{total_tax_skills}+** verified tech skills across "
        "Python, Cloud, Data Science, AI/ML, and Web frameworks."
    )

    with st.expander("🔍 View Tracked Skills"):
        st.write(", ".join(sorted(SKILLS.keys())))

    st.divider()
    st.markdown("### 💡 Tips for Better Scores")
    st.markdown(
        "- Use standard job title and skill phrasing.\n"
        "- Highlight concrete technologies in experience bullets.\n"
        "- Ensure PDF resumes are text-selectable (not scanned images)."
    )

    st.caption("v1.2.0 • Deployed on Render")


# ---------------------------------------------------------
# Main Header / Hero
# ---------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-pill">⚡ Transparent NLP Analysis</div>
    <h1 class="hero-title">HireLens Resume Matcher</h1>
    <p class="hero-subtitle">
        Evaluate your resume's relevance against any job posting in seconds. 
        Get transparent TF-IDF semantic similarity scores and instant skill gap detection.
    </p>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Input Section (Two Panels)
# ---------------------------------------------------------
left_col, right_col = st.columns(2, gap="large")

with left_col:
    st.markdown("""
    <div class="panel-header">
        📄 1. Candidate Resume
    </div>
    <div class="panel-caption">Upload your PDF resume or paste raw text directly.</div>
    """, unsafe_allow_html=True)

    input_mode = st.radio(
        "Input Format",
        ["Paste Text", "Upload PDF"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if input_mode == "Upload PDF":
        pdf_file = st.file_uploader(
            "Select text-based PDF resume",
            type=["pdf"],
            help="PDF should be text-searchable (not a scanned image)."
        )
        if pdf_file is not None:
            try:
                extracted = extract_pdf_text(pdf_file)
                st.session_state.resume_input = extracted
                st.success("✅ PDF text extracted successfully!")
                with st.expander("👁️ Preview Extracted PDF Text", expanded=False):
                    st.text(extracted[:3000] + ("..." if len(extracted) > 3000 else ""))
            except Exception as exc:
                st.error(f"Error reading PDF: {exc}")

    # Text area for resume
    resume_text = st.text_area(
        "Resume Content",
        value=st.session_state.resume_input,
        height=320,
        placeholder="Paste your resume sections (Skills, Experience, Education, Projects)...",
        key="resume_textarea"
    )
    # Sync manual edits back to state
    st.session_state.resume_input = resume_text

    word_count_resume = len(re.findall(r"\w+", resume_text))
    st.markdown(f"<span class='word-badge'>📝 {word_count_resume} words detected</span>", unsafe_allow_html=True)


with right_col:
    st.markdown("""
    <div class="panel-header">
        🎯 2. Target Job Description
    </div>
    <div class="panel-caption">Paste the complete job requirements, qualifications & responsibilities.</div>
    """, unsafe_allow_html=True)

    job_text = st.text_area(
        "Job Description Content",
        value=st.session_state.job_input,
        height=362,
        placeholder="Paste the target job description here...",
        key="job_textarea"
    )
    st.session_state.job_input = job_text

    word_count_job = len(re.findall(r"\w+", job_text))
    st.markdown(f"<span class='word-badge'>📌 {word_count_job} words detected</span>", unsafe_allow_html=True)


# ---------------------------------------------------------
# Action Button
# ---------------------------------------------------------
st.write("")
analyze_btn = st.button("🚀 Analyze Alignment & Skill Match", type="primary", use_container_width=True)


# ---------------------------------------------------------
# Results Processing & Visualizations
# ---------------------------------------------------------
if analyze_btn:
    if not resume_text.strip() or not job_text.strip():
        st.warning("⚠️ Please provide both a Resume and a Job Description before analyzing.")
    else:
        with st.spinner("Analyzing semantic similarity and extracting skill taxonomy..."):
            try:
                result = compare_resume_to_job(resume_text, job_text)

                sim_pct = result["similarity"] * 100
                coverage_val = result["skill_coverage"]
                cov_pct = (coverage_val * 100) if coverage_val is not None else 0.0

                matched_count = len(result["matched_skills"])
                missing_count = len(result["missing_skills"])
                extra_count = len(result["extra_skills"])
                total_job_skills = len(result["job_skills"])

                st.markdown("<hr style='margin: 2rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                st.markdown("## 📊 Analysis Dashboard")

                # Verdict Banner
                if sim_pct >= 65 and cov_pct >= 60:
                    verdict_class = "verdict-high"
                    verdict_title = "🌟 Strong Alignment"
                    verdict_desc = "Your resume demonstrates high semantic overlap and covers the majority of core technical skills required by this role."
                elif sim_pct >= 40 or cov_pct >= 40:
                    verdict_class = "verdict-medium"
                    verdict_title = "⚡ Moderate Alignment"
                    verdict_desc = "Your background is relevant, but adding key missing terms and aligning project phrasing with the job description will improve match quality."
                else:
                    verdict_class = "verdict-low"
                    verdict_title = "📌 Potential Skill Gap"
                    verdict_desc = "There is relatively low textual and skill overlap. Review the missing skill tags below to tailor your resume if you have relevant experience."

                st.markdown(f"""
                <div class="verdict-banner {verdict_class}">
                    <div style="font-size: 2rem;">{"✅" if "Strong" in verdict_title else "⚠️" if "Moderate" in verdict_title else "🔍"}</div>
                    <div>
                        <div style="font-weight: 700; font-size: 1.15rem;">{verdict_title}</div>
                        <div style="font-size: 0.95rem; margin-top: 0.2rem;">{verdict_desc}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # KPI Metrics Cards
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)

                with kpi1:
                    sim_color = "#10b981" if sim_pct >= 60 else "#f59e0b" if sim_pct >= 40 else "#ef4444"
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Text Similarity</div>
                        <div class="kpi-value" style="color: {sim_color};">{sim_pct:.1f}%</div>
                        <div class="kpi-subtext">TF-IDF & Cosine Metric</div>
                    </div>
                    """, unsafe_allow_html=True)

                with kpi2:
                    cov_display = f"{cov_pct:.1f}%" if coverage_val is not None else "N/A"
                    cov_color = "#10b981" if cov_pct >= 60 else "#f59e0b" if cov_pct >= 40 else "#ef4444"
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Skill Coverage</div>
                        <div class="kpi-value" style="color: {cov_color};">{cov_display}</div>
                        <div class="kpi-subtext">{matched_count} of {total_job_skills} required skills</div>
                    </div>
                    """, unsafe_allow_html=True)

                with kpi3:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Matched Skills</div>
                        <div class="kpi-value" style="color: #4f46e5;">{matched_count}</div>
                        <div class="kpi-subtext">Verified in both documents</div>
                    </div>
                    """, unsafe_allow_html=True)

                with kpi4:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Skills to Address</div>
                        <div class="kpi-value" style="color: #e11d48;">{missing_count}</div>
                        <div class="kpi-subtext">Missing from job criteria</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.write("")

                # Tabs for detailed views
                tab_skills, tab_tips, tab_details = st.tabs([
                    "🎯 Skill Gap Breakdown",
                    "💡 Tailoring Recommendations",
                    "🔍 Extracted Data & Taxonomy"
                ])

                with tab_skills:
                    col_m, col_u = st.columns(2)

                    with col_m:
                        st.markdown("#### ✅ Matched Skills In Resume")
                        st.caption("Skills found in the job description that also appear in your resume.")
                        if result["matched_skills"]:
                            chips_html = "".join([
                                f'<span class="chip chip-matched">✓ {skill.title()}</span>'
                                for skill in result["matched_skills"]
                            ])
                            st.markdown(f'<div class="chip-container">{chips_html}</div>', unsafe_allow_html=True)
                        else:
                            st.info("No overlapping skills detected based on the current skill dictionary.")

                        st.markdown("#### ➕ Additional Skills Found in Resume")
                        st.caption("Skills in your resume not explicitly requested in this job posting.")
                        if result["extra_skills"]:
                            chips_extra_html = "".join([
                                f'<span class="chip chip-extra">★ {skill.title()}</span>'
                                for skill in result["extra_skills"]
                            ])
                            st.markdown(f'<div class="chip-container">{chips_extra_html}</div>', unsafe_allow_html=True)
                        else:
                            st.write("No additional skills detected.")

                    with col_u:
                        st.markdown("#### 📌 Missing Skills Mentioned in Job")
                        st.caption("Skills prioritized in the job posting that were not detected in your resume.")
                        if result["missing_skills"]:
                            chips_missing_html = "".join([
                                f'<span class="chip chip-missing">✕ {skill.title()}</span>'
                                for skill in result["missing_skills"]
                            ])
                            st.markdown(f'<div class="chip-container">{chips_missing_html}</div>', unsafe_allow_html=True)
                            st.info(
                                "💡 **ATS Tip:** If you have experience with any of these missing skills, "
                                "make sure to explicitly include them in your resume bullet points."
                            )
                        else:
                            st.success("🎉 Outstanding! Your resume covers all detected skills requested by the job description.")

                with tab_tips:
                    st.markdown("### 📋 Actionable Steps to Improve Your Resume")
                    rec_cols = st.columns(3)
                    with rec_cols[0]:
                        st.markdown("##### 1. Incorporate Missing Keywords")
                        if result["missing_skills"]:
                            sample_missing = ", ".join([s.title() for s in result["missing_skills"][:4]])
                            st.write(
                                f"Add concrete project achievements mentioning skills like **{sample_missing}** "
                                "if you have prior experience with them."
                            )
                        else:
                            st.write("Your technical keyword density matches the job requirements nicely.")

                    with rec_cols[1]:
                        st.markdown("##### 2. Emphasize Context & Impact")
                        st.write(
                            "Rather than just listing keywords in a skills section, demonstrate their use: "
                            "*'Deployed scalable REST API using FastAPI and Docker on AWS with 99.9% uptime.'*"
                        )

                    with rec_cols[2]:
                        st.markdown("##### 3. ATS Formatting Advice")
                        st.write(
                            "Avoid multi-column tables, text boxes, or non-standard fonts. "
                            "ATS parsers read best with clean headings and standard bullet points."
                        )

                with tab_details:
                    st.markdown("#### Normalized Extracted Content")
                    col_raw1, col_raw2 = st.columns(2)
                    with col_raw1:
                        st.markdown("**All Skills Detected in Resume:**")
                        st.write(", ".join([s.title() for s in result["resume_skills"]]) or "None detected")
                    with col_raw2:
                        st.markdown("**All Skills Detected in Job Description:**")
                        st.write(", ".join([s.title() for s in result["job_skills"]]) or "None detected")

            except ValueError as ve:
                st.warning(f"Input validation notice: {ve}")
            except Exception as err:
                st.error(f"Analysis failed: {err}")

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("<hr style='margin-top: 3rem; margin-bottom: 1rem; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 0.85rem; padding-bottom: 2rem;">
    🎯 <strong>HireLens</strong> — Transparent NLP Resume Matcher • Built with Streamlit, Scikit-learn & TF-IDF • Ready for Render
</div>
""", unsafe_allow_html=True)
