
import pandas as pd


def validate_dataset(df: pd.DataFrame, rules: dict) -> dict:
    """
    Validate a DataFrame using user-defined rules.

    Supported rules:
    - required_columns
    - numeric_ranges
    - allowed_values
    - unique_columns
    """

    issues = []

    # Rule 1: Check that required columns exist.
    required_columns = rules.get("required_columns", [])

    for column in required_columns:
        if column not in df.columns:
            issues.append({
                "column": column,
                "rule": "required_column",
                "message": f"Required column '{column}' is missing.",
                "affected_rows": 0,
            })
        else:
            missing_count = int(df[column].isna().sum())

            if missing_count > 0:
                issues.append({
                    "column": column,
                    "rule": "required_value",
                    "message": (
                        f"Column '{column}' contains "
                        f"{missing_count} missing value(s)."
                    ),
                    "affected_rows": missing_count,
                })

    # Rule 2: Check numerical minimum and maximum values.
    numeric_ranges = rules.get("numeric_ranges", {})

    for column, limits in numeric_ranges.items():
        if column not in df.columns:
            issues.append({
                "column": column,
                "rule": "numeric_range",
                "message": (
                    f"Cannot check the range: "
                    f"column '{column}' is missing."
                ),
                "affected_rows": 0,
            })
            continue

        values = pd.to_numeric(df[column], errors="coerce")

        invalid = values.isna() & df[column].notna()

        if "min" in limits:
            invalid |= values.notna() & (values < limits["min"])

        if "max" in limits:
            invalid |= values.notna() & (values > limits["max"])

        invalid_count = int(invalid.sum())

        if invalid_count > 0:
            issues.append({
                "column": column,
                "rule": "numeric_range",
                "message": (
                    f"Column '{column}' has {invalid_count} "
                    f"value(s) outside the allowed numeric range."
                ),
                "affected_rows": invalid_count,
            })

    # Rule 3: Check values against an approved list.
    allowed_values = rules.get("allowed_values", {})

    for column, allowed in allowed_values.items():
        if column not in df.columns:
            issues.append({
                "column": column,
                "rule": "allowed_values",
                "message": (
                    f"Cannot check allowed values: "
                    f"column '{column}' is missing."
                ),
                "affected_rows": 0,
            })
            continue

        invalid = (
            df[column].notna()
            & ~df[column].isin(allowed)
        )

        invalid_count = int(invalid.sum())

        if invalid_count > 0:
            issues.append({
                "column": column,
                "rule": "allowed_values",
                "message": (
                    f"Column '{column}' contains {invalid_count} "
                    f"value(s) outside the approved list."
                ),
                "affected_rows": invalid_count,
            })

    # Rule 4: Check that selected columns contain unique values.
    unique_columns = rules.get("unique_columns", [])

    for column in unique_columns:
        if column not in df.columns:
            issues.append({
                "column": column,
                "rule": "unique_column",
                "message": (
                    f"Cannot check uniqueness: "
                    f"column '{column}' is missing."
                ),
                "affected_rows": 0,
            })
            continue

        duplicate_mask = (
            df[column].notna()
            & df[column].duplicated(keep="first")
        )

        duplicate_count = int(duplicate_mask.sum())

        if duplicate_count > 0:
            issues.append({
                "column": column,
                "rule": "unique_column",
                "message": (
                    f"Column '{column}' contains "
                    f"{duplicate_count} duplicate value(s)."
                ),
                "affected_rows": duplicate_count,
            })

    return {
        "valid": len(issues) == 0,
        "total_issues": len(issues),
        "issues": issues,
    }
