"""
Integration tests for database repository implementations.
"""

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.entities.company import Company
from app.domain.entities.document import Document, DocumentType, ParsingStatus
from app.domain.entities.financial_statement import (
    FinancialStatement,
    NormalizationAdjustment,
    StatementType,
)
from app.domain.entities.user import User, UserRole
from app.domain.entities.workspace import Workspace
from app.domain.value_objects.exchange import Exchange
from app.domain.value_objects.fiscal_period import FiscalPeriod
from app.domain.value_objects.ticker import Ticker
from app.infrastructure.db.models.base import Base
from app.infrastructure.db.repositories.company_repo import (
    SQLAlchemyCompanyRepository,
)
from app.infrastructure.db.repositories.document_repo import (
    SQLAlchemyDocumentRepository,
)
from app.infrastructure.db.repositories.statement_repo import (
    SQLAlchemyFinancialStatementRepository,
)
from app.infrastructure.db.repositories.user_repo import SQLAlchemyUserRepository
from app.infrastructure.db.repositories.workspace_repo import (
    SQLAlchemyWorkspaceRepository,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Sets up an in-memory SQLite database and yields an active session.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Initialize all table schemas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_company_repository_crud(db_session: AsyncSession) -> None:
    """
    Verifies saving and querying companies through SQLAlchemyCompanyRepository.
    """
    repo = SQLAlchemyCompanyRepository(db_session)
    ws_id = uuid.uuid4()
    company = Company(
        id=uuid.uuid4(),
        workspace_id=ws_id,
        ticker=Ticker("AAPL"),
        exchange=Exchange("NASDAQ"),
        name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        country="US",
        fiscal_year_end="09-30",
        currency="USD",
    )

    # Test Save (insert)
    saved = await repo.save(company)
    assert saved.ticker.symbol == "AAPL"

    # Test Get by ID
    fetched_by_id = await repo.get_by_id(ws_id, company.id)
    assert fetched_by_id is not None
    assert fetched_by_id.name == "Apple Inc."

    # Test Get by Ticker
    fetched_by_ticker = await repo.get_by_ticker(ws_id, "AAPL")
    assert fetched_by_ticker is not None
    assert fetched_by_ticker.id == company.id

    # Test Update Save
    updated_company = Company(
        id=company.id,
        workspace_id=ws_id,
        ticker=company.ticker,
        exchange=company.exchange,
        name="Apple Inc. Updated",
        sector=company.sector,
        industry=company.industry,
        country="US",
        fiscal_year_end=company.fiscal_year_end,
        currency=company.currency,
    )
    saved_update = await repo.save(updated_company)
    assert saved_update.name == "Apple Inc. Updated"


@pytest.mark.asyncio
async def test_document_repository_crud(db_session: AsyncSession) -> None:
    """
    Verifies document mapping and query helpers in SQLAlchemyDocumentRepository.
    """
    # Create test user and workspace first to satisfy Foreign Key constraints
    user_repo = SQLAlchemyUserRepository(db_session)
    user = User(
        id=uuid.uuid4(),
        email="test_doc@equityiq.com",
        hashed_password="somehashpassword",
        role=UserRole.ANALYST,
    )
    await user_repo.save(user)

    workspace_repo = SQLAlchemyWorkspaceRepository(db_session)
    workspace = Workspace(
        id=uuid.uuid4(),
        name="Test Doc Workspace",
        owner_id=user.id,
    )
    await workspace_repo.save(workspace)

    # Create parent company first to satisfy Foreign Key constraints
    comp_repo = SQLAlchemyCompanyRepository(db_session)
    company = Company(
        id=uuid.uuid4(),
        workspace_id=workspace.id,
        ticker=Ticker("MSFT"),
        exchange=Exchange("NASDAQ"),
        name="Microsoft Corp.",
        sector="Technology",
        industry="Software",
        country="US",
        fiscal_year_end="06-30",
        currency="USD",
    )
    await comp_repo.save(company)

    doc_repo = SQLAlchemyDocumentRepository(db_session)
    document = Document(
        id=uuid.uuid4(),
        workspace_id=workspace.id,
        company_id=company.id,
        doc_type=DocumentType.TEN_K,
        fiscal_period=FiscalPeriod("FY", 2024),
        storage_path="/path/to/msft_10k.pdf",
        parsing_status=ParsingStatus.PENDING,
        parsing_confidence=0.98,
        uploaded_by=user.id,
    )

    # Test Save
    saved = await doc_repo.save(document)
    assert saved.doc_type == DocumentType.TEN_K

    # Test Get by ID
    fetched = await doc_repo.get(document.id)
    assert fetched is not None
    assert fetched.storage_path == "/path/to/msft_10k.pdf"

    # Test List by Company
    docs = await doc_repo.list_by_company(company.id)
    assert len(docs) == 1
    assert docs[0].id == document.id


@pytest.mark.asyncio
async def test_financial_statement_repository_crud(
    db_session: AsyncSession,
) -> None:
    """
    Verifies statement serialization/deserialization and query helpers.
    """
    # Create test user and workspace first to satisfy Foreign Key constraints
    user_repo = SQLAlchemyUserRepository(db_session)
    user = User(
        id=uuid.uuid4(),
        email="test_stmt@equityiq.com",
        hashed_password="somehashpassword",
        role=UserRole.ANALYST,
    )
    await user_repo.save(user)

    workspace_repo = SQLAlchemyWorkspaceRepository(db_session)
    workspace = Workspace(
        id=uuid.uuid4(),
        name="Test Stmt Workspace",
        owner_id=user.id,
    )
    await workspace_repo.save(workspace)

    # Create parent company and document to satisfy Foreign Key constraints
    comp_repo = SQLAlchemyCompanyRepository(db_session)
    company = Company(
        id=uuid.uuid4(),
        workspace_id=workspace.id,
        ticker=Ticker("GOOGL"),
        exchange=Exchange("NASDAQ"),
        name="Alphabet Inc.",
        sector="Technology",
        industry="Internet Services",
        country="US",
        fiscal_year_end="12-31",
        currency="USD",
    )
    await comp_repo.save(company)

    doc_repo = SQLAlchemyDocumentRepository(db_session)
    document = Document(
        id=uuid.uuid4(),
        workspace_id=workspace.id,
        company_id=company.id,
        doc_type=DocumentType.TEN_Q,
        fiscal_period=FiscalPeriod("Q1", 2024),
        storage_path="/path/to/googl_q1.pdf",
        parsing_status=ParsingStatus.COMPLETED,
        parsing_confidence=1.0,
        uploaded_by=user.id,
    )
    await doc_repo.save(document)

    # Setup statement with an adjustment
    stmt_repo = SQLAlchemyFinancialStatementRepository(db_session)
    adjustment = NormalizationAdjustment(
        line_item="revenue",
        adjustment=-500000.0,
        reason="exclude one-time gain",
        source_document_id=document.id,
        source_page=10,
    )
    statement = FinancialStatement(
        id=uuid.uuid4(),
        company_id=company.id,
        document_id=document.id,
        statement_type=StatementType.INCOME,
        fiscal_period=FiscalPeriod("Q1", 2024),
        line_items={"revenue": 80000000.0, "net_income": 20000000.0},
        normalization_adjustments=[adjustment],
        normalized_line_items={"revenue": 79500000.0, "net_income": 19500000.0},
        extraction_confidence={"revenue": 1.0, "net_income": 0.95},
    )

    # Test Save
    saved = await stmt_repo.save(statement)
    assert saved.statement_type == StatementType.INCOME
    assert len(saved.normalization_adjustments) == 1

    # Test Get by ID
    fetched = await stmt_repo.get(statement.id)
    assert fetched is not None
    assert fetched.line_items["revenue"] == 80000000.0
    assert fetched.normalization_adjustments[0].reason == "exclude one-time gain"

    # Test Get by Period
    fetched_period = await stmt_repo.get_by_period(company.id, "income", "Q1-2024")
    assert fetched_period is not None
    assert fetched_period.id == statement.id


@pytest.mark.asyncio
async def test_ratio_repository_crud(db_session: AsyncSession) -> None:
    from app.domain.entities.ratio import Ratio
    from app.infrastructure.db.repositories.ratio_repo import SQLAlchemyRatioRepository

    repo = SQLAlchemyRatioRepository(db_session)
    comp_id = uuid.uuid4()
    ratio = Ratio(
        id=uuid.uuid4(),
        company_id=comp_id,
        fiscal_period=FiscalPeriod("FY", 2024),
        ratio_name="current_ratio",
        value=1.5,
        formula_version="1.0.0",
    )

    await repo.save_batch([ratio])
    ratios = await repo.get_by_period(comp_id, "FY-2024")
    assert len(ratios) == 1
    assert ratios[0].value == 1.5

    await repo.delete_by_period(comp_id, "FY-2024")
    ratios_deleted = await repo.get_by_period(comp_id, "FY-2024")
    assert len(ratios_deleted) == 0


@pytest.mark.asyncio
async def test_health_score_repository_crud(db_session: AsyncSession) -> None:
    from app.domain.entities.financial_intelligence import FinancialHealthScore
    from app.infrastructure.db.repositories.health_score_repo import (
        SQLAlchemyHealthScoreRepository,
    )

    repo = SQLAlchemyHealthScoreRepository(db_session)
    comp_id = uuid.uuid4()
    health = FinancialHealthScore(
        id=uuid.uuid4(),
        company_id=comp_id,
        fiscal_period=FiscalPeriod("FY", 2024),
        overall_score=7.5,
        category_scores={"liquidity": 8.0, "profitability": 7.0},
        weights={"liquidity": 0.5, "profitability": 0.5},
        score_explanation=["Strong overall health"],
        confidence=1.0,
        percentile=None,
        ratio_engine_version="1.0.0",
    )

    await repo.save(health)
    fetched = await repo.get(comp_id, "FY-2024")
    assert fetched is not None
    assert fetched.overall_score == 7.5

    await repo.delete(comp_id, "FY-2024")
    fetched_deleted = await repo.get(comp_id, "FY-2024")
    assert fetched_deleted is None


@pytest.mark.asyncio
async def test_risk_assessment_repository_crud(db_session: AsyncSession) -> None:
    from app.domain.entities.financial_intelligence import RiskAssessment, SeverityLevel
    from app.infrastructure.db.repositories.risk_assessment_repo import (
        SQLAlchemyRiskAssessmentRepository,
    )

    repo = SQLAlchemyRiskAssessmentRepository(db_session)
    comp_id = uuid.uuid4()
    risk = RiskAssessment(
        id=uuid.uuid4(),
        company_id=comp_id,
        fiscal_period=FiscalPeriod("FY", 2024),
        risk_category="liquidity",
        severity=SeverityLevel.SEVERE,
        confidence=1.0,
        supporting_evidence="Current ratio below 1.0",
        ratio_engine_version="1.0.0",
    )

    await repo.save_batch([risk])
    risks = await repo.list_by_period(comp_id, "FY-2024")
    assert len(risks) == 1
    assert risks[0].severity == SeverityLevel.SEVERE

    await repo.delete_by_period(comp_id, "FY-2024")
    risks_deleted = await repo.list_by_period(comp_id, "FY-2024")
    assert len(risks_deleted) == 0


@pytest.mark.asyncio
async def test_recommendation_repository_crud(db_session: AsyncSession) -> None:
    # Setup parent User and Company first to satisfy Foreign Key constraints for triggered_by and company_id
    user_repo = SQLAlchemyUserRepository(db_session)
    user = User(
        id=uuid.uuid4(),
        email="test_rec@equityiq.com",
        hashed_password="somehashpassword",
        role=UserRole.ANALYST,
    )
    await user_repo.save(user)

    workspace_repo = SQLAlchemyWorkspaceRepository(db_session)
    workspace = Workspace(
        id=uuid.uuid4(),
        name="Test Rec Workspace",
        owner_id=user.id,
    )
    await workspace_repo.save(workspace)

    comp_repo = SQLAlchemyCompanyRepository(db_session)
    company = Company(
        id=uuid.uuid4(),
        workspace_id=workspace.id,
        ticker=Ticker("NFLX"),
        exchange=Exchange("NASDAQ"),
        name="Netflix Inc.",
        sector="Technology",
        industry="Entertainment",
        country="US",
        fiscal_year_end="12-31",
        currency="USD",
    )
    await comp_repo.save(company)

    from app.domain.entities.financial_intelligence import (
        RecommendationHistory,
        RecommendationPolicy,
    )
    from app.domain.entities.recommendation import Recommendation, RecommendationType
    from app.infrastructure.db.repositories.recommendation_repo import (
        SQLAlchemyRecommendationRepository,
    )

    repo = SQLAlchemyRecommendationRepository(db_session)

    # 1. Policy test
    policy = RecommendationPolicy(
        policy_id=uuid.uuid4(),
        policy_name="Standard Test Policy",
        policy_version="1.0.0",
        health_score_thresholds={"buy": 7.0},
        max_severe_risks_allowed={"buy": 1},
        requires_positive_growth=["buy"],
        is_active=True,
    )
    await repo.save_policy(policy)
    fetched_policy = await repo.get_active_policy()
    assert fetched_policy is not None
    assert fetched_policy.policy_version == "1.0.0"

    # 2. Recommendation test
    rec = Recommendation(
        id=uuid.uuid4(),
        company_id=company.id,
        recommendation=RecommendationType.BUY,
        composite_score=7.5,
        rationale="Passes buy thresholds",
        fiscal_period=FiscalPeriod("FY", 2024),
    )
    await repo.save(rec)
    fetched_rec = await repo.get(company.id, "FY-2024")
    assert fetched_rec is not None
    assert fetched_rec.composite_score == 7.5

    # 3. RecommendationHistory test
    history = RecommendationHistory(
        id=uuid.uuid4(),
        recommendation_id=rec.id,
        company_id=company.id,
        fiscal_period=FiscalPeriod("FY", 2024),
        rating=RecommendationType.BUY,
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        composite_score=7.5,
        reasoning_steps=["Checks passed"],
        triggered_by=user.id,
    )
    await repo.save_history(history)
    histories = await repo.list_history(company.id, "FY-2024")
    assert len(histories) == 1
    assert histories[0].triggered_by == user.id

    # 4. Delete test
    await repo.delete(company.id, "FY-2024")
    fetched_deleted_rec = await repo.get(company.id, "FY-2024")
    assert fetched_deleted_rec is None

