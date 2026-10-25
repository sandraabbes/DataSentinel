
import { useState } from "react";
import "./App.css";
import { MissingValuesChart, ScoreHistogram } from "./components/Charts";
import {
  exportFlaggedRows,
  exportReportJson,
  exportValidationIssues,
} from "./utils/exporters";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";


async function postToApi(path, fields) {
  const formData = new FormData();
  Object.entries(fields).forEach(([key, value]) => formData.append(key, value));

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, { method: "POST", body: formData });
  } catch {
    throw new Error("Could not connect to DataSentinel. Is the backend running?");
  }

  let data = {};
  try {
    data = await response.json();
  } catch {
    /* non-JSON error body */
  }

  if (!response.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((item) => item.msg).join("; ")
      : data.detail;
    throw new Error(detail || "Request failed.");
  }
  return data;
}

async function runTask(setBusy, setErr, task) {
  setBusy(true);
  setErr("");
  try {
    await task();
  } catch (err) {
    setErr(err.message);
  } finally {
    setBusy(false);
  }
}

function App() {
  const [file, setFile] = useState(null);
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  const [validation, setValidation] = useState(null);
  const [anomalyReport, setAnomalyReport] = useState(null);
  const [detecting, setDetecting] = useState(false);
  const [anomalyError, setAnomalyError] = useState("");
  const [qualityScore, setQualityScore] = useState(null);
  const [runningAll, setRunningAll] = useState(false);
  const [contamination, setContamination] = useState("0.05");

  function handleDetectAnomalies() {
    if (!file) return setAnomalyError("Please select a CSV file first.");
    setAnomalyReport(null);
    return runTask(setDetecting, setAnomalyError, async () =>
      setAnomalyReport(
        await postToApi("/detect-anomalies", { file, contamination, rules: "{}" })
      )
    );
  }

  function handleRunAll() {
    if (!file) return setError("Please select a CSV file first.");
    setReport(null);
    setValidation(null);
    setAnomalyReport(null);
    setQualityScore(null);
    setAnomalyError("");
    return runTask(setRunningAll, setError, async () => {
      const data = await postToApi("/report", {
        file,
        contamination,
        rules: "{}",
      });
      setQualityScore(data.quality_score);
      setReport(data.profile);
      setValidation(data.validation);
      setAnomalyReport(data.anomalies);
      if (data.anomaly_error) setAnomalyError(data.anomaly_error);
    });
  }


  function handleFileChange(event) {
    const selectedFile = event.target.files[0];

    setFile(selectedFile || null);
    setReport(null);
    setValidation(null);
    setAnomalyReport(null);
    setQualityScore(null);
    setError("");

    if (selectedFile && !selectedFile.name.toLowerCase().endsWith(".csv")) {
      setError("Please choose a file with a .csv extension.");
      setFile(null);
      event.target.value = "";
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">D</div>
          <div>
            <h2>DataSentinel</h2>
            <span>DATA QUALITY PLATFORM</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <div className="nav-item active">
          <span>▦</span> Overview
        </div>
        <div className="nav-item">
          <span>⇧</span> Dataset analysis
        </div>

        <div className="sidebar-bottom">
          <div className="status-dot" />
          <div>
            <strong>Local environment</strong>
            <span>DataSentinel API</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <span className="breadcrumb">Workspace / Overview</span>
          <span className="connection-status">
            <span className="status-dot" /> Local development
          </span>
        </header>

        <section className="page-heading">
          <div>
            <p className="eyebrow">DATA INTELLIGENCE</p>
            <h1>Data quality overview</h1>
            <p className="subtitle">
              Upload a dataset to uncover missing values, duplicates, and
              useful statistics.
            </p>
          </div>
          <div className="date-chip">CSV ANALYZER</div>
        </section>

        <section className="upload-card">
          <div className="section-heading">
            <div>
              <h2>Analyze a dataset</h2>
              <p>Start by uploading a CSV file from your computer.</p>
            </div>
            <span className="upload-symbol">↑</span>
          </div>

          <div>
            <label className="drop-zone">
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={handleFileChange}
              />
              <span className="upload-icon">⇧</span>
              <strong>
                {file ? file.name : "Choose a CSV file"}
              </strong>
              <span>
                {file
                  ? `${(file.size / 1024).toFixed(1)} KB · Ready to analyze`
                  : "Click here to browse your files"}
              </span>
              <span className="file-hint">CSV files only</span>
            </label>

            <div className="upload-actions">
              <span className="helper-text">Your file is analyzed by your local backend.</span>
              <div className="button-group">
                <button
                  type="button"
                  className="analyze-button"
                  onClick={handleRunAll}
                  disabled={!file || runningAll}
                >
                  {runningAll ? "Running..." : "Run everything"}
                </button>
              </div>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}
        </section>

        {qualityScore && <ScoreCard result={qualityScore} />}

        <section className="results-section">
          <div className="section-heading results-heading">
            <div>
              <h2>Quality summary</h2>
              <p>
                {report
                  ? "Analysis results for your uploaded dataset."
                  : "Your dataset metrics will appear here after analysis."}
              </p>
            </div>
            {report && (
              <div className="heading-actions">
                <span className="success-badge">Analysis complete</span>
                <button
                  type="button"
                  className="export-button"
                  onClick={() =>
                    exportReportJson({
                      fileName: file?.name,
                      qualityScore,
                      report,
                      validation,
                      anomalyReport,
                    })
                  }
                >
                  Download report (JSON)
                </button>
              </div>
            )}
          </div>

          <div className="metrics-grid">

            <MetricCard
              label="Total rows"
              value={report ? report.total_rows : "—"}
              icon="▤"
              description="Records in dataset"
            />
            <MetricCard
              label="Total columns"
              value={report ? report.total_columns : "—"}
              icon="▥"
              description="Features detected"
            />
            <MetricCard
              label="Missing values"
              value={report ? report.missing_values : "—"}
              icon="!"
              description="Empty cells found"
              warning={report && report.missing_values > 0}
            />
            <MetricCard
              label="Duplicate rows"
              value={report ? report.duplicate_rows : "—"}
              icon="⧉"
              description="Repeated records"
              warning={report && report.duplicate_rows > 0}
            />
          </div>

          {report && (
            <>
              <h3 className="anomaly-subheading">Missing values by column</h3>
              <MissingValuesChart columns={report.columns} />
            </>
          )}
        </section>

        <section className="table-card">
          <div className="section-heading">
            <div>
              <h2>Column-level analysis</h2>
              <p>Inspect the quality and statistics of each feature.</p>
            </div>
            {report && (
              <span className="count-badge">
                {report.columns.length} columns
              </span>
            )}
          </div>

          {report ? (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Column</th>
                    <th>Data type</th>
                    <th>Missing</th>
                    <th>Missing %</th>
                    <th>Unique values</th>
                    <th>Min</th>
                    <th>Max</th>
                    <th>Mean</th>
                  </tr>
                </thead>
                <tbody>
                  {report.columns.map((column) => (
                    <tr key={column.name}>
                      <td className="column-name">{column.name}</td>
                      <td>
                        <span className="type-badge">
                          {column.data_type}
                        </span>
                      </td>
                      <td>{column.missing_values}</td>
                      <td>
                        <span
                          className={
                            column.missing_percentage > 0
                              ? "missing-value"
                              : ""
                          }
                        >
                          {column.missing_percentage}%
                        </span>
                      </td>
                      <td>{column.unique_values}</td>
                      <td>{formatNumber(column.statistics?.min)}</td>
                      <td>{formatNumber(column.statistics?.max)}</td>
                      <td>{formatNumber(column.statistics?.mean)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">▤</div>
              <strong>No dataset analyzed yet</strong>
              <p>Upload a CSV file above to see your column-level report.</p>
            </div>
          )}
        </section>
          
        <section className="table-card validation-card">
          <div className="section-heading">
            <div>
              <h2>Data validation</h2>
              <p>Check your dataset against the configured quality rules.</p>
            </div>

            {validation && (
              <div className="heading-actions">
                <span className={validation.valid ? "validation-pass" : "validation-fail"}>
                  {validation.valid ? "All checks passed" : "Issues detected"}
                </span>
                {!validation.valid && (
                  <button
                    type="button"
                    className="export-button"
                    onClick={() => exportValidationIssues(validation, file?.name)}
                  >
                    Export issues (CSV)
                  </button>
                )}
              </div>
            )}
          </div>

          {!validation ? (
            <div className="empty-state">
              <strong>No validation results yet</strong>
              <p>Upload a CSV and click Run everything to check it.</p>
            </div>
          ) : validation.total_issues === 0 ? (
            <div className="validation-success">
              Your dataset passed all configured validation rules.
            </div>
          ) : (
            <>
              <p className="validation-count">
                {validation.total_issues} validation issue(s) found.
              </p>

              <div className="issues-list">
                {validation.issues.map((issue, index) => (
                  <article
                    className="issue-item"
                    key={`${issue.column}-${issue.rule}-${index}`}
                  >
                    <div>
                      <strong>{issue.column}</strong>
                      <p>{issue.message}</p>
                    </div>

                    <span className="issue-count">
                      {issue.affected_rows} affected
                    </span>
                  </article>
                ))}
              </div>
            </>
          )}
        </section>
        
        <section className="table-card anomaly-card">
          <div className="section-heading">
            <div>
              <h2>AI Anomaly Detection</h2>
              <p>
                Use machine learning to identify unusual data patterns.
              </p>
            </div>
          </div>

          <div className="anomaly-controls">
            <label htmlFor="contamination">
              Expected anomaly proportion
            </label>

            <select
              id="contamination"
              value={contamination}
              onChange={(event) =>
                setContamination(event.target.value)
              }
            >
              <option value="0.01">1%</option>
              <option value="0.05">5%</option>
              <option value="0.10">10%</option>
              <option value="0.20">20%</option>
            </select>



            <button
              type="button"
              className="analyze-button"
              onClick={handleDetectAnomalies}
              disabled={!file || detecting}
            >
              {detecting
                ? "Detecting..."
                : "Detect anomalies"}
            </button>
          </div>

          {anomalyError && (
            <div className="error-message">{anomalyError}</div>
          )}

          {!anomalyReport ? (
            <div className="empty-state">
              <strong>No anomaly report yet</strong>
              <p>
                Select a CSV file and run AI anomaly detection.
              </p>
            </div>
          ) : (
            <>
              <div className="metrics-grid anomaly-metrics">
                <div className="metric-card">
                  <span>Total rows</span>
                  <strong>{anomalyReport.total_rows}</strong>
                </div>

                <div className="metric-card">
                  <span>Normal rows</span>
                  <strong>{anomalyReport.normal_count}</strong>
                </div>

                <div className="metric-card">
                  <span>Needs review</span>
                  <strong>{anomalyReport.review_count}</strong>
                </div>

                <div className="metric-card">
                  <span>Anomalies found</span>
                  <strong>{anomalyReport.anomaly_count}</strong>
                </div>

                <div className="metric-card">
                  <span>Anomaly percentage</span>
                  <strong>
                    {anomalyReport.anomaly_percentage}%
                  </strong>
                </div>
              </div>

              {anomalyReport.score_histogram && (
                <>
                  <h3 className="anomaly-subheading">Anomaly score distribution</h3>
                  <ScoreHistogram histogram={anomalyReport.score_histogram} />
                </>
              )}

              <div className="heading-actions between">
                <h3 className="anomaly-subheading">Detected rows</h3>
                {anomalyReport.anomaly_count + anomalyReport.review_count > 0 && (
                  <button
                    type="button"
                    className="export-button"
                    onClick={() => exportFlaggedRows(anomalyReport, file?.name)}
                  >
                    Export flagged rows (CSV)
                  </button>
                )}
              </div>

              {anomalyReport.anomaly_count === 0 ? (
                <div className="validation-success">
                  {anomalyReport.review_count === 0
                    ? "No anomaly signals were detected by the model."
                    : "No definite anomalies were detected. Some records need review."}
                </div>
              ) : (
                <div className="table-wrapper">
                  <table>
                    <thead>
                      <tr>
                        <th>Row</th>
                        <th>Values</th>
                        <th>Anomaly score</th>
                        <th>Status</th>
                        <th>Why flagged</th>
                      </tr>
                    </thead>

                    <tbody>
                      {anomalyReport.results
                        .filter((row) => row.status !== "Normal")
                        .map((row) => (
                          <tr key={row.row_number}>
                            <td>{row.row_number}</td>

                            <td>
                              {Object.entries(row.values)
                                .map(([key, value]) =>
                                  `${key}: ${value ?? "—"}`
                                )
                                .join(" | ")}
                            </td>

                            <td>{row.anomaly_score}</td>

                            <td>
                              <span className={row.status === "Anomaly" ? "validation-fail" : "review-badge"}>
                                {row.status}
                              </span>
                            </td>

                            <td className="reasons-cell">
                              {row.reasons.slice(0, 3).map((reason, i) => (
                                <div key={i}>{reason}</div>
                              ))}
                              {row.reasons.length > 3 && (
                                <small>+{row.reasons.length - 3} more (see CSV export)</small>
                              )}
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              )}

              <p className="anomaly-note">
                Flags show unusual patterns (numeric outliers, rare categories,
                possible typos), not necessarily incorrect data. Review flagged
                rows before taking action.
              </p>
            </>
          )}
        </section>

        <footer className="footer">
          <span>DataSentinel · Data quality monitoring</span>
          <span>Built with React + FastAPI</span>
        </footer>
      </main>
    </div>
  );
}

function ScoreCard({ result }) {
  return (
    <section className="table-card score-card">
      <div className="section-heading">
        <div>
          <h2>Data quality score</h2>
          <p>Weighted from completeness, uniqueness, validity and anomalies.</p>
        </div>
        <span className="score-badge">
          {result.score}/100 · Grade {result.grade}
        </span>
      </div>

      <div className="score-components">
        {result.components.map((part) => (
          <div className="score-row" key={part.key}>
            <div className="score-row-top">
              <strong>{part.label}</strong>
              <span>{part.score}%</span>
            </div>
            <div className="score-bar">
              <div className="score-bar-fill" style={{ width: `${part.score}%` }} />
            </div>
            <small>{part.detail}</small>
          </div>
        ))}
      </div>

      {result.skipped.length > 0 && (
        <p className="anomaly-note">Not included: {result.skipped.join(" · ")}</p>
      )}
    </section>
  );
}

function MetricCard({ label, value, icon, description, warning }) {
  return (
    <article className="metric-card">
      <div className="metric-top">
        <span>{label}</span>
        <span className={`metric-icon ${warning ? "warning-icon" : ""}`}>
          {icon}
        </span>
      </div>
      <div className="metric-value">{value}</div>
      <div className="metric-description">{description}</div>
    </article>
  );
}

function formatNumber(value) {
  if (value === undefined || value === null) {
    return "—";
  }

  return Number(value).toLocaleString(undefined, {
    maximumFractionDigits: 2,
  });
}

export default App;
