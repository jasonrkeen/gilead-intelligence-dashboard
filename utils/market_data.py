import yfinance as yf
import numpy as np
import pandas as pd


def get_price_history(ticker_symbol="GILD", period="1y"):
    """
    Fetch historical price data from Yahoo Finance.

    Returns an empty dataframe if data is unavailable so the dashboard can
    continue running.
    """

    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)

        if hist.empty:
            return pd.DataFrame()

        return hist

    except Exception:
        return pd.DataFrame()


def calculate_period_return(series, periods):
    """
    Calculate percentage return over a specified lookback period.

    If the full lookback is not available, the function uses the longest
    available lookback.
    """

    if series is None or series.empty:
        return 0

    lookback = min(periods, len(series) - 1)

    if lookback <= 0:
        return 0

    start_value = series.iloc[-(lookback + 1)]
    end_value = series.iloc[-1]

    if start_value == 0 or pd.isna(start_value) or pd.isna(end_value):
        return 0

    return (end_value / start_value - 1) * 100


def calculate_relative_performance(hist, benchmark_symbol="^GSPC", period="1y"):
    """
    Calculate stock performance relative to a benchmark.
    """

    try:
        benchmark = yf.Ticker(benchmark_symbol).history(period=period)

        if benchmark.empty or hist is None or hist.empty:
            return 0

        if "Close" not in hist.columns or "Close" not in benchmark.columns:
            return 0

        stock_close = hist["Close"].dropna()
        benchmark_close = benchmark["Close"].dropna()

        if stock_close.empty or benchmark_close.empty:
            return 0

        stock_start = stock_close.iloc[0]
        benchmark_start = benchmark_close.iloc[0]

        if stock_start == 0 or benchmark_start == 0:
            return 0

        stock_return = (stock_close.iloc[-1] / stock_start) - 1
        benchmark_return = (benchmark_close.iloc[-1] / benchmark_start) - 1

        return (stock_return - benchmark_return) * 100

    except Exception:
        return 0


def classify_risk_regime(volatility):
    """
    Classify market risk regime from annualized volatility.
    """

    if volatility < 20:
        return "Low"
    elif volatility < 35:
        return "Moderate"
    else:
        return "High"


def classify_trend_signal(hist):
    """
    Classify trend signal using 50-day and 200-day moving averages.
    """

    if hist is None or hist.empty:
        return "Neutral"

    if "MA_50" not in hist.columns or "MA_200" not in hist.columns:
        return "Neutral"

    ma_50_latest = hist["MA_50"].iloc[-1]
    ma_200_latest = hist["MA_200"].iloc[-1]

    if pd.isna(ma_50_latest) or pd.isna(ma_200_latest):
        return "Neutral"

    if ma_50_latest > ma_200_latest:
        return "Bullish"
    elif ma_50_latest < ma_200_latest:
        return "Bearish"
    else:
        return "Neutral"


def classify_recovery_signal(hist):
    """
    Classify recovery signal using recent drawdown behavior.
    """

    if hist is None or hist.empty or "Drawdown" not in hist.columns:
        return "Moderate"

    recent_drawdown = hist["Drawdown"].iloc[-30:].min()

    if pd.isna(recent_drawdown):
        return "Moderate"

    if recent_drawdown > -5:
        return "Strong"
    elif recent_drawdown > -15:
        return "Moderate"
    else:
        return "Weak"


def calculate_metrics(hist):
    """
    Calculate market metrics used throughout the dashboard.
    """

    if hist is None or hist.empty or "Close" not in hist.columns:
        return {
            "price": 0,
            "returns_30": 0,
            "returns_90": 0,
            "volatility": 0,
            "max_drawdown": 0,
            "trend_signal": "Neutral",
            "trend_strength": 0,
            "momentum_14": 0,
            "relative_performance": 0,
            "risk_regime": "Moderate",
            "recovery_signal": "Moderate",
            "history": pd.DataFrame(),
        }

    hist = hist.copy()
    hist["Close"] = pd.to_numeric(hist["Close"], errors="coerce")
    hist = hist.dropna(subset=["Close"])

    if hist.empty:
        return {
            "price": 0,
            "returns_30": 0,
            "returns_90": 0,
            "volatility": 0,
            "max_drawdown": 0,
            "trend_signal": "Neutral",
            "trend_strength": 0,
            "momentum_14": 0,
            "relative_performance": 0,
            "risk_regime": "Moderate",
            "recovery_signal": "Moderate",
            "history": pd.DataFrame(),
        }

    current_price = hist["Close"].iloc[-1]

    returns_30 = calculate_period_return(hist["Close"], 30)
    returns_90 = calculate_period_return(hist["Close"], 90)

    daily_returns = hist["Close"].pct_change().dropna()
    volatility = (
        daily_returns.std() * np.sqrt(252) * 100
        if not daily_returns.empty else 0
    )

    hist["Rolling Volatility"] = (
        hist["Close"]
        .pct_change()
        .rolling(window=30)
        .std()
        * np.sqrt(252)
        * 100
    )

    cumulative_max = hist["Close"].cummax()
    hist["Drawdown"] = ((hist["Close"] / cumulative_max) - 1) * 100
    max_drawdown = hist["Drawdown"].min() if not hist["Drawdown"].empty else 0

    hist["MA_50"] = hist["Close"].rolling(window=50).mean()
    hist["MA_200"] = hist["Close"].rolling(window=200).mean()

    trend_signal = classify_trend_signal(hist)

    ma_50_latest = hist["MA_50"].iloc[-1]
    ma_200_latest = hist["MA_200"].iloc[-1]

    if pd.isna(ma_50_latest) or pd.isna(ma_200_latest) or ma_200_latest == 0:
        trend_strength = 0
    else:
        trend_strength = ((ma_50_latest / ma_200_latest) - 1) * 100

    momentum = hist["Close"].pct_change(periods=14)
    momentum_14 = momentum.iloc[-1] * 100 if not momentum.empty and not pd.isna(momentum.iloc[-1]) else 0

    relative_performance = calculate_relative_performance(hist)

    risk_regime = classify_risk_regime(volatility)
    recovery_signal = classify_recovery_signal(hist)

    return {
        "price": current_price,
        "returns_30": returns_30,
        "returns_90": returns_90,
        "volatility": volatility,
        "max_drawdown": max_drawdown,
        "trend_signal": trend_signal,
        "trend_strength": trend_strength,
        "momentum_14": momentum_14,
        "relative_performance": relative_performance,
        "risk_regime": risk_regime,
        "recovery_signal": recovery_signal,
        "history": hist,
    }
