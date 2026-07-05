# ADR 001: Clean Architecture Pattern

## Status
Proposed & Approved

## Problem
The core business logic of EquityIQ (financial models, DCF valuations, scoring algorithms) represents the high-value IP of the system. If this logic is tightly coupled to external frameworks (like FastAPI, SQLAlchemy, LangChain, or LlamaIndex), changes to those frameworks or a desire to run the logic offline or in alternative environments will cause major code churn. Furthermore, we must enforce that the domain layer remains free of framework dependencies in CI.

## Decision
We adopt Clean Architecture with a strict inward-pointing dependency flow:
`Domain` <- `Application` <- `Infrastructure` / `API`

1. **Domain Layer**: Contains pure business entities, value objects, rules (DCF/ratios), and interfaces.
2. **Application Layer**: Contains use-case orchestrators (Services) which depend strictly on Domain entities and abstract interfaces.
3. **Infrastructure / API Layer**: Contains concrete framework and database integrations (FastAPI routers, SQLAlchemy models, LLM providers, vector stores, news API clients).

No framework code (e.g. `fastapi`, `sqlalchemy`, `langchain`) may be imported into the `domain` module.

## Alternatives Considered
- **Traditional Model-View-Controller (MVC) or Flat Service Layer**: Under MVC, business logic and database access are tightly bound (often with ORM models owning active records). This was rejected because it violates Principle 1 and makes mocking or framework-swapping highly complex.
- **Port-and-Adapters (Hexagonal)**: Very similar to Clean Architecture. We chose Clean Architecture as it is highly compatible with Domain-Driven Design (DDD) constructs.

## Trade-offs
- **Pros**:
  - Extremely high unit testability of the core domain without mocking databases or external APIs.
  - Complete decoupling from frameworks: swapping databases or vector stores doesn't touch business rules.
  - Static analysis enforcement via `import-linter` ensures architecture rules are maintained over time by multiple engineers.
- **Cons**:
  - More file overhead: requires mapping domain entities to ORM models.
  - Initial boilerplate: must define interfaces (Protocols) first.

## Consequences
- Every new feature requires defining the Domain entity/interfaces first, then implementing the Application service, and finally writing concrete adapters in Infrastructure.
- CI pipeline will fail if a PR imports libraries like `fastapi` or `sqlalchemy` in the `domain` directory.
