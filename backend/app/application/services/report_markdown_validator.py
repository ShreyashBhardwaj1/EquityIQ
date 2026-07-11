"""
MarkdownValidator — validates that generated report content is well-formed markdown.
"""

import re


class MarkdownValidationError(Exception):
    """Raised when generated markdown content fails validation checks."""


class MarkdownValidator:
    """
    Validates LLM-generated markdown content to ensure structural correctness.

    Checks performed:
    - Minimum content length
    - Presence of expected section headers
    - No unclosed code blocks
    - No placeholder artifacts remaining in text
    """

    MIN_CONTENT_LENGTH = 200
    PLACEHOLDER_PATTERN = re.compile(r"\{[a-zA-Z_]+\}")
    CODE_BLOCK_MARKER = "```"

    def validate(self, content: str, section_name: str = "section") -> None:
        """
        Validate a generated markdown section. Raises MarkdownValidationError on failure.

        Args:
            content: The markdown string to validate.
            section_name: Human-readable section label for error messages.
        """
        self._check_not_empty(content, section_name)
        self._check_minimum_length(content, section_name)
        self._check_no_raw_placeholders(content, section_name)
        self._check_balanced_code_blocks(content, section_name)

    def _check_not_empty(self, content: str, section_name: str) -> None:
        if not content or not content.strip():
            raise MarkdownValidationError(
                f"Section '{section_name}': content is empty."
            )

    def _check_minimum_length(self, content: str, section_name: str) -> None:
        if len(content.strip()) < self.MIN_CONTENT_LENGTH:
            raise MarkdownValidationError(
                f"Section '{section_name}': content length {len(content.strip())} "
                f"is below minimum {self.MIN_CONTENT_LENGTH} characters."
            )

    def _check_no_raw_placeholders(self, content: str, section_name: str) -> None:
        matches = self.PLACEHOLDER_PATTERN.findall(content)
        if matches:
            raise MarkdownValidationError(
                f"Section '{section_name}': unresolved template placeholders found: "
                f"{matches[:5]}"
            )

    def _check_balanced_code_blocks(self, content: str, section_name: str) -> None:
        count = content.count(self.CODE_BLOCK_MARKER)
        if count % 2 != 0:
            raise MarkdownValidationError(
                f"Section '{section_name}': unclosed code block (odd number of ``` markers)."
            )

    def validate_full_report(
        self, content: str, expected_sections: list[str]
    ) -> list[str]:
        """
        Validate a complete report and return a list of missing section headers.

        Args:
            content: Full assembled report markdown.
            expected_sections: List of section heading strings to check for.

        Returns:
            List of missing section names (empty list = all present).
        """
        if not content.strip():
            return expected_sections

        missing: list[str] = []
        for section in expected_sections:
            if section not in content:
                missing.append(section)
        return missing
