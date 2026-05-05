def get_market_implied_targets():
    """
    Market-implied analyst price target assumptions.

    These values are directional model inputs used for the dashboard's
    bear/base/bull valuation scenario analysis. They should be updated
    periodically if analyst targets or market assumptions change.
    """

    return {
        "bear_target": 120,
        "base_target": 158,
        "bull_target": 180,
    }


def get_valuation_inputs(current_price=131.65):
    """
    Build market-based valuation assumptions.
    """

    targets = get_market_implied_targets()

    return {
        "current_price": current_price,
        "fair_value_base": targets["base_target"],
        "fair_value_bull": targets["bull_target"],
        "fair_value_bear": targets["bear_target"],
        "pe_current": 18,
        "pe_historical": 23,
    }


def calculate_valuation_metrics(inputs):
    """
    Calculate valuation gap, target dispersion, and P/E discount metrics.
    """

    current = inputs.get("current_price", 0)
    fair_base = inputs.get("fair_value_base", 0)
    fair_bull = inputs.get("fair_value_bull", 0)
    fair_bear = inputs.get("fair_value_bear", 0)

    pe_current = inputs.get("pe_current", 0)
    pe_historical = inputs.get("pe_historical", 0)

    if current <= 0:
        raise ValueError("Current price must be greater than zero for valuation calculations.")

    upside_base = ((fair_base / current) - 1) * 100
    upside_bull = ((fair_bull / current) - 1) * 100
    downside_bear = ((fair_bear / current) - 1) * 100

    if pe_historical > 0:
        pe_discount = ((pe_historical - pe_current) / pe_historical) * 100
    else:
        pe_discount = 0

    target_dispersion = fair_bull - fair_bear

    return {
        "upside_base": upside_base,
        "upside_bull": upside_bull,
        "downside_bear": downside_bear,
        "pe_discount": pe_discount,
        "target_dispersion": target_dispersion,
        "bear_target": fair_bear,
        "base_target": fair_base,
        "bull_target": fair_bull,
    }


def classify_valuation_signal(upside_base):
    """
    Convert base-case upside into a valuation signal.
    """

    if upside_base > 20:
        return "Strong Undervaluation"
    elif upside_base > 10:
        return "Moderate Undervaluation"
    elif upside_base > 0:
        return "Fair Value"
    else:
        return "Overvalued"


def classify_target_dispersion(target_dispersion):
    """
    Classify analyst target dispersion.

    Wider dispersion implies greater uncertainty around the valuation range.
    """

    if target_dispersion > 60:
        return "High"
    elif target_dispersion > 35:
        return "Moderate"
    else:
        return "Low"


def get_valuation_summary(metrics):
    """
    Generate a concise valuation summary for the dashboard.
    """

    signal = classify_valuation_signal(metrics["upside_base"])
    dispersion_signal = classify_target_dispersion(metrics["target_dispersion"])

    summary = (
        f"Gilead shows {signal.lower()}, with ~{metrics['upside_base']:.1f}% "
        f"base-case upside. Analyst target dispersion is {dispersion_signal.lower()}, "
        "reflecting uncertainty around pipeline execution, product concentration, "
        "and diversification success."
    )

    return {
        "signal": signal,
        "dispersion_signal": dispersion_signal,
        "summary": summary,
    }


def get_valuation_source_note():
    return (
        "Valuation assumptions use market-implied analyst target scenarios and historical P/E comparison. "
        "Outputs are directional and should not be treated as precise price forecasts."
    )
