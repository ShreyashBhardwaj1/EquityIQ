"""
PromptBuilder application service.
"""

from app.domain.entities.conversation import ConversationMessage
from app.infrastructure.llm.prompts.prompt_loader import (
    BASE_INSTRUCTIONS,
    PROMPT_VERSION,
)


class PromptBuilder:
    """
    Compiles prompt context structures combining instructions, safety constraints,
    history, context chunks, and user queries.
    """

    def __init__(self, prompt_version: str = PROMPT_VERSION) -> None:
        self.prompt_version = prompt_version
        self.base_instructions = BASE_INSTRUCTIONS

    def build_prompt(
        self,
        context_text: str,
        recent_messages: list[ConversationMessage],
        summary: str | None,
        user_query: str,
    ) -> str:
        """
        Assemble components into a final LLM instructions prompt.
        """
        parts = []

        # 1. Base Instructions (System prompt, safety guidelines, citation rules)
        parts.append("=== INSTRUCTIONS AND SAFETY RULES ===")
        parts.append(self.base_instructions)

        # 2. Retrieved context chunks (already XML-wrapped by ContextAssembler)
        parts.append("=== GROUNDING REFERENCE CONTEXT ===")
        if context_text:
            parts.append(context_text)
        else:
            parts.append(
                "<retrieved_context>\n[No context retrieved]\n</retrieved_context>"
            )

        # 3. Conversation Memory
        parts.append("=== CONVERSATION HISTORY ===")
        if summary:
            parts.append(f"Conversation Summary (Older Turns):\n{summary}\n")

        if recent_messages:
            parts.append("Recent Active Turns:")
            for msg in recent_messages:
                # Capitalize role for standard dialog format
                role_label = "User" if msg.role == "user" else "Assistant"
                parts.append(f"{role_label}: {msg.content}")
            parts.append("")
        else:
            if not summary:
                parts.append("[No history available - new conversation session]\n")

        # 4. User Question
        parts.append("=== NEW USER QUERY ===")
        parts.append(f"User: {user_query}")
        parts.append("Assistant:")

        return "\n".join(parts)

    def get_version(self) -> str:
        """
        Return prompt template semantic version index.
        """
        return self.prompt_version
