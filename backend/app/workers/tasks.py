"""
Celery task handlers executing layout parsing and chunking in background processes.
"""

import asyncio
import logging
from typing import Any
from uuid import UUID, uuid4

from celery import Task

from app.application.services.chunking_service import ChunkingService
from app.core.config import settings
from app.domain.entities.document import ParsingStatus
from app.domain.entities.parsing_manifest import ParsingManifest
from app.domain.exceptions import EntityValidationError
from app.domain.rules.chunk_validation import ChunkValidator
from app.infrastructure.db.manager import db_manager
from app.infrastructure.db.repositories.chunk_repo import SQLAlchemyChunkRepository
from app.infrastructure.db.repositories.document_repo import (
    SQLAlchemyDocumentRepository,
)
from app.infrastructure.db.repositories.parsing_manifest_repo import (
    SQLAlchemyParsingManifestRepository,
)
from app.infrastructure.parsers.pdf_parser import PARSER_VERSION, PDFParser
from app.workers.celery_app import celery_app

logger = logging.getLogger("equityiq.workers.tasks")


class ParsingTask(Task):  # type: ignore[misc]
    """
    Custom Celery Task base handling DB connection manager setup and cleanups.
    """

    _loop: asyncio.AbstractEventLoop | None = None

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        return self._loop

    def run_async(self, coro: Any) -> Any:
        """Runs an async coroutine synchronously, spawning a thread if loop is already running."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import threading

            result = []
            exception = []

            def target() -> None:
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    val = new_loop.run_until_complete(coro)
                    result.append(val)
                except Exception as e:
                    exception.append(e)
                finally:
                    new_loop.close()

            t = threading.Thread(target=target)
            t.start()
            t.join()

            if exception:
                raise exception[0]
            return result[0] if result else None
        else:
            return self.loop.run_until_complete(coro)


@celery_app.task(bind=True, base=ParsingTask, max_retries=3, default_retry_delay=5)  # type: ignore[untyped-decorator]
def parse_document_task(
    self: ParsingTask, document_id_str: str, workspace_id_str: str
) -> None:
    """
    Celery background worker task entry point for parsing and chunking a document.

    Purpose:
        Deserializes inputs, sets up context, and delegates execution to the transactional
        async parsing pipeline handler.

    Inputs:
        self: The active celery Task instance context.
        document_id_str: UUID string of the target document.
        workspace_id_str: UUID string of the target workspace.

    Outputs:
        None.

    Failure Behavior:
        Logs exceptions and fails the task. Celery handles retries based on configured task retry rules.
    """
    doc_id = UUID(document_id_str)
    ws_id = UUID(workspace_id_str)

    logger.info(
        f"Starting parsing task for document: {doc_id} under workspace: {ws_id}"
    )

    # Synchronous wrapper executing the async pipeline
    self.run_async(execute_parsing_pipeline(doc_id, ws_id))


async def execute_parsing_pipeline(document_id: UUID, workspace_id: UUID) -> None:
    """
    Orchestrates the transactional database lifecycle, document text/table parsing, validation, and chunk persistence.

    Purpose:
        Retrieves document details, transitions its parsing status, parses it, chunks the content,
        validates structural boundaries, updates execution manifests, and commits changes atomically.

    Inputs:
        document_id: UUID of the target document.
        workspace_id: UUID of the workspace controlling access.

    Outputs:
        None.

    Failure Behavior:
        Logs error warnings and persists a failed ParsingManifest, transitioning document status to FAILED
        in the database. Raises EntityValidationError or database exceptions if structural validation fails.
    """
    # Enforce db manager initialization if running in worker process
    db_manager.initialize()

    # Open db connection session
    async with db_manager.session_factory() as session:
        doc_repo = SQLAlchemyDocumentRepository(session)
        chunk_repo = SQLAlchemyChunkRepository(session)
        manifest_repo = SQLAlchemyParsingManifestRepository(session)

        # Retrieve document metadata
        document = await doc_repo.get(
            document_id=document_id, workspace_id=workspace_id
        )
        if not document:
            logger.error(
                f"Document {document_id} not found in workspace {workspace_id}"
            )
            return

        # 1. Update status to PROCESSING
        updated_doc = document.model_copy(
            update={"parsing_status": ParsingStatus.PROCESSING}
        )
        await doc_repo.save(updated_doc)
        await session.commit()

        # Retrieve document versions to set upload history context
        versions = await doc_repo.list_versions(document_id=document_id)
        doc_version_idx = len(versions) + 1

        # We also count parsing manifests to track the parse run attempt index
        existing_manifest = await manifest_repo.get_by_document(document_id)
        parse_run_idx = 1
        if existing_manifest:
            # Increment parse iteration count if reprocessing
            parse_run_idx += 1

        # Create parser and extract text pages
        parser = PDFParser()
        warnings = []
        try:
            parse_result = parser.parse(document.storage_path)
            warnings.extend(parse_result.warnings)
        except Exception as e:
            err_msg = f"PDF Parser failed during extraction: {e!s}"
            logger.exception(err_msg)
            # Update status to FAILED
            failed_doc = document.model_copy(
                update={
                    "parsing_status": ParsingStatus.FAILED,
                    "parsing_confidence": 0.0,
                }
            )
            await doc_repo.save(failed_doc)

            # Persist failure manifest
            fail_manifest = ParsingManifest(
                id=uuid4(),
                document_id=document_id,
                parser_version=PARSER_VERSION,
                chunk_strategy="semantic_layout",
                chunk_size=settings.DEFAULT_CHUNK_SIZE,
                overlap=settings.DEFAULT_CHUNK_OVERLAP,
                parse_duration=0.0,
                chunk_count=0,
                table_count=0,
                warnings=[err_msg],
                extraction_confidence=0.0,
            )
            await manifest_repo.save(fail_manifest)
            await session.commit()
            return

        # 2. Chunking Stage
        chunker = ChunkingService(
            chunk_size=settings.DEFAULT_CHUNK_SIZE,
            overlap=settings.DEFAULT_CHUNK_OVERLAP,
        )
        # Note: statement_type can be inferred if Document structure allows it, otherwise default to None
        statement_type_val = None
        chunks = chunker.chunk_document(
            document=document,
            pages_content=parse_result.pages_content,
            document_version=doc_version_idx,
            parse_version=parse_run_idx,
            statement_type=statement_type_val,
        )

        # 3. Validation Stage before persistence
        validator = ChunkValidator(max_chunk_size=settings.DEFAULT_CHUNK_SIZE)
        try:
            validator.validate_batch(chunks)
        except EntityValidationError as e:
            err_msg = f"Chunks validation failed: {e!s}"
            logger.error(err_msg)
            warnings.append(err_msg)

            # Update document to FAILED
            failed_doc = document.model_copy(
                update={
                    "parsing_status": ParsingStatus.FAILED,
                    "parsing_confidence": 0.0,
                }
            )
            await doc_repo.save(failed_doc)

            # Persist failure manifest
            fail_manifest = ParsingManifest(
                id=uuid4(),
                document_id=document_id,
                parser_version=PARSER_VERSION,
                chunk_strategy="semantic_layout",
                chunk_size=settings.DEFAULT_CHUNK_SIZE,
                overlap=settings.DEFAULT_CHUNK_OVERLAP,
                parse_duration=parse_result.parse_duration,
                chunk_count=0,
                table_count=parse_result.table_count,
                warnings=warnings,
                extraction_confidence=0.0,
            )
            await manifest_repo.save(fail_manifest)
            await session.commit()
            return

        # 4. Persistence Stage (Clean up existing chunks and manifests on overwrite / re-run)
        await chunk_repo.delete_by_document(document_id)
        await manifest_repo.delete_by_document(document_id)

        # Save generated chunks in batch
        await chunk_repo.save_batch(chunks)

        # Save success ParsingManifest
        manifest = ParsingManifest(
            id=uuid4(),
            document_id=document_id,
            parser_version=PARSER_VERSION,
            chunk_strategy="semantic_layout",
            chunk_size=settings.DEFAULT_CHUNK_SIZE,
            overlap=settings.DEFAULT_CHUNK_OVERLAP,
            parse_duration=parse_result.parse_duration,
            chunk_count=len(chunks),
            table_count=parse_result.table_count,
            warnings=warnings,
            extraction_confidence=parse_result.extraction_confidence,
        )
        await manifest_repo.save(manifest)

        # 5. Complete document status update
        completed_doc = document.model_copy(
            update={
                "parsing_status": ParsingStatus.COMPLETED,
                "parsing_confidence": parse_result.extraction_confidence,
            }
        )
        await doc_repo.save(completed_doc)

        # 6. Generate vector embeddings and build search index
        try:
            from app.application.services.index_builder import IndexBuilder
            from app.core.dependencies import get_embedding_provider, get_vector_store
            from app.infrastructure.db.repositories.embedding_manifest_repo import (
                SQLAlchemyEmbeddingManifestRepository,
            )
            from app.infrastructure.db.repositories.embedding_repo import (
                SQLAlchemyEmbeddingRepository,
            )

            embedding_repo = SQLAlchemyEmbeddingRepository(session)
            embedding_manifest_repo = SQLAlchemyEmbeddingManifestRepository(session)

            provider = get_embedding_provider()
            vector_store = get_vector_store()
            index_builder = IndexBuilder(
                embedding_provider=provider, vector_store=vector_store
            )

            # Rebuild workspace index first to clear any obsolete vector coordinates
            await index_builder.rebuild_workspace_index(
                workspace_id=workspace_id,
                doc_repo=doc_repo,
                chunk_repo=chunk_repo,
                embedding_repo=embedding_repo,
            )

            # Generate new embeddings, save to DB, and add to FAISS index
            await index_builder.build_index_for_document(
                workspace_id=workspace_id,
                document_id=document_id,
                chunk_repo=chunk_repo,
                embedding_repo=embedding_repo,
                manifest_repo=embedding_manifest_repo,
            )
        except Exception as e:
            err_msg = (
                f"Failed to build vector search index for document {document_id}: {e!s}"
            )
            logger.exception(err_msg)
            warnings.append(err_msg)
            # Re-serialize parsing manifest with warning appended
            manifest = manifest.model_copy(update={"warnings": warnings})
            await manifest_repo.save(manifest)

        # Commit final transaction
        await session.commit()
        logger.info(
            f"Parsing, chunking, and vector indexing successfully completed for document: {document_id}"
        )


# ─── Report Generation Task ───────────────────────────────────────────────────


@celery_app.task(bind=True, base=ParsingTask, max_retries=2, default_retry_delay=10)  # type: ignore[untyped-decorator]
def generate_report_task(
    self: ParsingTask,
    report_id_str: str,
    company_id_str: str,
    workspace_id_str: str,
    fiscal_period: str,
    company_name: str,
    ticker: str,
    generated_by_str: str,
) -> None:
    """
    Celery background worker task for asynchronous financial report generation.

    Purpose:
        Deserializes inputs, sets up database context, and runs the
        full report generation pipeline asynchronously.

    Inputs:
        self: Active Celery task context.
        report_id_str: UUID string of the pre-created FinancialReport entity.
        company_id_str: UUID string of the target company.
        workspace_id_str: UUID string of the owning workspace.
        fiscal_period: Target fiscal period string (e.g., 'FY-2024').
        company_name: Human-readable company name.
        ticker: Exchange ticker symbol.
        generated_by_str: UUID string of the initiating user.

    Outputs:
        None.

    Failure Behavior:
        On exception, the FinancialReport entity is updated to FAILED status
        with the error message persisted. Celery retries up to max_retries times.
    """
    report_id = UUID(report_id_str)
    company_id = UUID(company_id_str)
    workspace_id = UUID(workspace_id_str)
    generated_by = UUID(generated_by_str)

    logger.info(
        f"Starting report generation task: report_id={report_id} "
        f"company={company_id} period={fiscal_period}"
    )

    self.run_async(
        execute_report_generation_pipeline(
            report_id=report_id,
            company_id=company_id,
            workspace_id=workspace_id,
            fiscal_period=fiscal_period,
            company_name=company_name,
            ticker=ticker,
            generated_by=generated_by,
        )
    )


async def execute_report_generation_pipeline(
    report_id: UUID,
    company_id: UUID,
    workspace_id: UUID,
    fiscal_period: str,
    company_name: str,
    ticker: str,
    generated_by: UUID,
) -> None:
    """
    Async pipeline executing the report generation flow.

    Sets up all dependencies, retrieves the pre-created report, and delegates
    to ReportGenerationService to execute the full section generation pipeline.
    """
    from app.application.services.report_context_assembler import ReportContextAssembler
    from app.application.services.report_generation_service import (
        ReportGenerationService,
    )
    from app.application.services.report_markdown_validator import MarkdownValidator
    from app.application.services.report_prompt_builder import ReportPromptBuilder
    from app.application.services.report_section_validator import ReportSectionValidator
    from app.core.dependencies import get_llm_provider
    from app.domain.entities.report import ReportStatus
    from app.infrastructure.db.repositories.health_score_repo import (
        SQLAlchemyHealthScoreRepository,
    )
    from app.infrastructure.db.repositories.ratio_repo import SQLAlchemyRatioRepository
    from app.infrastructure.db.repositories.recommendation_repo import (
        SQLAlchemyRecommendationRepository,
    )
    from app.infrastructure.db.repositories.report_repo import (
        SQLAlchemyReportRepository,
    )
    from app.infrastructure.db.repositories.risk_assessment_repo import (
        SQLAlchemyRiskAssessmentRepository,
    )
    from app.infrastructure.db.repositories.statement_repo import (
        SQLAlchemyFinancialStatementRepository,
    )

    db_manager.initialize()

    async with db_manager.session_factory() as session:
        report_repo = SQLAlchemyReportRepository(session)

        # Retrieve pre-created report
        report = await report_repo.get(report_id, workspace_id)
        if not report:
            logger.error(
                f"Report {report_id} not found in workspace {workspace_id}. Aborting."
            )
            return

        # Mark Celery task ID on report
        try:
            from celery import current_task

            if current_task and current_task.request.id:
                report = report.model_copy(
                    update={"celery_task_id": current_task.request.id}
                )
                await report_repo.save(report)
                await session.commit()
        except Exception:
            pass  # Non-critical

        # Build service stack
        statement_repo = SQLAlchemyFinancialStatementRepository(session)
        ratio_repo = SQLAlchemyRatioRepository(session)
        health_repo = SQLAlchemyHealthScoreRepository(session)
        risk_repo = SQLAlchemyRiskAssessmentRepository(session)
        rec_repo = SQLAlchemyRecommendationRepository(session)

        context_assembler = ReportContextAssembler(
            statement_repo=statement_repo,
            ratio_repo=ratio_repo,
            health_repo=health_repo,
            risk_repo=risk_repo,
            rec_repo=rec_repo,
        )
        prompt_builder = ReportPromptBuilder()
        markdown_validator = MarkdownValidator()
        section_validator = ReportSectionValidator()
        llm_provider = get_llm_provider()

        service = ReportGenerationService(
            context_assembler=context_assembler,
            prompt_builder=prompt_builder,
            markdown_validator=markdown_validator,
            section_validator=section_validator,
            llm_provider=llm_provider,
            report_repo=report_repo,
        )

        try:
            final_report = await service.generate_report(
                report=report,
                company_name=company_name,
                ticker=ticker,
            )
            await session.commit()
            logger.info(
                f"Report {report_id} completed successfully. "
                f"Status: {final_report.status}"
            )
        except Exception as e:
            logger.exception(f"Report generation pipeline failed: {e}")
            try:
                from app.domain.entities.report import ReportStatus

                failed = report.model_copy(
                    update={
                        "status": ReportStatus.FAILED,
                        "error_message": str(e),
                    }
                )
                await report_repo.save(failed)
                await session.commit()
            except Exception:
                pass
            raise
