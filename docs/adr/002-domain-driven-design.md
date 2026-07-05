# ADR 002: Domain-Driven Design (DDD)

## Status
Proposed & Approved

## Problem
Financial analysis software deals with complex domain concepts (e.g. currency, fiscal periods, tickers, companies, financial statements, valuations). Representing these purely as primitive data structures (like dictionaries or strings) leads to code duplication, validation scattering, and a high risk of runtime calculation errors (e.g., comparing numbers in different currencies or confusing historical statement periods).

## Decision
We adopt Domain-Driven Design (DDD) patterns for our core Domain layer:
- **Entities**: Objects with distinct identities that persist over time (e.g., `Company`, `Document`, `FinancialStatement`, `Valuation`, `Recommendation`).
- **Value Objects**: Immutable data packages defined by their attributes rather than an identity (e.g., `Money` with amount/currency, `FiscalPeriod` with period/year, `Ticker`).
- **Repositories (Interfaces)**: Encapsulate data access logic via abstraction (e.g., `CompanyRepository`, `DocumentRepository`).
- **Domain Rules**: Pure functions encapsulating business math (e.g., DCF calculation, ratio formulas, scoring rubrics) that validate their constraints immediately (e.g., WACC must exceed terminal growth).

## Alternatives Considered
- **Anemic Domain Model**: Modeling data structures as simple structs or dictionaries with all behavior living in flat utility files. This leads to weak encapsulation and high probability of domain rules violation.
- **Active Record Pattern**: Combining entity data and DB operations in one class. Rejected because it couples Domain logic with Infrastructure database drivers.

## Trade-offs
- **Pros**:
  - Encapsulates domain validation (e.g. `Money` handles addition rules, preventing adding USD to EUR).
  - Clean separation of business logic from representation.
  - Test cases read like finance textbooks rather than database or web scripts.
- **Cons**:
  - Requires translating domain models to DTOs/ORM models.
  - High degree of precision required to design and write type-safe domain entities.

## Consequences
- Domain objects are created using Pydantic v2 (or dataclasses) for immediate structure and type validation.
- Services never directly execute database queries; they use constructor-injected `Repository` abstractions.
