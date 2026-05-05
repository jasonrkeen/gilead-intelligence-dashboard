import json
import os
from datetime import datetime


SNAPSHOT_PATH = "data/last_dashboard_snapshot.json"


def build_current_snapshot(
    metrics,
    summary=None,
    expected_return=None,
    signal=None,
    intelligence_risk=None,
    risk_adjusted=None,
):
    """
    Capture key dashboard outputs for change detection.
    """

    metrics = metrics or {}

    return {
        "timestamp": datetime.now().isoformat(),
        "price": metrics.get("price"),
        "returns_30": metrics.get("returns_30"),
        "returns_90": metrics.get("returns_90"),
        "volatility": metrics.get("volatility"),
        "max_drawdown": metrics.get("max_drawdown"),
        "trend_signal": metrics.get("trend_signal"),
        "risk_score": summary.get("composite_score") if summary else None,
        "risk_rating": summary.get("rating") if summary else None,
        "expected_return": expected_return,
        "signal": signal,
        "intelligence_risk_score": (
            intelligence_risk.get("intelligence_risk_score")
            if intelligence_risk else None
        ),
        "intelligence_risk_label": (
            intelligence_risk.get("intelligence_risk_label")
            if intelligence_risk else None
        ),
        "risk_haircut": (
            risk_adjusted.get("risk_haircut")
            if risk_adjusted else None
        ),
    }


def load_previous_snapshot():
    """
    Load the previous dashboard snapshot if it exists.

    Returns None if the file does not exist or cannot be read.
    """

    if not os.path.exists(SNAPSHOT_PATH):
        return None

    try:
        with open(SNAPSHOT_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return None


def save_current_snapshot(snapshot):
    """
    Save the current dashboard snapshot to disk.
    """

    os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)

    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as file:
        json.dump(snapshot, file, indent=4)


def calculate_change(current_value, previous_value):
    """
    Calculate numeric change between current and previous values.
    """

    if current_value is None or previous_value is None:
        return None

    try:
        return current_value - previous_value
    except TypeError:
        return None


def detect_dashboard_changes(current_snapshot, previous_snapshot):
    """
    Compare current dashboard snapshot against the last saved run.
    """

    current_snapshot = current_snapshot or {}

    if previous_snapshot is None:
        return {
            "has_previous": False,
            "summary": "No previous dashboard snapshot found. This run will create the baseline.",
            "changes": {},
            "signal_changed": False,
            "rating_changed": False,
            "trend_changed": False,
            "intelligence_risk_changed": False,
        }

    tracked_fields = [
        "price",
        "returns_30",
        "returns_90",
        "volatility",
        "max_drawdown",
        "risk_score",
        "expected_return",
        "intelligence_risk_score",
        "risk_haircut",
    ]

    changes = {}

    for field in tracked_fields:
        changes[field] = calculate_change(
            current_snapshot.get(field),
            previous_snapshot.get(field),
        )

    rating_changed = (
        current_snapshot.get("risk_rating")
        != previous_snapshot.get("risk_rating")
    )

    signal_changed = (
        current_snapshot.get("signal")
        != previous_snapshot.get("signal")
    )

    trend_changed = (
        current_snapshot.get("trend_signal")
        != previous_snapshot.get("trend_signal")
    )

    intelligence_risk_changed = (
        current_snapshot.get("intelligence_risk_label")
        != previous_snapshot.get("intelligence_risk_label")
    )

    summary_parts = []

    if signal_changed:
        summary_parts.append(
            f"Signal changed from {previous_snapshot.get('signal')} "
            f"to {current_snapshot.get('signal')}."
        )

    if rating_changed:
        summary_parts.append(
            f"Risk rating changed from {previous_snapshot.get('risk_rating')} "
            f"to {current_snapshot.get('risk_rating')}."
        )

    if trend_changed:
        summary_parts.append(
            f"Trend changed from {previous_snapshot.get('trend_signal')} "
            f"to {current_snapshot.get('trend_signal')}."
        )

    if intelligence_risk_changed:
        summary_parts.append(
            f"Intelligence risk changed from "
            f"{previous_snapshot.get('intelligence_risk_label')} to "
            f"{current_snapshot.get('intelligence_risk_label')}."
        )

    if (
        changes.get("expected_return") is not None
        and abs(changes["expected_return"]) >= 2
    ):
        summary_parts.append(
            f"Expected return moved by {changes['expected_return']:.1f} percentage points."
        )

    if (
        changes.get("risk_score") is not None
        and abs(changes["risk_score"]) >= 0.25
    ):
        summary_parts.append(
            f"Composite risk score moved by {changes['risk_score']:.2f}."
        )

    if (
        changes.get("intelligence_risk_score") is not None
        and abs(changes["intelligence_risk_score"]) >= 0.50
    ):
        summary_parts.append(
            f"Intelligence risk score moved by {changes['intelligence_risk_score']:.2f}."
        )

    if (
        changes.get("risk_haircut") is not None
        and abs(changes["risk_haircut"]) >= 2
    ):
        summary_parts.append(
            f"Risk haircut moved by {changes['risk_haircut']:.1f} percentage points."
        )

    if not summary_parts:
        summary_parts.append("No major dashboard signal changes detected.")

    return {
        "has_previous": True,
        "summary": " ".join(summary_parts),
        "changes": changes,
        "signal_changed": signal_changed,
        "rating_changed": rating_changed,
        "trend_changed": trend_changed,
        "intelligence_risk_changed": intelligence_risk_changed,
    }
