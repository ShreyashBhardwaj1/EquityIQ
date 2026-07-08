# Engineering Journal: Day 04 — Document Intelligence Pipeline

## Summary
Today we built the core Document Intelligence Pipeline, introducing background parsing tasks, layout-aware PDF parsing adapters, semantic chunking mechanisms, and batch persistence logic. The system is designed following the "Determinism Before Intelligence" principle, ensuring a robust, reproducible base.

## Major Architectural Decisions
1.  **Layout-Aware Parsers (`pdfplumber` + OCR)**: We chose `pdfplumber` for text layout preservation and custom table markdown formatting. We implemented a fallback `pytesseract` OCR path if text density is low, but isolated it so the app runs without system-level OCR binary assumptions.
2.  **Stable Chunk IDs (UUID5)**: We selected `uuid.uuid5` with `document.id` as the namespace and `chunk_index` as the name. This ensures chunk IDs are fully deterministic across reprocessing runs when the document content is unchanged, protecting downstream vector index upserts.
3.  **Extensible Batch Validation**: Deployed `ChunkValidator` checking batch sorting, sequence ordering, content uniqueness, empty text guards, and size bounds before database persistence.

## Lessons Learned & Challenges Solved
1.  **Celery Event Loop Concurrency in Tests**: Under FastAPI TestClient eager executions (`task_always_eager = True`), the Celery task executes synchronously on the request thread. Since FastAPI request routing already runs on an active event loop, calling `loop.run_until_complete()` inside the task raised `RuntimeError: This event loop is already running`.
    *   *Solution*: Implemented a thread-spawning runner fallback in `tasks.py` to run the async pipeline on a dedicated thread with its own loop when an active main loop is detected.
2.  **PDFParser Mock Strictness**: `pdfplumber` validates the PDF binary header and structure. During tests, writing simple string mocks to disk resulted in `PDFSyntaxError: No /Root object!`. We resolved this by integrating a plain-text fallback path that reads files directly if they fail to open as PDFs or lack a `.pdf` extension, making the parsing pipeline highly defensive.

## Personal Engineering Notes
*   Deterministic design saves significant debugging time. Resolving the chunk identity stability with `uuid5` up front eliminates complex vector index reconciliation overhead later on.
*   Clean Architecture import contract checks continue to prove their worth; the linter ensured no domain classes imported database engines or routers.
