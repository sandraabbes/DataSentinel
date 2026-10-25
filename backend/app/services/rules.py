from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class RuleViolation:
    column: str
    rule: str
    message: str  # column-level text, used by the validator
    row_detail: str  # short text, used per row by the anomaly detector
    row_positions: list[int] = field(default_factory=list)  # 0-based

    @property
    def affected_rows(self) -> int:
        return len(self.row_positions)


def _positions(mask: pd.Series) -> list[int]:
    return np.flatnonzero(mask.to_numpy()).tolist()


def _normalize(value) -> str:
    """Make 1, 1.0 and '1' compare equal (the frontend sends strings)."""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def _missing_column(column: str, rule: str, action: str) -> RuleViolation:
    return RuleViolation(
        column=column,
        rule=rule,
        message=f"Cannot {action}: column '{column}' is missing.",
        row_detail="column is missing",
    )


def check_required(df: pd.DataFrame, columns: list[str]) -> list[RuleViolation]:
    violations = []
    for column in columns:
        if column not in df.columns:
            violations.append(RuleViolation(
                column=column,
                rule="required_column",
                message=f"Required column '{column}' is missing.",
                row_detail="column is missing",
            ))
            continue

        positions = _positions(df[column].isna())
        if positions:
            violations.append(RuleViolation(
                column=column,
                rule="required_value",
                message=f"Column '{column}' contains {len(positions)} missing value(s).",
                row_detail="a value is required",
                row_positions=positions,
            ))
    return violations


def check_numeric_ranges(df: pd.DataFrame, ranges: dict) -> list[RuleViolation]:
    violations = []
    for column, limits in ranges.items():
        if column not in df.columns:
            violations.append(_missing_column(column, "numeric_range", "check the range"))
            continue

        values = pd.to_numeric(df[column], errors="coerce")
        invalid = values.isna() & df[column].notna()  # non-numeric text

        if "min" in limits:
            invalid |= values.notna() & (values < limits["min"])
        if "max" in limits:
            invalid |= values.notna() & (values > limits["max"])

        positions = _positions(invalid)
        if positions:
            violations.append(RuleViolation(
                column=column,
                rule="numeric_range",
                message=(
                    f"Column '{column}' has {len(positions)} value(s) "
                    f"outside the allowed numeric range."
                ),
                row_detail="value is outside the configured range",
                row_positions=positions,
            ))
    return violations


def check_allowed_values(df: pd.DataFrame, allowed_map: dict) -> list[RuleViolation]:
    violations = []
    for column, allowed in allowed_map.items():
        if column not in df.columns:
            violations.append(_missing_column(column, "allowed_values", "check allowed values"))
            continue

        approved = {_normalize(item) for item in allowed}
        series = df[column]
        invalid = series.notna() & ~series.map(_normalize).isin(approved)

        positions = _positions(invalid)
        if positions:
            violations.append(RuleViolation(
                column=column,
                rule="allowed_values",
                message=(
                    f"Column '{column}' contains {len(positions)} "
                    f"value(s) outside the approved list."
                ),
                row_detail="value is not in the approved list",
                row_positions=positions,
            ))
    return violations


def check_unique(df: pd.DataFrame, columns: list[str]) -> list[RuleViolation]:
    violations = []
    for column in columns:
        if column not in df.columns:
            violations.append(_missing_column(column, "unique_column", "check uniqueness"))
            continue

        positions = _positions(df[column].notna() & df[column].duplicated(keep="first"))
        if positions:
            violations.append(RuleViolation(
                column=column,
                rule="unique_column",
                message=f"Column '{column}' contains {len(positions)} duplicate value(s).",
                row_detail="value must be unique",
                row_positions=positions,
            ))
    return violations


def evaluate_rules(df: pd.DataFrame, rules: dict) -> list[RuleViolation]:
    """Single source of truth for all data quality rules."""
    return (
        check_required(df, rules.get("required_columns", []))
        + check_numeric_ranges(df, rules.get("numeric_ranges", {}))
        + check_allowed_values(df, rules.get("allowed_values", {}))
        + check_unique(df, rules.get("unique_columns", []))
    )