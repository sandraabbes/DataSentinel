import pandas as pd

from app.services.rules import evaluate_rules
from app.services.validator import validate_dataset
from app.services.anomaly_detector import detect_anomalies


def make_df():
    return pd.DataFrame({
        "id": [1, 2, 2, 4],
        "age": [25, 200, None, 30],
        "grade": [1, 2, 3, 9],
        "city": ["Tunis", "Sfax", "Sfax", None],
    })


def test_all_rule_types_report_row_positions():
    rules = {
        "required_columns": ["age"],
        "numeric_ranges": {"age": {"min": 0, "max": 120}},
        "allowed_values": {"grade": ["1", "2", "3"]},
        "unique_columns": ["id"],
    }
    by_rule = {v.rule: v for v in evaluate_rules(make_df(), rules)}

    assert by_rule["required_value"].row_positions == [2]
    assert by_rule["numeric_range"].row_positions == [1]
    assert by_rule["allowed_values"].row_positions == [3]  # numeric vs string fix
    assert by_rule["unique_column"].row_positions == [2]


def test_missing_column_is_reported_not_skipped():
    violations = evaluate_rules(make_df(), {"required_columns": ["email"]})
    assert violations[0].rule == "required_column"
    assert violations[0].affected_rows == 0


def test_validator_and_detector_agree():
    rules = {"numeric_ranges": {"age": {"min": 0, "max": 120}}}
    df = make_df()

    issue = validate_dataset(df, rules)["issues"][0]
    report = detect_anomalies(df, rules=rules)
    flagged = [r for r in report["results"] if "data_quality_rule" in r["detection_methods"]]

    assert issue["affected_rows"] == len(flagged) == 1


def test_detector_warns_about_missing_rule_column():
    report = detect_anomalies(make_df(), rules={"required_columns": ["email"]})
    assert report["rule_warnings"]