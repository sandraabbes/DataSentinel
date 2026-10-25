import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.services.report import build_report

client = TestClient(app)


def clean_df():
    return pd.DataFrame({
        "name": [f"user{i}" for i in range(30)],
        "age": [20 + i % 10 for i in range(30)],
    })


def dirty_df():
    df = clean_df()
    df.loc[0, "age"] = None
    df.loc[1, "age"] = 500
    return pd.concat([df, df.iloc[[2]]], ignore_index=True)  # duplicate row


RULES = {
    "required_columns": ["name", "age"],
    "numeric_ranges": {"age": {"min": 0, "max": 120}},
}


def test_clean_data_scores_high_and_dirty_data_scores_lower():
    clean = build_report(clean_df(), RULES, 0.05)["quality_score"]
    dirty = build_report(dirty_df(), RULES, 0.05)["quality_score"]

    assert clean["score"] > 95
    assert dirty["score"] < clean["score"]
    assert 0 <= dirty["score"] <= 100


def test_validity_is_skipped_without_rules():
    score = build_report(clean_df(), {}, 0.05)["quality_score"]
    keys = [c["key"] for c in score["components"]]

    assert "validity" not in keys
    assert any("Validity" in note for note in score["skipped"])


def test_tiny_dataset_still_returns_a_score():
    df = pd.DataFrame({"a": [1, 2]})
    report = build_report(df, {}, 0.05)

    assert report["anomalies"] is None
    assert report["anomaly_error"]
    assert report["quality_score"]["score"] > 0


def test_histogram_covers_all_rows_even_in_report():
    df = clean_df()
    df.loc[0, "age"] = 5000
    report = build_report(df, {}, 0.05)

    hist = report["anomalies"]["score_histogram"]
    assert sum(hist["normal"]) + sum(hist["flagged"]) == len(df)
    assert len(hist["bin_edges"]) == len(hist["normal"]) + 1


def test_report_endpoint():

    csv = clean_df().to_csv(index=False)
    response = client.post(
        "/report",
        files={"file": ("data.csv", csv, "text/csv")},
        data={"rules": "{}", "contamination": "0.05"},
    )

    assert response.status_code == 200
    body = response.json()
    assert {"quality_score", "profile", "validation", "anomalies"} <= body.keys()
