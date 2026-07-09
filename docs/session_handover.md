# Session Handover: Milestone 7 to Milestone 8

## 1. Current Repository State
*   **Version Tag**: `v0.9.0-rag-llm-integration`
*   **Status**: Stable, verified, reformatted, and type-checked.
*   **Test Suite**: 84 tests passing with 87% statement coverage.
*   **Linter & Formatter**: Ruff checks passed cleanly, format check green.
*   **MyPy**: Success (0 issues found across 143 source files).
*   **Import Linter**: Domain boundary kept (0 contracts broken).

## 2. Completed Work (Milestone 7)
*   **Gemini Provider Adapter**: Created `GeminiAdapter` wrapping the official Google GenAI SDK. Sets **Gemini 2.5 Pro** as the primary synthesis engine and automatically hot-swaps to **Gemini 2.5 Flash** if connection, quota, or network failures occur.
*   **Safety & Compliance Guards**: Deployed `PromptInjectionGuard` scanning user inputs and grounding context chunks for malicious patterns (instruction extraction, role-override, or XML injection).
*   **Context & Token Optimization**: Engineered `ContextAssembler` to group adjacent sequence chunks within the same document section, and `TokenBudgetManager` to audit and prune chat history turns and retrieved chunks under a 20,000 token limit.
*   **Explainable Telemetry & Schema**: Added `LLMRequest` model and `llm_requests` table tracking latency, token usage, model fallbacks, and scores. Extended citations with retrieval metrics (`rank`, `semantic_score`, `keyword_score`, `hybrid_score`, and `retrieval_method`).
*   **Deterministic Evaluation Scorer**: Exposed a sentence-level `grounding_score` measuring exactly the citation density ratio, along with a composite `confidence_score` combining semantic similarity, chunk density, coverage, and source agreement.
*   **API Chat Endpoints**:
    *   `POST /chat/ask`: Stateless grounding checks returning formatted responses, confidence/grounding scores, and citation mappings.
    *   `POST /chat/chat`: Stateful conversation sessions saving queries, responses, and citations, with Celery background jobs summarizing turns if history exceeds 10 turns.

## 3. Starting Point for Milestone 8
Tomorrow's goal is **Milestone 8 — Financial Intelligence & Recommendation Engine**.
*   **Scope**:
    1.  Implement deterministic financial analysis rules in the domain engine (calculating key ratios, scoring liquidity, profitability, leverage, and efficiency).
    2.  Integrate sentiment analysis pipeline parsing news, corporate filings, and analyst notes.
    3.  Develop a recommendation engine matching financial indicators and sentiment score to scoring rubrics to generate stock signals (Buy, Hold, Sell).
    4.  Expose API endpoints for company rating scores and recommendation summaries.

## 4. Key Assumptions
*   **Model Provider Access**: Gemini API keys are mocked to `mock-testing-key` in the test environment configuration to run the suite offline, and must resolve to valid API keys in development/production.
*   **Database URL**: SQLite is the primary database driver for testing. PostgreSQL is configured as the target database for staging/production.

## 5. Technical Debt Register
1.  **`datetime.utcnow()` Deprecations**: Hashing, database, and index building layers contain calls to `datetime.utcnow()`, raising deprecation warnings under Python 3.12+.
2.  **Local Storage Directory**: Documents and FAISS index files are written to local disk directories (`storage/uploads` and `storage/indices`). In production, this requires cloud block storage (e.g. AWS S3).
3.  **Prompt Response Caching**: Serve cached answers for repeated queries to save LLM tokens.
4.  **Multi-Provider Registry**: Support dynamic model routing (Gemini, Claude, GPT, Ollama).
5.  **Token-Level Streaming**: Stream tokens in real-time from the API router using Server-Sent Events (SSE) (Scheduled for Milestone 9).
