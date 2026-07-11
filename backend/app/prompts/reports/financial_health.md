## Section 2: Financial Health Assessment

Write a narrative analysis of the financial health scores for **{company_name}** ({ticker}).

### DETERMINISTIC DATA — USE VERBATIM:
- Overall Score: **{overall_score}** / 10.0 `[computed: overall_score]`
- Category Scores (all out of 10.0):
{category_scores_table}
- Score Explanations:
{score_explanation_list}
- Confidence Breakdown:
{confidence_breakdown_table}

### Instructions:
1. Analyze each category score in 2–3 sentences, referencing the exact computed value.
2. Highlight the strongest and weakest categories with evidence.
3. Discuss the overall confidence level and what data limitations may affect it.

### Format:
```markdown
## Financial Health Assessment

> ⚡ _Values marked `[computed]` are deterministic outputs from the EquityIQ Financial Intelligence Engine v{financial_engine_version}._

### Overall Health Score: {overall_score}/10.0 [computed: overall_score]

| Category | Score | Interpretation |
|---|---|---|
[populated from category_scores]

[2–4 paragraphs analyzing the scores]

### Confidence Analysis
[1 paragraph discussing confidence levels]
```
