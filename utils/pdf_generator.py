from datetime import datetime
from fpdf import FPDF


# =========================
# TEXT / FORMAT HELPERS
# =========================

def clean_text(text):
    """
    Convert text to a safer ASCII-friendly format for FPDF's default fonts.
    This prevents errors from smart quotes, em dashes, bullets, emojis, etc.
    """
    if text is None:
        return ""

    return (
        str(text)
        .replace("—", "-")
        .replace("–", "-")
        .replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
        .replace("‘", "'")
        .replace("•", "-")
        .replace("…", "...")
        .replace("→", "->")
        .replace("↑", "Up")
        .replace("↓", "Down")
        .replace("🟢", "")
        .replace("🟡", "")
        .replace("🟠", "")
        .replace("🔴", "")
        .replace("⚪", "")
        .strip()
    )


def safe_float(value, default=0.0):
    """Safely convert values to float for PDF formatting."""
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_get(dictionary, key, default="N/A"):
    """Safely get a value from a dictionary-like object."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, default)
    return default


def fmt_pct(value, decimals=1, default="N/A"):
    """Format a value as a percentage."""
    if value is None:
        return default
    return f"{safe_float(value):.{decimals}f}%"


def fmt_money(value, decimals=0, suffix="M", default="$0M"):
    """Format a value as dollars."""
    if value is None:
        return default
    return f"${safe_float(value):,.{decimals}f}{suffix}"


def fmt_ratio(value, decimals=2, suffix="x", default="N/A"):
    """Format a value as a ratio."""
    if value is None:
        return default
    return f"{safe_float(value):.{decimals}f}{suffix}"


# =========================
# PDF CLASS
# =========================

class IntelligenceBriefPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 8, "Gilead Security Intelligence Brief", ln=True, align="C")

        self.set_font("Arial", "", 8)
        self.cell(
            0,
            5,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            ln=True,
            align="C",
        )
        self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_font("Arial", "I", 7)
        self.cell(
            0,
            5,
            f"Educational / informational use only | Page {self.page_no()}",
            align="C",
        )

    def section_title(self, title):
        self.ln(3)
        self.set_font("Arial", "B", 11)
        self.set_fill_color(235, 235, 235)
        self.cell(0, 7, clean_text(title), ln=True, fill=True)
        self.ln(1)
        self.set_font("Arial", "", 9)

    def metric_line(self, label, value):
        self.set_font("Arial", "B", 8.5)
        self.cell(62, 5.5, f"{clean_text(label)}:")
        self.set_font("Arial", "", 8.5)
        self.multi_cell(0, 5.5, clean_text(value))

    def paragraph(self, text):
        if not text:
            return
        self.set_font("Arial", "", 8.5)
        self.multi_cell(0, 5, clean_text(text))
        self.ln(1)

    def bullet(self, text):
        self.set_font("Arial", "", 8.5)
        self.cell(4, 5, "-")
        self.multi_cell(0, 5, clean_text(text))

    def divider(self):
        self.ln(1)
        self.set_draw_color(210, 210, 210)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)


# =========================
# MAIN PDF GENERATOR
# =========================

def generate_intelligence_brief(
    market_metrics,
    segment_metrics,
    risk_summary,
    output_path="gilead_intelligence_brief.pdf",
    fx_metrics=None,
    pipeline_metrics=None,
    scoring_summary=None,
    expected_return_summary=None,
    intelligence_risk=None,
    news_risk=None,
    capital_metrics=None,
    risk_adjusted=None,
    signal=None,
    confidence=None,
    financial_summary=None,
    security_signal=None,
):
    """
    Generate a concise PDF intelligence brief for the Gilead dashboard.

    This function is intentionally defensive:
    - Missing sections are skipped or filled with N/A.
    - Unicode characters are cleaned for FPDF compatibility.
    - Existing app.py calls remain compatible.
    """

    market_metrics = market_metrics or {}
    segment_metrics = segment_metrics or {}
    risk_summary = risk_summary or {}
    fx_metrics = fx_metrics or None
    pipeline_metrics = pipeline_metrics or None
    scoring_summary = scoring_summary or None
    expected_return_summary = expected_return_summary or None
    intelligence_risk = intelligence_risk or None
    news_risk = news_risk or None
    capital_metrics = capital_metrics or None
    risk_adjusted = risk_adjusted or None
    confidence = confidence or None
    financial_summary = financial_summary or None
    security_signal = security_signal or None

    pdf = IntelligenceBriefPDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    # =========================
    # EXECUTIVE SUMMARY
    # =========================
    pdf.section_title("Executive Intelligence Summary")

    executive_summary = (
        f"Gilead currently operates within a {safe_get(market_metrics, 'risk_regime')} "
        f"market risk regime, with a {safe_get(market_metrics, 'trend_signal')} "
        f"trend signal and {fmt_pct(safe_get(market_metrics, 'returns_90', 0), 1)} "
        "90-day return. This brief integrates market signals, SEC financial baselines, "
        "product exposure, FX dynamics, pipeline intelligence, valuation scenarios, "
        "news/filings monitoring, and risk-adjusted expected return modeling into a "
        "security-level intelligence view."
    )
    pdf.paragraph(executive_summary)

    pdf.bullet("Product concentration remains a key structural risk because HIV represents the majority of product sales.")
    pdf.bullet("Pipeline execution and oncology diversification remain important drivers of long-term upside.")
    pdf.bullet("Valuation and risk-adjusted return outputs should be treated as directional model estimates.")

    # =========================
    # SECURITY INTELLIGENCE SIGNAL
    # =========================
    pdf.section_title("Security Intelligence Signal")

    final_signal = signal
    if final_signal is None and isinstance(expected_return_summary, dict):
        final_signal = expected_return_summary.get("signal")
    if final_signal is None and isinstance(security_signal, dict):
        final_signal = security_signal.get("signal")

    pdf.metric_line("Expected Return Signal", final_signal if final_signal else "N/A")

    if confidence:
        pdf.metric_line(
            "Confidence",
            f"{safe_float(confidence.get('confidence_score')):.0f}% "
            f"({confidence.get('confidence_label', 'N/A')})",
        )

    if risk_adjusted:
        pdf.metric_line(
            "Risk-Adjusted Return",
            fmt_pct(risk_adjusted.get("risk_adjusted_return"), 1),
        )
        pdf.metric_line(
            "Risk Haircut",
            fmt_pct(risk_adjusted.get("risk_haircut"), 1),
        )

    if security_signal:
        pdf.metric_line("Fundamental Signal", security_signal.get("signal", "N/A"))
        pdf.metric_line("Fundamental Signal Score", security_signal.get("score", "N/A"))

    if scoring_summary:
        pdf.metric_line(
            "Composite Risk Score",
            f"{safe_float(scoring_summary.get('composite_score')):.2f} / 5",
        )
        pdf.metric_line("Composite Rating", scoring_summary.get("rating", "N/A"))

    # =========================
    # MARKET INTELLIGENCE
    # =========================
    pdf.section_title("Market Intelligence")

    pdf.metric_line("Current Price", f"${safe_float(market_metrics.get('price')):.2f}")
    pdf.metric_line("30-Day Return", fmt_pct(market_metrics.get("returns_30"), 2))
    pdf.metric_line("90-Day Return", fmt_pct(market_metrics.get("returns_90"), 2))
    pdf.metric_line("Momentum (14D)", fmt_pct(market_metrics.get("momentum_14"), 2))
    pdf.metric_line("Relative vs S&P", fmt_pct(market_metrics.get("relative_performance"), 2))
    pdf.metric_line("Annualized Volatility", fmt_pct(market_metrics.get("volatility"), 2))
    pdf.metric_line("Max Drawdown", fmt_pct(market_metrics.get("max_drawdown"), 2))
    pdf.metric_line("Risk Regime", market_metrics.get("risk_regime", "N/A"))
    pdf.metric_line("Trend Signal", market_metrics.get("trend_signal", "N/A"))

    # =========================
    # FINANCIAL QUALITY
    # =========================
    if financial_summary is not None:
        pdf.section_title("Financial Quality")

        pdf.metric_line("Revenue Growth", fmt_pct(financial_summary.get("revenue_growth"), 1))
        pdf.metric_line("Operating Margin", fmt_pct(financial_summary.get("operating_margin"), 1))
        pdf.metric_line("R&D Intensity", fmt_pct(financial_summary.get("rd_intensity"), 1))
        pdf.metric_line("Debt / OCF", fmt_ratio(financial_summary.get("debt_ocf"), 2))

        pdf.paragraph(
            "Financial quality summarizes margin strength, growth, reinvestment intensity, "
            "and debt coverage. Strong financial quality can partially offset product concentration "
            "and pipeline execution risk."
        )

    # =========================
    # BUSINESS SEGMENT EXPOSURE
    # =========================
    pdf.section_title("Business Segment Exposure")

    pdf.metric_line("Total Product Sales", fmt_money(segment_metrics.get("total_product_sales"), 0, "M"))
    pdf.metric_line("HIV Sales", fmt_money(segment_metrics.get("hiv_sales"), 0, "M"))
    pdf.metric_line("HIV Concentration", fmt_pct(segment_metrics.get("hiv_concentration"), 1))
    pdf.metric_line("Largest Segment", segment_metrics.get("largest_segment", "N/A"))
    pdf.metric_line("Top 3 Concentration", fmt_pct(segment_metrics.get("top_3_concentration"), 1))
    pdf.metric_line("Revenue Dependence", segment_metrics.get("revenue_dependence", "N/A"))
    pdf.metric_line("Growth Exposure", fmt_pct(segment_metrics.get("growth_exposure"), 1))
    pdf.metric_line("Declining Exposure", fmt_pct(segment_metrics.get("declining_exposure"), 1))

    if safe_float(segment_metrics.get("hiv_concentration")) >= 60:
        pdf.paragraph(
            "Product concentration remains a key structural risk. HIV sales represent a majority "
            "of product revenue, making franchise durability, pricing pressure, competitive "
            "positioning, and pipeline diversification key monitoring priorities."
        )

    # =========================
    # CAPITAL ALLOCATION
    # =========================
    if capital_metrics is not None:
        pdf.section_title("Capital Allocation")

        pdf.metric_line("Dividends", fmt_money(capital_metrics.get("dividends"), 0, "M"))
        pdf.metric_line("Buybacks", fmt_money(capital_metrics.get("buybacks"), 0, "M"))
        pdf.metric_line("FCF Returned", fmt_pct(capital_metrics.get("fcf_return_pct"), 0))
        pdf.metric_line(
            "Capital Allocation Score",
            f"{capital_metrics.get('capital_allocation_score', 0)} / 5",
        )
        pdf.metric_line("Allocation Signal", capital_metrics.get("allocation_label", "N/A"))

        pdf.paragraph(
            "Capital allocation can support downside protection through dividends and buybacks, "
            "but excessive capital return may reduce reinvestment flexibility."
        )

    # =========================
    # PIPELINE INTELLIGENCE
    # =========================
    if pipeline_metrics is not None:
        pdf.section_title("Pipeline Intelligence")

        pdf.metric_line("Clinical Stage Programs", pipeline_metrics.get("clinical_stage_programs", "N/A"))
        pdf.metric_line("Phase 1 Programs", pipeline_metrics.get("phase_1_programs", "N/A"))
        pdf.metric_line("Phase 2 Programs", pipeline_metrics.get("phase_2_programs", "N/A"))
        pdf.metric_line("Phase 3 Programs", pipeline_metrics.get("phase_3_programs", "N/A"))
        pdf.metric_line("Late-Stage Pipeline", fmt_pct(pipeline_metrics.get("late_stage_pct"), 1))
        pdf.metric_line("Pipeline Maturity", pipeline_metrics.get("pipeline_maturity", "N/A"))

        pdf.paragraph(
            "Pipeline execution is central to the security intelligence view because future "
            "diversification depends on successful expansion beyond the core HIV franchise."
        )

    # =========================
    # FX EXPOSURE
    # =========================
    if fx_metrics is not None:
        pdf.section_title("FX Exposure")

        pdf.metric_line("Foreign Currency Sales", fmt_pct(fx_metrics.get("foreign_currency_sales_pct"), 0))
        pdf.metric_line("EUR/USD 30-Day Return", fmt_pct(fx_metrics.get("eurusd_return_30"), 2))
        pdf.metric_line("EUR/USD 90-Day Return", fmt_pct(fx_metrics.get("eurusd_return_90"), 2))
        pdf.metric_line("FX Volatility", fmt_pct(fx_metrics.get("eurusd_volatility"), 2))
        pdf.metric_line("USD Trend", fx_metrics.get("usd_trend", "N/A"))
        pdf.metric_line("FX Risk Regime", fx_metrics.get("fx_risk_regime", "N/A"))
        pdf.metric_line("Estimated Revenue Impact", fmt_pct(fx_metrics.get("estimated_revenue_sensitivity"), 2))

    # =========================
    # NEWS / FILINGS RISK
    # =========================
    if news_risk is not None:
        pdf.section_title("News and Filings Risk")

        pdf.metric_line("News Risk Score", f"{safe_float(news_risk.get('news_risk_score')):.2f} / 5")
        pdf.metric_line("News Risk Label", news_risk.get("news_risk_label", "N/A"))
        pdf.paragraph(news_risk.get("news_risk_summary", ""))

    # =========================
    # UNIFIED INTELLIGENCE RISK
    # =========================
    if intelligence_risk is not None:
        pdf.section_title("Unified Intelligence Risk")

        pdf.metric_line(
            "Intelligence Risk Score",
            f"{safe_float(intelligence_risk.get('intelligence_risk_score')):.2f} / 5",
        )
        pdf.metric_line("Intelligence Risk Label", intelligence_risk.get("intelligence_risk_label", "N/A"))
        pdf.paragraph(intelligence_risk.get("intelligence_risk_summary", ""))

    # =========================
    # EXPECTED RETURN MODEL
    # =========================
    if expected_return_summary is not None:
        pdf.section_title("Risk-Adjusted Expected Return")

        if isinstance(expected_return_summary, dict):
            pdf.metric_line(
                "Expected Price Target",
                f"${safe_float(expected_return_summary.get('expected_price_target')):.2f}",
            )
            pdf.metric_line("Expected Return", fmt_pct(expected_return_summary.get("expected_return"), 1))
            pdf.metric_line(
                "Risk-Adjusted Return",
                fmt_pct(expected_return_summary.get("risk_adjusted_return"), 1),
            )
            pdf.metric_line("Signal", expected_return_summary.get("signal", "N/A"))

            if "confidence_score" in expected_return_summary:
                pdf.metric_line(
                    "Confidence",
                    f"{safe_float(expected_return_summary.get('confidence_score')):.0f}%",
                )

            pdf.paragraph(expected_return_summary.get("summary", ""))
        else:
            pdf.paragraph(expected_return_summary)

    # =========================
    # RISK INTELLIGENCE
    # =========================
    pdf.section_title("Risk Intelligence")

    if scoring_summary is not None:
        pdf.metric_line(
            "Composite Risk Score",
            f"{safe_float(scoring_summary.get('composite_score')):.2f} / 5",
        )
        pdf.metric_line("Composite Rating", scoring_summary.get("rating", "N/A"))
        pdf.paragraph(scoring_summary.get("summary", ""))
    else:
        pdf.metric_line(
            "Overall Risk Score",
            f"{safe_float(risk_summary.get('overall_score')):.2f} / 5",
        )
        pdf.metric_line("Risk Rating", risk_summary.get("risk_rating", "N/A"))
        pdf.paragraph(risk_summary.get("summary", ""))

    # =========================
    # ANALYST NOTE
    # =========================
    pdf.section_title("Analyst Note")

    pdf.paragraph(
        "Primary security intelligence focus should remain on product concentration, "
        "pipeline execution, market volatility, FX exposure, policy/regulatory risk, "
        "news and filings activity, and capital allocation discipline. These areas "
        "represent the clearest link between external risk signals and business impact."
    )

    pdf.section_title("Disclaimer")
    pdf.paragraph(
        "This report is for educational and informational purposes only. It is not "
        "investment advice, financial advice, or a recommendation to buy or sell securities. "
        "Model outputs are directional estimates and should not be treated as precise forecasts."
    )

    pdf.output(output_path)
    return output_path
