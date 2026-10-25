import pandas as pd

from app.services.profiler import profile_dataset
from app.services.validator import validate_dataset
from app.services.anomaly_detector import detect_anomalies
from app.services.rules import evaluate_rules
from app.services.scoring import compute_quality_score

RULE_KEYS = ("required_columns", "numeric_ranges", "allowed_values", "unique_columns")


def build_report(df: pd.DataFrame, rules: dict, contamination: float) -> dict:
    if len(df) == 0:
        raise ValueError("The CSV has column headers but no data rows.")

    profile = profile_dataset(df)
    validation = validate_dataset(df, rules)
    violations = evaluate_rules(df, rules)

    anomalies = None
    anomaly_error = None
    try:
        anomalies = detect_anomalies(df, contamination=contamination, rules=rules)
    except ValueError as error:  # e.g. fewer than 3 rows
        anomaly_error = str(error)

    quality_score = compute_quality_score(
        profile,
        violations,
        anomalies,
        rules_configured=any(rules.get(key) for key in RULE_KEYS),
    )

    # Keep the payload small: the UI only lists non-normal rows anyway.
    if anomalies is not None:
        anomalies["results"] = [
            row for row in anomalies["results"] if row["status"] != "Normal"
        ]

    return {
        "quality_score": quality_score,
        "profile": profile,
        "validation": validation,
        "anomalies": anomalies,
        "anomaly_error": anomaly_error,
    }
