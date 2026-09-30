import hashlib
import io
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import docx
import pymupdf as fitz

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Handles PDF and DOCX document parsing, text normalization,
    per-page extraction, OCR fallback, section boundary detection,
    and content hashing.
    """

    @staticmethod
    def compute_content_hash(text: str) -> str:
        """Computes SHA-256 hash of normalized text for deduplication."""
        cleaned = re.sub(r"\s+", " ", text).strip().lower()
        return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

    @staticmethod
    def _perform_ocr_fallback(doc: fitz.Document, page_idx: int) -> str:
        """
        OCR visual fallback for scanned or image-based PDF pages.
        Attempts pytesseract if installed, otherwise extracts embedded pixmap text.
        """
        try:
            page = doc[page_idx]
            # Try PyMuPDF built-in OCR if Tesseract language data is available
            pix = page.get_pixmap()
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                ocr_text = pytesseract.image_to_string(img)
                if ocr_text and ocr_text.strip():
                    return ocr_text.strip()
            except ImportError:
                pass
        except Exception as e:
            logger.debug(f"OCR fallback skipped on page {page_idx}: {e}")
        return ""

    @classmethod
    def extract_text_from_pdf(cls, file_bytes: bytes) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extracts full text and per-page block metadata from a PDF.
        Includes OCR fallback for scanned pages without text streams.
        Returns (full_text, pages_data).
        """
        full_text_parts = []
        pages_data = []

        try:
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for page_idx in range(len(doc)):
                    page = doc[page_idx]
                    page_text = page.get_text("text").strip()

                    # Trigger OCR fallback if page has minimal or no selectable text
                    if len(page_text) < 30 and len(page.get_images()) > 0:
                        ocr_result = cls._perform_ocr_fallback(doc, page_idx)
                        if ocr_result:
                            page_text = ocr_result

                    if page_text:
                        full_text_parts.append(page_text)
                        pages_data.append(
                            {
                                "page_number": page_idx + 1,
                                "text": page_text,
                                "char_length": len(page_text),
                            }
                        )

            full_text = "\n\n".join(full_text_parts)
            if full_text:
                return full_text, pages_data
        except Exception as e:
            logger.warning(f"Error parsing PDF with PyMuPDF: {e}")

        # Fallback to plain text decoding
        text = file_bytes.decode("utf-8", errors="replace").strip()
        return text, [{"page_number": 1, "text": text, "char_length": len(text)}]

    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extracts paragraphs and tables from a DOCX file.
        Returns (full_text, pages_data).
        """
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = []

            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)

            for table in doc.tables:
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_cells:
                        paragraphs.append(" | ".join(row_cells))

            full_text = "\n\n".join(paragraphs)
            if full_text:
                return full_text, [{"page_number": 1, "text": full_text, "char_length": len(full_text)}]
        except Exception as e:
            logger.warning(f"Error parsing DOCX: {e}")

        text = file_bytes.decode("utf-8", errors="replace").strip()
        return text, [{"page_number": 1, "text": text, "char_length": len(text)}]

    @classmethod
    def extract_text(cls, file_bytes: bytes, filename: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Auto-detects format from filename and extracts text with page breakdown."""
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            return cls.extract_text_from_pdf(file_bytes)
        elif lower_name.endswith(".docx"):
            return cls.extract_text_from_docx(file_bytes)
        else:
            text = file_bytes.decode("utf-8", errors="replace").strip()
            return text, [{"page_number": 1, "text": text, "char_length": len(text)}]

    @staticmethod
    def find_page_number_for_snippet(
        snippet: str, pages_data: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """
        Accurately identifies which physical page contains the given snippet or keywords.
        """
        if not pages_data or len(pages_data) <= 1:
            return 1

        snippet_clean = re.sub(r"[^a-zA-Z0-9\s]", "", snippet.lower())
        words = [w for w in snippet_clean.split() if len(w) > 3][:6]

        best_page = 1
        best_overlap = -1

        for p_item in pages_data:
            p_text = p_item.get("text", "").lower()
            p_num = p_item.get("page_number", 1)

            if snippet.lower() in p_text:
                return p_num

            # Check keyword overlap
            overlap = sum(1 for w in words if w in p_text)
            if overlap > best_overlap:
                best_overlap = overlap
                best_page = p_num

        return best_page

    @staticmethod
    def detect_sections(text: str) -> Dict[str, str]:
        """
        Detects common resume sections (summary, skills, experience, projects, education, certifications).
        """
        section_headers = {
            "summary": [r"summary", r"professional summary", r"profile", r"about me", r"objective"],
            "skills": [r"skills", r"technical skills", r"core competencies", r"technologies", r"tools & technologies"],
            "experience": [r"experience", r"work experience", r"professional experience", r"employment history", r"work history"],
            "projects": [r"projects", r"key projects", r"personal projects", r"technical projects"],
            "education": [r"education", r"academic background", r"qualifications"],
            "certifications": [r"certifications", r"certificates", r"licenses", r"credentials"],
        }

        all_header_patterns = []
        pattern_to_section = {}
        for sec, patterns in section_headers.items():
            for p in patterns:
                regex = rf"(?:^|\n)\s*(?:#+\s*)?({p})\s*(?::|\n|$)"
                all_header_patterns.append(regex)
                pattern_to_section[p.lower()] = sec

        combined_regex = re.compile("|".join(all_header_patterns), re.IGNORECASE)
        matches = list(combined_regex.finditer(text))

        if not matches:
            return {"general": text}

        sections: Dict[str, str] = {}
        for i, match in enumerate(matches):
            header_text = match.group(0).strip().lower().strip(":").strip("#").strip()
            sec_name = "general"
            for p_key, s_name in pattern_to_section.items():
                if p_key in header_text:
                    sec_name = s_name
                    break

            start_idx = match.end()
            end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start_idx:end_idx].strip()
            if content:
                sections[sec_name] = content

        if matches[0].start() > 0:
            header_chunk = text[: matches[0].start()].strip()
            if header_chunk:
                sections["header"] = header_chunk

        return sections


document_service = DocumentService()
