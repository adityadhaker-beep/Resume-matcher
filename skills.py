
import re

SKILLS = {
    "python": ["python"],
    "java": ["java"],
    "c++": ["c++", "cpp"],
    "sql": ["sql", "structured query language"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "dl"],
    "natural language processing": ["natural language processing", "nlp"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch", "torch"],
    "transformers": ["transformers", "hugging face"],
    "spacy": ["spacy", "spaCy"],
    "nltk": ["nltk"],
    "data analysis": ["data analysis", "data analytics"],
    "data visualization": ["data visualization", "data visualisation"],
    "statistics": ["statistics", "statistical analysis"],
    "regression": ["regression", "linear regression"],
    "classification": ["classification"],
    "neural networks": ["neural networks", "neural network"],
    "computer vision": ["computer vision"],
    "sql databases": ["mysql", "postgresql", "postgres", "sqlite"],
    "mongodb": ["mongodb", "mongo db"],
    "git": ["git", "github"],
    "docker": ["docker"],
    "streamlit": ["streamlit"],
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "rest api": ["rest api", "restful api"],
    "aws": ["aws", "amazon web services"],
}


def extract_skills(text):
    """Extract known skills using case-insensitive whole-word matching."""
    text = text.lower()
    found = set()

    for skill, aliases in SKILLS.items():
        for alias in aliases:
            pattern = r"(?<!\w)" + re.escape(alias.lower()) + r"(?!\w)"
            if re.search(pattern, text):
                found.add(skill)
                break

    return sorted(found)
