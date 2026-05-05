def get_metric_explanation(metric_name):
    """
    Return a plain-English explanation for dashboard metrics.
    """

    explanations = {
        "Expected Price Target": (
            "Probability-weighted estimate of fair value based on bear, base, and bull scenarios."
        ),
        "Expected Return": (
            "Potential upside or downside before applying business-specific adjustments."
        ),
        "Diversification Adj.": (
            "Adjustment for revenue concentration. High HIV dependence lowers confidence."
        ),
        "Capital Allocation Adj.": (
            "Adjustment for dividends and buybacks. Strong shareholder returns can support downside protection."
        ),
        "Segment Role Adj.": (
            "Adjustment based on whether revenue comes from core, growth, legacy, or other segments."
        ),
        "Forward Mix Adj.": (
            "Adjustment based on projected future revenue mix. Lower future HIV dependence and higher oncology/other exposure can support upside."
        ),
        "Risk-Adjusted Return": (
            "Expected return after applying the composite risk haircut."
        ),
        "Signal": (
            "Directional read of whether the risk-adjusted return appears attractive, moderate, neutral, or unattractive."
        ),
        "Confidence": (
            "Measures confidence in the signal based on risk, volatility, analyst dispersion, and financial quality."
        ),
        "Composite Score": (
            "Overall risk score combining market, product concentration, strategy, valuation, FX, and financial quality."
        ),
        "Product Concentration": (
            "Measures reliance on HIV revenue. Higher concentration increases strategic risk."
        ),
        "Strategic Alignment": (
            "Measures whether current revenue mix aligns with Gilead's future strategy."
        ),
        "Financial Quality": (
            "Measures financial strength using margins, cash flow, revenue growth, and debt burden."
        ),
    }

    return explanations.get(metric_name, "No explanation available.")


def explain_metric(metric_name):
    """
    Format a metric explanation for Streamlit markdown.
    """

    return f"**Why it matters:** {get_metric_explanation(metric_name)}"


def get_headline_signal(signal, confidence, expected_return):
    """
    Generate a headline interpretation for the expected return signal.
    """

    confidence = confidence or {}
    conf_label = confidence.get("confidence_label", "Moderate")

    if signal == "Attractive":
        posture = (
            "Strong Upside Signal"
            if conf_label == "High"
            else "Upside Signal - Monitor Execution Risks"
        )
    elif signal == "Moderate":
        posture = "Moderate Upside - Needs Confirmation"
    elif signal == "Neutral":
        posture = "Balanced Risk/Reward - No Clear Edge"
    else:
        posture = "Downside Risk Dominant - Caution Warranted"

    direction = "Upside" if expected_return > 0 else "Downside"

    return f"{posture} ({direction} Bias, {conf_label} Confidence)"


def get_catalyst_trigger_line(signal, confidence, risk_adjusted_return):
    """
    Generate a catalyst/risk trigger line based on the current signal.
    """

    if signal in ["Attractive", "Moderate"]:
        return (
            "Upside requires pipeline execution, oncology growth traction, and stable financial performance. "
            "Downside risk increases if pipeline setbacks occur, concentration risk rises, or volatility expands."
        )

    if signal == "Neutral":
        return (
            "Signal requires confirmation. Improvement depends on stronger expected return, valuation expansion, "
            "or pipeline catalysts. Deterioration would come from rising risk or execution uncertainty."
        )

    return (
        "Signal may stabilize if valuation support or financial quality improves. Further downside risk if "
        "execution weakens or risk-adjusted return remains negative."
    )


def get_expected_return_narrative(
    expected_return,
    risk_adjusted_return,
    signal,
    confidence,
    diversification_adjustment,
    capital_allocation_adjustment,
    segment_role_adjustment=0,
    forward_mix_adjustment=0,
):
    """
    Generate a concise narrative explaining the expected return bridge.
    """

    confidence = confidence or {}
    confidence_label = confidence.get("confidence_label", "Moderate")

    total_adjustment = (
        diversification_adjustment
        + capital_allocation_adjustment
        + segment_role_adjustment
        + forward_mix_adjustment
    )

    return (
        f"Expected return begins at {expected_return:.1f}%. "
        f"Business-specific adjustments total {total_adjustment:.1f} pts, including "
        f"diversification ({diversification_adjustment:.1f} pts), capital allocation "
        f"({capital_allocation_adjustment:.1f} pts), segment role "
        f"({segment_role_adjustment:.1f} pts), and forward revenue mix "
        f"({forward_mix_adjustment:.1f} pts). "
        f"After applying the composite risk haircut, risk-adjusted return is {risk_adjusted_return:.1f}%. "
        f"Current signal: **{signal}** with {confidence_label.lower()} confidence. "
        "This should be interpreted as a directional security intelligence signal rather than a precise forecast."
    )
