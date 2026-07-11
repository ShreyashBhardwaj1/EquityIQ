"""
Reports API Router — endpoints for generating, listing, streaming, and exporting
financial analysis reports.
"""

import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from app.application.services.report_export_service import ExportService
from app.application.services.report_generation_service import ReportGenerationService
from app.application.services.report_streaming_service import (
    ReportSSEStreamingService,
    build_failed_event,
)
from app.core.dependencies import (
    get_company_repository,
    get_current_user,
    get_current_workspace_id,
    get_report_generation_service,
    get_report_repository,
)
from app.domain.entities.report import FinancialReport, ReportStatus
from app.domain.entities.user import User
from app.infrastructure.db.repositories.company_repo import SQLAlchemyCompanyRepository
from app.infrastructure.db.repositories.report_repo import SQLAlchemyReportRepository

logger = logging.getLogger("equityiq.api.v1.reports")

router = APIRouter(prefix="/companies", tags=["Reports"])


# ─── Response Models ──────────────────────────────────────────────────────────


class GenerateReportRequest(BaseModel):
    """Request body for triggering report generation."""

    fiscal_period: str


class ReportSummaryResponse(BaseModel):
    """Lightweight report summary for list endpoints."""

    id: UUID
    company_id: UUID
    workspace_id: UUID
    fiscal_period: str
    title: str
    status: str
    generated_by: UUID
    model_name: str
    report_template_version: str
    financial_engine_version: str
    generation_duration: float
    created_at: str
    error_message: str | None


class ReportDetailResponse(ReportSummaryResponse):
    """Full report detail including markdown content."""

    content: str
    prompt_version: str
    rag_version: str
    embedding_version: str
    celery_task_id: str | None


def _report_to_summary(
    report: FinancialReport, created_at: str = ""
) -> ReportSummaryResponse:
    return ReportSummaryResponse(
        id=report.id,
        company_id=report.company_id,
        workspace_id=report.workspace_id,
        fiscal_period=str(report.fiscal_period),
        title=report.title,
        status=report.status.value,
        generated_by=report.generated_by,
        model_name=report.model_name,
        report_template_version=report.report_template_version,
        financial_engine_version=report.financial_engine_version,
        generation_duration=round(report.generation_duration, 2),
        created_at=created_at or datetime.now(tz=UTC).isoformat(),
        error_message=report.error_message,
    )


def _report_to_detail(
    report: FinancialReport, created_at: str = ""
) -> ReportDetailResponse:
    return ReportDetailResponse(
        id=report.id,
        company_id=report.company_id,
        workspace_id=report.workspace_id,
        fiscal_period=str(report.fiscal_period),
        title=report.title,
        status=report.status.value,
        generated_by=report.generated_by,
        model_name=report.model_name,
        report_template_version=report.report_template_version,
        financial_engine_version=report.financial_engine_version,
        generation_duration=round(report.generation_duration, 2),
        created_at=created_at or datetime.now(tz=UTC).isoformat(),
        error_message=report.error_message,
        content=report.content,
        prompt_version=report.prompt_version,
        rag_version=report.rag_version,
        embedding_version=report.embedding_version,
        celery_task_id=report.celery_task_id,
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post(
    "/{company_id}/reports/generate",
    response_model=ReportSummaryResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_report(
    company_id: UUID,
    request: GenerateReportRequest,
    active_workspace_id: UUID = Depends(get_current_workspace_id),
    current_user: User = Depends(get_current_user),
    company_repo: SQLAlchemyCompanyRepository = Depends(get_company_repository),
    report_repo: SQLAlchemyReportRepository = Depends(get_report_repository),
    generation_service: ReportGenerationService = Depends(
        get_report_generation_service
    ),
) -> ReportSummaryResponse:
    """
    Trigger async report generation for a company and fiscal period.

    Validates company access, creates a PENDING report entity, and dispatches
    a Celery background task. Returns the report ID for subsequent polling or streaming.

    Workspace isolation: strictly enforced via X-Workspace-ID header.
    """
    # Verify company exists within active workspace
    company = await company_repo.get_by_id(active_workspace_id, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found in active workspace.",
        )

    fiscal_period = request.fiscal_period
    company_name = company.name
    ticker = company.ticker.symbol if company.ticker else "UNKNOWN"

    try:
        # Create PENDING report entity
        report = await generation_service.create_pending_report(
            company_id=company_id,
            workspace_id=active_workspace_id,
            fiscal_period=fiscal_period,
            generated_by=current_user.id,
            company_name=company_name,
            ticker=ticker,
        )

        # Dispatch Celery background task
        from app.workers.tasks import generate_report_task

        task = generate_report_task.delay(
            report_id_str=str(report.id),
            company_id_str=str(company_id),
            workspace_id_str=str(active_workspace_id),
            fiscal_period=fiscal_period,
            company_name=company_name,
            ticker=ticker,
            generated_by_str=str(current_user.id),
        )

        logger.info(
            f"Report generation dispatched: report_id={report.id} "
            f"celery_task_id={task.id}"
        )

        return _report_to_summary(report)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get(
    "/{company_id}/reports",
    response_model=list[ReportSummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def list_reports(
    company_id: UUID,
    active_workspace_id: UUID = Depends(get_current_workspace_id),
    company_repo: SQLAlchemyCompanyRepository = Depends(get_company_repository),
    report_repo: SQLAlchemyReportRepository = Depends(get_report_repository),
) -> list[ReportSummaryResponse]:
    """
    List all reports for a company in the active workspace.

    Returns most recent first. Workspace isolation strictly enforced.
    """
    company = await company_repo.get_by_id(active_workspace_id, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found in active workspace.",
        )

    reports = await report_repo.list_by_company(company_id, active_workspace_id)
    return [_report_to_summary(r) for r in reports]


@router.get(
    "/{company_id}/reports/{report_id}",
    response_model=ReportDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_report(
    company_id: UUID,
    report_id: UUID,
    active_workspace_id: UUID = Depends(get_current_workspace_id),
    company_repo: SQLAlchemyCompanyRepository = Depends(get_company_repository),
    report_repo: SQLAlchemyReportRepository = Depends(get_report_repository),
) -> ReportDetailResponse:
    """
    Retrieve a specific report by ID including full markdown content.

    Workspace isolation strictly enforced.
    """
    company = await company_repo.get_by_id(active_workspace_id, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found in active workspace.",
        )

    report = await report_repo.get(report_id, active_workspace_id)
    if not report or report.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    return _report_to_detail(report)


@router.get(
    "/{company_id}/reports/{report_id}/stream",
    status_code=status.HTTP_200_OK,
)
async def stream_report(
    company_id: UUID,
    report_id: UUID,
    active_workspace_id: UUID = Depends(get_current_workspace_id),
    company_repo: SQLAlchemyCompanyRepository = Depends(get_company_repository),
    report_repo: SQLAlchemyReportRepository = Depends(get_report_repository),
) -> StreamingResponse:
    """
    Stream a completed report's content via Server-Sent Events (SSE).

    For completed reports: replays the content token-by-token from the database.
    For pending/generating reports: returns a progress status event.

    SSE event types: queued | progress | token | section_started |
                     section_completed | completed | failed | heartbeat
    """
    company = await company_repo.get_by_id(active_workspace_id, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found in active workspace.",
        )

    report = await report_repo.get(report_id, active_workspace_id)
    if not report or report.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    streaming_service = ReportSSEStreamingService()

    if report.status == ReportStatus.FAILED:

        async def failed_stream() -> AsyncGenerator[str, None]:
            yield build_failed_event(
                report.error_message or "Report generation failed.", code=500
            )

        return StreamingResponse(
            failed_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    if report.status in (ReportStatus.PENDING, ReportStatus.GENERATING):
        from app.application.services.report_streaming_service import (
            build_progress_event,
        )

        async def pending_stream() -> AsyncGenerator[str, None]:
            pct = 10.0 if report.status == ReportStatus.PENDING else 50.0
            msg = (
                "Report queued for generation"
                if report.status == ReportStatus.PENDING
                else "Report generation in progress"
            )
            yield build_progress_event(pct, msg)

        return StreamingResponse(
            pending_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # COMPLETED — stream content from DB
    return StreamingResponse(
        streaming_service.stream_completed_report(
            report_id=str(report.id),
            company_id=str(company.id),
            content=report.content,
            duration_seconds=report.generation_duration,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/{company_id}/reports/{report_id}/download",
    status_code=status.HTTP_200_OK,
)
async def download_report(
    company_id: UUID,
    report_id: UUID,
    fmt: str = Query(
        default="markdown", description="Export format: markdown | pdf | docx"
    ),
    active_workspace_id: UUID = Depends(get_current_workspace_id),
    company_repo: SQLAlchemyCompanyRepository = Depends(get_company_repository),
    report_repo: SQLAlchemyReportRepository = Depends(get_report_repository),
) -> Response:
    """
    Download a completed report in the requested format.

    Supported formats: markdown, pdf, docx.
    Returns the file as an inline or attachment response with appropriate MIME type.
    """
    if fmt not in ("markdown", "pdf", "docx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format '{fmt}'. Use: markdown, pdf, docx.",
        )

    company = await company_repo.get_by_id(active_workspace_id, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found in active workspace.",
        )

    report = await report_repo.get(report_id, active_workspace_id)
    if not report or report.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Report is not yet complete. Current status: {report.status.value}",
        )

    ticker = company.ticker.symbol if company.ticker else "UNKNOWN"
    export_service = ExportService()

    from app.application.services.report_export_service import _build_footer

    footer = _build_footer(
        report_template_version=report.report_template_version,
        financial_engine_version=report.financial_engine_version,
        recommendation_policy_version="1.0.0",
        rag_version=report.rag_version,
        embedding_version=report.embedding_version,
        company_name=company.name,
        ticker=ticker,
        fiscal_period=str(report.fiscal_period),
        generated_at=datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M"),
        workspace_name="EquityIQ",
    )

    safe_name = f"equityiq_{ticker}_{report.fiscal_period}_{report.id}"

    if fmt == "markdown":
        content_bytes = export_service.export_markdown(report.content)
        return Response(
            content=content_bytes,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.md"'},
        )
    elif fmt == "pdf":
        pdf_bytes = export_service.export_pdf(
            content=report.content,
            footer_text=footer,
            title=report.title,
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.pdf"'},
        )
    else:  # docx
        docx_bytes = export_service.export_docx(
            content=report.content,
            footer_text=footer,
            title=report.title,
        )
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.docx"'},
        )
