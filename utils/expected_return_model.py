import pandas as pd


def calibrate_scenario_probabilities(
    summary=None,
    market_metrics=None,
    valuation_metrics=None,
    financial_summary=None,
    capital_metrics=None,
):
    """
    Calibrate bear/base/bull scenario probabilities using risk, market,
    valuation, financial quality, and capital allocation inputs.
    """

    bear_probability = 0.25
    base_probability = 0.50
    bull_probability = 0.25

    if summary:
        risk_score = summary.get("composite_score", 3)

        if risk_score >= 3.5:
            bear_probability += 0.10
            bull_probability -= 0.10
        elif risk_score >= 3:
            bear_probability += 0.05
            bull_probability -= 0.05
        elif risk_score <= 2:
            bear_probability -= 0.05
            bull_probability += 0.05

    if market_metrics:
        volatility = market_metrics.get("volatility", 0)

        if volatility >= 35:
            bear_probability += 0.05
            base_probability -= 0.05
        elif volatility <= 20:
            bear_probability -= 0.03
            base_probability += 0.03

    if valuation_metrics:
        dispersion = valuation_metrics.get("target_dispersion", 0)

        if dispersion >= 60:
            bear_probability += 0.05
            bull_probability -= 0.05
        elif dispersion <= 35:
            base_probability += 0.05
            bear_probability -= 0.025
            bull_probability -= 0.025

    if financial_summary:
        operating_margin = financial_summary.get("operating_margin", 0)
        ocf_margin = financial_summary.get("ocf_margin", 0)

        if operating_margin >= 30 and ocf_margin >= 25:
            bear_probability -= 0.05
            base_probability += 0.03
            bull_probability += 0.02

    if capital_metrics:
        allocation_score = capital_metrics.get("capital_allocation_score", 3)
        fcf_return_pct = capital_metrics.get("fcf_return_pct", 0)

        if allocation_score <= 2 or fcf_return_pct >= 70:
            bear_probability -= 0.04
            base_probability += 0.02
            bull_probability += 0.02
        elif allocation_score == 3:
            bear_probability -= 0.02
            base_probability += 0.02
        elif allocation_score >= 4:
            bear_probability += 0.04
            bull_probability -= 0.04

    bear_probability = max(0.05, bear_probability)
    base_probability = max(0.10, base_probability)
    bull_probability = max(0.05, bull_probability)

    total = bear_probability + base_probability + bull_probability

    if total <= 0:
        return {
            "bear_probability": 0.25,
            "base_probability": 0.50,
            "bull_probability": 0.25,
        }

    return {
        "bear_probability": bear_probability / total,
        "base_probability": base_probability / total,
        "bull_probability": bull_probability / total,
    }


def calculate_confidence_score(
    summary=None,
    market_metrics=None,
    valuation_metrics=None,
    financial_summary=None,
):
    """
    Calculate confidence in the expected return signal.
    """

    confidence = 70

    if summary:
        risk_score = summary.get("composite_score", 3)

        if risk_score >= 4:
            confidence -= 20
        elif risk_score >= 3:
            confidence -= 10
        elif risk_score <= 2:
            confidence += 5

    if market_metrics:
        volatility = market_metrics.get("volatility", 0)

        if volatility >= 35:
            confidence -= 15
        elif volatility >= 25:
            confidence -= 7
        elif volatility <= 20:
            confidence += 5

    if valuation_metrics:
        dispersion = valuation_metrics.get("target_dispersion", 0)

        if dispersion >= 60:
            confidence -= 15
        elif dispersion >= 40:
            confidence -= 7
        elif dispersion <= 30:
            confidence += 5

    if financial_summary:
        operating_margin = financial_summary.get("operating_margin", 0)
        ocf_margin = financial_summary.get("ocf_margin", 0)

        if operating_margin >= 30 and ocf_margin >= 25:
            confidence += 10

    confidence = max(0, min(100, confidence))

    if confidence >= 75:
        label = "High"
    elif confidence >= 55:
        label = "Moderate"
    else:
        label = "Low"

    return {
        "confidence_score": confidence,
        "confidence_label": label,
    }


def calculate_segment_role_target_adjustment(segment_df=None):
    """
    Adjust bear/base/bull target levels based on segment role mix.
    """

    if (
        segment_df is None
        or segment_df.empty
        or "Segment Role" not in segment_df.columns
        or "Sales" not in segment_df.columns
    ):
        return {
            "bear_multiplier": 1.00,
            "base_multiplier": 1.00,
            "bull_multiplier": 1.00,
            "role_target_summary": "Segment role target adjustment unavailable.",
        }

    total_sales = segment_df["Sales"].sum()

    if total_sales <= 0:
        return {
            "bear_multiplier": 1.00,
            "base_multiplier": 1.00,
            "bull_multiplier": 1.00,
            "role_target_summary": "Segment role target adjustment unavailable.",
        }

    role_mix = (
        segment_df.groupby("Segment Role")["Sales"].sum()
        / total_sales
        * 100
    )

    core_pct = role_mix.get("Core", 0)
    growth_pct = role_mix.get("Growth", 0)
    legacy_pct = role_mix.get("Legacy", 0)

    bear_multiplier = 1.00
    base_multiplier = 1.00
    bull_multiplier = 1.00

    if growth_pct >= 20:
        bull_multiplier += 0.08
        base_multiplier += 0.02
    elif growth_pct >= 10:
        bull_multiplier += 0.04
        base_multiplier += 0.01

    if legacy_pct >= 20:
        bear_multiplier -= 0.04
        base_multiplier -= 0.01
    elif legacy_pct >= 10:
        bear_multiplier -= 0.02

    if core_pct >= 70:
        bull_multiplier -= 0.03
        bear_multiplier += 0.01

    return {
        "bear_multiplier": bear_multiplier,
        "base_multiplier": base_multiplier,
        "bull_multiplier": bull_multiplier,
        "role_target_summary": (
            f"Role target adjustment reflects Core {core_pct:.1f}%, "
            f"Growth {growth_pct:.1f}%, Legacy {legacy_pct:.1f}%."
        ),
    }


def build_price_target_scenarios(
    current_price,
    val_metrics=None,
    segment_metrics=None,
    summary=None,
    market_metrics=None,
    financial_summary=None,
    segment_df=None,
    capital_metrics=None,
):
    """
    Build bear/base/bull price target scenarios and expected return.
    """

    if current_price is None or current_price <= 0:
        raise ValueError("Current price must be greater than zero.")

    base_upside = val_metrics.get("upside_base", 10) if val_metrics else 10
    base_target = current_price * (1 + base_upside / 100)

    growth_boost = 0

    if segment_metrics:
        growth_exposure = segment_metrics.get("growth_exposure", 0)
        revenue_dependence = segment_metrics.get("revenue_dependence", "")

        if growth_exposure >= 20:
            growth_boost += 0.12
        elif growth_exposure >= 15:
            growth_boost += 0.08
        elif growth_exposure >= 10:
            growth_boost += 0.04

        if revenue_dependence == "Highly Concentrated":
            growth_boost -= 0.03
        elif revenue_dependence == "Diversified":
            growth_boost += 0.03

    bull_target = base_target * (1.15 + growth_boost)

    risk_penalty = 0.10

    if summary:
        risk_score = summary.get("composite_score", 3)

        if risk_score > 3:
            risk_penalty += 0.05
        elif risk_score < 2:
            risk_penalty -= 0.03

    bear_target = current_price * (1 - risk_penalty)

    role_target_adjusted = calculate_segment_role_target_adjustment(
        segment_df=segment_df,
    )

    bear_target *= role_target_adjusted["bear_multiplier"]
    base_target *= role_target_adjusted["base_multiplier"]
    bull_target *= role_target_adjusted["bull_multiplier"]

    probabilities = calibrate_scenario_probabilities(
        summary=summary,
        market_metrics=market_metrics,
        valuation_metrics=val_metrics,
        financial_summary=financial_summary,
        capital_metrics=capital_metrics,
    )

    scenarios = pd.DataFrame({
        "Scenario": ["Bear", "Base", "Bull"],
        "Price Target": [bear_target, base_target, bull_target],
        "Probability": [
            probabilities["bear_probability"],
            probabilities["base_probability"],
            probabilities["bull_probability"],
        ],
    })

    scenarios["Expected Value Contribution"] = (
        scenarios["Price Target"] * scenarios["Probability"]
    )

    scenarios["Return %"] = (
        (scenarios["Price Target"] / current_price) - 1
    ) * 100

    expected_price_target = scenarios["Expected Value Contribution"].sum()
    expected_return = ((expected_price_target / current_price) - 1) * 100

    return {
        "scenarios": scenarios,
        "expected_price_target": expected_price_target,
        "expected_return": expected_return,
        "probabilities": probabilities,
        "role_target_adjustment": role_target_adjusted,
    }


def apply_diversification_adjustment(expected_return, segment_metrics=None):
    """
    Adjust expected return for product concentration and growth exposure.
    """

    if segment_metrics is None:
        return {
            "diversification_adjustment": 0,
            "diversification_adjusted_return": expected_return,
        }

    hiv_concentration = segment_metrics.get("hiv_concentration", 0)
    growth_exposure = segment_metrics.get("growth_exposure", 0)

    adjustment = 0

    if hiv_concentration > 70:
        adjustment -= 2.5
    elif hiv_concentration > 60:
        adjustment -= 1.5

    if growth_exposure > 15:
        adjustment += 1.5
    elif growth_exposure > 10:
        adjustment += 0.75

    return {
        "diversification_adjustment": adjustment,
        "diversification_adjusted_return": expected_return + adjustment,
    }


def apply_capital_allocation_adjustment(expected_return, capital_metrics=None):
    """
    Adjust expected return for shareholder return and capital allocation quality.
    """

    if capital_metrics is None:
        return {
            "capital_allocation_adjustment": 0,
            "capital_allocation_adjusted_return": expected_return,
        }

    fcf_return_pct = capital_metrics.get("fcf_return_pct", 0)
    allocation_score = capital_metrics.get("capital_allocation_score", 3)

    adjustment = 0

    if fcf_return_pct >= 70:
        adjustment += 1.5
    elif fcf_return_pct >= 50:
        adjustment += 1.0
    elif fcf_return_pct >= 30:
        adjustment += 0.25
    else:
        adjustment -= 1.0

    if allocation_score <= 2:
        adjustment += 0.75
    elif allocation_score == 3:
        adjustment += 0.25
    elif allocation_score == 4:
        adjustment -= 0.25
    else:
        adjustment -= 0.75

    return {
        "capital_allocation_adjustment": adjustment,
        "capital_allocation_adjusted_return": expected_return + adjustment,
    }


def calculate_segment_role_adjustment(segment_df=None):
    """
    Calculate expected return adjustment based on segment role mix.
    """

    if (
        segment_df is None
        or segment_df.empty
        or "Segment Role" not in segment_df.columns
        or "Sales" not in segment_df.columns
    ):
        return {
            "segment_role_adjustment": 0,
            "role_summary": "Segment role data unavailable.",
        }

    total_sales = segment_df["Sales"].sum()

    if total_sales <= 0:
        return {
            "segment_role_adjustment": 0,
            "role_summary": "Segment role data unavailable.",
        }

    role_mix = (
        segment_df.groupby("Segment Role")["Sales"].sum()
        / total_sales
        * 100
    )

    growth_pct = role_mix.get("Growth", 0)
    legacy_pct = role_mix.get("Legacy", 0)
    core_pct = role_mix.get("Core", 0)

    adjustment = 0

    if growth_pct >= 20:
        adjustment += 1.5
    elif growth_pct >= 10:
        adjustment += 0.75

    if legacy_pct >= 20:
        adjustment -= 1.0
    elif legacy_pct >= 10:
        adjustment -= 0.5

    if core_pct >= 70:
        adjustment -= 0.75

    return {
        "segment_role_adjustment": adjustment,
        "role_summary": (
            f"Segment role mix: Core {core_pct:.1f}%, "
            f"Growth {growth_pct:.1f}%, Legacy {legacy_pct:.1f}%."
        ),
    }


def apply_forward_mix_adjustment(expected_return, future_mix=None):
    """
    Adjust expected return based on projected revenue mix.
    """

    if future_mix is None:
        return {
            "forward_mix_adjustment": 0,
            "forward_mix_adjusted_return": expected_return,
            "forward_mix_summary": "Forward mix data unavailable.",
        }

    projected_hiv = future_mix.get("HIV", 0) * 100
    projected_other = future_mix.get("Oncology / Other", 0) * 100

    adjustment = 0

    if projected_hiv < 60:
        adjustment += 1.5
    elif projected_hiv < 70:
        adjustment += 0.75
    else:
        adjustment -= 0.75

    if projected_other > 40:
        adjustment += 1.0
    elif projected_other > 30:
        adjustment += 0.5

    return {
        "forward_mix_adjustment": adjustment,
        "forward_mix_adjusted_return": expected_return + adjustment,
        "forward_mix_summary": (
            f"Projected mix: HIV {projected_hiv:.1f}%, "
            f"Oncology / Other {projected_other:.1f}%."
        ),
    }


def risk_adjust_expected_return(
    expected_return,
    composite_risk_score,
    intelligence_risk=None,
    pipeline_metrics=None,
    news_risk=None,
):
    """
    Apply a risk haircut to expected return using composite, intelligence,
    pipeline, and news risk inputs.
    """

    composite_risk_score = composite_risk_score if composite_risk_score is not None else 3

    base_risk_haircut = (composite_risk_score - 1) / 5
    intelligence_haircut = 0
    pipeline_haircut = 0
    news_haircut = 0

    if intelligence_risk is not None:
        intelligence_score = intelligence_risk.get("intelligence_risk_score", 3)

        if intelligence_score >= 4:
            intelligence_haircut += 0.10
        elif intelligence_score >= 3:
            intelligence_haircut += 0.05
        elif intelligence_score <= 2:
            intelligence_haircut -= 0.03

    if pipeline_metrics is not None:
        pipeline_maturity = pipeline_metrics.get("pipeline_maturity", "")
        late_stage_pct = pipeline_metrics.get("late_stage_pct", 0)

        if pipeline_maturity == "Early-Stage Weighted":
            pipeline_haircut += 0.05
        elif pipeline_maturity == "Moderate / Late-Stage Weighted":
            pipeline_haircut -= 0.03

        if late_stage_pct >= 25:
            pipeline_haircut -= 0.02
        elif late_stage_pct < 15:
            pipeline_haircut += 0.02

    if news_risk is not None:
        news_score = news_risk.get("news_risk_score", 3)

        if news_score >= 4:
            news_haircut += 0.05
        elif news_score <= 2:
            news_haircut -= 0.02

    total_haircut = (
        base_risk_haircut
        + intelligence_haircut
        + pipeline_haircut
        + news_haircut
    )

    total_haircut = max(0, min(0.75, total_haircut))
    risk_adjusted_return = expected_return * (1 - total_haircut)

    return {
        "risk_haircut": total_haircut * 100,
        "base_risk_haircut": base_risk_haircut * 100,
        "intelligence_haircut": intelligence_haircut * 100,
        "pipeline_haircut": pipeline_haircut * 100,
        "news_haircut": news_haircut * 100,
        "risk_adjusted_return": risk_adjusted_return,
    }


def classify_expected_return_signal(risk_adjusted_return):
    """
    Classify risk-adjusted return into a directional signal.
    """

    if risk_adjusted_return >= 15:
        return "Attractive"
    elif risk_adjusted_return >= 5:
        return "Moderate"
    elif risk_adjusted_return >= 0:
        return "Neutral"
    else:
        return "Unattractive"


def get_expected_return_summary(
    expected_price_target,
    expected_return,
    risk_adjusted_return,
    signal,
    diversification_adjustment=0,
    capital_allocation_adjustment=0,
    segment_role_adjustment=0,
    forward_mix_adjustment=0,
):
    """
    Generate a concise summary of the expected return model.
    """

    total_adjustment = (
        diversification_adjustment
        + capital_allocation_adjustment
        + segment_role_adjustment
        + forward_mix_adjustment
    )

    return (
        f"The probability-weighted price target is ${expected_price_target:.2f}, "
        f"implying a raw expected return of {expected_return:.1f}%. "
        f"Business-specific adjustments total {total_adjustment:.1f} percentage points, "
        f"including diversification ({diversification_adjustment:.1f}), "
        f"capital allocation ({capital_allocation_adjustment:.1f}), "
        f"segment role ({segment_role_adjustment:.1f}), and "
        f"forward revenue mix ({forward_mix_adjustment:.1f}). "
        f"After applying the risk haircut, the risk-adjusted return is "
        f"{risk_adjusted_return:.1f}%, producing a {signal.lower()} signal."
    )
