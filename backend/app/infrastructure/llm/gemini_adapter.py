"""
Google Gemini API adapter implementation of LLMProvider.
"""

import asyncio
import logging
import time
from typing import Any, TypeVar

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from pydantic import BaseModel

from app.core.config import settings
from app.domain.interfaces.providers import LLMProvider, LLMResponse, Tool

logger = logging.getLogger("equityiq.infrastructure.llm.gemini_adapter")

T = TypeVar("T", bound=BaseModel)


class GeminiAdapter(LLMProvider):
    """
    Adapter implementing the LLMProvider protocol using the google-generativeai library.
    Supports primary (Gemini 2.5 Pro) and fallback (Gemini 2.5 Flash) model execution.
    """

    def __init__(
        self,
        api_key: str | None = None,
        primary_model: str | None = None,
        fallback_model: str | None = None,
        temperature: float | None = None,
    ) -> None:
        """
        Initialize the Gemini SDK connection.
        """
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.primary_model_name = primary_model or settings.PRIMARY_LLM_MODEL
        self.fallback_model_name = fallback_model or settings.FALLBACK_LLM_MODEL
        self.temperature = (
            temperature if temperature is not None else settings.LLM_TEMPERATURE
        )

        if self.api_key:
            genai.configure(api_key=self.api_key)  # type: ignore[attr-defined]

        else:
            logger.warning(
                "Gemini API key is not configured. Requests will fail if not mocked."
            )

    async def complete(self, prompt: str, schema: type[T] | None = None) -> LLMResponse:
        """
        Execute completion with the primary model, automatically falling back on failure.
        """
        start_time = time.perf_counter()
        model_used = self.primary_model_name
        fallback_used = False

        try:
            response = await self._generate(self.primary_model_name, prompt, schema)
        except Exception as primary_exc:
            logger.warning(
                f"Primary model {self.primary_model_name} failed: {primary_exc}. "
                f"Attempting automatic fallback to {self.fallback_model_name}."
            )
            fallback_used = True
            model_used = self.fallback_model_name
            try:
                response = await self._generate(
                    self.fallback_model_name, prompt, schema
                )
            except Exception as fallback_exc:
                logger.error(
                    f"Fallback model {self.fallback_model_name} also failed: {fallback_exc}"
                )
                raise fallback_exc

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        text = response.text if hasattr(response, "text") else ""
        structured_data = None

        if schema and text:
            try:
                structured_data = schema.model_validate_json(text)
            except Exception as parse_exc:
                logger.error(
                    f"Failed to parse structured schema from output text: {parse_exc}"
                )

        prompt_tokens = 0
        completion_tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            prompt_tokens = response.usage_metadata.prompt_token_count
            completion_tokens = response.usage_metadata.candidates_token_count

        # Log metrics via structured telemetry logger
        logger.info(
            f"RAG Telemetry: model={model_used} latency_ms={latency_ms:.2f} "
            f"prompt_tokens={prompt_tokens} completion_tokens={completion_tokens} "
            f"fallback_used={fallback_used}"
        )

        return LLMResponse(
            text=text,
            structured_data=structured_data,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
        )

    async def _generate(
        self, model_name: str, prompt: str, schema: type[T] | None = None
    ) -> Any:
        """
        Helper method executing generate_content inside the current event loop.
        """
        model = genai.GenerativeModel(model_name)  # type: ignore[attr-defined]

        config_args: dict[str, Any] = {
            "temperature": self.temperature,
        }
        if schema:
            config_args["response_mime_type"] = "application/json"
            config_args["response_schema"] = schema

        generation_config = GenerationConfig(**config_args)
        loop = asyncio.get_running_loop()

        def _sync_call() -> Any:
            return model.generate_content(prompt, generation_config=generation_config)

        return await loop.run_in_executor(None, _sync_call)

    async def complete_with_tools(self, prompt: str, tools: list[Tool]) -> LLMResponse:
        """
        Tool calling placeholder.
        """
        raise NotImplementedError(
            "Tool calling complete_with_tools is not implemented."
        )
