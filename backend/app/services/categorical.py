from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher

import pandas as pd

MIN_NON_MISSING = 20       # too few values: frequencies mean nothing
MAX_UNIQUE = 50            # more distinct values: probably free text / IDs
MAX_UNIQUE_RATIO = 0.5
RARE_SHARE = 0.01          # "rare" = at most 1% of the column's values
MAX_RARE_ROW_SHARE = 0.05  # if rare values exceed 5% of rows, rarity is normal
TYPO_SIMILARITY = 0.80     # difflib ratio
DOMINANCE = 5              # a typo target must be 5x more common than the typo


@dataclass
class CategoricalFinding:
    column: str
    method: str     # category_variant | category_typo | rare_category
    strength: int   # evidence points: 2 = strong, 1 = weak
    message: str


def _key(value: str) -> str:
    return " ".join(value.split()).casefold()


def _is_candidate(series: pd.Series) -> bool:
    if (
        pd.api.types.is_bool_dtype(series)
        or pd.api.types.is_numeric_dtype(series)
        or pd.api.types.is_datetime64_any_dtype(series)
    ):
        return False

    non_missing = series.dropna()
    total = len(non_missing)
    if total < MIN_NON_MISSING:
        return False

    unique = non_missing.nunique()
    return 2 <= unique <= MAX_UNIQUE and unique / total <= MAX_UNIQUE_RATIO


def _closest_frequent(value: str, frequent: list, count: int) -> str | None:
    needle = value.casefold()
    best, best_ratio = None, 0.0
    for candidate, candidate_count in frequent:
        if candidate_count < DOMINANCE * count:
            continue
        ratio = SequenceMatcher(None, needle, candidate.casefold()).ratio()
        if ratio >= TYPO_SIMILARITY and ratio > best_ratio:
            best, best_ratio = candidate, ratio
    return best


def _analyze_column(column: str, series: pd.Series) -> list[tuple[int, CategoricalFinding]]:
    text = series.reset_index(drop=True).map(lambda v: None if pd.isna(v) else str(v))
    counts = text.value_counts()
    total = int(counts.sum())
    positions = {value: idx.tolist() for value, idx in text.groupby(text).indices.items()}

    found: list[tuple[int, CategoricalFinding]] = []

    def flag(value: str, method: str, strength: int, message: str):
        for position in positions[value]:
            found.append((position, CategoricalFinding(column, method, strength, message)))

    # 1. Spelling variants: "tunis" / "TUNIS " next to "Tunis".
    groups = defaultdict(list)
    for value, count in counts.items():
        groups[_key(value)].append((value, int(count)))

    variants = set()
    for members in groups.values():
        if len(members) < 2:
            continue
        members.sort(key=lambda m: -m[1])
        main = members[0][0]
        for value, _ in members[1:]:
            variants.add(value)
            flag(
                value, "category_variant", 2,
                f"Value '{value}' in column '{column}' looks like a "
                f"spelling variant of '{main}'.",
            )

    # 2 and 3. Typos and rare categories.
    rare_cutoff = max(1, int(total * RARE_SHARE))
    rare = [v for v, c in counts.items() if c <= rare_cutoff and v not in variants]
    frequent = [(v, int(c)) for v, c in counts.items() if c > rare_cutoff and v not in variants]

    rare_rows = sum(int(counts[v]) for v in rare)
    rarity_is_meaningful = rare_rows / total <= MAX_RARE_ROW_SHARE

    for value in rare:
        count = int(counts[value])
        target = _closest_frequent(value, frequent, count)
        if target is not None:
            flag(
                value, "category_typo", 2,
                f"Value '{value}' in column '{column}' appears {count}x and "
                f"is very similar to '{target}' - possible typo.",
            )
        elif rarity_is_meaningful:
            flag(
                value, "rare_category", 1,
                f"Value '{value}' in column '{column}' is rare "
                f"({count} of {total} rows, {count / total:.1%}).",
            )

    return found


def detect_categorical_issues(
    df: pd.DataFrame, exclude: set[str]
) -> tuple[dict[int, list[CategoricalFinding]], list[str]]:
    """Return {row_position: [findings]} and the list of columns analyzed."""
    findings: dict[int, list[CategoricalFinding]] = defaultdict(list)
    columns_used: list[str] = []

    for column in df.columns:
        name = str(column)
        if name in exclude or not _is_candidate(df[column]):
            continue
        columns_used.append(name)
        for position, finding in _analyze_column(name, df[column]):
            findings[position].append(finding)

    return dict(findings), columns_used
