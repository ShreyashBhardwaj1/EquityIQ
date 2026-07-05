# ADR 003: LLM and External Provider Abstraction

## Status
Proposed & Approved

## Problem
EquityIQ integrates with several external service APIs: LLM models (OpenAI or Gemini), financial data providers (yfinance), SEC filing downloaders, and news APIs. Direct integration with specific SDK libraries in the core application logic would make swapping providers or testing offline extremely difficult, violating Principle 4 (provider swap = config change) and Principle 13.3 (provider parity testing).

## Decision
We enforce strict abstractions using Python's `typing.Protocol` (structural subtyping) inside the domain layer. 

We define abstract contracts:
- `LLMProvider`: Standardizes text completion and tool calling.
- `EmbeddingProvider`: Standardizes embedding text to a vector.
- `CompanyRepository` / `DocumentRepository`: Standardizes core storage operations.

Implementations are written under `infrastructure/llm/` and `infrastructure/external/` (e.g. `OpenAIProvider`, `GeminiProvider`, `YFinanceClient`). The application layer accesses these dependencies *only* via dependency injection (constructor-injected protocols). The actual provider to instanciate is determined at runtime based on environment variables (`LLM_PROVIDER=openai|gemini`).

## Alternatives Considered
- **Direct Library Integration**: Using LangChain or LlamaIndex modules directly in the Application Services. Rejected because it binds the service layer to specific third-party library classes and versions, preventing easy API key or provider swaps.
- **Inheritance-based Base Classes**: Using traditional abstract base classes (`abc.ABC`). Python's `Protocol` is preferred as it supports structural typing (duck typing), which reduces boilerplate and simplifies testing mocks.

## Trade-offs
- **Pros**:
  - Allows full provider swappability (e.g., swapping OpenAI to Gemini or offline mocks is a configuration change in `.env`).
  - Enables provider parity testing (`tests/provider_parity/`) to run the exact same test suites against both OpenAI and Gemini models.
  - Simplifies testing: mocks do not need to inherit from large third-party classes.
- **Cons**:
  - Requires writing wrapper classes for every external library we consume.
  - Limits vendor-specific features to what can be generalized behind our common interface.

## Consequences
- No codebase files outside `infrastructure/` may import `openai` or `google.generativeai`.
- Mocks can be easily created for unit and integration testing without connecting to live APIs.
