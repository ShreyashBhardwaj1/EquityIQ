## Section 1: Executive Summary

Write a 3–4 paragraph executive summary for **{company_name}** ({ticker}) for the period **{fiscal_period}**.

### DETERMINISTIC DATA — USE VERBATIM:
- Overall Financial Health Score: **{overall_score}** / 10.0 `[computed: overall_score]`
- Recommendation: **{recommendation_rating}** `[computed: recommendation_rating]`
- Severe Risk Count: **{severe_risk_count}** `[computed: severe_risk_count]`
- Confidence Level: **{health_confidence:.1%}** `[computed: health_confidence]`

### Instructions:
1. Open with a one-sentence company and period overview.
2. Summarize the overall financial health score and what it implies.
3. State the investment recommendation and its primary rationale (from `recommendation_rationale`).
4. Close with a risk overview sentence referencing `severe_risk_count`.

### Format:
```markdown
## Executive Summary

> ⚡ _Values marked `[computed]` are deterministic outputs from the EquityIQ Financial Intelligence Engine v{financial_engine_version}._

[4-paragraph narrative following the instructions above]
```
