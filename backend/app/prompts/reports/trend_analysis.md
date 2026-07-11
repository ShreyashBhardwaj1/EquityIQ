## Section 4: Trend Analysis

Write a trend analysis for **{company_name}** ({ticker}) across multiple reporting periods.

### DETERMINISTIC DATA — USE VERBATIM:
The following trend states have been classified by the EquityIQ trend engine:

| Metric | Trend State |
|---|---|
| Revenue | {trend_revenue} `[computed: trend_revenue]` |
| Net Income | {trend_net_income} `[computed: trend_net_income]` |
| Operating Cash Flow | {trend_ocf} `[computed: trend_ocf]` |

Trend states are one of: ACCELERATING, DECELERATING, RECOVERY, DECLINE, STABLE, VOLATILE.

### Instructions:
1. Explain each trend state in 2–3 sentences with respect to what it means for the business.
2. Discuss cross-metric relationships (e.g., revenue growth vs. profitability trends).
3. Do NOT invent historical values or growth rates not provided above.

### Format:
```markdown
## Trend Analysis

> ⚡ _Values marked `[computed]` are deterministic outputs from the EquityIQ Financial Intelligence Engine v{financial_engine_version}._

### Revenue Trend: {trend_revenue} [computed: trend_revenue]
[2–3 sentence narrative]

### Net Income Trend: {trend_net_income} [computed: trend_net_income]
[2–3 sentence narrative]

### Operating Cash Flow Trend: {trend_ocf} [computed: trend_ocf]
[2–3 sentence narrative]

### Cross-Metric Observations
[1–2 paragraph synthesis]
```
