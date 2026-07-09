"""
TokenBudgetManager application service.
"""

import logging

from app.domain.entities.conversation import ConversationMessage
from app.domain.entities.retrieval import RetrievalResult
from app.domain.interfaces.providers import TokenizerProvider

logger = logging.getLogger("equityiq.application.token_budget_manager")


class TokenBudgetManager:
    """
    Manages prompt token budgets and prunes history or context chunks to fit constraints.
    Enforces a default budget limit of 20,000 tokens.
    Pruning occurs in the sequence: History turns first, then Retrieved context chunks.
    """

    def __init__(
        self, tokenizer: TokenizerProvider, default_budget: int = 20000
    ) -> None:
        self.tokenizer = tokenizer
        self.default_budget = default_budget

    def prune_history_and_context(
        self,
        system_instructions: str,
        user_query: str,
        recent_messages: list[ConversationMessage],
        summary: str | None,
        retrieval_results: list[RetrievalResult],
        max_context_tokens: int = 12000,
    ) -> tuple[list[ConversationMessage], list[RetrievalResult]]:
        """
        Calculates budget allocation and prunes history messages first, followed by context chunks.
        """
        # Step 1: Calculate fixed token costs
        instr_tokens = self.tokenizer.count_tokens(system_instructions)
        query_tokens = self.tokenizer.count_tokens(user_query)
        summary_tokens = self.tokenizer.count_tokens(summary) if summary else 0

        fixed_tokens = instr_tokens + query_tokens + summary_tokens

        # Available budget for dynamic components (history + context)
        available_budget = self.default_budget - fixed_tokens
        if available_budget <= 0:
            logger.warning(
                "Fixed tokens exceed default budget! Pruning all history and chunks."
            )
            return [], []

        # Step 2: Prune history first if needed
        # We estimate history tokens turn-by-turn from newest to oldest
        active_messages: list[ConversationMessage] = []
        history_tokens = 0

        # Iterate reverse (newest first)
        for msg in reversed(recent_messages):
            msg_tokens = self.tokenizer.count_tokens(f"{msg.role}: {msg.content}\n")
            # Check if adding this message exceeds the default budget
            if fixed_tokens + history_tokens + msg_tokens <= self.default_budget:
                active_messages.insert(0, msg)
                history_tokens += msg_tokens
            else:
                logger.info(
                    f"History message {msg.id} pruned due to token budget constraint."
                )
                break

        # Step 3: Prune retrieved context chunks next if total budget is still exceeded
        active_results = list(retrieval_results)

        while active_results:
            context_text = "\n".join([res.content for res in active_results])
            context_tokens = self.tokenizer.count_tokens(context_text)

            total_estimate = fixed_tokens + history_tokens + context_tokens

            if (
                total_estimate <= self.default_budget
                and context_tokens <= max_context_tokens
            ):
                break
            else:
                # Remove the lowest-score chunk (last in list)
                pruned_chunk = active_results.pop()
                logger.info(
                    f"Retrieved chunk {pruned_chunk.chunk_id} pruned to fit token budget."
                )

        return active_messages, active_results
