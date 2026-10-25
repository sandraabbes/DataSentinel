import pandas as pd

from app.services.rules import evaluate_rules

MAX_ROW_NUMBERS = 100  # keep responses small; useful for "jump to rows" later


def validate_dataset(df: pd.DataFrame, rules: dict) -> dict:
    """Validate a DataFrame using user-defined rules."""
    issues = [
        {
            "column": v.column,
            "rule": v.rule,
            "message": v.message,
            "affected_rows": v.affected_rows,
            "row_numbers": [p + 1 for p in v.row_positions[:MAX_ROW_NUMBERS]],
        }
        for v in evaluate_rules(df, rules)
    ]

    return {
        "valid": len(issues) == 0,
        "total_issues": len(issues),
        "issues": issues,
    }