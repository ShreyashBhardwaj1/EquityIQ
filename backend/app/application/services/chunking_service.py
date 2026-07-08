"""
Application service for segmenting document text pages into semantic chunks.
"""

import os
import re
from datetime import datetime
from uuid import uuid5

from app.domain.entities.document import Document
from app.domain.entities.document_chunk import ChunkMetadata, DocumentChunk
from app.infrastructure.parsers.pdf_parser import PARSER_VERSION

# Common SEC/financial report section header regex patterns
SECTION_HEADER_PATTERNS = [
    re.compile(r"^\s*Item\s+\d+[A-Z]?[\.\s:]", re.IGNORECASE),
    re.compile(r"^\s*Note\s+\d+[\.\s:]", re.IGNORECASE),
    re.compile(r"^\s*Part\s+[I|V|X\d]+[\.\s:]", re.IGNORECASE),
    re.compile(
        r"^\s*(Management\'s\s+Discussion\s+and\s+Analysis|Financial\s+Statements|Controls\s+and\s+Procedures|Risk\s+Factors|Legal\s+Proceedings)\b",
        re.IGNORECASE,
    ),
]


class ChunkingService:
    """
    Splits raw parsed pages of text into semantic chunks with metadata annotations.
    """

    def __init__(self, chunk_size: int, overlap: int) -> None:
        """
        Initializes the ChunkingService with configurable bounds.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _is_section_header(self, text: str) -> bool:
        """
        Returns True if the line matches common financial report section heading formats.
        """
        line = text.strip()
        if not line or len(line) > 120:
            return False
        return any(pattern.match(line) for pattern in SECTION_HEADER_PATTERNS)

    def chunk_document(
        self,
        document: Document,
        pages_content: list[str],
        document_version: int = 1,
        parse_version: int = 1,
        statement_type: str | None = None,
    ) -> list[DocumentChunk]:
        """
        Splits raw pages content into a list of structured and annotated DocumentChunk entities.

        Purpose:
            Takes raw pages of text and splits them into paragraphs/sentences based on configured size and overlap
            bounds, while identifying section headers and attaching comprehensive audit metadata.

        Inputs:
            document: Associated Document domain model.
            pages_content: List of text content per page.
            document_version: The version index of the uploaded file.
            parse_version: The version index of the parser execution attempt.
            statement_type: Optional categorization of statement type.

        Outputs:
            A list of validated DocumentChunk domain entities.

        Failure Behavior:
            Returns an empty list if pages_content is empty or null.
        """
        chunks: list[DocumentChunk] = []
        chunk_idx = 0
        current_section: str | None = None

        for page_idx, page_text in enumerate(pages_content):
            page_num = page_idx + 1
            # Split page text into paragraphs
            paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]

            current_chunk_paragraphs: list[str] = []
            current_len = 0

            for para in paragraphs:
                # Detect and update current active section header
                first_line = para.split("\n")[0]
                if self._is_section_header(first_line):
                    current_section = first_line.strip()[:100]  # Cap length of heading

                para_len = len(para)

                # If a single paragraph is larger than the max chunk size, we must force-split it by sentences
                if para_len > self.chunk_size:
                    # Flush current chunk buffer first
                    if current_chunk_paragraphs:
                        chunks.append(
                            self._create_chunk_entity(
                                document=document,
                                paragraphs=current_chunk_paragraphs,
                                page_number=page_num,
                                chunk_index=chunk_idx,
                                section_heading=current_section,
                                document_version=document_version,
                                parse_version=parse_version,
                                statement_type=statement_type,
                            )
                        )
                        chunk_idx += 1
                        current_chunk_paragraphs = []
                        current_len = 0

                    # Force split paragraph by sentences
                    sentences = [s.strip() for s in para.split(". ") if s.strip()]
                    sub_paragraphs: list[str] = []
                    sub_len = 0
                    for sentence in sentences:
                        s_text = sentence + "."
                        s_len = len(s_text)
                        if sub_len + s_len > self.chunk_size:
                            if sub_paragraphs:
                                chunks.append(
                                    self._create_chunk_entity(
                                        document=document,
                                        paragraphs=sub_paragraphs,
                                        page_number=page_num,
                                        chunk_index=chunk_idx,
                                        section_heading=current_section,
                                        document_version=document_version,
                                        parse_version=parse_version,
                                        statement_type=statement_type,
                                    )
                                )
                                chunk_idx += 1
                                # Apply overlap for sentences
                                overlap_sentences: list[str] = []
                                overlap_len = 0
                                for osent in reversed(sub_paragraphs):
                                    if overlap_len + len(osent) <= self.overlap:
                                        overlap_sentences.insert(0, osent)
                                        overlap_len += len(osent)
                                    else:
                                        break
                                sub_paragraphs = overlap_sentences
                                sub_len = overlap_len
                            sub_paragraphs.append(s_text)
                            sub_len += s_len
                        else:
                            sub_paragraphs.append(s_text)
                            sub_len += s_len
                    if sub_paragraphs:
                        current_chunk_paragraphs = sub_paragraphs
                        current_len = sub_len
                    continue

                # Normal paragraph accumulation
                if current_len + para_len > self.chunk_size:
                    # Flush current chunk
                    chunks.append(
                        self._create_chunk_entity(
                            document=document,
                            paragraphs=current_chunk_paragraphs,
                            page_number=page_num,
                            chunk_index=chunk_idx,
                            section_heading=current_section,
                            document_version=document_version,
                            parse_version=parse_version,
                            statement_type=statement_type,
                        )
                    )
                    chunk_idx += 1

                    # Keep last paragraphs for overlap
                    overlap_paragraphs: list[str] = []
                    overlap_len = 0
                    for op in reversed(current_chunk_paragraphs):
                        if overlap_len + len(op) <= self.overlap:
                            overlap_paragraphs.insert(0, op)
                            overlap_len += len(op)
                        else:
                            break
                    current_chunk_paragraphs = overlap_paragraphs
                    current_len = overlap_len

                current_chunk_paragraphs.append(para)
                current_len += para_len

            # Flush remaining paragraphs of the page
            if current_chunk_paragraphs:
                chunks.append(
                    self._create_chunk_entity(
                        document=document,
                        paragraphs=current_chunk_paragraphs,
                        page_number=page_num,
                        chunk_index=chunk_idx,
                        section_heading=current_section,
                        document_version=document_version,
                        parse_version=parse_version,
                        statement_type=statement_type,
                    )
                )
                chunk_idx += 1

        return chunks

    def _create_chunk_entity(
        self,
        document: Document,
        paragraphs: list[str],
        page_number: int,
        chunk_index: int,
        section_heading: str | None,
        document_version: int,
        parse_version: int,
        statement_type: str | None,
    ) -> DocumentChunk:
        """
        Assembles a validated DocumentChunk and ChunkMetadata model.
        """
        content = "\n\n".join(paragraphs).strip()
        metadata = ChunkMetadata(
            workspace_id=document.workspace_id,
            company_id=document.company_id,
            document_id=document.id,
            statement_type=statement_type,
            document_type=document.doc_type.value,
            fiscal_year=document.fiscal_period.year,
            fiscal_period=document.fiscal_period.period,
            page_number=page_number,
            chunk_index=chunk_index,
            section_heading=section_heading,
            source_file=os.path.basename(document.storage_path),
            parser_version=PARSER_VERSION,
            document_version=document_version,
            parse_version=parse_version,
            created_at=datetime.utcnow(),
        )
        return DocumentChunk(
            id=uuid5(document.id, f"chunk_{chunk_index}"),
            document_id=document.id,
            content=content,
            page_number=page_number,
            chunk_index=chunk_index,
            section_heading=section_heading,
            metadata=metadata,
        )
