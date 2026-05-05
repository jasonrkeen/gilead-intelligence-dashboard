import pandas as pd


def clamp_score(score, minimum=1, maximum=5):
    """
    Keep risk scores within the 1-5 range.
    """

    return max(minimum, min(maximum, score))


def score_market_risk(volatility, max_drawdown, trend_strength=0):
    """
    Score market risk from 1-5 using volatility, drawdown, and trend strength.
    """

    vol_score = volatility / 7
    drawdown_score = abs(max_drawdown) / 4

    score = (vol_score + drawdown_score) / 2

    if trend_strength > 3:
        score -= 0.5
    elif trend_strength < -3:
        score += 0.5

    return clamp_score(score)


def score_product_concentration(hiv_concentration):
    """
    Score product concentration risk based on HIV revenue dependence.
    """

    if hiv_concentration < 35:
        return 2
    elif hiv_concentration < 50:
        return 3
    elif hiv_concentration < 65:
        return 4
    else:
        return 5


def score_fx_risk(
    foreign_currency_sales_pct,
    eurusd_volatility,
    estimated_revenue_sensitivity=0,
):
    """
    Score FX risk using:
    - foreign currency sales exposure
    - EUR/USD volatility
    - estimated revenue sensitivity
    """

    exposure_score = foreign_currency_sales_pct / 10
    volatility_score = eurusd_volatility / 5
    sensitivity_score = abs(estimated_revenue_sensitivity) * 2

    score = (
        exposure_score * 0.40
        + volatility_score * 0.40
        + sensitivity_score * 0.20
    )

    return clamp_score(score)


def score_sec_risk_theme(keyword_count, total_mentions):
    """
    Score 10-K risk factor intensity based on share of mentions.
    """

    if total_mentions == 0:
        return 1

    share = keyword_count / total_mentions

    if share < 0.10:
        return 2
    elif share < 0.20:
        return 3
    elif share < 0.35:
        return 4
    else:
        return 5


def score_valuation_risk(upside_base):
    """
    Score valuation risk from 1-5.

    Higher upside = lower valuation risk.
    Lower or negative upside = higher valuation risk.
    """

    if upside_base >= 25:
        return 1
    elif upside_base >= 15:
        return 2
    elif upside_base >= 5:
        return 3
    elif upside_base >= 0:
        return 4
    else:
        return 5


def score_financial_quality(financial_summary):
    """
    Score financial quality risk from 1-5.

    Lower score = stronger financial quality.
    """

    if financial_summary is None:
        return 3

    revenue_growth = financial_summary.get("revenue_growth", 0)
    operating_margin = financial_summary.get("operating_margin", 0)
    ocf_margin = financial_summary.get("ocf_margin", 0)
    debt_ocf = financial_summary.get("debt_ocf", 0)

    score = 3

    if revenue_growth > 5:
        score -= 0.5
    elif revenue_growth < 0:
        score += 0.5

    if operating_margin > 30:
        score -= 0.5
    elif operating_margin < 15:
        score += 0.5

    if ocf_margin > 30:
        score -= 0.5
    elif ocf_margin < 15:
        score += 0.5

    if debt_ocf > 3:
        score += 0.5
    elif debt_ocf < 2:
        score -= 0.5

    return clamp_score(score)


def score_strategy_transition_risk(
    hiv_concentration,
    pipeline_maturity=None,
    late_stage_pct=0,
):
    """
    Score strategy / transition risk.

    Captures the risk that Gilead remains highly dependent on HIV while needing
    pipeline and M&A execution to diversify future growth.
    """

    score = 2

    if hiv_concentration >= 70:
        score += 3
    elif hiv_concentration >= 60:
        score += 2
    elif hiv_concentration >= 50:
        score += 1

    if pipeline_maturity == "Early-Stage Weighted":
        score += 1
    elif pipeline_maturity == "Balanced":
        score += 0.5
    elif pipeline_maturity == "Moderate / Late-Stage Weighted":
        score -= 0.5

    if late_stage_pct >= 25:
        score -= 0.5
    elif late_stage_pct < 15:
        score += 0.5

    return clamp_score(score)


def score_strategic_alignment(growth_exposure, hiv_concentration):
    """
    Score the gap between Gilead's future strategy and current revenue mix.

    Higher score = greater mismatch between strategic ambition and current
    revenue base.
    """

    if growth_exposure >= 20:
        return 2
    elif growth_exposure >= 12:
        return 3
    elif hiv_concentration >= 65:
        return 5
    else:
        return 4


def build_data_driven_scores(
    market_metrics=None,
    segment_metrics=None,
    fx_metrics=None,
    sec_risk_df=None,
    valuation_metrics=None,
    pipeline_metrics=None,
    financial_summary=None,
):
    """
    Build data-driven risk scores from available dashboard modules.

    Falls back gracefully if a module is unavailable.
    """

    scores = {}

    if market_metrics is not None:
        scores["Market Risk"] = score_market_risk(
            volatility=market_metrics.get("volatility", 0),
            max_drawdown=market_metrics.get("max_drawdown", 0),
            trend_strength=market_metrics.get("trend_strength", 0),
        )

    if segment_metrics is not None:
        hiv_concentration = segment_metrics.get("hiv_concentration", 0)

        scores["Product Concentration"] = score_product_concentration(
            hiv_concentration=hiv_concentration,
        )

        scores["Strategy / Transition Risk"] = score_strategy_transition_risk(
            hiv_concentration=hiv_concentration,
            pipeline_maturity=(
                pipeline_metrics.get("pipeline_maturity", None)
                if pipeline_metrics is not None else None
            ),
            late_stage_pct=(
                pipeline_metrics.get("late_stage_pct", 0)
                if pipeline_metrics is not None else 0
            ),
        )

        scores["Strategic Alignment"] = score_strategic_alignment(
            growth_exposure=segment_metrics.get("growth_exposure", 0),
            hiv_concentration=hiv_concentration,
        )

    if fx_metrics is not None:
        scores["FX"] = score_fx_risk(
            foreign_currency_sales_pct=fx_metrics.get(
                "foreign_currency_sales_pct",
                0,
            ),
            eurusd_volatility=fx_metrics.get(
                "eurusd_volatility",
                0,
            ),
            estimated_revenue_sensitivity=fx_metrics.get(
                "estimated_revenue_sensitivity",
                0,
            ),
        )

    if valuation_metrics is not None:
        scores["Valuation Risk"] = score_valuation_risk(
            upside_base=valuation_metrics.get("upside_base", 0),
        )

    if financial_summary is not None:
        scores["Financial Quality"] = score_financial_quality(financial_summary)

    if sec_risk_df is not None and not sec_risk_df.empty:
        total_mentions = sec_risk_df["Keyword Count"].sum()

        for _, row in sec_risk_df.iterrows():
            category = row["Risk Category"]
            keyword_count = row["Keyword Count"]

            scores[category] = score_sec_risk_theme(
                keyword_count=keyword_count,
                total_mentions=total_mentions,
            )

    return scores


def score_intelligence_risk(
    market_metrics=None,
    sec_risk_score=None,
    news_risk=None,
):
    """
    Combine market risk, SEC filing risk, and news risk into one intelligence score.

    Higher score = greater monitoring concern.
    """

    scores = []

    if market_metrics is not None:
        volatility = market_metrics.get("volatility", 0)

        if volatility < 20:
            market_score = 2
        elif volatility < 35:
            market_score = 3
        else:
            market_score = 4

        scores.append(market_score)

    if sec_risk_score is not None:
        scores.append(sec_risk_score.get("sec_risk_score", 3))

    if news_risk is not None:
        scores.append(news_risk.get("news_risk_score", 3))

    if not scores:
        return {
            "intelligence_risk_score": 3,
            "intelligence_risk_label": "Moderate",
            "intelligence_risk_summary": "Insufficient intelligence inputs available.",
        }

    intelligence_score = sum(scores) / len(scores)

    if intelligence_score < 2:
        label = "Low"
    elif intelligence_score < 3:
        label = "Moderate"
    elif intelligence_score < 4:
        label = "Elevated"
    else:
        label = "High"

    return {
        "intelligence_risk_score": intelligence_score,
        "intelligence_risk_label": label,
        "intelligence_risk_summary": (
            f"Unified intelligence risk is {label.lower()} "
            f"with a score of {intelligence_score:.2f}/5. "
            "This combines market volatility, SEC risk factor intensity, "
            "and recent news / filing urgency."
        ),
    }


def build_score_dataframe(scores):
    """
    Convert score dictionary into a clean dataframe.
    """

    score_df = pd.DataFrame(
        list(scores.items()),
        columns=["Risk Category", "Score"],
    )

    if score_df.empty:
        return score_df

    score_df["Score"] = score_df["Score"].round(2)

    return score_df.sort_values("Score", ascending=False).reset_index(drop=True)


def calculate_composite_score(scores):
    """
    Calculate weighted composite score emphasizing structural risks.
    """

    if not scores:
        return 0

    weights = {
        "Product Concentration": 2.0,
        "Strategy / Transition Risk": 1.5,
        "Strategic Alignment": 1.5,
        "Market Risk": 1.2,
        "Financial Quality": 1.2,
        "FX": 0.8,
        "Valuation Risk": 1.0,
    }

    total_score = 0
    total_weight = 0

    for key, value in scores.items():
        weight = weights.get(key, 1.0)
        total_score += value * weight
        total_weight += weight

    return total_score / total_weight if total_weight else 0


def classify_composite_score(score):
    """
    Convert composite risk score into a risk rating.
    """

    if score < 2:
        return "Low"
    elif score < 3.5:
        return "Moderate"
    elif score < 4.5:
        return "Elevated"
    else:
        return "High"


def get_scoring_summary(scores):
    """
    Create an executive-style summary of data-driven risk scores.
    """

    composite_score = calculate_composite_score(scores)
    rating = classify_composite_score(composite_score)

    top_risks = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:3]

    top_risk_text = ", ".join([risk[0] for risk in top_risks]) if top_risks else "available inputs"

    summary = (
        f"Composite risk is classified as {rating}, "
        f"driven primarily by {top_risk_text}."
    )

    if scores.get("Product Concentration", 0) >= 4:
        summary += " Structural concentration remains a key underlying risk."

    if scores.get("Strategic Alignment", 0) >= 4:
        summary += (
            " Current revenue mix remains meaningfully misaligned with the "
            "future diversification strategy."
        )

    if scores.get("Financial Quality", 3) <= 2:
        summary += " Financial quality remains a stabilizing factor."

    return {
        "composite_score": composite_score,
        "rating": rating,
        "top_risks": top_risks,
        "summary": summary,
    }
