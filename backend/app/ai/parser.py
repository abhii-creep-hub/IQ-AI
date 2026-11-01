import io
import logging
import re
from datetime import datetime
from typing import Optional

import fitz
import pdfplumber
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_content: bytes) -> str:
    text = ""

    # ---------- METHOD 1 : PyMuPDF ----------
    try:
        logger.info("========== PyMuPDF Extraction Started ==========")

        doc = fitz.open(stream=file_content, filetype="pdf")

        logger.info(f"Total Pages: {len(doc)}")

        for i, page in enumerate(doc):
            page_text = page.get_text()

            logger.info(f"Page {i+1}: Extracted {len(page_text)} characters")

            if page_text:
                text += page_text + "\n"

        doc.close()

        logger.info(f"Total Extracted Characters: {len(text)}")

        if text.strip():
            logger.info("========== PyMuPDF Extraction Successful ==========")
            return text.strip()

        logger.warning("PyMuPDF extracted ZERO text.")

    except Exception:
        logger.exception("PyMuPDF extraction failed")

    # ---------- METHOD 2 : pdfplumber ----------
    try:
        logger.info("========== pdfplumber Extraction Started ==========")

        with pdfplumber.open(io.BytesIO(file_content)) as pdf:

            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()

                if page_text:
                    logger.info(f"Page {i+1}: Extracted {len(page_text)} characters")
                    text += page_text + "\n"

        if text.strip():
            logger.info("========== pdfplumber Extraction Successful ==========")
            return text.strip()

        logger.warning("pdfplumber extracted ZERO text.")

    except Exception:
        logger.exception("pdfplumber extraction failed")

    # ---------- METHOD 3 : OCR (Scanned PDF) ----------
    try:
        logger.info("========== OCR Extraction Started ==========")

        doc = fitz.open(stream=file_content, filetype="pdf")

        ocr_text = ""

        for i, page in enumerate(doc):

            pix = page.get_pixmap(dpi=300)

            img = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples,
            )

            page_text = pytesseract.image_to_string(img, lang="eng")

            logger.info(f"OCR Page {i+1}: {len(page_text)} characters")

            ocr_text += page_text + "\n"

        doc.close()

        logger.info(f"OCR Total Characters: {len(ocr_text)}")

        return ocr_text.strip()

    except Exception:
        logger.exception("OCR extraction failed")
        return ""


def _extract_text_with_pdfplumber(file_content: bytes) -> str:
    try:
        import pdfplumber

        logger.info("========== pdfplumber Extraction Started ==========")

        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            text = ""

            logger.info(f"Total Pages: {len(pdf.pages)}")

            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()

                if page_text:
                    logger.info(f"Page {i + 1}: Extracted {len(page_text)} characters")
                    text += page_text + "\n"
                else:
                    logger.warning(f"Page {i + 1}: No text found")

            logger.info(f"Total Extracted Characters: {len(text)}")

            if not text.strip():
                logger.error("pdfplumber also extracted ZERO text")

            logger.info("========== pdfplumber Extraction Finished ==========")

            return text.strip()

    except Exception:
        logger.exception("pdfplumber extraction failed")
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
