
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from app.services.anomaly_detector import detect_anomalies


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python evaluate_detector.py "
            "path/to/labeled_dataset.csv"
        )
        return

    csv_path = Path(sys.argv[1])

    if not csv_path.exists():
        print(f"File not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)

    if "is_anomaly" not in df.columns:
        print(
            "The CSV must contain an 'is_anomaly' column "
            "with 1 for anomalies and 0 for normal rows."
        )
        return

    labels = df["is_anomaly"]

    if labels.isna().any() or not set(labels.unique()).issubset({0, 1}):
        print("'is_anomaly' must contain only 0 and 1.")
        return

    # Never give the known labels to the detector.
    features = df.drop(columns=["is_anomaly"])

    report = detect_anomalies(
        features,
        contamination=0.05,
    )

    actual = labels.astype(int).to_numpy()
    predicted = [
        int(row["is_anomaly"])
        for row in report["results"]
    ]

    print("\n--- DataSentinel Evaluation ---")
    print(f"Rows evaluated: {len(actual)}")
    print(f"Known anomalies: {sum(actual)}")
    print(f"Flagged anomalies: {sum(predicted)}")
    print(f"Accuracy:  {accuracy_score(actual, predicted):.3f}")
    print(f"Precision: {precision_score(actual, predicted, zero_division=0):.3f}")
    print(f"Recall:    {recall_score(actual, predicted, zero_division=0):.3f}")
    print(f"F1-score:  {f1_score(actual, predicted, zero_division=0):.3f}")

    print("\nConfusion matrix:")
    print("Rows = actual; columns = predicted")
    print(confusion_matrix(actual, predicted, labels=[0, 1]))

    print("\nDetailed report:")
    print(
        classification_report(
            actual,
            predicted,
            labels=[0, 1],
            target_names=["Normal", "Anomaly"],
            zero_division=0,
        )
    )


if __name__ == "__main__":
    main()
