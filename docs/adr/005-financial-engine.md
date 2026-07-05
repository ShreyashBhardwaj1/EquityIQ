# ADR 005: Pure Python Financial Engine and Data Precedence

## Status
Proposed & Approved

## Problem
In financial analysis, calculations must be precise, deterministic, and traceable. Letting the LLM perform mathematical equations or estimate values (such as calculating DCF values, WACC, or ratios) is unacceptable due to the risk of hallucinations. We must also reconcile conflicting inputs from financial filings (extracted) versus live market APIs (like yfinance).

## Decision
1. **Separation of Concerns**: The LLM's role is strictly limited to qualitative narrative synthesis. All math and financial calculations (DCF, WACC, ratios, comps) are implemented in pure, unit-tested Python inside the `domain/rules/` layer.
2. **Post-Processing Validation**: Response validation checks that all numeric figures produced by the LLM match the outputs of the Python financial engine. Any mismatch triggers a regeneration or flag.
3. **Data Precedence Rules**:
   - **Historical Financials**: Filings (extracted via RAG/parsing) are authoritative.
   - **Current Market Data**: Live APIs (`yfinance`) are authoritative for share prices, market capitalization, and shares outstanding as of today.
   - **Conflict Logging**: If data from both sources mismatch by more than 0.5% (e.g. shares outstanding), we log the discrepancy in `data_source_log` and apply the filing value for historical periods and API value for current valuations.

## Alternatives Considered
- **LLM Arithmetic with Code Interpreter**: Letting the LLM generate python code and run it in a sandbox. This was rejected because it introduces complexity, latency, security risks, and is less deterministic than static, compiled-in domain logic.
- **Direct Database Math**: Performing ratio calculations inside SQL queries. Rejected as it couples business logic to database schema and database dialects.

## Trade-offs
- **Pros**:
  - Deterministic and auditable math: calculations can be verified with standard unit tests.
  - Zero hallucination rate for numbers.
  - Conflicts are resolved transparently and logged for human review.
- **Cons**:
  - Requires writing robust parser and alignment logic for financial statements.

## Consequences
- Every mathematical formula must be documented and tested against textbook hand-calculated cases.
- Any attempt to feed raw, unnormalized figures to downstream valuation services without passing through a normalization step will result in failure.
