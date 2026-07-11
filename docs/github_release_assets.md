# GitHub Release Assets: v1.1.0-report-generation-streaming

## Release Title
EquityIQ v1.1.0 — Report Generation & Streaming Engine

## Executive Summary
This release completes Milestone 9, introducing the full Report Generation & Streaming Engine. The engine produces multi-section, LLM-synthesized investment research reports grounded exclusively in the deterministic outputs of the Milestone 8 Financial Intelligence pipeline. The LLM acts strictly as a narrative synthesizer — it never recalculates or invents financial metrics. This release also delivers the first fully clean MyPy type check (0 errors) across the entire codebase.

---

## Architecture Highlights
*   **Deterministic-Only Grounding**: `ReportContextAssembler` reads exclusively from Milestone 8 pre-computed tables (health scores, ratios, risks, recommendations) — the LLM never recalculates a metric.
*   **Anti-Hallucination Validation**: Two-layer post-generation validation — structural markdown checks (`MarkdownValidator`) and domain boundary enforcement per section (`ReportSectionValidator`).
*   **SSE Token Streaming**: Structured, typed Server-Sent Events protocol (`queued`, `progress`, `token`, `section_started`, `section_completed`, `completed`, `failed`, `heartbeat`) enabling rich real-time frontend UX.
*   **Multi-Format Export**: Markdown (raw), PDF (WeasyPrint with CSS), and DOCX (python-docx) with graceful plaintext fallback if optional dependencies are absent.
*   **Async Celery Pipeline**: Full report generation runs as a background Celery task — API returns 202 Accepted immediately; clients poll or stream for results.
*   **Version Snapshots**: Every completed report creates a `FinancialReportVersionORM` snapshot enabling future diff/history views.

---

## What's New

### Domain
*   `FinancialReport` and `FinancialReportVersion` Pydantic entities with full lifecycle tracking.
*   `ReportRepository` Protocol interface.

### Infrastructure
*   `FinancialReportORM`, `FinancialReportVersionORM` SQLAlchemy models.
*   Alembic migration `f1a2b3c4d5e6` — `financial_reports` and `financial_report_versions` tables.

### Application Services
*   `ReportContextAssembler` — typed `ReportContext` grounding object.
*   `ReportPromptBuilder` — 8 Markdown section templates.
*   `MarkdownValidator` — structural LLM output validation.
*   `ReportSectionValidator` — per-section domain boundary enforcement.
*   `ReportGenerationService` — full 7-section orchestrator.
*   `ReportSSEStreamingService` — async SSE event protocol.
*   `ExportService` — MD / PDF / DOCX with footer and fallback.

### API Routes
*   `POST /companies/{id}/reports/generate` — 202 Accepted, triggers Celery task.
*   `GET  /companies/{id}/reports` — list reports (most recent first).
*   `GET  /companies/{id}/reports/{report_id}` — full detail with content.
*   `GET  /companies/{id}/reports/{report_id}/stream` — SSE token stream.
*   `GET  /companies/{id}/reports/{report_id}/download?fmt=markdown|pdf|docx` — file download.

### Engineering Refinement
*   Fixed pre-existing MyPy `attr-defined` error in `recommendation_engine.py`.
*   Result: **0 MyPy errors** codebase-wide.

---

## Engineering Metrics
*   **Test Suite**: 133 tests passing (100% green).
*   **MyPy**: **0 errors** — fully clean type checks.
*   **Ruff**: Clean lints and formatting.
*   **Import-Linter**: Domain boundary KEPT — 194 files, 893 dependencies analyzed.

---

## Upgrade Notes
*   Run database migrations to apply the new report tables:
    ```bash
    alembic upgrade head
    ```
*   Optional: install PDF/DOCX dependencies for full export support:
    ```bash
    pip install weasyprint python-docx
    ```
*   Start the Celery worker to enable background report generation:
    ```bash
    celery -A app.workers.celery_app worker --loglevel=info
    ```

---

## Repository Status
*   **Milestones Completed**: 9 / 10 (95% Completion).
*   **Status**: Frozen at version `v1.1.0-report-generation-streaming`.
*   **Next**: Milestone 10 — Next.js Frontend Application.
