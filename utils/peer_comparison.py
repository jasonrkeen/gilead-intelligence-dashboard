import yfinance as yf
import pandas as pd
import numpy as np


PEERS = {
    "Gilead": "GILD",
    "Amgen": "AMGN",
    "Bristol Myers Squibb": "BMY",
    "Merck": "MRK",
    "Pfizer": "PFE",
    "AbbVie": "ABBV",
}


def calculate_period_return(series, periods):
    """
    Calculate percentage return over a lookback period.

    If the full requested lookback is not available, the function uses the
    longest available lookback.
    """

    if series is None or series.empty:
        return 0

    lookback = min(periods, len(series) - 1)

    if lookback <= 0:
        return 0

    return (series.iloc[-1] / series.iloc[-(lookback + 1)] - 1) * 100


def get_peer_price_history(peers=None, period="1y"):
    """
    Download peer stock price history and calculate market comparison metrics.
    """

    if peers is None:
        peers = PEERS

    rows = []

    for company, ticker_symbol in peers.items():
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period=period)
        except Exception:
            continue

        if hist.empty or "Close" not in hist.columns:
            continue

        close = hist["Close"].dropna()

        if close.empty:
            continue

        current_price = close.iloc[-1]
        return_30 = calculate_period_return(close, 30)
        return_90 = calculate_period_return(close, 90)

        daily_returns = close.pct_change().dropna()
        annualized_volatility = (
            daily_returns.std() * np.sqrt(252) * 100
            if not daily_returns.empty else 0
        )

        cumulative_max = close.cummax()
        drawdown = ((close / cumulative_max) - 1) * 100
        max_drawdown = drawdown.min() if not drawdown.empty else 0

        rows.append({
            "Company": company,
            "Ticker": ticker_symbol,
            "Price": current_price,
            "30D Return": return_30,
            "90D Return": return_90,
            "Volatility": annualized_volatility,
            "Max Drawdown": max_drawdown,
        })

    return pd.DataFrame(rows)


def rank_peer_metrics(peer_df):
    """
    Rank peers using 90-day return, volatility, and max drawdown.

    Lower composite rank is better.
    """

    if peer_df is None or peer_df.empty:
        return pd.DataFrame()

    ranked = peer_df.copy()

    required_cols = ["90D Return", "Volatility", "Max Drawdown"]
    for col in required_cols:
        if col not in ranked.columns:
            ranked[col] = 0

    ranked["Return Rank"] = ranked["90D Return"].rank(ascending=False)
    ranked["Volatility Rank"] = ranked["Volatility"].rank(ascending=True)
    ranked["Drawdown Rank"] = ranked["Max Drawdown"].rank(ascending=False)

    ranked["Composite Rank"] = (
        ranked["Return Rank"]
        + ranked["Volatility Rank"]
        + ranked["Drawdown Rank"]
    )

    return ranked.sort_values("Composite Rank").reset_index(drop=True)


def get_gilead_peer_summary(peer_ranked):
    """
    Generate a concise summary of Gilead's peer ranking.
    """

    if peer_ranked is None or peer_ranked.empty:
        return {
            "gilead_rank": "N/A",
            "peer_count": 0,
            "summary": "Peer comparison data unavailable.",
        }

    peer_ranked = peer_ranked.reset_index(drop=True)

    if "Ticker" not in peer_ranked.columns:
        return {
            "gilead_rank": "N/A",
            "peer_count": len(peer_ranked),
            "summary": "Ticker data was not available in the peer comparison set.",
        }

    gilead_row = peer_ranked[peer_ranked["Ticker"] == "GILD"]

    if gilead_row.empty:
        return {
            "gilead_rank": "N/A",
            "peer_count": len(peer_ranked),
            "summary": "Gilead was not found in the peer comparison set.",
        }

    gilead_rank = gilead_row.index[0] + 1
    peer_count = len(peer_ranked)

    summary = (
        f"Gilead ranks {gilead_rank} of {peer_count} peers based on a composite "
        "market score combining 90-day return, volatility, and max drawdown."
    )

    return {
        "gilead_rank": gilead_rank,
        "peer_count": peer_count,
        "summary": summary,
    }
