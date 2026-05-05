import pandas as pd


def get_capital_allocation_signal():
    """
    Return capital allocation baseline.

    Values are USD millions.
    """

    return {
        "dividends": 4000,
        "buybacks": 1900,
        "fcf_return_pct": 63,
        "signal": "Shareholder Return Focused",
    }


def build_capital_allocation_dataframe():
    """
    Build dataframe showing capital returned to shareholders.
    """

    data = get_capital_allocation_signal()

    df = pd.DataFrame({
        "Category": ["Dividends", "Buybacks"],
        "Amount": [data["dividends"], data["buybacks"]],
    })

    total_amount = df["Amount"].sum()

    if total_amount > 0:
        df["Share %"] = (df["Amount"] / total_amount) * 100
    else:
        df["Share %"] = 0

    return df


def score_capital_allocation(fcf_return_pct):
    """
    Score capital allocation profile.

    Lower score = more conservative / shareholder-friendly.
    Higher score = reinvestment or capital inefficiency risk.
    """

    if fcf_return_pct >= 70:
        return 2
    elif fcf_return_pct >= 50:
        return 3
    elif fcf_return_pct >= 30:
        return 4
    else:
        return 5


def classify_capital_allocation_signal(score):
    """
    Convert score into a readable signal and color.
    """

    if score <= 2:
        return "Strong Shareholder Returns", "#16a34a"
    elif score == 3:
        return "Balanced Allocation", "#84cc16"
    elif score == 4:
        return "Reinvestment Focused", "#f59e0b"
    else:
        return "Weak Capital Discipline", "#dc2626"


def get_capital_allocation_metrics():
    """
    Return capital allocation metrics used by the dashboard and expected return model.
    """

    data = get_capital_allocation_signal()

    score = score_capital_allocation(data["fcf_return_pct"])
    label, color = classify_capital_allocation_signal(score)

    return {
        "dividends": data["dividends"],
        "buybacks": data["buybacks"],
        "fcf_return_pct": data["fcf_return_pct"],
        "capital_allocation_score": score,
        "signal": data["signal"],
        "allocation_label": label,
        "allocation_color": color,
    }


def get_capital_allocation_summary():
    """
    Generate a concise capital allocation summary.
    """

    data = get_capital_allocation_signal()
    metrics = get_capital_allocation_metrics()

    return (
        f"Gilead returns {data['fcf_return_pct']}% of free cash flow to shareholders, "
        f"indicating a {metrics['allocation_label'].lower()} capital allocation profile. "
        f"This corresponds to a risk score of {metrics['capital_allocation_score']}, suggesting "
        "a balance between income support, buybacks, and reinvestment capacity. "
        "Capital allocation strength can provide downside protection but may limit reinvestment-driven upside."
    )


def get_capital_allocation_source_note():
    return (
        "Capital allocation figures are based on Gilead's 2025 public filing / financial baseline. "
        "Values shown in USD millions."
    )
