
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def detect_anomalies(
    df: pd.DataFrame,
    contamination: float = 0.05,
) -> dict:
    """
    Detect unusual rows using Isolation Forest.

    Only numerical columns are used by the model.
    Missing numerical values are imputed before training.
    """

    if not 0 < contamination < 0.5:
        raise ValueError(
            "Contamination must be greater than 0 and less than 0.5."
        )

    if len(df) < 3:
        raise ValueError(
            "At least 3 rows are required for anomaly detection."
        )

    numeric_df = df.select_dtypes(include="number")

    if numeric_df.shape[1] == 0:
        raise ValueError(
            "The dataset must contain at least one numerical column."
        )

    # Remove columns that have no usable values or no variation.
    usable_columns = [
        column
        for column in numeric_df.columns
        if numeric_df[column].notna().any()
        and numeric_df[column].nunique(dropna=True) > 1
    ]

    if not usable_columns:
        raise ValueError(
            "No numerical columns with enough variation were found."
        )

    features = numeric_df[usable_columns].copy()

    # Replace infinite values with missing values.
    features = features.replace([float("inf"), float("-inf")], float("nan"))

    # Remove columns that became entirely missing.
    features = features.dropna(axis=1, how="all")

    if features.shape[1] == 0:
        raise ValueError(
            "No usable numerical values were found."
        )

    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        (
            "detector",
            IsolationForest(
                n_estimators=100,
                contamination=contamination,
                random_state=42,
            ),
        ),
    ])

    predictions = model.fit_predict(features)
    scores = model.named_steps["detector"].decision_function(
        model[:-1].transform(features)
    )

    results = []

    for position, prediction in enumerate(predictions):
        results.append({
            "row_number": int(position + 1),
            "is_anomaly": bool(prediction == -1),
            "anomaly_score": round(float(scores[position]), 6),
            "values": {
                str(column): (
                    None if pd.isna(value) else (
                        value.item() if hasattr(value, "item") else value
                    )
                )
                for column, value in df.iloc[position].items()
            },
        })

    anomaly_count = sum(
        result["is_anomaly"] for result in results
    )

    return {
        "total_rows": int(len(df)),
        "numeric_columns_used": [
            str(column) for column in features.columns
        ],
        "anomaly_count": int(anomaly_count),
        "normal_count": int(len(df) - anomaly_count),
        "anomaly_percentage": round(
            anomaly_count / len(df) * 100, 2
        ),
        "contamination": contamination,
        "results": results,
    }
