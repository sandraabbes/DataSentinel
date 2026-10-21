
import pandas as pd

from app.services.anomaly_detector import detect_anomalies


def test_detect_anomalies_returns_expected_structure():
    df = pd.DataFrame({
        "age": [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 200],
        "salary": [
            1000, 1100, 1200, 1300, 1400, 1500,
            1600, 1700, 1800, 1900, 2000, 100000,
        ],
    })

    result = detect_anomalies(df)

    assert result["total_rows"] == 12
    assert result["anomaly_count"] >= 1
    assert (
        result["normal_count"]
        + result["review_count"]
        + result["anomaly_count"]
        == 12
    )
    assert {row["status"] for row in result["results"]} <= {
        "Normal", "Needs review", "Anomaly"
    }
    assert len(result["results"]) == 12


def test_detect_anomalies_handles_missing_values():
    df = pd.DataFrame({
        "age": [20, 21, 22, None, 24, 25],
        "salary": [1000, 1100, 1200, 1300, None, 1500],
    })

    result = detect_anomalies(df)

    assert result["total_rows"] == 6
    assert len(result["results"]) == 6



def test_detect_anomalies_handles_categorical_data():
    df = pd.DataFrame({
        "department": [
            "IT", "IT", "Sales", "IT", "Sales", "HR"
        ],
    })

    result = detect_anomalies(df)

    assert result["total_rows"] == 6
    assert len(result["results"]) == 6
    assert "anomaly_count" in result

def test_detect_anomalies_rejects_invalid_contamination():
    df = pd.DataFrame({
        "age": [20, 21, 22, 23],
    })

    try:
        detect_anomalies(df, contamination=0.8)
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "Contamination" in str(error)
