import csv
from io import StringIO

import pandas as pd
from fastapi import HTTPException, UploadFile

MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


async def load_csv_upload(file: UploadFile) -> pd.DataFrame:
    """Validate an uploaded CSV file and return it as a DataFrame."""

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Please upload a CSV file.")

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            413, f"File is too large. Maximum size is {MAX_FILE_SIZE_MB} MB."
        )

    if not contents.strip():
        raise HTTPException(400, "The uploaded CSV file is empty.")

    try:
        text = contents.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, "The CSV file must use UTF-8 encoding.")

    # Auto-detect the delimiter (comma, semicolon, tab, pipe).
    try:
        dialect = csv.Sniffer().sniff(text[:10_000], delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","

    try:
        df = pd.read_csv(StringIO(text), sep=delimiter)
    except pd.errors.EmptyDataError:
        raise HTTPException(400, "The uploaded CSV file is empty.")
    except pd.errors.ParserError:
        raise HTTPException(400, "The CSV file could not be parsed.")

    if df.shape[1] == 0:
        raise HTTPException(400, "The CSV file has no columns.")

    return df


def parse_rules(rules: str) -> dict:
    """Parse the JSON rules string sent by the frontend."""
    import json

    try:
        parsed = json.loads(rules)
    except json.JSONDecodeError:
        raise HTTPException(400, "Rules must be valid JSON.")

    if not isinstance(parsed, dict):
        raise HTTPException(400, "Rules must be a JSON object.")

    return parsed
