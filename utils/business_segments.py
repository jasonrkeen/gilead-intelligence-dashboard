import pandas as pd


def get_business_segment_data():
    """
    Return Gilead product sales baseline.

    Values are in USD millions.
    Source baseline: Gilead 2025 Form 10-K.
    """

    data = {
        "Segment": [
            "HIV (Core Franchise)",
            "Liver Disease (Legacy)",
            "COVID-19 (Veklury)",
            "Cell Therapy (Strategic)",
            "Trodelvy (Oncology)",
            "Other",
        ],
        "Sales": [
            20816,
            3200,
            911,
            1800,
            1400,
            788,
        ],
    }

    segment_df = pd.DataFrame(data)

    segment_df["Segment Role"] = segment_df["Segment"].apply(
        classify_segment_role,
    )

    total_sales = segment_df["Sales"].sum()

    if total_sales > 0:
        segment_df["Sales Share %"] = (
            segment_df["Sales"] / total_sales
        ) * 100
    else:
        segment_df["Sales Share %"] = 0

    return segment_df


def classify_segment_role(segment):
    """
    Classify segment into core, growth, legacy, or other role.
    """

    segment = str(segment).lower()

    if "hiv" in segment:
        return "Core"
    elif "oncology" in segment or "cell therapy" in segment:
        return "Growth"
    elif "covid" in segment or "liver" in segment:
        return "Legacy"
    else:
        return "Other"


def calculate_revenue_dependence(hiv_concentration):
    """
    Classify revenue concentration risk.
    """

    if hiv_concentration > 70:
        return "Highly Concentrated"
    elif hiv_concentration > 55:
        return "Moderately Concentrated"
    else:
        return "Diversified"


def calculate_segment_metrics(segment_df):
    """
    Calculate product concentration and segment exposure metrics.
    """

    if segment_df is None or segment_df.empty:
        return {
            "total_product_sales": 0,
            "hiv_sales": 0,
            "hiv_concentration": 0,
            "largest_segment": "N/A",
            "largest_segment_sales": 0,
            "largest_segment_concentration": 0,
            "top_3_sales": 0,
            "top_3_concentration": 0,
            "diversification_score": 0,
            "revenue_dependence": "N/A",
            "growth_exposure": 0,
            "declining_exposure": 0,
        }

    segment_df = segment_df.copy()

    if "Segment Role" not in segment_df.columns:
        segment_df["Segment Role"] = segment_df["Segment"].apply(
            classify_segment_role,
        )

    if "Sales" not in segment_df.columns:
        raise ValueError("Segment dataframe must include a 'Sales' column.")

    total_sales = segment_df["Sales"].sum()

    if total_sales <= 0:
        return {
            "total_product_sales": 0,
            "hiv_sales": 0,
            "hiv_concentration": 0,
            "largest_segment": "N/A",
            "largest_segment_sales": 0,
            "largest_segment_concentration": 0,
            "top_3_sales": 0,
            "top_3_concentration": 0,
            "diversification_score": 0,
            "revenue_dependence": "N/A",
            "growth_exposure": 0,
            "declining_exposure": 0,
        }

    hiv_sales = segment_df.loc[
        segment_df["Segment Role"] == "Core",
        "Sales",
    ].sum()

    largest_segment = segment_df.sort_values(
        "Sales",
        ascending=False,
    ).iloc[0]

    hiv_concentration = (hiv_sales / total_sales) * 100

    largest_segment_concentration = (
        largest_segment["Sales"] / total_sales
    ) * 100

    top_3_sales = (
        segment_df.sort_values("Sales", ascending=False)
        .head(3)["Sales"]
        .sum()
    )

    top_3_concentration = (top_3_sales / total_sales) * 100
    diversification_score = 100 - largest_segment_concentration
    dependence = calculate_revenue_dependence(hiv_concentration)

    growth_segments = segment_df.loc[
        segment_df["Segment Role"] == "Growth",
        "Sales",
    ].sum()

    growth_exposure = (growth_segments / total_sales) * 100

    declining_segments = segment_df.loc[
        segment_df["Segment Role"] == "Legacy",
        "Sales",
    ].sum()

    declining_exposure = (declining_segments / total_sales) * 100

    return {
        "total_product_sales": total_sales,
        "hiv_sales": hiv_sales,
        "hiv_concentration": hiv_concentration,
        "largest_segment": largest_segment["Segment"],
        "largest_segment_sales": largest_segment["Sales"],
        "largest_segment_concentration": largest_segment_concentration,
        "top_3_sales": top_3_sales,
        "top_3_concentration": top_3_concentration,
        "diversification_score": diversification_score,
        "revenue_dependence": dependence,
        "growth_exposure": growth_exposure,
        "declining_exposure": declining_exposure,
    }


def get_fx_exposure_from_10k():
    """
    Return FX disclosure baseline from Gilead's 2025 10-K.
    """

    return {
        "foreign_currency_sales_pct_2025": 26,
        "foreign_currency_sales_pct_2024": 27,
        "primary_currency_exposure": "Euro",
    }


def get_segment_source_note():
    return (
        "Segment/product sales are based on Gilead's 2025 Form 10-K baseline. "
        "Values shown in USD millions."
    )
