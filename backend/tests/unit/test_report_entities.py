"""
Unit tests for FinancialReport and FinancialReportVersion domain entities.
"""

from datetime import datetime
from uuid import uuid4

from app.domain.entities.report import (
    REPORT_TEMPLATE_VERSION,
    FinancialReport,
    FinancialReportVersion,
    ReportStatus,
)
from app.domain.value_objects.fiscal_period import FiscalPeriod


class TestReportStatus:
    def test_all_status_values(self) -> None:
        assert ReportStatus.PENDING == "PENDING"
        assert ReportStatus.GENERATING == "GENERATING"
        assert ReportStatus.COMPLETED == "COMPLETED"
        assert ReportStatus.FAILED == "FAILED"

    def test_status_is_str_enum(self) -> None:
        assert isinstance(ReportStatus.PENDING, str)


class TestFinancialReport:
    def _make_report(self, **overrides: object) -> FinancialReport:
        defaults: dict[str, object] = {
            "id": uuid4(),
            "company_id": uuid4(),
            "workspace_id": uuid4(),
            "fiscal_period": FiscalPeriod("FY", 2024),
            "title": "Test Investment Report",
            "content": "",
            "status": ReportStatus.PENDING,
            "generated_by": uuid4(),
        }
        defaults.update(overrides)
        return FinancialReport(**defaults)  # type: ignore[arg-type]

    def test_default_status_is_pending(self) -> None:
        report = self._make_report()
        assert report.status == ReportStatus.PENDING

    def test_default_content_is_empty(self) -> None:
        report = self._make_report()
        assert report.content == ""

    def test_default_template_version(self) -> None:
        report = self._make_report()
        assert report.report_template_version == REPORT_TEMPLATE_VERSION

    def test_default_generation_duration_is_zero(self) -> None:
        report = self._make_report()
        assert report.generation_duration == 0.0

    def test_error_message_defaults_to_none(self) -> None:
        report = self._make_report()
        assert report.error_message is None

    def test_celery_task_id_defaults_to_none(self) -> None:
        report = self._make_report()
        assert report.celery_task_id is None

    def test_model_copy_updates_status(self) -> None:
        report = self._make_report()
        completed = report.model_copy(update={"status": ReportStatus.COMPLETED})
        assert completed.status == ReportStatus.COMPLETED
        # Original is unchanged (Pydantic model)
        assert report.status == ReportStatus.PENDING

    def test_model_copy_updates_content(self) -> None:
        report = self._make_report()
        content = "# My Report\n\nThis is the content."
        updated = report.model_copy(update={"content": content})
        assert updated.content == content

    def test_fiscal_period_stored_correctly(self) -> None:
        fp = FiscalPeriod("Q3", 2023)
        report = self._make_report(fiscal_period=fp)
        assert str(report.fiscal_period) == "Q3-2023"

    def test_failed_report_has_error_message(self) -> None:
        report = self._make_report(
            status=ReportStatus.FAILED, error_message="LLM generation timeout"
        )
        assert report.status == ReportStatus.FAILED
        assert report.error_message == "LLM generation timeout"

    def test_completed_report_with_duration(self) -> None:
        report = self._make_report(
            status=ReportStatus.COMPLETED,
            content="# Report\n\nComplete content here.",
            generation_duration=42.5,
            generated_at=datetime.utcnow(),
        )
        assert report.status == ReportStatus.COMPLETED
        assert report.generation_duration == 42.5
        assert report.generated_at is not None


class TestFinancialReportVersion:
    def test_version_entity_creation(self) -> None:
        report_id = uuid4()
        version = FinancialReportVersion(
            id=uuid4(),
            report_id=report_id,
            version=1,
            content="# Version 1\n\nOriginal content.",
            changed_by_id=uuid4(),
        )
        assert version.report_id == report_id
        assert version.version == 1
        assert version.change_reason is None

    def test_version_with_reason(self) -> None:
        version = FinancialReportVersion(
            id=uuid4(),
            report_id=uuid4(),
            version=2,
            content="# Version 2\n\nUpdated content.",
            changed_by_id=uuid4(),
            change_reason="Updated after new data",
        )
        assert version.version == 2
        assert version.change_reason == "Updated after new data"

    def test_version_changed_at_defaults_to_now(self) -> None:
        before = datetime.utcnow()
        version = FinancialReportVersion(
            id=uuid4(),
            report_id=uuid4(),
            version=1,
            content="Test",
            changed_by_id=uuid4(),
        )
        after = datetime.utcnow()
        assert before <= version.changed_at <= after
