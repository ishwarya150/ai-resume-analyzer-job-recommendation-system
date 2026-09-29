"""Resume text extraction (PDF / DOCX / TXT) and light cleaning."""
import io
import re


def extract_text(file_bytes: bytes, filename: str) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        text = _pdf_text(file_bytes)
    elif name.endswith(".docx"):
        text = _docx_text(file_bytes)
    else:
        text = file_bytes.decode("utf-8", errors="ignore")
    return clean_text(text)


def _pdf_text(file_bytes: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _docx_text(file_bytes: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            parts.extend(cell.text for cell in row.cells)
    return "\n".join(parts)


def clean_text(text: str) -> str:
    text = text.replace("\u2022", " ").replace("\u25cf", " ").replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_email(text: str) -> str:
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    return m.group(0) if m else ""


def guess_name(text: str) -> str:
    """Heuristic: first short line without digits/@ that looks like a name."""
    for line in text.splitlines():
        line = line.strip()
        if not line or len(line) > 40:
            continue
        if re.search(r"[\d@:/]", line):
            continue
        words = line.split()
        if 1 <= len(words) <= 4 and all(w[0].isalpha() for w in words):
            if line.lower() in {"resume", "curriculum vitae", "cv"}:
                continue
            return line.title() if line.isupper() else line
    return ""
