"""
PromptInjectionGuard application service.
"""

import logging
import re

from app.domain.exceptions import PromptInjectionFlaggedError

logger = logging.getLogger("equityiq.application.prompt_injection_guard")


class PromptInjectionGuard:
    """
    Scans user inputs and retrieved context chunks for instruction overrides,
    role manipulation, or prompt extraction attempts using rule-based heuristics.
    """

    def __init__(self) -> None:
        """
        Initialize scanning patterns.
        """
        # Case-insensitive patterns for prompt injection vectors
        self.injection_patterns = [
            # XML Tag Manipulation
            re.compile(
                r"</?(?:chunk|context|system|assistant|retrieved_context|developer)Message*>",
                re.IGNORECASE,
            ),
            # Prompt Extraction Attempts
            re.compile(
                r"\b(?:begin|system|developer|internal)\s+(?:prompt|message|instruction|rule|constraint|text)s?\b",
                re.IGNORECASE,
            ),
            # Instruction Override & Role Escalation Attempts
            re.compile(
                r"ignore\s+(?:all\s+)?(?:previous|system|developer|core)\s+(?:instruction|rule|setting|constraint)s?",
                re.IGNORECASE,
            ),
            re.compile(r"you\s+are\s+now\s+(?:a|an|the)\b", re.IGNORECASE),
            re.compile(r"act\s+as\s+(?:a|an|the)\b", re.IGNORECASE),
            re.compile(r"override\s+role\b", re.IGNORECASE),
            # Prompt boundary escaping / nested XML
            re.compile(r"\]\s*\]\s*>", re.IGNORECASE),
            re.compile(r"<!\[CDATA\[", re.IGNORECASE),
        ]

    def validate_text(self, text: str, source_label: str = "Input") -> None:
        """
        Validate a string block. Raises PromptInjectionFlaggedError if flagged.
        """
        if not text:
            return

        for idx, pattern in enumerate(self.injection_patterns):
            if pattern.search(text):
                logger.warning(
                    f"Prompt injection pattern {idx} matched in {source_label} content."
                )
                raise PromptInjectionFlaggedError(
                    f"Safety Violation: Malicious or forbidden patterns detected in {source_label}."
                )
