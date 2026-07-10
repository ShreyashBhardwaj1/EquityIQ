"""
Risk Assessment Rules Engine.
Evaluates ratios against risk thresholds to flag Low, Moderate, or Severe risks.
"""

from typing import Any

from app.domain.entities.financial_intelligence import SeverityLevel


def evaluate_risks(ratios: dict[str, float | None]) -> list[dict[str, Any]]:
    """
    Evaluates computed financial ratios to identify potential risk factors.
    Returns a list of dicts suitable for building RiskAssessment entities.
    """
    risks = []

    # 1. Liquidity Risk Evaluation
    curr_ratio = ratios.get("current_ratio")
    quick_ratio = ratios.get("quick_ratio")
    if curr_ratio is not None or quick_ratio is not None:
        evidence = []
        severity = None

        c_val = curr_ratio if curr_ratio is not None else 1.5
        q_val = quick_ratio if quick_ratio is not None else 1.0

        if c_val < 1.0 or q_val < 0.5:
            severity = SeverityLevel.SEVERE
            evidence.append(
                f"Severe liquidity distress. Current Ratio: {curr_ratio}, Quick Ratio: {quick_ratio}"
            )
        elif c_val < 1.2 or q_val < 0.8:
            severity = SeverityLevel.MODERATE
            evidence.append(
                f"Moderate liquidity strain. Current Ratio: {curr_ratio}, Quick Ratio: {quick_ratio}"
            )

        if severity:
            risks.append(
                {
                    "risk_category": "liquidity",
                    "severity": severity,
                    "confidence": 1.0
                    if (curr_ratio is not None and quick_ratio is not None)
                    else 0.7,
                    "supporting_evidence": " | ".join(evidence),
                }
            )

    # 2. Solvency / Leverage Risk Evaluation
    d2e = ratios.get("debt_to_equity")
    icr = ratios.get("interest_coverage")
    if d2e is not None or icr is not None:
        evidence = []
        severity = None

        d_val = d2e if d2e is not None else 1.0
        i_val = icr if icr is not None else 5.0

        if d_val > 2.5 or i_val < 1.5:
            severity = SeverityLevel.SEVERE
            evidence.append(
                f"High debt levels or low interest coverage. Debt to Equity: {d2e}, Interest Coverage: {icr}"
            )
        elif d_val > 1.8 or i_val < 3.0:
            severity = SeverityLevel.MODERATE
            evidence.append(
                f"Moderate debt levels. Debt to Equity: {d2e}, Interest Coverage: {icr}"
            )

        if severity:
            risks.append(
                {
                    "risk_category": "solvency",
                    "severity": severity,
                    "confidence": 1.0 if (d2e is not None and icr is not None) else 0.7,
                    "supporting_evidence": " | ".join(evidence),
                }
            )

    # 3. Profitability Risk Evaluation
    net_margin = ratios.get("net_margin")
    roe = ratios.get("roe")
    if net_margin is not None or roe is not None:
        evidence = []
        severity = None

        nm_val = net_margin if net_margin is not None else 0.10
        roe_val = roe if roe is not None else 0.10

        if nm_val < -0.05 or roe_val < -0.10:
            severity = SeverityLevel.SEVERE
            evidence.append(
                f"Significant net losses or negative ROE. Net Margin: {net_margin}, ROE: {roe}"
            )
        elif nm_val < 0.0 or roe_val < 0.0:
            severity = SeverityLevel.MODERATE
            evidence.append(
                f"Unprofitable operations. Net Margin: {net_margin}, ROE: {roe}"
            )

        if severity:
            risks.append(
                {
                    "risk_category": "profitability",
                    "severity": severity,
                    "confidence": 1.0
                    if (net_margin is not None and roe is not None)
                    else 0.7,
                    "supporting_evidence": " | ".join(evidence),
                }
            )

    # 4. Cash Flow Risk Evaluation
    op_cf_margin = ratios.get("operating_cf_margin")
    fcf = ratios.get("free_cash_flow")
    if op_cf_margin is not None or fcf is not None:
        evidence = []
        severity = None

        oc_val = op_cf_margin if op_cf_margin is not None else 0.10
        f_val = fcf if fcf is not None else 1000000.0

        if oc_val < -0.10 or f_val < -100000000.0:  # Severe negative cash flows
            severity = SeverityLevel.SEVERE
            evidence.append(
                f"Severe cash outflows. Operating CF Margin: {op_cf_margin}, FCF: {fcf}"
            )
        elif oc_val < 0.0 or f_val < 0.0:
            severity = SeverityLevel.MODERATE
            evidence.append(
                f"Negative operating or free cash flow. Operating CF Margin: {op_cf_margin}, FCF: {fcf}"
            )

        if severity:
            risks.append(
                {
                    "risk_category": "cash_flow",
                    "severity": severity,
                    "confidence": 1.0
                    if (op_cf_margin is not None and fcf is not None)
                    else 0.7,
                    "supporting_evidence": " | ".join(evidence),
                }
            )

    return risks
