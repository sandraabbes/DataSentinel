
import pandas as pd

from app.services.anomaly_detector import detect_anomalies

df = pd.read_csv("../data/raw/datasentinel_labeled_test_dataset.csv")

labels = df["is_anomaly"].astype(int)
features = df.drop(columns=["is_anomaly", "customer_id"], errors="ignore")

report = detect_anomalies(features, contamination=0.05)

for i, result in enumerate(report["results"]):
    actual = labels.iloc[i]
    predicted = int(result["is_anomaly"])

    if actual != predicted:
        print("\nPrediction error")
        print("Row:", i)
        print("Actual label:", actual)
        print("Predicted:", predicted)
        print("Values:", result.get("values", {}))
        print("Methods:", result.get("detection_methods", []))
        print("Reasons:", result.get("reasons", []))
