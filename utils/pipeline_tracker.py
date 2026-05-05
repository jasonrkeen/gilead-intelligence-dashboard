import pandas as pd


def get_pipeline_summary():
    """
    Return Gilead pipeline snapshot.

    Source baseline:
    - Gilead public pipeline page, updated February 12, 2026
    - Data as of end of Q4 2025
    """

    data = {
        "Metric": [
            "Clinical Stage Programs",
            "Opt-in Programs",
            "Phase 1 Programs",
            "Phase 2 Programs",
            "Phase 3 Programs",
        ],
        "Count": [
            53,
            5,
            25,
            13,
            15,
        ],
    }

    return pd.DataFrame(data)


def get_pipeline_focus_areas():
    """
    Return pipeline focus areas aligned with Gilead's strategy.
    """

    data = {
        "Therapeutic Area": [
            "Virology (HIV & Liver)",
            "Oncology",
            "Inflammation / Immunology",
        ],
        "Strategic Role": [
            "Core revenue engine; long-acting innovation and prevention-focused expansion",
            "Primary diversification driver beyond HIV",
            "Emerging growth area built through acquisitions and early-stage pipeline",
        ],
        "Pipeline Maturity": [
            "Advanced (multiple Phase 3 + commercial assets)",
            "Mixed (late-stage + early-stage)",
            "Early-stage weighted",
        ],
        "Intelligence Relevance": [
            "Critical to sustaining current revenue dominance",
            "Key determinant of long-term growth success",
            "Optional upside with higher execution uncertainty",
        ],
    }

    return pd.DataFrame(data)


def get_key_pipeline_watchlist():
    """
    Return key pipeline programs and events to monitor.
    """

    data = {
        "Asset / Area": [
            "BIC/LEN (Priority Review)",
            "Lenacapavir-based HIV programs",
            "GS-1720 / GS-4182 (Wonders-2)",
            "Bulevirtide",
            "Arcellx / anito-cel (Acquisition - Approved)",
            "Trodelvy",
            "Cell Therapy / Kite",
            "Oncology business development",
            "NASH (Novo Nordisk collaboration)",
        ],
        "Category": [
            "HIV",
            "HIV",
            "HIV",
            "Virology",
            "Oncology / Cell Therapy",
            "Oncology",
            "Oncology / Cell Therapy",
            "Oncology",
            "Liver Disease / Metabolic",
        ],
        "Why It Matters": [
            "FDA priority review with August 2026 decision; potential next-generation HIV regimen.",
            "Supports long-term HIV franchise protection and innovation.",
            "Trial termination highlights safety and regulatory risk in next-generation HIV pipeline.",
            "Upcoming launch contributes to liver disease diversification.",
            "Fully approved acquisition; central to oncology expansion and long-term diversification beyond HIV.",
            "Key oncology asset with execution-sensitive expansion.",
            "Supports diversification but carries manufacturing and adoption complexity.",
            "Central to long-term growth via acquisitions.",
            "Previously targeted multi-billion-dollar NASH market opportunity.",
        ],
        "Risk Signal": [
            "Near-term FDA decision; regulatory approval and launch risk",
            "Clinical safety and competitive positioning",
            "Clinical hold and safety risk",
            "Commercial uptake and regulatory execution risk",
            "Integration, regulatory milestone execution, and commercial adoption risk",
            "Clinical expansion risk",
            "Manufacturing and scale-up risk",
            "Integration and ROI uncertainty",
            "Program discontinued; highlights execution risk and strategic pivot",
        ],
        "Time Horizon": [
            "Near-term (Aug 2026)",
            "Medium-term",
            "Near-term (risk event)",
            "Near-term (2026-2027)",
            "Near-term integration + medium-term catalyst",
            "Medium-term",
            "Medium-term",
            "Ongoing",
            "Exited",
        ],
        "Impact Level": [
            "Very High",
            "High",
            "High",
            "Medium",
            "Very High",
            "Medium",
            "Medium",
            "High",
            "Medium",
        ],
        "Event Type": [
            "Catalyst",
            "Strategic",
            "Negative Event",
            "Catalyst",
            "Strategic / Catalyst",
            "Strategic",
            "Strategic",
            "Strategic",
            "Exited / Negative",
        ],
    }

    return pd.DataFrame(data)


def _get_metric_count(pipeline_df, metric_name):
    """
    Safely pull a count from the pipeline summary dataframe.
    """

    if pipeline_df is None or pipeline_df.empty:
        return 0

    if "Metric" not in pipeline_df.columns or "Count" not in pipeline_df.columns:
        return 0

    values = pipeline_df.loc[
        pipeline_df["Metric"] == metric_name,
        "Count",
    ]

    if values.empty:
        return 0

    return int(values.sum())


def calculate_pipeline_metrics(pipeline_df):
    """
    Calculate pipeline risk and maturity indicators.
    """

    clinical_stage = _get_metric_count(
        pipeline_df,
        "Clinical Stage Programs",
    )
    phase_1 = _get_metric_count(
        pipeline_df,
        "Phase 1 Programs",
    )
    phase_2 = _get_metric_count(
        pipeline_df,
        "Phase 2 Programs",
    )
    phase_3 = _get_metric_count(
        pipeline_df,
        "Phase 3 Programs",
    )
    opt_in = _get_metric_count(
        pipeline_df,
        "Opt-in Programs",
    )

    late_stage_pct = (phase_3 / clinical_stage) * 100 if clinical_stage else 0
    early_stage_pct = (phase_1 / clinical_stage) * 100 if clinical_stage else 0
    mid_late_stage_pct = (
        ((phase_2 + phase_3) / clinical_stage) * 100
        if clinical_stage else 0
    )

    if late_stage_pct >= 25:
        pipeline_maturity = "Moderate / Late-Stage Weighted"
    elif late_stage_pct >= 15:
        pipeline_maturity = "Balanced"
    else:
        pipeline_maturity = "Early-Stage Weighted"

    return {
        "clinical_stage_programs": clinical_stage,
        "opt_in_programs": opt_in,
        "phase_1_programs": phase_1,
        "phase_2_programs": phase_2,
        "phase_3_programs": phase_3,
        "late_stage_pct": late_stage_pct,
        "early_stage_pct": early_stage_pct,
        "mid_late_stage_pct": mid_late_stage_pct,
        "pipeline_maturity": pipeline_maturity,
    }


def get_pipeline_source_note():
    return (
        "Pipeline data is based on Gilead's public pipeline snapshot, updated "
        "February 12, 2026, with data as of end of Q4 2025."
    )
