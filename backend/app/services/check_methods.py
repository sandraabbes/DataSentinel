
import pandas as pd

from app.services.anomaly_detector import detect_anomalies

path = "../data/raw/datasentinel_labeled_test_dataset.csv"
df = pd.read_csv(path)

labels = df["is_anomaly"].astype(int)
features = df.drop(
    columns=["is_anomaly", "customer_id"],
    errors="ignore",
)

report = detect_anomalies(features, contamination=0.05)

for i, result in enumerate(report["results"]):
    if labels.iloc[i] == 1 or result["is_anomaly"]:
        print(
            f"Row {i + 1} | "
            f"Actual: {labels.iloc[i]} | "
            f"Predicted: {result['is_anomaly']} | "
            f"IF: {result['isolation_forest_anomaly']} | "
            f"IQR: {result['iqr_anomaly']} | "
            f"Score: {result['anomaly_score']}"
        )
