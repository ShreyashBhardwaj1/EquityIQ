# GitHub Release Assets: v1.0.0-financial-intelligence

## Release Title
EquityIQ v1.0.0 — Financial Intelligence & Recommendation Engine

## Executive Summary
This release marks the completion of the core Financial Intelligence & Recommendation Engine (Milestone 8) of EquityIQ. It introduces a configurable, registry-driven ratio engine, multi-period trend classifications, category and overall health scoring, risk and distress evaluations, policy-driven investment recommendations, and a consolidated dashboard endpoint with detailed confidence breakdowns. RAG prompts are hardened to prevent recomputation and enforce alignment with deterministic values.

---

## Architecture Highlights
*   **Registry-Driven Ratio Engine**: Decouples ratio math into declarative formulas, automatically classifying qualitative statuses (Excellent, Healthy, Watch, Weak, Critical).
*   **Multi-Period Trend engine**: Classifies QoQ/YoY growth rates (accelerating, decelerating, recovery, decline, stable, volatile) dynamically.
*   **Weighted Scoring Engine**: Applies configurable category weights to output overall and category-level health scores.
*   **Distress Risk engine**: Maps calculated ratios to low/moderate/severe risk factors.
*   **Policy-driven Recommendation Engine**: Evaluates active policy thresholds against health, severe risks, and growth constraints.
*   **Structured Explainability & Dashboard**: Exposes all deterministic rules, positive/negative signals, policy logs, and ratios/risks/trends influencing ratings under a single consolidated payload.

---

## What's New
*   **Centralized Configuration**: All thresholds and scoring weights reside under `app/core/financial_config.py`.
*   **ORM Persistence Mappings**: Maps computed outcomes directly to database schemas with audit history versioning.
*   **API Routes**: 
    *   `POST /companies/{id}/calculate`: Triggers the calculation pipeline.
    *   `GET /companies/{id}/explainability`: Retrieves the step-by-step reasoning logs and signals.
    *   `GET /companies/{id}/dashboard`: Compiles the unified dashboard payload.
*   **Hardened RAG Grounding**: Strengthened LLM prompt safety rules in `app/prompts/answer_prompt.md`.

---

## Engineering Metrics
*   **Verification Status**: 94 tests passing (100% green).
*   **MyPy Validation**: Clean type checks across the entire codebase.
*   **Ruff Quality**: Clean lints and formatting.
*   **Import Contracts**: Domain layer remains completely clean (0 architecture contract violations).

---

## Upgrade Notes
*   Ensure the database migrations are upgraded to head (`89ee9532b883`).
*   Run database migrations:
    ```bash
    alembic upgrade head
    ```

---

## Repository Status
*   **Milestones Completed**: 8 / 10 (80% Completion).
*   **Status**: Frozen at version `v1.0.0-financial-intelligence`.
