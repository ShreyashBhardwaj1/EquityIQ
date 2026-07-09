# Engineering Journal: Day 04 — LLM Integration & Retrieval-Augmented Generation (RAG)

## 1. Objectives
The primary objective of today's session was to implement **Milestone 7 — LLM Integration & Retrieval-Augmented Generation (RAG)** under the guiding project principle: **"Determinism Before Intelligence."**
Key tasks included:
1. Building the `GeminiAdapter` with a dynamic fallback from Gemini 2.5 Pro to Gemini 2.5 Flash.
2. Implementing the `PromptInjectionGuard` scanning queries for override patterns, role-swaps, and XML tag injections.
3. Creating the `TokenBudgetManager` to enforce a 20,000 token limit using `tiktoken`.
4. Designing a sentence-level `grounding_score` calculation and a multi-factor `confidence_score`.
5. Externalizing prompt templates into dedicated markdown files loaded via `prompt_loader.py`.
6. Storing latency and token usage metrics in an `llm_requests` ORM table while avoiding raw text/input leaks.

---

## 2. Major Architectural Decisions
*   **Dual-Model Provider Fallback**: We deployed Gemini 2.5 Pro as the primary reasoning model and Gemini 2.5 Flash as a fallback. Any connection, rate-limit, or quota errors automatically route queries to Flash, ensuring system resilience.
*   **XML Untrusted Input Wrapping**: Retrieved chunks are wrapped in XML tags, and the system prompt instructs the model to treat XML tags as untrusted data to mitigate indirect prompt injection.
*   **Strict Separated Telemetry**: To comply with privacy standards, we record token counts, latencies, model fallbacks, and scores in `llm_requests`, but completely omit raw user queries or synthesized responses.
*   **Deterministic Evaluation Formulas**: We avoided using LLM-based evaluators for validation. Grounding scores are calculated deterministically via sentence-level citation analysis:
    $$\text{Grounding Score} = \frac{\text{Cited Sentences}}{\text{Total Sentences}}$$

---

## 3. Problems Encountered & Solutions
*   **SQLite Relative Path in Test Execution**:
    *   *Problem*: Running pytest from the root folder caused SQLite to create an empty `test.db` in the root directory rather than locating the migrated database in `backend/test.db`, triggering "no such table: citations" errors.
    *   *Solution*: Run the pytest suite with the working directory set to `backend`, or set `DATABASE_URL` explicitly to `sqlite+aiosqlite:///backend/test.db`.
*   **MyPy Reassignment Type Error**:
    *   *Problem*: MyPy flagged variable reassignment in `hybrid_search_service.py` because `sem_score` was initially inferred as `float` (using default `0.0`), but later assigned to `float | None` (via `.get(cid, None)`).
    *   *Solution*: Renamed the second-loop local variables to `retrieved_sem_score` and `retrieved_key_score`, resolving type conflict errors.

---

## 4. Metrics
*   **Pytest Verification**: 84 / 84 tests passing (100% green).
*   **Test Coverage**: 87% overall statement coverage.
*   **MyPy Static Checking**: 0 errors across 143 files.
*   **Import Linter**: 0 boundary contract violations.

---

## 5. Personal Engineering Observations
Wrote a complete integration test suite in `test_refinements.py` that verifies external prompt loading, grounding math, telemetry schemas, and citation mappings. Decoupling prompt strings into markdown files significantly improved readability, and keeping the token manager completely offline using local tiktoken heuristics keeps the RAG pipeline fast and cost-effective.
