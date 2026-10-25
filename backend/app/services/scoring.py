WEIGHTS = {
    "completeness": 25,
    "uniqueness": 15,
    "validity": 35,
    "anomalies": 25,
}
REVIEW_WEIGHT = 0.25          # a "Needs review" row counts as 25% of an anomaly
MISSING_COLUMN_PENALTY = 0.10  # per rule that targets a column that doesn't exist


def _clamp(ratio: float) -> float:
    return max(0.0, min(1.0, ratio))


def _grade(score: float) -> str:
    for threshold, grade in ((90, "A"), (80, "B"), (70, "C"), (60, "D")):
        if score >= threshold:
            return grade
    return "F"


def compute_quality_score(
    profile: dict,
    violations: list,
    anomalies: dict | None,
    rules_configured: bool,
) -> dict:
    rows = profile["total_rows"]
    cells = rows * profile["total_columns"]
    components = []
    skipped = []

    def add(key: str, label: str, ratio: float, detail: str):
        components.append({
            "key": key,
            "label": label,
            "weight": WEIGHTS[key],
            "score": round(_clamp(ratio) * 100, 1),
            "detail": detail,
        })

    # 1. Completeness
    missing = profile["missing_values"]
    add(
        "completeness", "Completeness",
        1 - missing / cells if cells else 1,
        f"{missing} empty cell(s) out of {cells}",
    )

    # 2. Uniqueness
    duplicates = profile["duplicate_rows"]
    add(
        "uniqueness", "Uniqueness",
        1 - duplicates / rows,
        f"{duplicates} duplicate row(s)",
    )

    # 3. Validity (only when the user configured rules)
    if rules_configured:
        bad_rows = set()
        structural = 0
        for violation in violations:
            if violation.row_positions:
                bad_rows.update(violation.row_positions)
            else:
                structural += 1  # rule points to a column that doesn't exist

        ratio = 1 - len(bad_rows) / rows - structural * MISSING_COLUMN_PENALTY
        detail = f"{len(bad_rows)} row(s) violate at least one rule"
        if structural:
            detail += f"; {structural} rule(s) target a missing column"
        add("validity", "Validity", ratio, detail)
    else:
        skipped.append("Validity: no quality rules configured")

    # 4. Anomalies (statistical signals only, rule violators already counted)
    if anomalies is not None:
        statistical = [
            row for row in anomalies["results"]
            if "data_quality_rule" not in row["detection_methods"]
        ]
        anomaly_rows = sum(r["status"] == "Anomaly" for r in statistical)
        review_rows = sum(r["status"] == "Needs review" for r in statistical)
        penalty = (anomaly_rows + REVIEW_WEIGHT * review_rows) / rows
        add(
            "anomalies", "Anomalies", 1 - penalty,
            f"{anomaly_rows} anomaly row(s), {review_rows} row(s) to review",
        )
    else:
        skipped.append("Anomalies: detection could not run on this dataset")

    total_weight = sum(c["weight"] for c in components)
    score = sum(c["weight"] * c["score"] for c in components) / total_weight

    return {
        "score": round(score, 1),
        "grade": _grade(score),
        "components": components,
        "skipped": skipped,
    }
