"""Skill catalog and skill extraction (rule-based NLP with alias handling)."""
import re

# Display name -> list of alternative spellings / aliases (all lowercase).
# Ambiguous one-letter skills (R, C, Go) only match via unambiguous aliases.
SKILLS = {
    # Programming languages
    "Python": ["python", "python3"],
    "Java": ["java"],
    "JavaScript": ["javascript", "js", "ecmascript"],
    "TypeScript": ["typescript"],
    "C++": ["c++"],
    "C#": ["c#", "c sharp"],
    "C": ["c programming", "c language"],
    "Go": ["golang", "go lang"],
    "R": ["r programming", "rstudio", "r language"],
    "PHP": ["php"],
    "Kotlin": ["kotlin"],
    "Swift": ["swift programming", "swiftui"],
    "Scala": ["scala"],
    "Bash": ["bash", "shell scripting", "shell script"],
    # Databases / SQL
    "SQL": ["sql", "structured query language"],
    "MySQL": ["mysql"],
    "PostgreSQL": ["postgresql", "postgres"],
    "SQLite": ["sqlite", "sqlite3"],
    "SQL Server": ["sql server", "mssql", "t-sql", "tsql"],
    "Oracle": ["oracle db", "oracle database", "pl/sql", "plsql"],
    "MongoDB": ["mongodb", "mongo db"],
    "DBMS": ["dbms", "database management system", "database management systems"],
    "NoSQL": ["nosql"],
    "Redis": ["redis"],
    # Data / BI
    "Excel": ["excel", "microsoft excel", "ms excel", "advanced excel"],
    "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"],
    "Looker": ["looker", "looker studio"],
    "Data Analysis": ["data analysis", "data analytics", "analyzing data", "analysing data"],
    "Data Visualization": ["data visualization", "data visualisation", "dashboards", "dashboarding"],
    "Data Cleaning": ["data cleaning", "data cleansing", "data wrangling", "data preprocessing"],
    "ETL": ["etl", "elt", "data pipeline", "data pipelines"],
    "Statistics": ["statistics", "statistical analysis", "statistical modeling", "hypothesis testing"],
    "A/B Testing": ["a/b testing", "ab testing", "a/b test"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Matplotlib": ["matplotlib"],
    "Seaborn": ["seaborn"],
    "Plotly": ["plotly"],
    "Google Analytics": ["google analytics"],
    "Data Warehousing": ["data warehouse", "data warehousing", "data warehouses"],
    "Snowflake": ["snowflake"],
    "BigQuery": ["bigquery"],
    "Apache Spark": ["spark", "pyspark", "apache spark"],
    "Hadoop": ["hadoop"],
    "Airflow": ["airflow"],
    "Kafka": ["kafka"],
    # ML / AI
    "Machine Learning": ["machine learning", "ml models", "predictive modeling", "predictive modelling"],
    "Deep Learning": ["deep learning", "neural network", "neural networks"],
    "NLP": ["nlp", "natural language processing", "text mining"],
    "Computer Vision": ["computer vision", "image processing", "opencv"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "Keras": ["keras"],
    "spaCy": ["spacy"],
    "NLTK": ["nltk"],
    "Hugging Face": ["hugging face", "huggingface", "transformers library"],
    "LLMs": ["llm", "llms", "large language model", "large language models", "generative ai", "gen ai"],
    "Feature Engineering": ["feature engineering"],
    "MLOps": ["mlops"],
    # Web / backend
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3"],
    "React": ["react", "reactjs", "react.js"],
    "Angular": ["angular", "angularjs"],
    "Vue.js": ["vue", "vuejs", "vue.js"],
    "Node.js": ["node.js", "nodejs", "node js"],
    "Express": ["express.js", "expressjs"],
    "Django": ["django"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi"],
    "Spring Boot": ["spring boot", "springboot", "spring framework"],
    "REST APIs": ["rest api", "rest apis", "restful api", "restful apis", "restful", "api development"],
    "GraphQL": ["graphql"],
    "Streamlit": ["streamlit"],
    "Bootstrap": ["bootstrap"],
    "Tailwind CSS": ["tailwind", "tailwind css"],
    # DevOps / cloud
    "Git": ["git"],
    "GitHub": ["github"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure", "microsoft azure"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "CI/CD": ["ci/cd", "cicd", "continuous integration", "jenkins", "github actions"],
    "Linux": ["linux", "unix"],
    "Terraform": ["terraform"],
    "Networking": ["networking", "tcp/ip"],
    # Testing / QA
    "Selenium": ["selenium"],
    "Manual Testing": ["manual testing"],
    "Test Automation": ["test automation", "automation testing", "automated testing"],
    "PyTest": ["pytest"],
    "JUnit": ["junit"],
    "Postman": ["postman"],
    "JIRA": ["jira"],
    # CS fundamentals
    "Data Structures": ["data structures", "data structure"],
    "Algorithms": ["algorithms", "algorithm design"],
    "OOP": ["oop", "oops", "object oriented", "object-oriented"],
    "System Design": ["system design"],
    "Agile": ["agile", "scrum", "kanban"],
    "Microservices": ["microservices", "microservice"],
    # Soft / business
    "Communication": ["communication skills", "communication", "presentation skills"],
    "Problem Solving": ["problem solving", "problem-solving", "analytical skills", "analytical thinking"],
    "Teamwork": ["teamwork", "team player", "collaboration", "collaborative"],
    "Leadership": ["leadership", "team lead", "team leadership"],
    "Project Management": ["project management", "project manager"],
    "Stakeholder Management": ["stakeholder management", "stakeholder communication"],
    "Business Analysis": ["business analysis", "business analyst", "requirement gathering", "requirements gathering"],
    "Critical Thinking": ["critical thinking"],
    # Misc tools
    "Figma": ["figma"],
    "UI/UX": ["ui/ux", "ux design", "ui design", "user experience", "user interface design"],
    "Jupyter": ["jupyter", "jupyter notebook", "jupyter notebooks"],
    "VS Code": ["vs code", "vscode", "visual studio code"],
    "SAP": ["sap"],
    "Salesforce": ["salesforce"],
    "Google Sheets": ["google sheets"],
    "VBA": ["vba", "macros"],
}

_LOOKUP = {name.lower(): name for name in SKILLS}


def _build_patterns():
    patterns = {}
    for display, aliases in SKILLS.items():
        terms = {display.lower(), *aliases}
        # Single-letter / ambiguous names are not matched by their bare name.
        if display in {"R", "C", "Go"}:
            terms = set(aliases)
        alt = "|".join(re.escape(t).replace(r"\ ", r"\s+") for t in sorted(terms, key=len, reverse=True))
        # Boundary that treats + # as part of a token (c++, c#)
        patterns[display] = re.compile(rf"(?<![A-Za-z0-9+#]){alt}(?![A-Za-z0-9+#])", re.IGNORECASE)
    return patterns


_PATTERNS = _build_patterns()


def extract_skills(text: str) -> list:
    """Return a sorted list of canonical skill names found in `text`."""
    if not text:
        return []
    flat = re.sub(r"\s+", " ", text)
    found = [name for name, pat in _PATTERNS.items() if pat.search(flat)]
    return sorted(found, key=str.lower)


def canonical(skill: str) -> str:
    """Normalise a user-typed skill to the catalog display name (or keep as typed)."""
    s = skill.strip()
    return _LOOKUP.get(s.lower(), s)
