import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.market_data import get_price_history, calculate_metrics
from utils.sec_data import (
    build_financial_baseline,
    get_latest_financial_summary,
    build_financial_tag_audit
)
from utils.business_segments import (
    get_business_segment_data,
    calculate_segment_metrics,
    get_segment_source_note,
)
from utils.fx_exposure import get_fx_history, calculate_fx_metrics
from utils.sec_risk_factors import build_sec_risk_factor_analysis
from utils.scoring_engine import (
    build_data_driven_scores,
    build_score_dataframe,
    get_scoring_summary,
    score_intelligence_risk,
)
from utils.pdf_generator import generate_intelligence_brief
from utils.news_tracker import (
    build_news_tracker,
    get_news_summary,
    calculate_news_risk_score,
)
from utils.peer_comparison import (
    get_peer_price_history,
    rank_peer_metrics,
    get_gilead_peer_summary,
)
from utils.pipeline_tracker import (
    get_pipeline_summary,
    get_pipeline_focus_areas,
    get_key_pipeline_watchlist,
    calculate_pipeline_metrics,
    get_pipeline_source_note,
)
from utils.valuation_model import (
    get_valuation_inputs,
    calculate_valuation_metrics,
    get_valuation_summary,
    get_valuation_source_note,
)
from utils.pipeline_forecast import (
    get_base_revenue_mix,
    project_future_mix,
    calculate_revenue_shift,
    get_forecast_summary,
)
from utils.expected_return_model import (
    build_price_target_scenarios,
    apply_diversification_adjustment,
    apply_capital_allocation_adjustment,
    calculate_segment_role_adjustment,
    apply_forward_mix_adjustment,
    risk_adjust_expected_return,
    classify_expected_return_signal,
    calculate_confidence_score,
    get_expected_return_summary,
)
from utils.capital_allocation import (
    get_capital_allocation_signal,
    build_capital_allocation_dataframe,
    get_capital_allocation_summary,
    get_capital_allocation_metrics,
    get_capital_allocation_source_note,
)
from utils.explainers import (
    explain_metric,
    get_expected_return_narrative,
    get_headline_signal,
    get_catalyst_trigger_line,
)
from utils.change_detection import (
    build_current_snapshot,
    load_previous_snapshot,
    save_current_snapshot,
    detect_dashboard_changes,
)
from utils.intelligence_engine import compute_security_signal

st.set_page_config(layout="wide")

# Safe defaults
fx_metrics = None
sec_risk = None
sec_risk_df = None
summary = None
segment_df = None
segment_metrics = None
pipeline_metrics = None
val_metrics = None
capital_metrics = None
financial_summary = None
news_risk = None
intelligence_risk = None
risk_adjusted = None
signal = None
security_signal_result = None
security_signal = None
security_signal_score = None
confidence = None
future_mix = None

st.title("Gilead Intelligence Dashboard")


# =========================
# MARKET DATA
# =========================
hist = get_price_history("GILD", period="1y")
metrics = calculate_metrics(hist)
hist = metrics["history"]


# =========================
# EXECUTIVE INTELLIGENCE SUMMARY
# =========================
st.markdown("## Executive Intelligence Summary")

st.info(
    f"""
Gilead currently operates within a **{metrics['risk_regime'].lower()} market risk regime**, 
with a **{metrics['trend_signal'].lower()} trend structure** supported by 
{metrics['returns_90']:.1f}% 90-day price momentum.

This platform integrates market signals, SEC financial baselines, segment exposure, FX dynamics, 
pipeline intelligence, peer benchmarking, valuation, forward revenue mix, and risk-adjusted expected 
return modeling into a unified **security intelligence framework**.
"""
)

st.markdown("**Key Risk Drivers:**")
st.markdown("- Product concentration from HIV sales exposure")
st.markdown("- Market volatility and drawdown risk")
st.markdown("- Pipeline execution risk tied to diversification beyond HIV")
st.markdown("- FX exposure from foreign-currency-denominated product sales")
st.markdown("- Policy, regulatory, and competitive risk from SEC filings")


# =========================
# MARKET SIGNALS
# =========================
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Price", f"${metrics['price']:.2f}")
col2.metric("30D Return", f"{metrics['returns_30']:.2f}%", f"{metrics['returns_30']:.2f}%")
col3.metric("90D Return", f"{metrics['returns_90']:.2f}%", f"{metrics['returns_90']:.2f}%")
col4.metric("Volatility", f"{metrics['volatility']:.2f}%", f"{metrics['volatility']:.2f}%", delta_color="inverse")
col5.metric("Max Drawdown", f"{metrics['max_drawdown']:.2f}%", f"{metrics['max_drawdown']:.2f}%", delta_color="inverse")

col6, col7, col8, col9 = st.columns(4)
trend = metrics["trend_signal"]

if trend == "Bullish":
    trend_display = "🟢 Bullish"
    line_color = "#16a34a"
elif trend == "Bearish":
    trend_display = "🔴 Bearish"
    line_color = "#dc2626"
else:
    trend_display = "⚪ Neutral"
    line_color = "#6b7280"

col6.metric("Trend", trend_display)
col7.metric("Momentum (14D)", f"{metrics['momentum_14']:.2f}%", f"{metrics['momentum_14']:.2f}%")
col8.metric("Rel. vs S&P", f"{metrics['relative_performance']:.2f}%", f"{metrics['relative_performance']:.2f}%")

risk = metrics["risk_regime"]
if risk == "Low":
    risk_display = "🟢 Low"
elif risk == "Moderate":
    risk_display = "🟡 Moderate"
else:
    risk_display = "🔴 High"

col9.metric("Risk Regime", risk_display)

with st.expander("What these market signals mean"):
    st.markdown("**Price:** Latest market price of the stock.")
    st.markdown("**30D Return:** Short-term performance indicator. Helps identify recent momentum or reversal.")
    st.markdown("**90D Return:** Medium-term trend signal. Often used to assess directional conviction.")
    st.markdown("**Volatility:** Annualized price variability. Higher values indicate greater uncertainty and risk.")
    st.markdown("**Max Drawdown:** Largest peak-to-trough decline. Measures downside risk and capital preservation risk.")
    st.markdown("**Trend:** Directional signal based on price movement and moving averages.")
    st.markdown("**Momentum (14D):** Short-term acceleration or deceleration in price movement.")
    st.markdown("**Rel. vs S&P:** Performance relative to the broader market. Indicates alpha generation or underperformance.")
    st.markdown("**Risk Regime:** Market environment classification. Helps contextualize signals.")


# =========================
# MARKET CHARTS
# =========================
st.subheader("Market Trend")
if not hist.empty and "Close" in hist.columns:
    fig_price = px.line(hist, x=hist.index, y="Close", title="GILD Price with 50D / 200D Moving Averages")
    fig_price.update_traces(line=dict(color=line_color, width=3), name="Close")

    if "MA_50" in hist.columns:
        fig_price.add_scatter(x=hist.index, y=hist["MA_50"], mode="lines", name="50D MA", line=dict(width=2, dash="dot"))
    if "MA_200" in hist.columns:
        fig_price.add_scatter(x=hist.index, y=hist["MA_200"], mode="lines", name="200D MA", line=dict(width=2, dash="dash"))

    fig_price.update_layout(legend_title_text="", hovermode="x unified")
    st.plotly_chart(fig_price, width="stretch", key="market_trend_chart")
else:
    st.warning("Market price history unavailable.")

if trend == "Bullish":
    st.success("Trend signal: upward bias supported by moving average structure.")
elif trend == "Bearish":
    st.error("Trend signal: downward bias with weaker technical structure.")
else:
    st.info("Trend signal: neutral positioning with no strong directional conviction.")

st.subheader("Rolling Volatility")
if not hist.empty and "Rolling Volatility" in hist.columns:
    fig_vol = px.line(hist, x=hist.index, y="Rolling Volatility", title="30-Day Rolling Volatility")
    st.plotly_chart(fig_vol, width="stretch", key="market_volatility_chart")
else:
    st.warning("Rolling volatility data unavailable.")

st.subheader("Drawdown")
if not hist.empty and "Drawdown" in hist.columns:
    fig_dd = px.line(hist, x=hist.index, y="Drawdown", title="Drawdown from 1-Year High")
    fig_dd.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.6)
    st.plotly_chart(fig_dd, width="stretch", key="market_drawdown_chart")
else:
    st.warning("Drawdown data unavailable.")

with st.expander("What these charts show"):
    st.markdown("**Price Trend:** Shows overall direction of the stock with moving averages to identify trend strength.")
    st.markdown("**50D vs 200D Moving Averages:** Used to identify trend shifts (bullish vs bearish crossover).")
    st.markdown("**Rolling Volatility:** Measures how unstable price movements are over time.")
    st.markdown("**Drawdown:** Shows how far the stock has fallen from its recent peak, highlighting downside risk.")


# =========================
# SEC FINANCIALS
# =========================
st.subheader("10-K Financial Baseline")


def format_pct(value):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.1f}%"


def format_ratio(value):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.2f}x"


def safe_metric_value(data, key, default=None):
    """Safely pull a metric from a dictionary-like object."""
    if data is None:
        return default
    try:
        value = data.get(key, default)
    except AttributeError:
        return default
    return default if value is None else value


def build_normalized_segment_metrics(segment_metrics):
    """
    Normalize segment keys so scoring functions can use either
    `hiv_pct` or `hiv_concentration` without breaking.
    """
    normalized = dict(segment_metrics or {})
    if "hiv_pct" not in normalized and "hiv_concentration" in normalized:
        normalized["hiv_pct"] = normalized["hiv_concentration"]
    return normalized


def render_signal_badge(label, value, color="#6b7280"):
    """Render a compact HTML badge for Streamlit metric-style signal cards."""
    st.markdown(
        f"""
        <div style="padding: 10px; border-radius: 8px; text-align: center; font-weight: 600; border: 2px solid {color}; color: {color};">
            {label}<br>{value}
        </div>
        """,
        unsafe_allow_html=True,
    )


try:
    financials = build_financial_baseline()

    if financials.empty:
        st.warning("SEC financial data unavailable.")
    else:
        # Calculate summary BEFORE scaling dollar values
        financial_summary = get_latest_financial_summary(financials)

        financials_display = financials.copy()

        dollar_cols = [
            "Revenue",
            "Net Income",
            "R&D Expense",
            "Operating Income",
            "Operating Cash Flow",
            "Cash & Equivalents",
            "Long-Term Debt",
            "Net Debt"
        ]

        for col in dollar_cols:
            if col in financials_display.columns:
                financials_display[col] = financials_display[col] / 1_000_000

        financials_display = financials_display.sort_values("year").tail(7)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Revenue Growth",
            format_pct(financial_summary["revenue_growth"])
        )
        col2.metric(
            "Operating Margin",
            format_pct(financial_summary["operating_margin"])
        )
        col3.metric(
            "R&D Intensity",
            format_pct(financial_summary["rd_intensity"])
        )
        col4.metric(
            "Debt / OCF",
            format_ratio(financial_summary["debt_ocf"])
        )

        with st.expander("What these financial metrics mean"):
            st.markdown("**Revenue Growth:** Measures whether the business is expanding or contracting year over year.")
            st.markdown("**Operating Margin:** Shows how efficiently Gilead turns revenue into operating profit.")
            st.markdown("**R&D Intensity:** Measures how much revenue is being reinvested into research and development.")
            st.markdown("**Debt / OCF:** Compares long-term debt to operating cash flow. Lower values suggest stronger debt coverage.")

        st.caption("Values shown in USD millions. Source: SEC companyfacts / 10-K filings.")
        st.dataframe(financials_display, width="stretch")

        with st.expander("SEC tag audit trail"):
            st.caption(
                "Shows which SEC XBRL tag was used for each financial metric and year. "
                "This improves auditability and helps validate companyfacts data quality."
            )

            audit_df = build_financial_tag_audit()

            if not audit_df.empty:
                st.dataframe(
                    audit_df.sort_values(["year", "metric"]).tail(50),
                    width="stretch"
                )
            else:
                st.warning("No SEC tag audit data available.")

        chart_cols = [
            col for col in [
                "Revenue",
                "R&D Expense",
                "Operating Cash Flow",
                "Operating Income",
                "Net Income"
            ] if col in financials_display.columns
        ]

        if chart_cols:
            fig_fin = px.line(
                financials_display,
                x="year",
                y=chart_cols,
                markers=True,
                title="Gilead 10-K Financial Trends"
            )

            st.plotly_chart(
                fig_fin,
                width="stretch",
                key="financial_trends_chart"
            )

except Exception as e:
    st.warning("SEC financial data failed.")
    st.error(e)


# =========================
# FINANCIAL QUALITY
# =========================
st.subheader("Financial Quality")
try:
    if financial_summary is None:
        raise ValueError("Financial summary unavailable.")

    col1, col2, col3, col4 = st.columns(4)
    rev_growth = financial_summary["revenue_growth"]
    op_margin = financial_summary["operating_margin"]
    rd_intensity = financial_summary["rd_intensity"]
    debt_ocf = financial_summary["debt_ocf"]

    col1.metric("Revenue Growth", f"{rev_growth:.1f}%", f"{rev_growth:.1f}%")
    col2.metric("Operating Margin", f"{op_margin:.1f}%", f"{op_margin:.1f}%")
    col3.metric("R&D Intensity", f"{rd_intensity:.1f}%")
    col4.metric("Debt / OCF", f"{debt_ocf:.2f}x", f"{debt_ocf:.2f}x", delta_color="inverse")

    with st.expander("What these financial quality metrics mean"):
        st.markdown("**Revenue Growth:** Indicates whether the company is expanding or contracting.")
        st.markdown("**Operating Margin:** Shows profitability and operating efficiency.")
        st.markdown("**R&D Intensity:** Shows how much revenue is being reinvested into future products.")
        st.markdown("**Debt / OCF:** Measures debt coverage using operating cash flow. Lower is better.")

except Exception:
    st.warning("Financial quality metrics unavailable.")


# =========================
# BUSINESS SEGMENTS
# =========================
st.subheader("Business Segment Exposure")
st.caption(get_segment_source_note())
try:
    segment_df = get_business_segment_data()
    segment_metrics = calculate_segment_metrics(segment_df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Sales", f"${segment_metrics['total_product_sales']:,.0f}M")
    col2.metric("HIV Sales", f"${segment_metrics['hiv_sales']:,.0f}M")
    col3.metric("HIV %", f"{segment_metrics['hiv_concentration']:.1f}%")
    col4.metric("Top 3 %", f"{segment_metrics['top_3_concentration']:.1f}%")

    col5, col6, col7 = st.columns(3)
    col5.metric("Revenue Dependence", segment_metrics["revenue_dependence"])
    col6.metric("Growth Exposure", f"{segment_metrics['growth_exposure']:.1f}%")
    col7.metric("Declining Exposure", f"{segment_metrics['declining_exposure']:.1f}%")

    with st.expander("What these segment metrics mean"):
        st.markdown("**Total Sales:** Total product sales in the segment baseline.")
        st.markdown("**HIV Sales:** Sales from Gilead’s core HIV franchise.")
        st.markdown("**HIV %:** Share of total sales from HIV. Higher values indicate concentration risk.")
        st.markdown("**Top 3 %:** Share of sales from the three largest categories. Higher values indicate less diversification.")
        st.markdown("**Revenue Dependence:** Classification of how concentrated revenue is.")
        st.markdown("**Growth Exposure:** Current exposure to future-facing areas such as oncology and cell therapy.")
        st.markdown("**Declining Exposure:** Exposure to legacy or declining categories such as COVID-19 and liver disease.")

    role_color_map = {"Core": "#6b7280", "Growth": "#16a34a", "Legacy": "#dc2626", "Other": "#9ca3af"}
    fig_segments = px.pie(
        segment_df,
        names="Segment",
        values="Sales",
        color="Segment Role",
        color_discrete_map=role_color_map,
        title="Product Sales Concentration by Franchise",
    )
    st.plotly_chart(fig_segments, width="stretch", key="segment_role_pie_chart")

    with st.expander("Segment role definitions"):
        st.markdown("**Core:** Current cash engine and main revenue base.")
        st.markdown("**Growth:** Future-facing areas expected to support diversification.")
        st.markdown("**Legacy:** Mature or declining categories with limited growth contribution.")
        st.markdown("**Other:** Smaller or miscellaneous revenue categories.")

    st.info(
        f"Gilead's largest segment is {segment_metrics['largest_segment']}, "
        f"representing approximately {segment_metrics['largest_segment_concentration']:.1f}% "
        "of product sales in this baseline. "
        f"Revenue dependence is classified as {segment_metrics['revenue_dependence'].lower()}, "
        f"with {segment_metrics['growth_exposure']:.1f}% current exposure to growth segments."
    )

except Exception as e:
    st.warning("Business segment data could not be loaded.")
    st.error(e)


# =========================
# CAPITAL ALLOCATION
# =========================
st.subheader("Capital Allocation")
st.caption(get_capital_allocation_source_note())
try:
    capital_signal = get_capital_allocation_signal()
    capital_df = build_capital_allocation_dataframe()
    capital_summary = get_capital_allocation_summary()
    capital_metrics = get_capital_allocation_metrics()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Dividends", f"${capital_signal['dividends']:,.0f}M")
    col2.metric("Buybacks", f"${capital_signal['buybacks']:,.0f}M")
    fcf_pct = capital_signal["fcf_return_pct"]
    col3.metric("FCF Returned", f"{fcf_pct}%", f"{fcf_pct}%")
    col4.metric("Allocation Score", f"{capital_metrics['capital_allocation_score']} / 5")

    with st.expander("What these capital allocation metrics mean"):
        st.markdown("**Dividends:** Cash returned directly to shareholders.")
        st.markdown("**Buybacks:** Share repurchases that reduce share count and support price.")
        st.markdown("**FCF Returned:** Percentage of free cash flow returned to shareholders.")
        st.markdown("**Allocation Score:** Evaluates balance between returning capital and reinvesting in growth.")

    fig_capital = px.pie(capital_df, names="Category", values="Amount", title="Capital Returned to Shareholders")
    st.plotly_chart(fig_capital, width="stretch", key="capital_allocation_pie_chart")
    st.info(capital_summary)

except Exception as e:
    st.warning("Capital allocation data could not be loaded.")
    st.error(e)


# =========================
# PIPELINE INTELLIGENCE
# =========================
st.subheader("Pipeline Intelligence")
st.caption(get_pipeline_source_note())
try:
    pipeline_df = get_pipeline_summary()
    pipeline_metrics = calculate_pipeline_metrics(pipeline_df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clinical Programs", f"{pipeline_metrics['clinical_stage_programs']}")
    col2.metric("Phase 3 Programs", f"{pipeline_metrics['phase_3_programs']}")
    col3.metric("Late-Stage Pipeline", f"{pipeline_metrics['late_stage_pct']:.1f}%")
    col4.metric("Pipeline Maturity", pipeline_metrics["pipeline_maturity"])

    with st.expander("What these pipeline metrics mean"):
        st.markdown("**Clinical Programs:** Total active clinical-stage pipeline assets.")
        st.markdown("**Phase 3 Programs:** Late-stage programs closest to potential commercialization.")
        st.markdown("**Late-Stage Pipeline:** Share of clinical programs in Phase 3. Higher values may indicate nearer-term execution potential.")
        st.markdown("**Pipeline Maturity:** Classification of how advanced the pipeline is overall.")

    phase_df = pipeline_df[pipeline_df["Metric"].str.contains("Phase", case=False, na=False)]
    fig_pipeline = px.bar(
        phase_df,
        x="Metric",
        y="Count",
        title="Pipeline Programs by Phase",
        color="Metric",
        text="Count",
    )
    fig_pipeline.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        cliponaxis=False,
    )
    fig_pipeline.update_layout(
        yaxis_title="Count",
        xaxis_title="Metric",
        uniformtext_minsize=12,
        uniformtext_mode="show",
    )
    st.plotly_chart(fig_pipeline, width="stretch", key="pipeline_phase_chart")

    focus_df = get_pipeline_focus_areas()
    st.dataframe(focus_df, width="stretch")

    watchlist_df = get_key_pipeline_watchlist()
    st.dataframe(watchlist_df, width="stretch")

    if "Impact Level" in watchlist_df.columns:
        impact_counts = watchlist_df["Impact Level"].value_counts().reset_index()
        impact_counts.columns = ["Impact Level", "Count"]
        impact_color_map = {"Very High": "#dc2626", "High": "#f59e0b", "Medium": "#84cc16", "Low": "#6b7280"}
        fig_impact = px.bar(
            impact_counts,
            x="Impact Level",
            y="Count",
            title="Pipeline Watchlist by Impact Level",
            color="Impact Level",
            color_discrete_map=impact_color_map,
        )
        st.plotly_chart(fig_impact, width="stretch", key="pipeline_impact_chart")

    catalyst_count = watchlist_df["Event Type"].str.contains("Catalyst", case=False, na=False).sum() if "Event Type" in watchlist_df.columns else 0
    negative_count = watchlist_df["Event Type"].str.contains("Negative|Exited", case=False, na=False).sum() if "Event Type" in watchlist_df.columns else 0
    st.info(
        "Pipeline intelligence connects current HIV concentration risk to future diversification potential. "
        f"The watchlist currently includes {catalyst_count} catalyst-linked items and {negative_count} negative or exited signals."
    )

except Exception as e:
    st.warning("Pipeline intelligence could not be loaded.")
    st.error(e)


# =========================
# FX EXPOSURE
# =========================
st.subheader("FX Exposure")
try:
    fx_df = get_fx_history()
    fx_metrics = calculate_fx_metrics(fx_df)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("FX Exposure", f"{fx_metrics['foreign_currency_sales_pct']}%")
    col2.metric("EUR/USD 90D", f"{fx_metrics['eurusd_return_90']:.2f}%", f"{fx_metrics['eurusd_return_90']:.2f}%")
    col3.metric("FX Volatility", f"{fx_metrics['eurusd_volatility']:.2f}%", f"{fx_metrics['eurusd_volatility']:.2f}%", delta_color="inverse")

    usd_trend = fx_metrics["usd_trend"]
    if usd_trend == "Strong USD":
        usd_display = "🔴 Strong USD"
    elif usd_trend == "Weak USD":
        usd_display = "🟢 Weak USD"
    else:
        usd_display = "⚪ Neutral"
    col4.metric("USD Trend", usd_display)

    fx_risk = fx_metrics["fx_risk_regime"]
    if fx_risk == "Low":
        fx_risk_display = "🟢 Low"
    elif fx_risk == "Moderate":
        fx_risk_display = "🟡 Moderate"
    else:
        fx_risk_display = "🔴 High"
    col5.metric("FX Risk", fx_risk_display)
    col6.metric(
        "Est. Revenue Impact",
        f"{fx_metrics['estimated_revenue_sensitivity']:.2f}%"
    )

    with st.expander("What these FX metrics mean"):
        st.markdown("**FX Exposure:** Share of sales exposed to foreign currency movements.")
        st.markdown("**EUR/USD 90D:** Recent movement in the euro versus the dollar. A stronger dollar can pressure translated foreign revenue.")
        st.markdown("**FX Volatility:** Measures instability in currency movements. Higher volatility increases uncertainty.")
        st.markdown("**USD Trend:** Indicates whether the dollar is strengthening or weakening.")
        st.markdown("**FX Risk:** Overall currency risk classification based on exposure and volatility.")
        st.markdown("**Est. Revenue Impact:** Directional estimate of revenue sensitivity from recent EUR/USD movement.")

    if not fx_metrics["history"].empty and "EURUSD" in fx_metrics["history"].columns:
        fig_fx = px.line(fx_metrics["history"], y="EURUSD", title="EUR/USD Exchange Rate")
        st.plotly_chart(fig_fx, width="stretch", key="fx_eurusd_chart")

    if not fx_metrics["history"].empty and "EURUSD Rolling Volatility" in fx_metrics["history"].columns:
        fig_fx_vol = px.line(fx_metrics["history"], y="EURUSD Rolling Volatility", title="EUR/USD 30-Day Rolling Volatility")
        fig_fx_vol.add_hline(y=fx_metrics["eurusd_volatility"], line_dash="dash", line_color="white", opacity=0.6)
        st.plotly_chart(fig_fx_vol, width="stretch", key="fx_volatility_chart")

    st.info(
        f"FX exposure is estimated at {fx_metrics['foreign_currency_sales_pct']}% of sales. "
        f"The current FX regime is classified as {fx_metrics['fx_risk_regime'].lower()}, "
        f"with estimated revenue sensitivity of {fx_metrics['estimated_revenue_sensitivity']:.2f}%."
    )

except Exception as e:
    st.warning("FX failed")
    st.error(e)


# =========================
# SECURITY INTELLIGENCE SIGNAL
# =========================
st.subheader("Security Intelligence Signal")
try:
    if financial_summary is None:
        raise ValueError("Financial summary unavailable.")
    if fx_metrics is None:
        raise ValueError("FX metrics unavailable.")
    if segment_metrics is None:
        raise ValueError("Segment metrics unavailable.")

    normalized_segment_metrics = build_normalized_segment_metrics(segment_metrics)
    security_signal_result = compute_security_signal(
        financial_summary=financial_summary,
        fx_metrics=fx_metrics,
        segment_metrics=normalized_segment_metrics,
    )
    security_signal = security_signal_result.get("signal", "Neutral")
    security_signal_score = security_signal_result.get("score", 0)

    security_signal_color_map = {
        "Attractive": "#16a34a",
        "Moderate": "#f59e0b",
        "Neutral": "#6b7280",
        "Unattractive": "#dc2626",
        "High Risk": "#991b1b",
    }
    security_signal_color = security_signal_color_map.get(security_signal, "#6b7280")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.markdown(
        f"""
        <div style="padding: 12px; border-radius: 8px; text-align: center; font-weight: 700; border: 2px solid {security_signal_color}; color: {security_signal_color};">
            Security Signal<br>{security_signal}
        </div>
        """,
        unsafe_allow_html=True,
    )
    col2.metric("Signal Score", f"{security_signal_score}")
    col3.metric("Operating Margin", format_pct(safe_metric_value(financial_summary, "operating_margin")))
    col4.metric("Revenue Growth", format_pct(safe_metric_value(financial_summary, "revenue_growth")))
    col5.metric("HIV Concentration", format_pct(safe_metric_value(normalized_segment_metrics, "hiv_pct")))

    with st.expander("How the security signal is calculated"):
        st.markdown("The security signal adds points for strong profitability, positive revenue growth, manageable debt coverage, and low FX risk.")
        st.markdown("It subtracts one point when HIV concentration is above the concentration threshold, because that increases franchise dependence risk.")
        st.markdown("This is a directional screening signal and should be interpreted alongside the risk-adjusted expected return model below.")

except Exception as e:
    st.warning("Security intelligence signal could not be calculated.")
    st.error(e)


# =========================
# SEC RISK FACTORS
# =========================
st.subheader("SEC Risk Factor Analysis")
try:
    sec_risk = build_sec_risk_factor_analysis()
    sec_risk_df = sec_risk["risk_df"]
    total_mentions = sec_risk_df["Keyword Count"].sum()

    if total_mentions == 0:
        st.warning("No risk factor keywords detected. Check parser or filing structure.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Risk Keywords Detected", f"{total_mentions:,.0f}")
    top_risk = sec_risk_df.sort_values("Keyword Count", ascending=False).iloc[0]["Risk Category"] if total_mentions > 0 else "N/A"
    col2.metric("Top Risk Theme", top_risk)
    sec_risk_score = sec_risk.get("sec_risk_score", {})
    col3.metric("SEC Risk Score", f"{sec_risk_score.get('sec_risk_score', 0)} / 5")

    with st.expander("What this risk factor analysis means"):
        st.markdown("**Risk Keywords Detected:** Total number of tracked risk terms found in the 10-K risk factor section.")
        st.markdown("**Top Risk Theme:** The category with the highest keyword count.")
        st.markdown("**SEC Risk Score:** Directional score based on total risk factor keyword intensity.")
        st.markdown("**Keyword Count:** A directional signal, not a precise probability estimate.")
        st.markdown("**Purpose:** Helps identify which risk themes may deserve closer monitoring.")

    st.dataframe(sec_risk_df, width="stretch")
    fig_sec = px.bar(
        sec_risk_df,
        x="Risk Category",
        y="Keyword Count",
        color="Keyword Count",
        color_continuous_scale="Blues",
        title="10-K Risk Factor Keyword Analysis",
    )
    fig_sec.update_layout(xaxis_title="Risk Category", yaxis_title="Keyword Count", hovermode="x unified")
    st.plotly_chart(fig_sec, width="stretch", key="sec_risk_factor_chart")

    st.info(
        f"SEC risk factor analysis detected {total_mentions:,.0f} tracked keyword mentions. "
        f"The most prominent theme is {top_risk}. This is intended as a monitoring signal "
        "to flag areas that may require closer review, not as a standalone risk conclusion."
    )

except Exception as e:
    st.warning("SEC risk analysis failed")
    st.error(e)


# =========================
# NEWS & FILINGS TRACKER
# =========================
st.subheader("News & Filings Tracker")
try:
    news_df = build_news_tracker()
    news_summary = get_news_summary(news_df)
    news_risk = calculate_news_risk_score(news_df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tracked Items", news_summary["total_items"])
    col2.metric("Top Category", news_summary["top_category"])

    urgency = news_summary["max_urgency"]
    if urgency >= 4:
        urgency_display = f"🔴 {urgency} / 5"
    elif urgency >= 3:
        urgency_display = f"🟡 {urgency} / 5"
    else:
        urgency_display = f"🟢 {urgency} / 5"
    col3.metric("Max Urgency", urgency_display)

    news_risk_label = news_risk["news_risk_label"]
    if news_risk_label == "High":
        news_risk_display = f"🔴 {news_risk_label}"
    elif news_risk_label == "Elevated":
        news_risk_display = f"🟠 {news_risk_label}"
    elif news_risk_label == "Moderate":
        news_risk_display = f"🟡 {news_risk_label}"
    else:
        news_risk_display = f"🟢 {news_risk_label}"
    col4.metric("News Risk", news_risk_display)

    st.info(f"Latest headline: {news_summary['latest_headline']}")
    st.info(news_risk["news_risk_summary"])

    with st.expander("What this tracker means"):
        st.markdown("**Tracked Items:** Number of recent news or filing items being monitored.")
        st.markdown("**Top Category:** Most common category among tracked items.")
        st.markdown("**Max Urgency:** Highest urgency score among recent items. Higher values deserve closer review.")
        st.markdown("**Purpose:** Helps flag whether new information may affect risk, valuation, or expected return assumptions.")

    if not news_df.empty:
        st.dataframe(news_df.head(10), width="stretch")
        if "category" in news_df.columns:
            category_counts = news_df["category"].value_counts().reset_index()
            category_counts.columns = ["Category", "Count"]
            fig_news = px.bar(category_counts, x="Category", y="Count", title="Recent News / Filing Categories", color="Category")
            fig_news.update_layout(showlegend=False, hovermode="x unified")
            st.plotly_chart(fig_news, width="stretch", key="news_category_chart")
        else:
            st.warning("No category data available for news analysis.")
    else:
        st.warning("No news or filing items were returned.")

except Exception as e:
    st.warning("News tracker could not be loaded.")
    st.error(e)


# =========================
# UNIFIED INTELLIGENCE RISK
# =========================
st.subheader("Unified Intelligence Risk")
try:
    intelligence_risk = score_intelligence_risk(
        market_metrics=metrics,
        sec_risk_score=sec_risk.get("sec_risk_score") if sec_risk else None,
        news_risk=news_risk if news_risk else None,
    )

    col1, col2 = st.columns(2)
    col1.metric("Intelligence Risk Score", f"{intelligence_risk['intelligence_risk_score']:.2f} / 5")

    risk_label = intelligence_risk["intelligence_risk_label"]
    if risk_label == "High":
        risk_display = f"🔴 {risk_label}"
    elif risk_label == "Elevated":
        risk_display = f"🟠 {risk_label}"
    elif risk_label == "Moderate":
        risk_display = f"🟡 {risk_label}"
    else:
        risk_display = f"🟢 {risk_label}"

    col2.metric("Risk Level", risk_display)
    st.info(intelligence_risk["intelligence_risk_summary"])

except Exception as e:
    st.warning("Unified intelligence risk could not be calculated.")
    st.error(e)


# =========================
# PEER COMPARISON
# =========================
st.subheader("Peer Comparison")
try:
    peer_df = get_peer_price_history(period="1y")
    peer_ranked = rank_peer_metrics(peer_df)
    peer_summary = get_gilead_peer_summary(peer_ranked)

    col1, col2 = st.columns(2)
    col1.metric("Gilead Peer Rank", f"{peer_summary['gilead_rank']} / {peer_summary['peer_count']}")
    col2.metric("Peer Set", f"{peer_summary['peer_count']} companies")

    with st.expander("What peer comparison means"):
        st.markdown("**Gilead Peer Rank:** Relative rank versus selected biopharma peers. Lower rank is better.")
        st.markdown("**Composite Rank:** Combines return, volatility, and drawdown ranking.")
        st.markdown("**90D Return:** Recent medium-term performance compared with peers.")
        st.markdown("**Volatility:** Measures relative price instability versus peers.")
        st.markdown("**Purpose:** Helps identify whether Gilead is outperforming, lagging, or moving with its peer group.")

    st.info(peer_summary["summary"])
    st.dataframe(peer_ranked, width="stretch")

    fig_peer_rank = px.bar(peer_ranked, x="Company", y="Composite Rank", title="Peer Composite Ranking (Lower = Better)", color="Composite Rank", color_continuous_scale="Blues")
    fig_peer_rank.update_layout(hovermode="x unified")
    st.plotly_chart(fig_peer_rank, width="stretch", key="peer_rank_chart")

    fig_peer_return = px.bar(peer_ranked, x="Company", y="90D Return", title="90-Day Return by Peer", color="90D Return", color_continuous_scale="RdYlGn")
    fig_peer_return.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.6)
    st.plotly_chart(fig_peer_return, width="stretch", key="peer_return_chart")

    fig_peer_vol = px.bar(peer_ranked, x="Company", y="Volatility", title="Annualized Volatility by Peer", color="Volatility", color_continuous_scale="Reds")
    st.plotly_chart(fig_peer_vol, width="stretch", key="peer_volatility_chart")

except Exception as e:
    st.warning("Peer comparison could not be loaded.")
    st.error(e)


# =========================
# VALUATION INTELLIGENCE
# =========================
st.subheader("Valuation Intelligence")
st.caption(get_valuation_source_note())
try:
    val_inputs = get_valuation_inputs(current_price=metrics["price"])
    val_metrics = calculate_valuation_metrics(val_inputs)
    val_summary = get_valuation_summary(val_metrics)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Base Upside", f"{val_metrics['upside_base']:.1f}%", f"{val_metrics['upside_base']:.1f}%")
    col2.metric("Bull Case", f"{val_metrics['upside_bull']:.1f}%", f"{val_metrics['upside_bull']:.1f}%")
    col3.metric("Bear Case", f"{val_metrics['downside_bear']:.1f}%", f"{val_metrics['downside_bear']:.1f}%")
    col4.metric("P/E Discount", f"{val_metrics['pe_discount']:.1f}%", f"{val_metrics['pe_discount']:.1f}%")
    col5.metric("Target Dispersion", f"${val_metrics['target_dispersion']:.0f}")

    valuation_signal = val_summary["signal"]
    if valuation_signal == "Strong Undervaluation":
        val_color = "#16a34a"
    elif valuation_signal == "Moderate Undervaluation":
        val_color = "#84cc16"
    elif valuation_signal == "Fair Value":
        val_color = "#6b7280"
    else:
        val_color = "#dc2626"

    st.markdown(
        f"""
        <div style="padding: 12px; border-radius: 8px; background-color: rgba(0,0,0,0.2); border-left: 5px solid {val_color}; font-size: 15px; font-weight: 600;">
            Valuation Signal: <span style="color:{val_color};">{valuation_signal}</span><br>
            <span style="font-size: 13px; font-weight: 400;">{val_summary['summary']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("What these valuation metrics mean"):
        st.markdown("**Base Upside:** Implied upside from the base-case fair value estimate.")
        st.markdown("**Bull Case:** Implied upside under a stronger execution or rerating scenario.")
        st.markdown("**Bear Case:** Implied downside or upside under the lower target scenario.")
        st.markdown("**P/E Discount:** Discount versus historical valuation multiple.")
        st.markdown("**Target Dispersion:** Difference between bull and bear targets. Wider dispersion means higher uncertainty.")

except Exception as e:
    st.warning("Valuation intelligence could not be loaded.")
    st.error(e)


# =========================
# DATA-DRIVEN SCORING
# =========================
st.subheader("Data-Driven Risk Scoring")
try:
    scores = build_data_driven_scores(
        market_metrics=metrics,
        segment_metrics=segment_metrics,
        fx_metrics=fx_metrics,
        sec_risk_df=sec_risk_df,
        valuation_metrics=val_metrics,
        pipeline_metrics=pipeline_metrics,
        financial_summary=financial_summary,
    )

    score_df = build_score_dataframe(scores)
    summary = get_scoring_summary(scores)

    financial_quality_score = scores.get("Financial Quality", None)
    if financial_quality_score is not None:
        if financial_quality_score <= 2:
            fq_color, fq_label = "#16a34a", "Strong"
        elif financial_quality_score <= 3:
            fq_color, fq_label = "#84cc16", "Stable"
        elif financial_quality_score <= 4:
            fq_color, fq_label = "#f59e0b", "Watch"
        else:
            fq_color, fq_label = "#dc2626", "Weak"

        st.markdown(
            f"""
            <div style="padding: 12px; border-radius: 8px; background-color: rgba(0,0,0,0.2); border-left: 5px solid {fq_color}; font-size: 15px; font-weight: 600;">
                Financial Quality Signal: <span style="color:{fq_color};">{fq_label}</span><br>
                <span style="font-size: 13px; font-weight: 400;">This summarizes margin strength, cash flow quality, growth, and debt coverage.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col1, col2 = st.columns(2)
    col1.metric("Composite Score", f"{summary['composite_score']:.2f} / 5")
    col2.metric("Rating", summary["rating"])

    with st.expander("What these scoring metrics mean"):
        st.markdown("**Composite Score:** Weighted risk score from 1 to 5. Higher means more risk.")
        st.markdown("**Rating:** Classification of the composite score.")
        st.markdown("**Financial Quality Signal:** Interprets margins, cash flow, growth, and debt coverage.")
        st.markdown("**Risk Category Scores:** Individual risk components feeding the composite score.")

    fig_scores = px.bar(score_df, x="Risk Category", y="Score", color="Score", color_continuous_scale="Blues", range_color=[1, 5], title="Data-Driven Risk Scores")
    st.plotly_chart(fig_scores, width="stretch", key="risk_scores_chart")
    st.dataframe(score_df, width="stretch")
    st.info(summary["summary"])

except Exception as e:
    st.warning("Scoring failed.")
    st.error(e)


# =========================
# COMPOSITE RISK POSITIONING
# =========================
st.markdown("## Composite Risk Positioning")

try:
    gauge_score = summary["composite_score"] * 2

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=gauge_score,
        title={"text": "Security Risk Score (0 = Low Risk, 10 = High Risk)"},
        gauge={
            "axis": {"range": [0, 10]},
            "bar": {"color": "white"},
            "steps": [
                {"range": [0, 3], "color": "#16a34a"},
                {"range": [3, 6], "color": "#f59e0b"},
                {"range": [6, 10], "color": "#dc2626"},
            ],
        },
    ))

    st.plotly_chart(
        fig_gauge,
        width="stretch",
        key="composite_risk_gauge"
    )

except Exception:
    st.warning("Composite risk gauge unavailable.")

# =========================
# FORWARD REVENUE FORECAST
# =========================
st.subheader("Forward Revenue Mix Projection")
try:
    if segment_metrics is None:
        raise ValueError("Segment metrics unavailable.")

    base_mix = get_base_revenue_mix(segment_metrics)
    future_mix = project_future_mix(base_mix, pipeline_metrics)
    shift = calculate_revenue_shift(base_mix, future_mix)
    forecast_summary = get_forecast_summary(base_mix, future_mix, shift)

    df_mix = pd.DataFrame({
        "Segment": list(base_mix.keys()),
        "Current Mix (%)": [v * 100 for v in base_mix.values()],
        "Projected Mix (%)": [future_mix.get(k, 0) * 100 for k in base_mix.keys()],
    })
    df_mix["Change (pts)"] = df_mix["Projected Mix (%)"] - df_mix["Current Mix (%)"]

    col1, col2, col3 = st.columns(3)
    hiv_current = df_mix.loc[df_mix["Segment"] == "HIV", "Current Mix (%)"].sum()
    hiv_projected = df_mix.loc[df_mix["Segment"] == "HIV", "Projected Mix (%)"].sum()
    hiv_change = hiv_projected - hiv_current
    col1.metric("Current HIV Mix", f"{hiv_current:.1f}%")
    col2.metric("Projected HIV Mix", f"{hiv_projected:.1f}%", f"{hiv_change:.1f} pts", delta_color="inverse")
    col3.metric("Revenue Shift", f"{hiv_change:.1f} pts", f"{hiv_change:.1f} pts", delta_color="inverse")

    with st.expander("What this forecast means"):
        st.markdown("**Current Mix:** Current estimated revenue distribution.")
        st.markdown("**Projected Mix:** Directional estimate of future revenue mix based on pipeline maturity.")
        st.markdown("**Change:** Difference between current and projected mix.")
        st.markdown("**Purpose:** This is not a precise forecast. It is a directional view of possible diversification.")

    st.dataframe(df_mix, width="stretch")
    fig_mix = px.bar(df_mix.melt(id_vars="Segment"), x="Segment", y="value", color="variable", barmode="group", title="Current vs Projected Revenue Mix")
    st.plotly_chart(fig_mix, width="stretch", key="forward_mix_chart")
    st.info(forecast_summary)

except Exception as e:
    st.warning("Forecast model failed.")
    st.error(e)


# =========================
# EXPECTED RETURN MODEL
# =========================
st.subheader("Expected Return Model")
try:
    expected_model = build_price_target_scenarios(
        current_price=metrics["price"],
        val_metrics=val_metrics,
        segment_metrics=segment_metrics,
        summary=summary,
        market_metrics=metrics,
        financial_summary=financial_summary,
        segment_df=segment_df,
        capital_metrics=capital_metrics,
    )

    expected_df = expected_model["scenarios"]
    expected_price_target = expected_model["expected_price_target"]
    expected_return = expected_model["expected_return"]

    diversification_adjusted = apply_diversification_adjustment(expected_return=expected_return, segment_metrics=segment_metrics)
    adjusted_expected_return = diversification_adjusted["diversification_adjusted_return"]
    diversification_adjustment = diversification_adjusted["diversification_adjustment"]

    capital_adjusted = apply_capital_allocation_adjustment(expected_return=adjusted_expected_return, capital_metrics=capital_metrics)
    adjusted_expected_return = capital_adjusted["capital_allocation_adjusted_return"]
    capital_allocation_adjustment = capital_adjusted["capital_allocation_adjustment"]

    role_adjusted = calculate_segment_role_adjustment(segment_df=segment_df)
    adjusted_expected_return += role_adjusted["segment_role_adjustment"]
    segment_role_adjustment = role_adjusted["segment_role_adjustment"]
    segment_role_summary = role_adjusted["role_summary"]

    forward_mix_adjusted = apply_forward_mix_adjustment(expected_return=adjusted_expected_return, future_mix=future_mix)
    adjusted_expected_return = forward_mix_adjusted["forward_mix_adjusted_return"]
    forward_mix_adjustment = forward_mix_adjusted["forward_mix_adjustment"]
    forward_mix_summary = forward_mix_adjusted["forward_mix_summary"]

    composite_risk_score = summary["composite_score"] if summary else 3
    risk_adjusted = risk_adjust_expected_return(
        expected_return=adjusted_expected_return,
        composite_risk_score=composite_risk_score,
        intelligence_risk=intelligence_risk,
        pipeline_metrics=pipeline_metrics,
        news_risk=news_risk,
    )

    signal = classify_expected_return_signal(risk_adjusted["risk_adjusted_return"])
    confidence = calculate_confidence_score(summary=summary, market_metrics=metrics, valuation_metrics=val_metrics, financial_summary=financial_summary)

    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)
    col1.metric("Expected Price Target", f"${expected_price_target:.2f}")
    col2.metric("Expected Return", f"{expected_return:.1f}%")
    col3.metric("Diversification Adj.", f"{diversification_adjustment:.1f} pts")
    col4.metric("Capital Allocation Adj.", f"{capital_allocation_adjustment:.1f} pts")
    col5.metric("Segment Role Adj.", f"{segment_role_adjustment:.1f} pts")
    col6.metric("Forward Mix Adj.", f"{forward_mix_adjustment:.1f} pts")
    col7.metric("Risk-Adjusted Return", f"{risk_adjusted['risk_adjusted_return']:.1f}%")

    signal_color = {"Attractive": "#16a34a", "Moderate": "#84cc16", "Neutral": "#6b7280", "Unattractive": "#dc2626"}.get(signal, "#6b7280")
    col8.markdown(
        f"""
        <div style="padding: 10px; border-radius: 8px; text-align: center; font-weight: 600; border: 2px solid {signal_color}; color: {signal_color};">
            Signal<br>{signal}
        </div>
        """,
        unsafe_allow_html=True,
    )

    conf_score = confidence["confidence_score"]
    conf_label = confidence["confidence_label"]
    conf_color = "#16a34a" if conf_score >= 75 else "#84cc16" if conf_score >= 55 else "#dc2626"
    col9.markdown(
        f"""
        <div style="padding: 10px; border-radius: 8px; text-align: center; font-weight: 600; border: 2px solid {conf_color}; color: {conf_color};">
            Confidence<br>{conf_score:.0f}% ({conf_label})
        </div>
        """,
        unsafe_allow_html=True,
    )

    headline_signal = get_headline_signal(signal, confidence, risk_adjusted["risk_adjusted_return"])
    catalyst_line = get_catalyst_trigger_line(signal, confidence, risk_adjusted["risk_adjusted_return"])
    st.info(headline_signal)
    st.info(catalyst_line)

    st.info(
        get_expected_return_narrative(
            expected_return=expected_return,
            risk_adjusted_return=risk_adjusted["risk_adjusted_return"],
            signal=signal,
            confidence=confidence,
            diversification_adjustment=diversification_adjustment,
            capital_allocation_adjustment=capital_allocation_adjustment,
            segment_role_adjustment=segment_role_adjustment,
            forward_mix_adjustment=forward_mix_adjustment,
        )
    )

    total_adjustment = diversification_adjustment + capital_allocation_adjustment + segment_role_adjustment + forward_mix_adjustment
    st.markdown(
        f"""
        <div style="padding: 12px; border-radius: 8px; background-color: rgba(0,0,0,0.2); border-left: 5px solid #3b82f6; font-size: 14px;">
            <b>Adjustment Breakdown:</b><br>
            Diversification: {diversification_adjustment:.1f} pts |
            Capital Allocation: {capital_allocation_adjustment:.1f} pts |
            Segment Role: {segment_role_adjustment:.1f} pts |
            Forward Mix: {forward_mix_adjustment:.1f} pts<br>
            <b>Total Adjustment: {total_adjustment:.1f} pts</b><br><br>
            <b>Segment Role Insight:</b> {segment_role_summary}<br>
            <b>Forward Mix Insight:</b> {forward_mix_summary}<br>
            <b>Risk Haircut:</b> {risk_adjusted['risk_haircut']:.1f}%
            (Base: {risk_adjusted['base_risk_haircut']:.1f}%,
            Intelligence: {risk_adjusted['intelligence_haircut']:.1f}%,
            Pipeline: {risk_adjusted['pipeline_haircut']:.1f}%,
            News: {risk_adjusted['news_haircut']:.1f}%)
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("What these expected return metrics mean"):
        st.markdown(explain_metric("Expected Price Target"))
        st.markdown(explain_metric("Expected Return"))
        st.markdown(explain_metric("Diversification Adj."))
        st.markdown(explain_metric("Capital Allocation Adj."))
        st.markdown(explain_metric("Segment Role Adj."))
        st.markdown(explain_metric("Forward Mix Adj."))
        st.markdown(explain_metric("Risk-Adjusted Return"))
        st.markdown(explain_metric("Signal"))
        st.markdown(explain_metric("Confidence"))

    st.dataframe(expected_df, width="stretch")
    fig_expected = px.bar(
        expected_df,
        x="Scenario",
        y="Return %",
        color="Scenario",
        text="Return %",
        title="Scenario Return by Price Target",
        color_discrete_map={"Bear": "#dc2626", "Base": "#6b7280", "Bull": "#16a34a"},
    )
    fig_expected.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
        cliponaxis=False,
    )
    fig_expected.update_layout(
        yaxis_title="Return %",
        xaxis_title="Scenario",
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )
    st.plotly_chart(fig_expected, width="stretch", key="expected_return_chart")

    st.info(
        get_expected_return_summary(
            expected_price_target=expected_price_target,
            expected_return=expected_return,
            risk_adjusted_return=risk_adjusted["risk_adjusted_return"],
            signal=signal,
            diversification_adjustment=diversification_adjustment,
            capital_allocation_adjustment=capital_allocation_adjustment,
            segment_role_adjustment=segment_role_adjustment,
            forward_mix_adjustment=forward_mix_adjustment,
        )
    )

except Exception as e:
    st.error("🚨 Expected Return Model failed to load.")
    st.code(str(e))


# =========================
# CHANGE DETECTION
# =========================
st.subheader("Change Detection")
try:
    previous_snapshot = load_previous_snapshot()
    current_snapshot = build_current_snapshot(
        metrics=metrics,
        summary=summary,
        expected_return=risk_adjusted["risk_adjusted_return"] if risk_adjusted is not None else None,
        signal=signal,
        intelligence_risk=intelligence_risk,
        risk_adjusted=risk_adjusted,
    )

    change_report = detect_dashboard_changes(current_snapshot, previous_snapshot)
    if (
        change_report.get("signal_changed")
        or change_report.get("rating_changed")
        or change_report.get("trend_changed")
        or change_report.get("intelligence_risk_changed")
    ):
        st.warning(change_report["summary"])
    else:
        st.info(change_report["summary"])

    save_current_snapshot(current_snapshot)

except Exception as e:
    st.warning("Change detection could not be completed.")
    st.error(e)


# =========================
# FINAL SECURITY POSITIONING
# =========================
st.markdown("## Final Security Positioning")

try:
    if risk_adjusted is None:
        raise ValueError("Risk-adjusted return unavailable.")
    if summary is None:
        raise ValueError("Composite scoring summary unavailable.")

    expected_signal_color_map = {
        "Attractive": "#16a34a",
        "Moderate": "#f59e0b",
        "Neutral": "#6b7280",
        "Unattractive": "#dc2626",
        "High Risk": "#991b1b",
    }
    expected_signal_color = expected_signal_color_map.get(signal, "#6b7280")
    confidence_label = confidence.get("confidence_label", "N/A") if confidence else "N/A"

    st.markdown(
        f"""
        <div style="
            padding: 20px;
            border-radius: 10px;
            background-color: rgba(255,255,255,0.05);
            border-left: 6px solid {expected_signal_color};
            font-size: 18px;
        ">
            <b>Expected Return Signal: {signal}</b> - {confidence_label} Confidence<br>
            <b>Fundamental Security Signal: {security_signal if security_signal else 'N/A'}</b>
            {f"(Score: {security_signal_score})" if security_signal_score is not None else ""}<br><br>
            Risk-Adjusted Return: <b>{risk_adjusted['risk_adjusted_return']:.1f}%</b><br>
            Composite Risk Score: <b>{summary['composite_score']:.2f} / 5</b><br>
            Risk Haircut: <b>{risk_adjusted['risk_haircut']:.1f}%</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

except Exception as e:
    st.warning("Final security positioning unavailable.")
    st.error(e)

# =========================
# PDF EXPORT
# =========================
st.subheader("Export Intelligence Brief")
if st.button("Generate PDF Brief"):
    try:
        expected_return_summary = None
        if risk_adjusted is not None:
            expected_return_summary = {
                "expected_price_target": expected_price_target if "expected_price_target" in locals() else 0,
                "expected_return": expected_return if "expected_return" in locals() else 0,
                "risk_adjusted_return": risk_adjusted.get("risk_adjusted_return", 0),
                "signal": signal if signal else "N/A",
                "summary": get_expected_return_summary(
                    expected_price_target=expected_price_target if "expected_price_target" in locals() else 0,
                    expected_return=expected_return if "expected_return" in locals() else 0,
                    risk_adjusted_return=risk_adjusted.get("risk_adjusted_return", 0),
                    signal=signal if signal else "N/A",
                    diversification_adjustment=diversification_adjustment if "diversification_adjustment" in locals() else 0,
                    capital_allocation_adjustment=capital_allocation_adjustment if "capital_allocation_adjustment" in locals() else 0,
                    segment_role_adjustment=segment_role_adjustment if "segment_role_adjustment" in locals() else 0,
                    forward_mix_adjustment=forward_mix_adjustment if "forward_mix_adjustment" in locals() else 0,
                ),
            }

        pdf_path = generate_intelligence_brief(
            market_metrics=metrics,
            segment_metrics=segment_metrics if segment_metrics is not None else {},
            risk_summary={
                "overall_score": summary["composite_score"] if summary else 0,
                "risk_rating": summary["rating"] if summary else "N/A",
                "summary": summary["summary"] if summary else "No summary available.",
            },
            fx_metrics=fx_metrics,
            pipeline_metrics=pipeline_metrics,
            scoring_summary=summary,
            expected_return_summary=expected_return_summary,
            intelligence_risk=intelligence_risk,
            news_risk=news_risk,
            capital_metrics=capital_metrics,
            risk_adjusted=risk_adjusted,
            signal=signal if signal else security_signal,
            confidence=confidence,
            financial_summary=financial_summary,
            security_signal=security_signal_result,
            output_path="gilead_intelligence_brief.pdf",
        )

        with open(pdf_path, "rb") as file:
            st.download_button(
                label="Download Intelligence Brief",
                data=file,
                file_name="gilead_intelligence_brief.pdf",
                mime="application/pdf",
            )

    except Exception as e:
        st.warning("PDF brief could not be generated.")
        st.error(e)
