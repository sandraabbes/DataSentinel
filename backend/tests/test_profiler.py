
import pandas as pd

from app.services.profiler import profile_dataset


def test_basic_profile():
    df = pd.DataFrame({
        "name": ["Ali", "Sara", "John", "Sara"],
        "age": [22, 25, None, 25],
        "salary": [1200, 1500, 1800, 1500],
    })

    report = profile_dataset(df)

    assert report["total_rows"] == 4
    assert report["total_columns"] == 3
    assert report["missing_values"] == 1
    assert report["duplicate_rows"] == 1


def test_missing_values_per_column():
    df = pd.DataFrame({
        "age": [20, None, 30, None],
    })

    report = profile_dataset(df)

    age = report["columns"][0]

    assert age["missing_values"] == 2
    assert age["missing_percentage"] == 50.0


def test_numeric_statistics():
    df = pd.DataFrame({
        "score": [10, 20, 30],
    })

    report = profile_dataset(df)
    stats = report["columns"][0]["statistics"]

    assert stats["min"] == 10.0
    assert stats["max"] == 30.0
    assert stats["mean"] == 20.0
    assert stats["median"] == 20.0


def test_empty_dataframe():
    df = pd.DataFrame(columns=["name", "age"])

    report = profile_dataset(df)

    assert report["total_rows"] == 0
    assert report["total_columns"] == 2
    assert report["missing_values"] == 0
    assert report["duplicate_rows"] == 0
