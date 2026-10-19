
from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_analyze_csv():
    csv_content = (
        b"name,age,salary\n"
        b"Ali,22,1200\n"
        b"Sara,25,1500\n"
        b"John,,1800\n"
        b"Sara,25,1500\n"
    )

    response = client.post(
        "/analyze",
        files={
            "file": (
                "sample.csv",
                BytesIO(csv_content),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    report = response.json()

    assert report["total_rows"] == 4
    assert report["total_columns"] == 3
    assert report["missing_values"] == 1
    assert report["duplicate_rows"] == 1


def test_analyze_rejects_non_csv():
    response = client.post(
        "/analyze",
        files={
            "file": (
                "document.txt",
                b"this is not a CSV file",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400



def test_validate_csv():
    csv_content = (
        b"name,age\n"
        b"Ali,22\n"
        b"Sara,-5\n"
    )

    response = client.post(
        "/validate",
        files={
            "file": (
                "sample.csv",
                BytesIO(csv_content),
                "text/csv",
            )
        },
        data={
            "rules": (
                '{"required_columns":["name","age"],'
                '"numeric_ranges":{"age":{"min":0,"max":120}}}'
            )
        },
    )

    assert response.status_code == 200

    result = response.json()
    assert result["valid"] is False
    assert result["total_issues"] == 1
    assert result["issues"][0]["column"] == "age"
    assert result["issues"][0]["affected_rows"] == 1


def test_validate_csv_with_no_issues():
    csv_content = (
        b"name,age\n"
        b"Ali,22\n"
        b"Sara,25\n"
    )

    response = client.post(
        "/validate",
        files={
            "file": (
                "sample.csv",
                BytesIO(csv_content),
                "text/csv",
            )
        },
        data={
            "rules": (
                '{"required_columns":["name","age"],'
                '"numeric_ranges":{"age":{"min":0,"max":120}}}'
            )
        },
    )

    assert response.status_code == 200

    result = response.json()
    assert result["valid"] is True
    assert result["total_issues"] == 0

def test_detect_anomalies_endpoint():
    csv_content = (
        b"age,salary\n"
        b"20,1000\n"
        b"21,1100\n"
        b"22,1200\n"
        b"23,1300\n"
        b"24,1400\n"
        b"25,1500\n"
        b"26,1600\n"
        b"27,1700\n"
        b"28,1800\n"
        b"29,1900\n"
        b"30,2000\n"
        b"200,100000\n"
    )

    response = client.post(
        "/detect-anomalies",
        files={
            "file": (
                "sample.csv",
                BytesIO(csv_content),
                "text/csv",
            )
        },
        data={"contamination": "0.05"},
    )

    assert response.status_code == 200

    result = response.json()

    assert result["total_rows"] == 12
    assert result["anomaly_count"] >= 1
    assert len(result["results"]) == 12
    assert "age" in result["numeric_columns_used"]


def test_detect_anomalies_rejects_invalid_contamination():
    csv_content = b"age,salary\n20,1000\n21,1100\n22,1200\n"

    response = client.post(
        "/detect-anomalies",
        files={
            "file": (
                "sample.csv",
                BytesIO(csv_content),
                "text/csv",
            )
        },
        data={"contamination": "0.8"},
    )

    assert response.status_code == 400
