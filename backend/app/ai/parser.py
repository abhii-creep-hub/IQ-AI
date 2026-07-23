import io
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_content: bytes) -> str:
    try:
        import fitz
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text.strip()
    except Exception as e:
        logger.error(f"PyMuPDF extraction failed: {e}")
        return _extract_text_with_pdfplumber(file_content)


def _extract_text_with_pdfplumber(file_content: bytes) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
    except Exception as e:
        logger.error(f"pdfplumber extraction failed: {e}")
        return ""


def extract_text_from_docx(file_content: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " "
                text += "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        return ""


def extract_text(file_content: bytes, file_type: str) -> str:
    file_type = file_type.lower()
    if file_type == "pdf":
        return extract_text_from_pdf(file_content)
    elif file_type in ("docx", "doc"):
        return extract_text_from_docx(file_content)
    else:
        logger.error(f"Unsupported file type: {file_type}")
        return ""


def clean_resume_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s@.\-+/()#,&]', '', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()


def calculate_total_experience(experience_list: list[dict]) -> float:
    import re
    from datetime import datetime

    total_months = 0
    for exp in experience_list:
        start = exp.get("start_date", "")
        end = exp.get("end_date", "Present")
        if not start:
            continue
        try:
            start_date = _parse_date(start)
            if end.lower() == "present":
                end_date = datetime.now()
            else:
                end_date = _parse_date(end)
            months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            total_months += max(0, months)
        except Exception:
            continue
    return round(total_months / 12, 1) if total_months > 0 else 0.0


def _parse_date(date_str: str) -> datetime:
    from datetime import datetime
    date_str = date_str.strip()
    formats = ["%b %Y", "%B %Y", "%m/%Y", "%m-%Y", "%Y-%m-%d", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    year_match = re.search(r'(\d{4})', date_str)
    if year_match:
        return datetime(int(year_match.group(1)), 1, 1)
    raise ValueError(f"Cannot parse date: {date_str}")


def determine_rank(ats_score: float, match_score: float) -> str:
    avg = (ats_score + match_score) / 2
    if avg >= 80:
        return "gold"
    elif avg >= 65:
        return "silver"
    elif avg >= 50:
        return "bronze"
    elif avg >= 35:
        return "pending"
    else:
        return "rejected"
