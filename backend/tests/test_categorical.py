import pandas as pd

from app.services.anomaly_detector import detect_anomalies
from app.services.categorical import detect_categorical_issues


def make_df():
    cities = ["Tunis"] * 40 + ["Sfax"] * 30 + ["Sousse"] * 28 + ["Tunsi", "Gabes"]
    return pd.DataFrame({"city": cities, "age": range(100)})


def methods_by_row(findings):
    return {pos: {f.method for f in fs} for pos, fs in findings.items()}


def test_typo_and_rare_category_are_found():
    findings, columns = detect_categorical_issues(make_df(), exclude=set())
    methods = methods_by_row(findings)

    assert columns == ["city"]
    assert methods[98] == {"category_typo"}   # Tunsi
    assert methods[99] == {"rare_category"}   # Gabes


def test_spelling_variant_is_found():
    df = make_df()
    df.loc[0, "city"] = "tunis "
    methods = methods_by_row(detect_categorical_issues(df, exclude=set())[0])
    assert methods[0] == {"category_variant"}


def test_many_rare_values_are_not_flagged():
    df = pd.DataFrame({"city": ["A"] * 60 + [f"c{i}" for i in range(40)]})
    findings, _ = detect_categorical_issues(df, exclude=set())
    assert findings == {}


def test_id_like_and_numeric_columns_are_ignored():
    df = pd.DataFrame({"id": [f"id{i}" for i in range(50)], "n": range(50)})
    _, columns = detect_categorical_issues(df, exclude=set())
    assert columns == []


def test_detector_uses_categorical_evidence():
    report = detect_anomalies(make_df())
    typo_row = report["results"][98]
    rare_row = report["results"][99]

    assert typo_row["categorical_anomaly"] and typo_row["status"] == "Anomaly"
    assert rare_row["categorical_anomaly"] and rare_row["status"] != "Normal"
    assert report["categorical_columns_used"] == ["city"]
