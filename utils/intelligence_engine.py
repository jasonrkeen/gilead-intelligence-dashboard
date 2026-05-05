def compute_security_signal(financial_summary, fx_metrics, segment_metrics):
    """
    Compute a simple directional security signal.

    The signal combines:
    - Profitability
    - Revenue growth
    - Debt coverage
    - FX risk regime
    - Product concentration penalty

    This is a screening signal, not a standalone investment recommendation.
    """

    financial_summary = financial_summary or {}
    fx_metrics = fx_metrics or {}
    segment_metrics = segment_metrics or {}

    score = 0

    # Profitability
    if financial_summary.get("operating_margin", 0) > 25:
        score += 1

    # Growth
    if financial_summary.get("revenue_growth", 0) > 3:
        score += 1

    # Balance sheet
    if financial_summary.get("debt_ocf", 999) < 3:
        score += 1

    # FX risk
    if fx_metrics.get("fx_risk_regime") == "Low":
        score += 1

    # Concentration penalty
    hiv_concentration = segment_metrics.get(
        "hiv_pct",
        segment_metrics.get("hiv_concentration", 0),
    )

    if hiv_concentration > 70:
        score -= 1

    signal_map = {
        4: "Attractive",
        3: "Attractive",
        2: "Moderate",
        1: "Neutral",
        0: "Unattractive",
        -1: "High Risk",
    }

    return {
        "signal": signal_map.get(score, "Neutral"),
        "score": score,
    }
