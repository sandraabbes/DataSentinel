from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.services.profiler import profile_dataset
from app.services.validator import validate_dataset
from app.services.anomaly_detector import detect_anomalies
from app.utils.csv_loader import load_csv_upload, parse_rules


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
    df = await load_csv_upload(file)
    return profile_dataset(df)


@app.post("/validate")
async def validate_csv(file: UploadFile = File(...), rules: str = Form("{}")):
    validation_rules = parse_rules(rules)
    df = await load_csv_upload(file)
    return validate_dataset(df, validation_rules)


@app.post("/detect-anomalies")
async def detect_csv_anomalies(
    file: UploadFile = File(...),
    contamination: float = Form(0.05),
    rules: str = Form("{}"),
):
    if not 0 < contamination < 0.5:
        raise HTTPException(
            400, "Contamination must be greater than 0 and less than 0.5."
        )

    quality_rules = parse_rules(rules)
    df = await load_csv_upload(file)

    try:
        return detect_anomalies(df, contamination=contamination, rules=quality_rules)
    except ValueError as error:
        raise HTTPException(400, str(error))
