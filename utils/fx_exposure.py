import yfinance as yf
import numpy as np
import pandas as pd


def get_fx_history(period="1y"):
    """
    Fetch EUR/USD and DXY history from Yahoo Finance.

    Returns an empty dataframe if FX data is unavailable so the dashboard can
    continue running.
    """

    try:
        eurusd = yf.Ticker("EURUSD=X").history(period=period)
        dxy = yf.Ticker("DX-Y.NYB").history(period=period)

        if eurusd.empty or "Close" not in eurusd.columns:
            return pd.DataFrame()

        eurusd = eurusd[["Close"]].rename(columns={"Close": "EURUSD"})

        if not dxy.empty and "Close" in dxy.columns:
            dxy = dxy[["Close"]].rename(columns={"Close": "DXY"})
            return eurusd.join(dxy, how="left")

        return eurusd.copy()

    except Exception:
        return pd.DataFrame()


def classify_usd_trend(dxy_series):
    """
    Classify USD strength trend using 50-day and 200-day moving averages.
    """

    if dxy_series is None or dxy_series.empty:
        return "Neutral"

    dxy_series = pd.to_numeric(dxy_series, errors="coerce").dropna()

    if dxy_series.empty:
        return "Neutral"

    ma_50 = dxy_series.rolling(50).mean()
    ma_200 = dxy_series.rolling(200).mean()

    if pd.isna(ma_50.iloc[-1]) or pd.isna(ma_200.iloc[-1]):
        return "Neutral"

    if ma_50.iloc[-1] > ma_200.iloc[-1]:
        return "Strong USD"
    elif ma_50.iloc[-1] < ma_200.iloc[-1]:
        return "Weak USD"
    else:
        return "Neutral"


def classify_fx_risk(volatility):
    """
    Classify FX volatility regime.
    """

    if volatility < 8:
        return "Low"
    elif volatility < 15:
        return "Moderate"
    else:
        return "High"


def calculate_period_return(series, periods):
    """
    Safely calculate return over a requested lookback period.
    """

    if series is None or series.empty:
        return 0

    series = pd.to_numeric(series, errors="coerce").dropna()

    if series.empty:
        return 0

    lookback = min(periods, len(series) - 1)

    if lookback <= 0:
        return 0

    start_value = series.iloc[-(lookback + 1)]
    end_value = series.iloc[-1]

    if start_value == 0 or pd.isna(start_value) or pd.isna(end_value):
        return 0

    return (end_value / start_value - 1) * 100


def calculate_fx_metrics(fx_df, foreign_currency_sales_pct=26):
    """
    Calculate FX exposure metrics.
    """

    if fx_df is None or fx_df.empty or "EURUSD" not in fx_df.columns:
        return {
            "foreign_currency_sales_pct": foreign_currency_sales_pct,
            "eurusd_return_30": 0,
            "eurusd_return_90": 0,
            "eurusd_volatility": 0,
            "estimated_revenue_sensitivity": 0,
            "usd_trend": "N/A",
            "fx_risk_regime": "Moderate",
            "history": pd.DataFrame(),
        }

    fx_df = fx_df.copy()
    fx_df["EURUSD"] = pd.to_numeric(fx_df["EURUSD"], errors="coerce")
    fx_df = fx_df.dropna(subset=["EURUSD"])

    if fx_df.empty:
        return {
            "foreign_currency_sales_pct": foreign_currency_sales_pct,
            "eurusd_return_30": 0,
            "eurusd_return_90": 0,
            "eurusd_volatility": 0,
            "estimated_revenue_sensitivity": 0,
            "usd_trend": "N/A",
            "fx_risk_regime": "Moderate",
            "history": pd.DataFrame(),
        }

    eurusd_return_30 = calculate_period_return(fx_df["EURUSD"], 30)
    eurusd_return_90 = calculate_period_return(fx_df["EURUSD"], 90)

    eurusd_daily_returns = fx_df["EURUSD"].pct_change().dropna()
    eurusd_volatility = (
        eurusd_daily_returns.std() * np.sqrt(252) * 100
        if not eurusd_daily_returns.empty else 0
    )

    fx_df["EURUSD Rolling Volatility"] = (
        fx_df["EURUSD"]
        .pct_change()
        .rolling(window=30)
        .std()
        * np.sqrt(252)
        * 100
    )

    usd_trend = "N/A"
    if "DXY" in fx_df.columns:
        usd_trend = classify_usd_trend(fx_df["DXY"])

    fx_risk_regime = classify_fx_risk(eurusd_volatility)

    estimated_revenue_sensitivity = (
        foreign_currency_sales_pct / 100
    ) * eurusd_return_90

    return {
        "foreign_currency_sales_pct": foreign_currency_sales_pct,
        "eurusd_return_30": eurusd_return_30,
        "eurusd_return_90": eurusd_return_90,
        "eurusd_volatility": eurusd_volatility,
        "estimated_revenue_sensitivity": estimated_revenue_sensitivity,
        "usd_trend": usd_trend,
        "fx_risk_regime": fx_risk_regime,
        "history": fx_df,
    }
