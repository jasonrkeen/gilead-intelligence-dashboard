import requests
import numpy as np
import pandas as pd
import streamlit as st


CIK = "0000882095"

HEADERS = {
    "User-Agent": "Jason Keen gilead-intelligence-dashboard keenjasonr@gmail.com"
}

FACTS_URL = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json"


@st.cache_data(ttl=3600)
def get_company_facts():
    """
    Fetch Gilead's SEC companyfacts JSON.

    Returns an empty dictionary if the request fails so the Streamlit app
    can continue running without crashing.
    """

    try:
        response = requests.get(FACTS_URL, headers=HEADERS, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {}


def get_annual_usd_fact(facts, tag):
    """
    Extract annual 10-K USD facts for a single SEC XBRL tag.
    """

    try:
        units = facts["facts"]["us-gaap"][tag]["units"]["USD"]
    except KeyError:
        return pd.DataFrame()

    rows = []

    for item in units:
        if item.get("form") == "10-K" and item.get("fp") == "FY":
            rows.append({
                "year": item.get("fy"),
                "filed": item.get("filed"),
                "value": item.get("val"),
                "tag": tag,
            })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["year", "value"])

    if df.empty:
        return df

    df["year"] = df["year"].astype(int)

    return (
        df.sort_values(["year", "filed"])
        .drop_duplicates("year", keep="last")
        .reset_index(drop=True)
    )


def get_annual_usd_fact_with_fallbacks(facts, tags):
    """
    Use priority-ordered fallback tags.

    Important:
    - The first tag in the list is preferred.
    - Later tags are used only for years where the preferred tag is missing.
    """

    combined = pd.DataFrame()

    for priority, tag in enumerate(tags):
        df = get_annual_usd_fact(facts, tag)

        if not df.empty:
            df["tag_priority"] = priority
            combined = pd.concat([combined, df], ignore_index=True)

    if combined.empty:
        return pd.DataFrame()

    combined = (
        combined.sort_values(["year", "tag_priority", "filed"])
        .drop_duplicates("year", keep="first")
        .reset_index(drop=True)
    )

    return combined


def get_metric_tag_map():
    """
    Centralized SEC tag map.

    Tags are ordered from preferred to fallback.
    """

    return {
        "Revenue": [
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "Revenues",
            "SalesRevenueNet",
        ],
        "Net Income": [
            "NetIncomeLoss",
            "ProfitLoss",
        ],
        "R&D Expense": [
            "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
            "ResearchAndDevelopmentExpense",
        ],
        "Operating Income": [
            "OperatingIncomeLoss",
        ],
        "Operating Cash Flow": [
            "NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        ],
        "Cash & Equivalents": [
            "CashAndCashEquivalentsAtCarryingValue",
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        ],
        "Long-Term Debt": [
            "LongTermDebtNoncurrent",
            "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
            "LongTermDebt",
        ],
    }


def build_financial_raw_long():
    """
    Build a long-form financial dataset with SEC tag audit trail.
    """

    facts = get_company_facts()

    if not facts:
        return pd.DataFrame()

    tags = get_metric_tag_map()
    frames = []

    for label, tag_list in tags.items():
        df = get_annual_usd_fact_with_fallbacks(facts, tag_list)

        if not df.empty:
            df["metric"] = label
            frames.append(
                df[["year", "metric", "value", "filed", "tag", "tag_priority"]]
            )

    if not frames:
        return pd.DataFrame()

    final = pd.concat(frames, ignore_index=True)

    final["year"] = pd.to_numeric(final["year"], errors="coerce")
    final["value"] = pd.to_numeric(final["value"], errors="coerce")

    final = final.dropna(subset=["year"])
    final["year"] = final["year"].astype(int)

    return final.sort_values(["year", "metric"]).reset_index(drop=True)


def build_financial_tag_audit():
    """
    Return a compact audit table showing which SEC tag was used.
    """

    final = build_financial_raw_long()

    if final.empty:
        return pd.DataFrame()

    audit = final[[
        "year",
        "metric",
        "tag",
        "filed",
        "tag_priority",
    ]].copy()

    return audit.sort_values(["year", "metric"]).reset_index(drop=True)


def build_financial_baseline():
    """
    Build wide financial baseline used by the dashboard.
    """

    final = build_financial_raw_long()

    if final.empty:
        return pd.DataFrame()

    pivot = final.pivot_table(
        index="year",
        columns="metric",
        values="value",
        aggfunc="last",
    ).reset_index()

    pivot["year"] = pivot["year"].astype(int)

    for col in pivot.columns:
        if col != "year":
            pivot[col] = pd.to_numeric(pivot[col], errors="coerce")

    pivot = pivot.sort_values("year").reset_index(drop=True)

    return add_financial_metrics(pivot)


def _safe_divide(numerator, denominator):
    """
    Safely divide two pandas Series or numeric values.
    """

    if hasattr(denominator, "replace"):
        denominator = denominator.replace(0, np.nan)
        return numerator / denominator

    if denominator in (0, None):
        return np.nan

    return numerator / denominator


def add_financial_metrics(df):
    """
    Add derived financial metrics for dashboard intelligence.
    """

    df = df.copy()

    if "Revenue" in df.columns:
        df["Revenue YoY Growth %"] = df["Revenue"].pct_change() * 100

    if "Operating Income" in df.columns and "Revenue" in df.columns:
        df["Operating Margin %"] = _safe_divide(
            df["Operating Income"],
            df["Revenue"],
        ) * 100

    if "Net Income" in df.columns and "Revenue" in df.columns:
        df["Net Margin %"] = _safe_divide(
            df["Net Income"],
            df["Revenue"],
        ) * 100

    if "R&D Expense" in df.columns and "Revenue" in df.columns:
        df["R&D Intensity %"] = _safe_divide(
            df["R&D Expense"],
            df["Revenue"],
        ) * 100

    if "Operating Cash Flow" in df.columns and "Revenue" in df.columns:
        df["OCF Margin %"] = _safe_divide(
            df["Operating Cash Flow"],
            df["Revenue"],
        ) * 100

    if "Cash & Equivalents" in df.columns and "Long-Term Debt" in df.columns:
        df["Net Debt"] = df["Long-Term Debt"] - df["Cash & Equivalents"]

    if "Operating Cash Flow" in df.columns and "Long-Term Debt" in df.columns:
        df["Debt / OCF"] = _safe_divide(
            df["Long-Term Debt"],
            df["Operating Cash Flow"],
        )

    return df.replace([np.inf, -np.inf], np.nan)


def safe_value(value, default=0):
    """
    Convert missing or invalid values to a safe default.
    """

    if value is None or pd.isna(value):
        return default

    return value


def get_latest_financial_summary(financials_df):
    """
    Return latest-year financial summary metrics used throughout the dashboard.
    """

    if financials_df is None or financials_df.empty:
        return {
            "latest_year": "N/A",
            "revenue": 0,
            "revenue_growth": 0,
            "operating_margin": 0,
            "net_margin": 0,
            "rd_intensity": 0,
            "ocf_margin": 0,
            "net_debt": 0,
            "debt_ocf": 0,
        }

    latest = financials_df.sort_values("year").iloc[-1]

    return {
        "latest_year": latest.get("year", "N/A"),
        "revenue": safe_value(latest.get("Revenue", 0)),
        "revenue_growth": safe_value(latest.get("Revenue YoY Growth %", 0)),
        "operating_margin": safe_value(latest.get("Operating Margin %", 0)),
        "net_margin": safe_value(latest.get("Net Margin %", 0)),
        "rd_intensity": safe_value(latest.get("R&D Intensity %", 0)),
        "ocf_margin": safe_value(latest.get("OCF Margin %", 0)),
        "net_debt": safe_value(latest.get("Net Debt", 0)),
        "debt_ocf": safe_value(latest.get("Debt / OCF", 0)),
    }
