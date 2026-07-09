"""
ConversationService application service.
"""

import logging
import uuid
from datetime import datetime
from uuid import UUID

from app.domain.entities.conversation import Conversation, ConversationMessage
from app.domain.exceptions import ConversationNotFoundError
from app.domain.interfaces.providers import LLMProvider
from app.domain.interfaces.repositories import (
    CitationRepository,
    ConversationRepository,
)

logger = logging.getLogger("equityiq.application.conversation_service")


class ConversationService:
    """
    Manages conversation sessions, message turns, and conversation memory summarization.
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        citation_repo: CitationRepository,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self.conversation_repo = conversation_repo
        self.citation_repo = citation_repo
        self.llm_provider = llm_provider

    async def create_conversation(
        self, workspace_id: UUID, user_id: UUID, title: str
    ) -> Conversation:
        """
        Creates a new conversation session.
        """
        conversation = Conversation(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            user_id=user_id,
            title=title,
            summary=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return await self.conversation_repo.save(conversation)

    async def get_conversation(
        self, conversation_id: UUID, workspace_id: UUID
    ) -> Conversation:
        """
        Retrieves a conversation, verifying workspace tenancy isolation.
        """
        conversation = await self.conversation_repo.get(conversation_id, workspace_id)
        if not conversation:
            raise ConversationNotFoundError(
                "Conversation session not found or access denied."
            )
        return conversation

    async def list_conversations(
        self, workspace_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Conversation]:
        """
        Lists active conversations in a workspace.
        """
        return await self.conversation_repo.list_by_workspace(
            workspace_id, limit, offset
        )

    async def delete_conversation(
        self, conversation_id: UUID, workspace_id: UUID
    ) -> None:
        """
        Deletes a conversation, verifying workspace tenancy.
        """
        await self.get_conversation(conversation_id, workspace_id)
        await self.conversation_repo.delete(conversation_id, workspace_id)

    async def add_message(
        self, conversation_id: UUID, workspace_id: UUID, role: str, content: str
    ) -> ConversationMessage:
        """
        Adds a new message turn to a conversation.
        """
        conv = await self.get_conversation(conversation_id, workspace_id)

        message = ConversationMessage(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=datetime.utcnow(),
            citations=[],
        )
        saved_msg = await self.conversation_repo.save_message(message)

        # Update updated_at on the conversation
        updated_conv = Conversation(
            id=conv.id,
            workspace_id=conv.workspace_id,
            user_id=conv.user_id,
            title=conv.title,
            summary=conv.summary,
            created_at=conv.created_at,
            updated_at=datetime.utcnow(),
        )
        await self.conversation_repo.save(updated_conv)

        return saved_msg

    async def get_active_messages(
        self, conversation_id: UUID, workspace_id: UUID
    ) -> list[ConversationMessage]:
        """
        Gets active messages for a conversation after verifying tenancy.
        """
        await self.get_conversation(conversation_id, workspace_id)
        return await self.conversation_repo.get_messages(conversation_id)

    async def trigger_summarization_if_needed(
        self, conversation_id: UUID, workspace_id: UUID
    ) -> None:
        """
        Checks if active conversation history exceeds 10 messages, and summarizes
        older turns to optimize token budgets.
        """
        if not self.llm_provider:
            return

        conv = await self.get_conversation(conversation_id, workspace_id)
        messages = await self.conversation_repo.get_messages(conversation_id)

        if len(messages) <= 10:
            return

        # Prune the oldest 6 messages (3 full turns)
        messages_to_summarize = messages[:6]

        history_lines = []
        for msg in messages_to_summarize:
            role = "User" if msg.role == "user" else "Assistant"
            history_lines.append(f"{role}: {msg.content}")

        history_text = "\n".join(history_lines)

        from app.infrastructure.llm.prompts.prompt_loader import SUMMARIZER_PROMPT

        prompt = f"{SUMMARIZER_PROMPT}\n"
        if conv.summary:
            prompt += f"Existing previous summary:\n{conv.summary}\n\n"

        prompt += f"New turns to merge and summarize:\n{history_text}\n\nConsolidated Summary:"

        try:
            response = await self.llm_provider.complete(prompt)
            new_summary = response.text.strip()

            updated_conv = Conversation(
                id=conv.id,
                workspace_id=conv.workspace_id,
                user_id=conv.user_id,
                title=conv.title,
                summary=new_summary,
                created_at=conv.created_at,
                updated_at=datetime.utcnow(),
            )
            await self.conversation_repo.save(updated_conv)

            # Soft-delete the summarized message records via repository method
            await self.conversation_repo.soft_delete_messages(
                [msg.id for msg in messages_to_summarize]
            )
            logger.info(
                f"Conversation {conversation_id} successfully summarized. 6 turns soft-deleted."
            )

        except Exception as e:
            logger.warning(
                f"Conversation summarization failed: {e}. Keeping active history intact."
            )
