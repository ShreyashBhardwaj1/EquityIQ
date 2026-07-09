# GitHub Release Assets: v0.9.0-rag-llm-integration

## Release Title
EquityIQ v0.9.0 — LLM Integration & Retrieval-Augmented Generation (RAG)

## Executive Summary
This release implements the Retrieval-Augmented Generation (RAG) and Large Language Model (LLM) integration layer. Utilizing Google GenAI SDK, the system binds workspace data queries to Gemini 2.5 Pro (with automatic Gemini 2.5 Flash fallback). Safety boundaries are enforced via Prompt Injection Guards, Token Budget Managers (20k ceiling), Response Validators, and deterministic Grounding/Confidence scorers. Latency and token usage telemetry are persisted in the database.

---

## Architecture Highlights
*   **Dual-Model Provider Fallback**: Uses Gemini 2.5 Pro as the primary reasoning engine, automatically routing to Gemini 2.5 Flash if connection, quota, or rate limits fail.
*   **Prompt Injection Guard**: Validates user queries and source text for system instruction overrides, role switching, or XML injection attempts.
*   **Context & Token Budgets**: Groups adjacent sequence chunks into unified XML blocks and prunes older chat turns and context chunks under a 20,000 token limit.
*   **Explainable Telemetry & Schema**: Records latencies, token counts, model fallbacks, and scores in an `llm_requests` table. Citations are enriched with `rank`, similarity scores, and retrieval methods.
*   **Deterministic Scorers**: Sentence-level grounding density calculations and multi-factor confidence verification.

---

## What's New
*   **Gemini Integration**: Adapter wrapping GenAI SDK with Pro/Flash failover.
*   **Externalized Prompts**: Prompts are stored in markdown templates under `backend/app/prompts/` and loaded dynamically.
*   **Grounding evaluation**: Exposes `grounding_score` measuring the ratio of cited sentences in responses.
*   **API Routes**: 
    *   `POST /chat/ask`: Stateless Q&A returning grounding checks.
    *   `POST /chat/chat`: Stateful conversation management.
    *   `GET /chat/conversation/{id}`: Scoped message turn fetch.
    *   `DELETE /chat/conversation/{id}`: Conversation deletion.

---

## Engineering Metrics
*   **Verification Status**: 84 tests passing (100% green).
*   **MyPy Validation**: Checked 143 source files with zero errors.
*   **Ruff Quality**: Clean lints and formatting.
*   **Import Contracts**: Domain layer remains completely clean (0 architecture contract violations).
*   **Test Coverage**: 87% overall statement coverage.

---

## Lessons Learned
1.  **SQLite Testing Path Resolution**: Pytest execution from root failed to locate migrated tables in `backend/test.db` until the environment path or working directory was adjusted.
2.  **MyPy Variable Reassignment Strictness**: Python variables reassigned to union types (`float` to `float | None`) must be renamed to maintain strict typing verification.

---

## Breaking Changes
*   None. Backward compatibility has been fully preserved.

---

## Upgrade Notes
*   Ensure the database migrations are upgraded to head (`b6c989ff64f7`).
*   Ensure environment variables `GEMINI_API_KEY` are configured.
*   Run database migrations:
    ```bash
    alembic upgrade head
    ```

---

## Repository Status
*   **Milestones Completed**: 9 / 10 (90% Completion).
*   **Status**: Frozen at version `v0.9.0-rag-llm-integration`.

---

## Screenshots Placeholder
*   [Insert API chat endpoint execution screenshots here]

---

## Future Roadmap (Milestone 8)
*   **Objective**: Financial Intelligence & Recommendation Engine. Establish rating scores, calculate key ratios, analyze filing/news sentiment, and build recommendation triggers.
