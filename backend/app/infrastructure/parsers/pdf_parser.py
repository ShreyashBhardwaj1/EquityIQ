"""
Layout-aware PDF parsing adapter utilizing pdfplumber and graceful OCR fallback.
"""

import logging
import os
import time

import pdfplumber

try:
    import pytesseract

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger("equityiq.pdf_parser")

PARSER_VERSION = "1.0.0"


class PDFParserResult:
    """
    Result container returning parsed pages and collection metrics.
    """

    def __init__(
        self,
        pages_content: list[str],
        table_count: int,
        warnings: list[str],
        extraction_confidence: float,
        parse_duration: float,
    ) -> None:
        self.pages_content = pages_content
        self.table_count = table_count
        self.warnings = warnings
        self.extraction_confidence = extraction_confidence
        self.parse_duration = parse_duration


class PDFParser:
    """
    Parses PDF documents page-by-page, extracts layout text and tables, and converts tables to Markdown.
    """

    def __init__(self, tesseract_cmd: str | None = None) -> None:
        """
        Initializes PDFParser, optionall configuring custom pytesseract command path.
        """
        self.tesseract_cmd = tesseract_cmd
        if TESSERACT_AVAILABLE and tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def _convert_table_to_markdown(self, table: list[list[str | None]]) -> str:
        """
        Converts a list-of-lists table extraction into a Markdown-formatted table.
        """
        if not table or not any(cell is not None for row in table for cell in row):
            return ""

        # Find maximum columns width across rows
        col_count = max(len(row) for row in table)
        cleaned_rows: list[list[str]] = []

        for row in table:
            # Pad row if short
            padded = list(row) + [None] * (col_count - len(row))
            # Clean cells (remove newlines and escape pipes)
            cleaned_cells = []
            for cell in padded:
                if cell is None:
                    cleaned_cells.append("")
                else:
                    val = str(cell).replace("\n", " ").replace("|", "\\|").strip()
                    cleaned_cells.append(val)
            cleaned_rows.append(cleaned_cells)

        # Build markdown lines
        lines = []
        # Header row
        header = cleaned_rows[0]
        lines.append("| " + " | ".join(header) + " |")
        # Separator row
        lines.append("| " + " | ".join(["---"] * col_count) + " |")
        # Data rows
        for r in cleaned_rows[1:]:
            lines.append("| " + " | ".join(r) + " |")

        return "\n".join(lines) + "\n"

    def parse(self, file_path: str) -> PDFParserResult:
        """
        Parses a PDF or plain text document on disk, extracting native text layout and formatting tables.

        Purpose:
            Extracts native text page-by-page. If characters are sparse, triggers Tesseract OCR fallback.
            Converts any structured tables to Markdown tables. If the document is plain text or is corrupt,
            falls back to raw text extraction.

        Inputs:
            file_path: The absolute filesystem path to the document file.

        Outputs:
            A PDFParserResult object carrying pages content list and extraction metrics.

        Failure Behavior:
            Raises FileNotFoundError if the file does not exist on disk.
            Raises RuntimeError if PDF opening/parsing fails and plain text fallback fails as well.
        """
        start_time = time.time()
        pages_content: list[str] = []
        table_count = 0
        warnings: list[str] = []
        confidence_scores: list[float] = []

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at path: {file_path}")

        try:
            if not file_path.lower().endswith(".pdf"):
                raise ValueError("Not a PDF file extension.")

            with pdfplumber.open(file_path) as pdf:
                for idx, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    page_tables = page.extract_tables() or []

                    # Convert and count tables
                    md_tables = []
                    for table in page_tables:
                        md_table = self._convert_table_to_markdown(table)
                        if md_table:
                            md_tables.append(md_table)
                            table_count += 1

                    # Combine page text and markdown tables
                    combined = page_text.strip()
                    if md_tables:
                        combined += "\n\n### Extracted Tables\n\n" + "\n".join(
                            md_tables
                        )

                    # If page text yield is extremely low and OCR fallback is possible
                    if len(page_text.strip()) < settings.MIN_NATIVE_TEXT_LENGTH:
                        ocr_text = ""
                        if TESSERACT_AVAILABLE:
                            try:
                                # Convert page to image
                                page_img = page.to_image(resolution=150)
                                pil_img = page_img.original
                                ocr_text = pytesseract.image_to_string(pil_img) or ""
                                confidence_scores.append(
                                    settings.OCR_CONFIDENCE_THRESHOLD
                                )  # Moderate confidence estimate for OCR fallback
                            except Exception as e:
                                warning_msg = (
                                    f"Page {idx + 1} OCR fallback failed: {e!s}"
                                )
                                warnings.append(warning_msg)
                                logger.warning(warning_msg)
                                confidence_scores.append(0.0)
                        else:
                            warning_msg = f"Page {idx + 1} has minimal text, and pytesseract/OCR is unavailable."
                            warnings.append(warning_msg)
                            logger.warning(warning_msg)
                            confidence_scores.append(0.0)

                        if ocr_text.strip():
                            # Merge OCR text with any tables
                            combined = ocr_text.strip()
                            if md_tables:
                                combined += "\n\n### Extracted Tables\n\n" + "\n".join(
                                    md_tables
                                )
                    else:
                        confidence_scores.append(
                            1.0
                        )  # Native PDF text is high-confidence

                    pages_content.append(combined)

        except Exception as e:
            # Fallback to plain text read
            try:
                with open(file_path, encoding="utf-8") as f:
                    text = f.read()
                warnings.append(f"PDF parsing fallback triggered: {e!s}")
                pages_content = [text]
                confidence_scores = [0.8]  # Reduced confidence for fallback
            except Exception as read_err:
                raise RuntimeError(
                    f"Failed to parse PDF and raw text fallback failed: {read_err!s}"
                ) from e

        duration = time.time() - start_time
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores
            else 1.0
        )

        return PDFParserResult(
            pages_content=pages_content,
            table_count=table_count,
            warnings=warnings,
            extraction_confidence=avg_confidence,
            parse_duration=duration,
        )
