"""
Unit tests for PDFParser.
"""

from unittest.mock import MagicMock, patch

from app.infrastructure.parsers.pdf_parser import PDFParser


def test_convert_table_to_markdown():
    parser = PDFParser()
    table = [
        ["Header 1", "Header 2"],
        ["Row 1 Col 1", "Row 1 Col 2"],
        ["Row 2 Col 1", "Row 2 Col 2"],
    ]

    expected = (
        "| Header 1 | Header 2 |\n"
        "| --- | --- |\n"
        "| Row 1 Col 1 | Row 1 Col 2 |\n"
        "| Row 2 Col 1 | Row 2 Col 2 |\n"
    )

    result = parser._convert_table_to_markdown(table)
    assert result == expected


def test_convert_empty_table_to_markdown():
    parser = PDFParser()
    assert parser._convert_table_to_markdown([]) == ""
    assert parser._convert_table_to_markdown([[None, None]]) == ""


@patch("pdfplumber.open")
@patch("os.path.exists")
def test_parse_pdf_file_layout_success(mock_exists, mock_pdf_open):
    mock_exists.return_value = True

    # Setup mock page
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Page 1 main text content. " * 3
    mock_page.extract_tables.return_value = [[["Metric", "Val"], ["Revenue", "100"]]]

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    # Enter context manager
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf

    parser = PDFParser()
    result = parser.parse("dummy.pdf")

    assert len(result.pages_content) == 1
    assert "Page 1 main text content." in result.pages_content[0]
    assert "### Extracted Tables" in result.pages_content[0]
    assert "| Revenue | 100 |" in result.pages_content[0]
    assert result.table_count == 1
    assert result.extraction_confidence == 1.0
