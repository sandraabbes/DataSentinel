
import pandas as pd


def profile_dataset(df: pd.DataFrame) -> dict:
    """
    Analyze a DataFrame and return basic data-quality statistics.
    """

    column_profiles = []

    for column in df.columns:
        series = df[column]
        missing = int(series.isna().sum())

        column_info = {
            "name": str(column),
            "data_type": str(series.dtype),
            "missing_values": missing,
            "missing_percentage": round(
                missing / len(df) * 100, 2
            ) if len(df) > 0 else 0.0,
            "unique_values": int(series.nunique()),
        }

        # Add descriptive statistics for numeric columns.
        if pd.api.types.is_numeric_dtype(series):
            numeric = series.dropna()

            if not numeric.empty:
                column_info["statistics"] = {
                    "min": float(numeric.min()),
                    "max": float(numeric.max()),
                    "mean": round(float(numeric.mean()), 2),
                    "median": float(numeric.median()),
                }

        column_profiles.append(column_info)

    return {
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "missing_values": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": column_profiles,
    }
