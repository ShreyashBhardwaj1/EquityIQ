"""
RAGService orchestrator application service.
"""

import logging
import time
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.citation_service import CitationService
from app.application.services.confidence_scorer import ConfidenceScorer
from app.application.services.context_assembler import ContextAssembler
from app.application.services.conversation_service import ConversationService
from app.application.services.hybrid_search_service import HybridSearchService
from app.application.services.prompt_builder import PromptBuilder
from app.application.services.prompt_injection_guard import PromptInjectionGuard
from app.application.services.response_validator import ResponseValidator
from app.application.services.token_budget_manager import TokenBudgetManager
from app.core.config import settings
from app.domain.entities.conversation import Citation, LLMRequest
from app.domain.entities.retrieval import RetrievalQuery
from app.domain.interfaces.providers import LLMProvider
from app.infrastructure.parsers.pdf_parser import PARSER_VERSION

logger = logging.getLogger("equityiq.application.rag_service")


class RAGService:
    """
    Orchestrates the entire Retrieval-Augmented Generation (RAG) lifecycle,
    including injection checks, hybrid retrieval, budget management, model generation,
    citation formatting, and conversation persistence.
    """

    def __init__(
        self,
        hybrid_search_service: HybridSearchService,
        prompt_injection_guard: PromptInjectionGuard,
        context_assembler: ContextAssembler,
        token_budget_manager: TokenBudgetManager,
        prompt_builder: PromptBuilder,
        llm_provider: LLMProvider,
        response_validator: ResponseValidator,
        confidence_scorer: ConfidenceScorer,
        citation_service: CitationService,
        conversation_service: ConversationService,
    ) -> None:
        self.hybrid_search = hybrid_search_service
        self.injection_guard = prompt_injection_guard
        self.assembler = context_assembler
        self.budget_manager = token_budget_manager
        self.prompt_builder = prompt_builder
        self.llm_provider = llm_provider
        self.validator = response_validator
        self.scorer = confidence_scorer
        self.citation_service = citation_service
        self.conversation_service = conversation_service

    async def execute_rag(
        self,
        db_session: AsyncSession,
        user_query: str,
        workspace_id: UUID,
        user_id: UUID,
        company_id: UUID | None = None,
        conversation_id: UUID | None = None,
        limit: int = 8,
    ) -> dict[str, Any]:
        """
        Executes the full RAG pipeline exactly according to instructions.
        """
        start_total = time.perf_counter()

        # Step 1: Prompt Injection Guard (scan user query)
        self.injection_guard.validate_text(user_query, source_label="User Query")

        # Step 2: Hybrid Retrieval (retrieve top context chunks)
        start_retrieval = time.perf_counter()
        retrieval_query = RetrievalQuery(
            query_text=user_query,
            workspace_id=workspace_id,
            company_id=company_id,
            limit=limit,
            offset=0,
        )

        raw_results = await self.hybrid_search.search(db_session, retrieval_query)
        retrieval_latency = (time.perf_counter() - start_retrieval) * 1000.0

        # Step 3: Run Prompt Injection Guard on retrieved chunks content
        for res in raw_results:
            self.injection_guard.validate_text(
                res.content, source_label=f"Chunk {res.chunk_id}"
            )

        # Step 4: Resolve conversation memory turns if conversation_id provided
        recent_messages = []
        summary = None
        if conversation_id:
            recent_messages = await self.conversation_service.get_active_messages(
                conversation_id, workspace_id
            )
            conv = await self.conversation_service.get_conversation(
                conversation_id, workspace_id
            )
            summary = conv.summary

        # Step 5: Token Budget Manager (prune history turns, then chunks to fit 20k tokens limit)
        system_instructions = self.prompt_builder.base_instructions
        active_messages, active_results = self.budget_manager.prune_history_and_context(
            system_instructions=system_instructions,
            user_query=user_query,
            recent_messages=recent_messages,
            summary=summary,
            retrieval_results=raw_results,
        )

        # Step 6: Context Assembler (deduplicate, merge adjacent chunks, group by document)
        context_text, merged_chunks = await self.assembler.assemble_context(
            active_results
        )

        # Step 6b: If company_id is provided, fetch pre-computed financial intelligence data
        precomputed_block = ""
        if company_id:
            try:
                from sqlalchemy import select

                from app.infrastructure.db.models.health_score import (
                    FinancialHealthScoreORM,
                )
                from app.infrastructure.db.repositories.health_score_repo import (
                    SQLAlchemyHealthScoreRepository,
                )
                from app.infrastructure.db.repositories.ratio_repo import (
                    SQLAlchemyRatioRepository,
                )
                from app.infrastructure.db.repositories.recommendation_repo import (
                    SQLAlchemyRecommendationRepository,
                )
                from app.infrastructure.db.repositories.risk_assessment_repo import (
                    SQLAlchemyRiskAssessmentRepository,
                )

                ratio_repo = SQLAlchemyRatioRepository(db_session)
                health_repo = SQLAlchemyHealthScoreRepository(db_session)
                risk_repo = SQLAlchemyRiskAssessmentRepository(db_session)
                rec_repo = SQLAlchemyRecommendationRepository(db_session)

                # Fetch most recent period's health score
                stmt = (
                    select(FinancialHealthScoreORM)
                    .where(FinancialHealthScoreORM.company_id == company_id)
                    .order_by(FinancialHealthScoreORM.fiscal_period.desc())
                    .limit(1)
                )
                db_res = await db_session.execute(stmt)
                latest_hs_orm = db_res.scalars().first()

                if latest_hs_orm:
                    period = latest_hs_orm.fiscal_period
                    health_score = health_repo._to_domain(latest_hs_orm)
                    ratios_list = await ratio_repo.get_by_period(company_id, period)
                    risks_list = await risk_repo.list_by_period(company_id, period)
                    rec = await rec_repo.get(company_id, period)

                    lines = [
                        f"=== DETERMINISTIC FINANCIAL INTELLIGENCE TABLES (PERIOD: {period}) ===",
                        f"Recommendation Rating: {rec.recommendation.value.upper() if rec else 'HOLD'}",
                        f"Overall Health Score: {health_score.overall_score:.2f} / 10.0 (Completeness Confidence: {health_score.confidence * 100:.1f}%)",
                        "Category Health Scores:",
                    ]
                    for cat, score in health_score.category_scores.items():
                        lines.append(f"  - {cat.title()}: {score:.2f} / 10.0")

                    lines.append("Deterministic Ratios calculated:")
                    for r in ratios_list:
                        lines.append(f"  - {r.ratio_name}: {r.value:.4f}")

                    lines.append("Flagged Risk Assessments:")
                    if risks_list:
                        for risk in risks_list:
                            lines.append(
                                f"  - [{risk.severity.value.upper()}] {risk.risk_category}: {risk.supporting_evidence}"
                            )
                    else:
                        lines.append("  - No risks flagged.")

                    if latest_hs_orm.score_explanation:
                        lines.append("Scoring Explanation:")
                        for expl in latest_hs_orm.score_explanation:
                            lines.append(f"  - {expl}")

                    lines.append(
                        "====================================================================="
                    )
                    precomputed_block = "\n".join(lines) + "\n\n"
            except Exception as e:
                logger.warning(
                    "Failed to fetch precomputed financial intelligence data: %s", e
                )

        if precomputed_block:
            context_text = precomputed_block + context_text

        # Step 7: Prompt Builder (Combine system instructions, context, history, and query)
        full_prompt = self.prompt_builder.build_prompt(
            context_text=context_text,
            recent_messages=active_messages,
            summary=summary,
            user_query=user_query,
        )

        # Step 8: Gemini Adapter (Complete LLM request)
        start_llm = time.perf_counter()
        llm_response = await self.llm_provider.complete(full_prompt)
        llm_latency = (time.perf_counter() - start_llm) * 1000.0

        generated_text = llm_response.text

        # Step 9: Response Validator (Verify citations, page numbers, numbers grounding)
        self.validator.validate_response(generated_text, merged_chunks)

        # Step 10: Citation Service (Parse citations and resolve to domain entities)
        assistant_message_id = uuid.uuid4()
        citations = self.citation_service.extract_citations(
            generated_text, assistant_message_id, merged_chunks
        )

        # Step 11: Confidence Scorer (Compute deterministic confidence score)
        cited_chunk_ids = [c.chunk_id for c in citations if c.chunk_id]
        confidence_score = self.scorer.calculate_score(
            retrieval_results=active_results,
            merged_chunks=merged_chunks,
            cited_chunk_ids=cited_chunk_ids,
        )

        # Step 12: Conversation Service (Save message history and citation records to DB - only for POST /chat)
        if conversation_id:
            # First, save User message
            await self.conversation_service.add_message(
                conversation_id, workspace_id, "user", user_query
            )
            # Second, save Assistant message
            assistant_msg = await self.conversation_service.add_message(
                conversation_id, workspace_id, "assistant", generated_text
            )
            # Re-map citations to point to the actual saved message id
            citations_to_save = []
            for c in citations:
                citations_to_save.append(
                    Citation(
                        id=c.id,
                        message_id=assistant_msg.id,
                        chunk_id=c.chunk_id,
                        document_id=c.document_id,
                        document_name=c.document_name,
                        page_number=c.page_number,
                        section_heading=c.section_heading,
                        snippet_preview=c.snippet_preview,
                        score=c.score,
                        rank=c.rank,
                        semantic_score=c.semantic_score,
                        keyword_score=c.keyword_score,
                        hybrid_score=c.hybrid_score,
                        retrieval_method=c.retrieval_method,
                    )
                )

            # Save citations via repository
            await self.conversation_service.citation_repo.save_batch(citations_to_save)
            citations = citations_to_save

            # Third, trigger summarization check
            await self.conversation_service.trigger_summarization_if_needed(
                conversation_id, workspace_id
            )

        # Step 11b: Grounding Scorer (Compute deterministic grounding score)
        grounding_score = self.scorer.calculate_grounding_score(generated_text)

        total_latency = (time.perf_counter() - start_total) * 1000.0

        # Step 12b: Save Telemetry record
        telemetry = LLMRequest(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            conversation_id=conversation_id,
            model_name=settings.PRIMARY_LLM_MODEL,
            prompt_version=self.prompt_builder.get_version(),
            embedding_version=settings.EMBEDDING_MODEL_NAME,
            parser_version=PARSER_VERSION,
            vector_index_version=settings.VECTOR_INDEX_VERSION,
            input_tokens=llm_response.prompt_tokens,
            output_tokens=llm_response.completion_tokens,
            retrieval_latency_ms=retrieval_latency,
            generation_latency_ms=llm_latency,
            total_latency_ms=total_latency,
            confidence_score=confidence_score,
            grounding_score=grounding_score,
        )
        await self.conversation_service.conversation_repo.save_telemetry(telemetry)

        avg_similarity = (
            sum(res.score for res in active_results) / len(active_results)
            if active_results
            else 0.0
        )

        response_data: dict[str, Any] = {
            "answer": generated_text,
            "citations": citations,
            "confidence_score": confidence_score,
            "grounding_score": grounding_score,
            "metadata": {
                "prompt_version": self.prompt_builder.get_version(),
                "model_version": settings.PRIMARY_LLM_MODEL,
                "embedding_version": settings.EMBEDDING_MODEL_NAME,
                "parser_version": PARSER_VERSION,
                "vector_index_version": settings.VECTOR_INDEX_VERSION,
                "retrieval_latency_ms": retrieval_latency,
                "llm_latency_ms": llm_latency,
                "total_latency_ms": total_latency,
                "input_tokens": llm_response.prompt_tokens,
                "output_tokens": llm_response.completion_tokens,
                "retrieved_chunks_count": len(active_results),
                "average_similarity_score": avg_similarity,
            },
        }

        metadata: dict[str, Any] = response_data["metadata"]
        logger.info(
            f"RAG Telemetry metrics logged: prompt_version={metadata['prompt_version']} "
            f"model_version={metadata['model_version']} "
            f"total_latency_ms={total_latency:.2f} "
            f"confidence_score={confidence_score:.4f} "
            f"grounding_score={grounding_score:.4f} "
            f"tokens_in={llm_response.prompt_tokens} "
            f"tokens_out={llm_response.completion_tokens} "
            f"chunks_count={len(active_results)}"
        )

        return response_data
