def get_base_revenue_mix(segment_metrics):
    """
    Build the current revenue mix used as the baseline for the forward mix projection.
    """

    if segment_metrics is None:
        return {
            "HIV": 0,
            "Oncology / Other": 0,
        }

    total = segment_metrics.get("total_product_sales", 0)
    hiv_sales = segment_metrics.get("hiv_sales", 0)

    if total <= 0:
        return {
            "HIV": 0,
            "Oncology / Other": 0,
        }

    hiv_mix = hiv_sales / total

    return {
        "HIV": hiv_mix,
        "Oncology / Other": 1 - hiv_mix,
    }


def project_future_mix(base_mix, pipeline_metrics=None, years_forward=3):
    """
    Project a directional future revenue mix.

    This is not intended to be a precise revenue forecast. It estimates whether
    the revenue mix may shift away from HIV based on pipeline maturity and a
    simple HIV decay assumption.
    """

    if base_mix is None:
        base_mix = {
            "HIV": 0,
            "Oncology / Other": 0,
        }

    hiv_weight = base_mix.get("HIV", 0)
    other_weight = base_mix.get("Oncology / Other", 0)

    late_stage = 0
    if pipeline_metrics is not None:
        late_stage = pipeline_metrics.get("late_stage_pct", 0)

    oncology_boost = (late_stage / 100) * 0.15
    hiv_decay = 0.02 * years_forward

    hiv_future = max(0.5, hiv_weight - hiv_decay)
    other_future = min(0.5, other_weight + oncology_boost)

    total = hiv_future + other_future

    if total <= 0:
        return {
            "HIV": 0,
            "Oncology / Other": 0,
        }

    return {
        "HIV": hiv_future / total,
        "Oncology / Other": other_future / total,
    }


def calculate_revenue_shift(base_mix, future_mix):
    """
    Calculate percentage-point shift between current and projected revenue mix.
    """

    shift = {}

    if base_mix is None:
        base_mix = {}

    if future_mix is None:
        future_mix = {}

    for key in base_mix:
        shift[key] = (future_mix.get(key, 0) - base_mix.get(key, 0)) * 100

    return shift


def get_forecast_summary(base_mix, future_mix, shift):
    """
    Generate a concise summary of the forward revenue mix projection.
    """

    hiv_change = shift.get("HIV", 0) if shift is not None else 0

    if hiv_change < -5:
        narrative = "meaningful diversification away from HIV"
    elif hiv_change < -2:
        narrative = "moderate diversification away from HIV"
    else:
        narrative = "limited diversification"

    return (
        f"Forward revenue mix suggests {narrative}, "
        f"with HIV changing by approximately {hiv_change:.1f} percentage points "
        "over the projection period."
    )
