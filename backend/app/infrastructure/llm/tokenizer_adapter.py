"""
Tiktoken-based tokenizer adapter implementing TokenizerProvider.
"""

import logging
from typing import Any

import tiktoken

from app.domain.interfaces.providers import TokenizerProvider

logger = logging.getLogger("equityiq.infrastructure.llm.tokenizer_adapter")


class TiktokenTokenizerAdapter(TokenizerProvider):
    """
    Concrete adapter using tiktoken's cl100k_base encoding to provide local token counting.
    """

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        """
        Initialize the tiktoken encoding.
        """
        self.encoding_name = encoding_name
        self.encoding: Any = None
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)

        except Exception as e:
            logger.warning(
                f"Failed to load tiktoken encoding '{encoding_name}': {e}. "
                "Falling back to character-based heuristic token counter."
            )
            self.encoding = None

    def count_tokens(self, text: str) -> int:
        """
        Calculate token count for a text string, falling back if tiktoken is unavailable.
        """
        if not text:
            return 0

        if self.encoding is not None:
            try:
                return len(self.encoding.encode(text, disallowed_special=()))
            except Exception as e:
                logger.debug(
                    f"Tiktoken encoding failed: {e}. Using fallback heuristic."
                )

        # Fallback heuristic: 1 token is roughly 4 characters
        return max(1, len(text) // 4)
