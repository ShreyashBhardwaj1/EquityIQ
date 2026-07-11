## Section 5: Risk Assessment

Write a risk narrative for **{company_name}** ({ticker}) based on detected risk flags.

### DETERMINISTIC DATA — USE VERBATIM:
The following risks have been detected by the EquityIQ Risk Engine. Do not add or remove any risk factors.

Total Risks Detected: {total_risk_count} `[computed: total_risk_count]`
Severe Risks: **{severe_risk_count}** `[computed: severe_risk_count]`

{risks_detail_block}

### Instructions:
1. Discuss each detected risk in 2–3 sentences, referencing its severity and the supporting evidence verbatim.
2. Start with the most severe risks.
3. Do NOT invent risk categories not listed above.
4. Conclude with an overall risk posture statement.

### Format:
```markdown
## Risk Assessment

> ⚡ _Values marked `[computed]` are deterministic outputs from the EquityIQ Financial Intelligence Engine v{financial_engine_version}._

**Total Detected Risks:** {total_risk_count} | **Severe:** {severe_risk_count} [computed: severe_risk_count]

### [Risk Category Name] — [Severity Level]
> Supporting Evidence: "[verbatim evidence]"

[2–3 sentence analysis]

[repeat for each risk]

### Overall Risk Posture
[1 paragraph summary]
```
