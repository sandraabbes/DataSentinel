
import pandas as pd

from app.services.validator import validate_dataset


def test_valid_dataset():
    df = pd.DataFrame({
        "name": ["Ali", "Sara"],
        "age": [22, 25],
        "status": ["active", "inactive"],
    })

    rules = {
        "required_columns": ["name", "age"],
        "numeric_ranges": {
            "age": {"min": 0, "max": 120}
        },
        "allowed_values": {
            "status": ["active", "inactive"]
        },
    }

    result = validate_dataset(df, rules)

    assert result["valid"] is True
    assert result["total_issues"] == 0


def test_detects_missing_values():
    df = pd.DataFrame({
        "name": ["Ali", None],
    })

    result = validate_dataset(
        df,
        {"required_columns": ["name"]},
    )

    assert result["valid"] is False
    assert result["total_issues"] == 1
    assert result["issues"][0]["affected_rows"] == 1


def test_detects_out_of_range_values():
    df = pd.DataFrame({
        "age": [22, -5, 150],
    })

    result = validate_dataset(
        df,
        {"numeric_ranges": {
            "age": {"min": 0, "max": 120}
        }},
    )

    assert result["valid"] is False
    assert result["issues"][0]["affected_rows"] == 2


def test_detects_duplicate_values():
    df = pd.DataFrame({
        "customer_id": [101, 102, 101],
    })

    result = validate_dataset(
        df,
        {"unique_columns": ["customer_id"]},
    )

    assert result["valid"] is False
    assert result["issues"][0]["affected_rows"] == 1


def test_detects_missing_required_column():
    df = pd.DataFrame({
        "name": ["Ali"],
    })

    result = validate_dataset(
        df,
        {"required_columns": ["age"]},
    )

    assert result["valid"] is False
    assert result["issues"][0]["rule"] == "required_column"
