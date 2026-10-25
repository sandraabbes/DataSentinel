![CI](https://github.com/sandraabbes/DataSentinel/actions/workflows/ci.yml/badge.svg)

# DataSentinel

**DataSentinel** is an automated data quality monitoring and tabular anomaly detection platform. It combines automated dataset profiling, declarative rule-based data validation, and multi-method anomaly detection (machine learning + statistical + categorical heuristics) with explainable reasoning and an interactive visual dashboard.

---

## Features

- **Automated Data Profiling**: Computes column types, missingness, memory footprint, and summary distributions (mean, std, quartiles, min/max).
- **Rule-Based Validation**: Validates datasets against customizable constraints (required fields, value ranges, allowed categories, regex patterns).
- **Multi-Method Anomaly Detection**:
  - **Isolation Forest**: Unsupervised multivariate anomaly detection for numerical columns.
  - **IQR (Interquartile Range)**: Statistical univariate outlier detection.
  - **Categorical Anomaly Detection**: Identifies spelling variants (casing/whitespace), likely typos (Levenshtein similarity to high-frequency values), and rare categories in low-cardinality text columns.
  - **Explainability**: Every flagged record includes human-readable reasons in the **Why flagged** breakdown.
- **Interactive Visualizations**:
  - Missing values bar chart.
  - Anomaly score distribution histogram split by normal vs. flagged records.
- **Data Exporting**:
  - Flagged rows CSV.
  - Validation issues CSV.
  - Complete assessment report JSON.

---

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Pandas, Scikit-Learn, NumPy, Uvicorn, Pytest, Ruff.
- **Frontend**: React 19, Vite, Vanilla CSS, SVG Charts.
- **DevOps & CI/CD**: Docker (multi-stage builds), Docker Compose, GitHub Actions.

---

## Project Structure

```
DataSentinel/
├── .github/workflows/ci.yml    # GitHub Actions workflow (test, lint, build)
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI entrypoint & routes
│   │   ├── services/
│   │   │   ├── profiler.py     # Data profiling engine
│   │   │   ├── validator.py    # Constraint validation
│   │   │   ├── anomaly_detector.py # Isolation Forest, IQR, score histogram
│   │   │   ├── categorical.py  # Categorical typo & rare value detection
│   │   │   └── report.py       # Consolidated report builder
│   │   └── utils/              # CSV and rule loaders
│   ├── tests/                  # Pytest test suite (35+ unit & integration tests)
│   ├── Dockerfile              # Production Python 3.12-slim image
│   ├── pytest.ini              # Pytest configuration
│   ├── requirements.txt        # Pinned runtime dependencies
│   └── requirements-dev.txt    # Testing & linting dependencies
├── frontend/
│   ├── src/
│   │   ├── components/         # SVG charts (MissingValuesChart, ScoreHistogram)
│   │   ├── utils/              # CSV/JSON exporters
│   │   ├── App.jsx             # Main dashboard UI
│   │   └── App.css             # Component styling
│   └── Dockerfile              # Multi-stage build (Node -> Nginx)
├── docker-compose.yml          # Container orchestration
└── README.md
```

---

## Quick Start (Docker Compose)

The easiest way to run the full application (frontend + backend) is with Docker Compose:

```bash
docker compose up --build
```

- **Web Dashboard**: [http://localhost:8080](http://localhost:8080)
- **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## Local Development Setup

### 1. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # On Linux/macOS
# or: .venv\Scripts\activate   # On Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Run linter
ruff check .

# Run test suite
pytest

# Start backend server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm ci

# Run linter
npm run lint

# Start development server
npm run dev
```

The frontend dev server runs at [http://localhost:5173](http://localhost:5173).

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service status welcome message |
| `GET` | `/health` | Healthcheck endpoint |
| `POST` | `/analyze` | Upload CSV and generate profiling summary |
| `POST` | `/validate` | Upload CSV with validation rules and retrieve issues |
| `POST` | `/detect-anomalies` | Detect multivariate and categorical anomalies |
| `POST` | `/report` | Unified execution of profiling, validation, and anomaly detection |

---

## Continuous Integration

The repository uses GitHub Actions (`.github/workflows/ci.yml`) to automatically validate every push and pull request to `main`:

1. **Backend job**: Sets up Python 3.12, checks formatting and linting with `ruff check .`, and runs the unit test suite with `pytest`.
2. **Frontend job**: Sets up Node 20, runs `oxlint` linting, and validates production compilation with `npm run build`.
3. **Docker job**: Verifies that both container images build successfully using `docker compose build`.
