"""
Unit tests for MarkdownValidator service.
"""

import pytest

from app.application.services.report_markdown_validator import (
    MarkdownValidationError,
    MarkdownValidator,
)


class TestMarkdownValidator:
    @pytest.fixture
    def validator(self) -> MarkdownValidator:
        return MarkdownValidator()

    def test_valid_content_passes(self, validator: MarkdownValidator) -> None:
        content = "## Executive Summary\n\n" + "A" * 300
        validator.validate(content, "executive_summary")  # Should not raise

    def test_empty_content_raises(self, validator: MarkdownValidator) -> None:
        with pytest.raises(MarkdownValidationError, match="empty"):
            validator.validate("", "test_section")

    def test_whitespace_only_raises(self, validator: MarkdownValidator) -> None:
        with pytest.raises(MarkdownValidationError, match="empty"):
            validator.validate("   \n\n   ", "test_section")

    def test_content_too_short_raises(self, validator: MarkdownValidator) -> None:
        with pytest.raises(MarkdownValidationError, match="minimum"):
            validator.validate("Short content", "test_section")

    def test_placeholder_in_content_raises(self, validator: MarkdownValidator) -> None:
        content = "## Section\n\nThe company {company_name} has a score of " + "x" * 250
        with pytest.raises(MarkdownValidationError, match="placeholder"):
            validator.validate(content, "test_section")

    def test_unclosed_code_block_raises(self, validator: MarkdownValidator) -> None:
        content = "## Section\n\n```python\nsome code\n" + "content " * 30
        with pytest.raises(MarkdownValidationError, match="unclosed code block"):
            validator.validate(content, "test_section")

    def test_balanced_code_blocks_pass(self, validator: MarkdownValidator) -> None:
        content = "## Section\n\n```python\ncode\n```\n\n" + "content " * 30
        validator.validate(content, "test_section")  # Should not raise

    def test_multiple_placeholders_reported(self, validator: MarkdownValidator) -> None:
        content = (
            "## Section\n\n{company_name} had {fiscal_period} results. " + "x" * 200
        )
        with pytest.raises(MarkdownValidationError, match="placeholder"):
            validator.validate(content, "test_section")

    def test_validate_full_report_finds_missing_sections(
        self, validator: MarkdownValidator
    ) -> None:
        content = "## Executive Summary\n\nContent here."
        expected = ["## Executive Summary", "## Ratio Analysis", "## Risk Assessment"]
        missing = validator.validate_full_report(content, expected)
        assert "## Ratio Analysis" in missing
        assert "## Risk Assessment" in missing
        assert "## Executive Summary" not in missing

    def test_validate_full_report_empty_returns_all_missing(
        self, validator: MarkdownValidator
    ) -> None:
        expected = ["## A", "## B"]
        missing = validator.validate_full_report("", expected)
        assert missing == expected

    def test_validate_full_report_all_present(
        self, validator: MarkdownValidator
    ) -> None:
        content = "## Executive Summary\nContent.\n## Risk Assessment\nMore."
        missing = validator.validate_full_report(
            content, ["## Executive Summary", "## Risk Assessment"]
        )
        assert missing == []
