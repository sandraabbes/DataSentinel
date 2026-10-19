
from io import StringIO
import json
from app.services.validator import validate_dataset
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

from app.services.profiler import profile_dataset


app = FastAPI(
    title="DataSentinel API",
    description="An API for data quality monitoring and anomaly detection.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "Welcome to DataSentinel!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "DataSentinel",
    }


@app.post("/analyze")
async def analyze_csv(file: UploadFile = File(...)):
    # 1. Check that the uploaded file is a CSV.
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file.",
        )

    # 2. Read the uploaded file and convert it into a DataFrame.
    try:
        contents = await file.read()
        csv_text = contents.decode("utf-8-sig")
        df = pd.read_csv(StringIO(csv_text), sep=None, engine="python")

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="The CSV file must use UTF-8 encoding.",
        )

    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=400,
            detail="The uploaded CSV file is empty.",
        )

    except pd.errors.ParserError:
        raise HTTPException(
            status_code=400,
            detail="The CSV file could not be parsed.",
        )

    # 3. Run the profiler.
    report = profile_dataset(df)

    # 4. Return the report to the user.
    return report


@app.post("/validate")
async def validate_csv(
    file: UploadFile = File(...),
    rules: str = Form("{}"),
):
    # Check the supplied rules.
    try:
        validation_rules = json.loads(rules)

        if not isinstance(validation_rules, dict):
            raise ValueError("Rules must be a JSON object.")

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid validation rules. Please provide a JSON object.",
        )

    # Check the uploaded file.
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file.",
        )

    try:
        contents = await file.read()
        csv_text = contents.decode("utf-8-sig")

        df = pd.read_csv(
            StringIO(csv_text),
            sep=None,
            engine="python",
        )

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="The CSV file must use UTF-8 encoding.",
        )

    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=400,
            detail="The uploaded CSV file is empty.",
        )

    except pd.errors.ParserError:
        raise HTTPException(
            status_code=400,
            detail="The CSV file could not be parsed.",
        )

    # Run the validation service.
    return validate_dataset(df, validation_rules)

