"""
Static prompt templates, developer instructions, and financial safety rules loaded dynamically from prompts/ directory.
"""

from pathlib import Path

PROMPT_VERSION = "1.0.0"

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "prompts"


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        raise RuntimeError(
            f"Failed to load prompt template {filename} from {path}: {e}"
        ) from e


SYSTEM_PROMPT = _load_prompt("system_prompt.md")
FINANCIAL_SAFETY_RULES = _load_prompt("answer_prompt.md")
CITATION_INSTRUCTIONS = _load_prompt("citation_prompt.md")
SUMMARIZER_PROMPT = _load_prompt("summarizer_prompt.md")

BASE_INSTRUCTIONS = f"""
{SYSTEM_PROMPT}

{FINANCIAL_SAFETY_RULES}

{CITATION_INSTRUCTIONS}
"""
