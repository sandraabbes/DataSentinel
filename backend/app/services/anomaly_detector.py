
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.services.categorical import detect_categorical_issues
from app.services.rules import evaluate_rules


def build_score_histogram(results: list[dict], bins: int = 20) -> dict | None:
    """Histogram of anomaly scores, split into normal and flagged rows."""
    scored = [
        (r["anomaly_score"], r["status"])
        for r in results
        if r["anomaly_score"] is not None
    ]
    if not scored:
        return None

    scores = np.array([score for score, _ in scored])
    low, high = float(scores.min()), float(scores.max())
    if high <= low:
        high = low + 1e-6

    normal = [0] * bins
    flagged = [0] * bins
    for score, status in scored:
        index = min(int((score - low) / (high - low) * bins), bins - 1)
        (normal if status == "Normal" else flagged)[index] += 1

    edges = np.linspace(low, high, bins + 1)
    return {
        "bin_edges": [round(float(e), 4) for e in edges],
        "normal": normal,
        "flagged": flagged,
    }


def detect_anomalies(
    df: pd.DataFrame,
    contamination: float = 0.05,
    rules: dict | None = None,
) -> dict:
    """Detect potentially anomalous rows in general tabular datasets."""

    if not 0 < contamination < 0.5:
        raise ValueError(
            "Contamination must be greater than 0 and less than 0.5."
        )

    if len(df) < 3:
        raise ValueError("At least 3 rows are required.")

    if df.shape[1] == 0:
        raise ValueError("The dataset must contain at least one column.")

    row_count = len(df)
    rules = rules or {}
    results = []

    for position in range(row_count):
        values = {}

        for column, value in df.iloc[position].items():
            if pd.isna(value):
                values[str(column)] = None
            elif isinstance(value, np.generic):
                values[str(column)] = value.item()
            else:
                values[str(column)] = value

        results.append({
            "row_number": position + 1,
            "is_anomaly": False,
            "status": "Normal",
            "anomaly_score": None,
            "isolation_forest_anomaly": False,
            "iqr_anomaly": False,
            "categorical_anomaly": False,
            "modified_z_score_anomaly": False,
            "detection_methods": [],
            "reasons": [],
            "values": values,
        })

    # Identify numeric columns, including numeric values stored as text.
    numeric_df = pd.DataFrame(index=range(row_count))

    for column in df.columns:
        original = df[column]

        if pd.api.types.is_bool_dtype(original):
            continue

        converted = pd.to_numeric(original, errors="coerce")
        non_missing = original.notna().sum()

        if non_missing == 0:
            continue

        if (
            pd.api.types.is_numeric_dtype(original)
            or converted.notna().sum() / non_missing >= 0.80
        ):
            numeric_df[str(column)] = converted.reset_index(drop=True)

    numeric_df = numeric_df.replace([np.inf, -np.inf], np.nan)

    usable_columns = [
        column
        for column in numeric_df.columns
        if numeric_df[column].nunique(dropna=True) > 1
    ]

    features = numeric_df[usable_columns].copy()

    # Method 1: Isolation Forest.
    if features.shape[1] > 0:
        model = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "detector",
                IsolationForest(
                    n_estimators=200,
                    contamination=contamination,
                    random_state=42,
                ),
            ),
        ])

        predictions = model.fit_predict(features)
        scores = model.decision_function(features)

        for position, prediction in enumerate(predictions):
            result = results[position]
            result["anomaly_score"] = round(
                float(scores[position]), 6
            )

            if prediction == -1:
                result["isolation_forest_anomaly"] = True
                result["detection_methods"].append("isolation_forest")
                result["reasons"].append(
                    "Isolation Forest identified an unusual "
                    "combination of numerical features."
                )

    # Method 2: robust modified Z-score using median absolute deviation.
    # This detects extreme individual values without relying on IQR fences.
    for column in features.columns:
        series = features[column]
        valid = series.dropna()

        if len(valid) < 5:
            continue

        median = valid.median()
        mad = (valid - median).abs().median()

        if not np.isfinite(mad) or mad <= 0:
            continue

        modified_scores = 0.6745 * (series - median).abs() / mad

        for position, score in enumerate(modified_scores):
            if pd.isna(score) or score <= 3.5:
                continue

            result = results[position]
            result["modified_z_score_anomaly"] = True

            if "modified_z_score" not in result["detection_methods"]:
                result["detection_methods"].append("modified_z_score")

            result["reasons"].append(
                f"Column '{column}' has a robust modified Z-score "
                f"of {score:.2f}, above the threshold of 3.5."
            )

    # Method 3: IQR is retained as an explanatory signal.
    # It does not independently determine the final classification.
    for column in features.columns:
        series = features[column]
        valid = series.dropna()

        if len(valid) < 4:
            continue

        q1 = valid.quantile(0.25)
        q3 = valid.quantile(0.75)
        iqr = q3 - q1

        if not np.isfinite(iqr) or iqr <= 0:
            continue

        lower = q1 - 3.0 * iqr
        upper = q3 + 3.0 * iqr

        for position, value in enumerate(series):
            if pd.isna(value) or lower <= value <= upper:
                continue

            result = results[position]
            result["iqr_anomaly"] = True
            result["reasons"].append(
                f"Column '{column}' has an IQR outlier ({value:g}); "
                f"bounds are {lower:.4g} to {upper:.4g}."
            )

    # Method 4: categorical signals (rare values, typos, spelling variants).
    categorical_findings, categorical_columns = detect_categorical_issues(
        df, exclude=set(numeric_df.columns)
    )
    categorical_strength = {}

    for position, findings in categorical_findings.items():
        result = results[position]
        result["categorical_anomaly"] = True
        categorical_strength[position] = sum(f.strength for f in findings)

        for finding in findings:
            if finding.method not in result["detection_methods"]:
                result["detection_methods"].append(finding.method)
            result["reasons"].append(finding.message)

    # Final classification: one signal warrants review; agreement between
    # independent signals is strong enough to classify as an anomaly.
    # IQR remains explanatory evidence and contributes to that agreement.
    rule_violations = {}
    rule_warnings = []

    for violation in evaluate_rules(df, rules):
        if not violation.row_positions:
            rule_warnings.append(violation.message)  # e.g. a missing column
            continue

        for position in violation.row_positions:
            rule_violations.setdefault(position, []).append(
                f"Rule '{violation.rule}' failed for column "
                f"'{violation.column}': {violation.row_detail}."
            )

    for position, messages in rule_violations.items():
        result = results[position]
        result["status"] = "Anomaly"
        result["is_anomaly"] = True
        result["detection_methods"].append("data_quality_rule")
        result["reasons"].extend(messages)

    for position, result in enumerate(results):
        evidence_count = sum([
            result["isolation_forest_anomaly"],
            result["modified_z_score_anomaly"],
            result["iqr_anomaly"],
        ]) + categorical_strength.get(position, 0)

        if result["status"] == "Anomaly":
            continue
        result["is_anomaly"] = evidence_count >= 2
        if evidence_count >= 2:
            result["status"] = "Anomaly"
        elif evidence_count == 1:
            result["status"] = "Needs review"

    anomaly_count = sum(r["is_anomaly"] for r in results)
    review_count = sum(r["status"] == "Needs review" for r in results)
    normal_count = sum(r["status"] == "Normal" for r in results)

    return {
        "total_rows": int(row_count),
        "numeric_columns_used": [str(c) for c in features.columns],
        "categorical_columns_used": categorical_columns,
        "anomaly_count": int(anomaly_count),
        "review_count": int(review_count),
        "normal_count": int(normal_count),
        "anomaly_percentage": round(
            anomaly_count / row_count * 100, 2
        ),
        "contamination": contamination,
        "quality_rules": rules,
        "rule_warnings": rule_warnings,
        "score_histogram": build_score_histogram(results),
        "results": results,
    }
