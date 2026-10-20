
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def detect_anomalies(
    df: pd.DataFrame,
    contamination: float = 0.05,
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

    # Initialize a result for every row.
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
            "anomaly_score": None,
            "isolation_forest_anomaly": False,
            "iqr_anomaly": False,
            "categorical_anomaly": False,
            "detection_methods": [],
            "reasons": [],
            "values": values,
        })

    # Identify numerical columns, including columns stored as text
    # when at least 80% of their non-missing values are numeric.
    numeric_df = pd.DataFrame(index=df.index)

    for column in df.columns:
        original = df[column]

        if pd.api.types.is_bool_dtype(original):
            continue

        converted = pd.to_numeric(original, errors="coerce")
        non_missing = original.notna().sum()

        if non_missing == 0:
            continue

        if pd.api.types.is_numeric_dtype(original):
            numeric_df[column] = converted
        elif converted.notna().sum() / non_missing >= 0.80:
            numeric_df[column] = converted

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

    # Method 2: IQR outlier detection for each numerical feature.
    for column in features.columns:
        series = features[column].dropna()

        if len(series) < 4:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        if not np.isfinite(iqr) or iqr <= 0:
            continue

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        for position, value in enumerate(features[column]):
            if pd.isna(value):
                continue

            if value < lower or value > upper:
                result = results[position]
                result["iqr_anomaly"] = True

                if "iqr" not in result["detection_methods"]:
                    result["detection_methods"].append("iqr")

                result["reasons"].append(
                    f"Column '{column}' has an extreme value "
                    f"({value:g}); IQR bounds are "
                    f"{lower:.4g} to {upper:.4g}."
                )

    # Method 3: rare-category detection for categorical columns.
    for column in df.columns:
        if column in numeric_df.columns:
            continue

        series = df[column]
        non_missing = series.dropna()

        if len(non_missing) < 3:
            continue

        counts = non_missing.astype(str).value_counts()
        unique_count = len(counts)

        # Avoid flagging near-unique text or identifier columns.
        if unique_count < 2 or unique_count > row_count * 0.5:
            continue

        # Flag categories occurring once in this dataset.
        for position, value in enumerate(series):
            if pd.isna(value):
                continue

            if counts.get(str(value), 0) == 1:
                result = results[position]
                result["categorical_anomaly"] = True

                if "rare_category" not in result["detection_methods"]:
                    result["detection_methods"].append("rare_category")

                result["reasons"].append(
                    f"Column '{column}' contains a category "
                    "that appears only once."
                )

    # Combine detections. A row is flagged if any method flags it.
    for result in results:
        result["is_anomaly"] = bool(
            result["isolation_forest_anomaly"]
            or result["iqr_anomaly"]
            or result["categorical_anomaly"]
        )

    anomaly_count = sum(r["is_anomaly"] for r in results)

    return {
        "total_rows": int(row_count),
        "numeric_columns_used": [str(c) for c in features.columns],
        "anomaly_count": int(anomaly_count),
        "normal_count": int(row_count - anomaly_count),
        "anomaly_percentage": round(
            anomaly_count / row_count * 100, 2
        ),
        "contamination": contamination,
        "results": results,
    }
