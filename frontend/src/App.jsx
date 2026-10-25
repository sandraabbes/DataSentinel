
import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";
const DEFAULT_QUALITY_RULES = {
  requiredColumns: "name, age",
  numericRanges: [
    { column: "age", min: "0", max: "120" },
    { column: "salary", min: "0", max: "" },
  ],
  allowedValues: [],
  uniqueColumns: "",
};

function loadQualityRules() {
  try {
    const saved = JSON.parse(localStorage.getItem("datasentinel-quality-rules"));
    return saved && typeof saved === "object"
      ? { ...DEFAULT_QUALITY_RULES, ...saved }
      : DEFAULT_QUALITY_RULES;
  } catch {
    return DEFAULT_QUALITY_RULES;
  }
}

function buildQualityRules(config) {
  const splitColumns = (value) => value.split(",").map((item) => item.trim()).filter(Boolean);
  const numericRanges = {};
  config.numericRanges.forEach(({ column, min, max }) => {
    const name = column.trim();
    if (!name) return;
    const limits = {};
    if (min !== "") limits.min = Number(min);
    if (max !== "") limits.max = Number(max);
    if (Object.keys(limits).length) numericRanges[name] = limits;
  });
  const allowedValues = {};
  config.allowedValues.forEach(({ column, values }) => {
    const name = column.trim();
    const choices = splitColumns(values);
    if (name && choices.length) allowedValues[name] = choices;
  });
  return {
    required_columns: splitColumns(config.requiredColumns),
    numeric_ranges: numericRanges,
    allowed_values: allowedValues,
    unique_columns: splitColumns(config.uniqueColumns),
  };
}

function App() {
  const [file, setFile] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [validation, setValidation] = useState(null);
  const [validating, setValidating] = useState(false);
  const [validationError, setValidationError] = useState("");
  const [anomalyReport, setAnomalyReport] = useState(null);
  const [detecting, setDetecting] = useState(false);
  const [anomalyError, setAnomalyError] = useState("");
  const [contamination, setContamination] = useState("0.05");
  const [qualityRuleConfig, setQualityRuleConfig] = useState(loadQualityRules);
  const qualityRules = JSON.stringify(buildQualityRules(qualityRuleConfig));

  useEffect(() => {
    localStorage.setItem("datasentinel-quality-rules", JSON.stringify(qualityRuleConfig));
  }, [qualityRuleConfig]);

  function updateQualityRuleConfig(key, value) {
    setQualityRuleConfig((current) => ({ ...current, [key]: value }));
  }

  function updateRuleRow(group, index, key, value) {
    setQualityRuleConfig((current) => ({
      ...current,
      [group]: current[group].map((rule, rowIndex) =>
        rowIndex === index ? { ...rule, [key]: value } : rule
      ),
    }));
  }

  function addRuleRow(group, rule) {
    setQualityRuleConfig((current) => ({
      ...current,
      [group]: [...current[group], rule],
    }));
  }

  function removeRuleRow(group, index) {
    setQualityRuleConfig((current) => ({
      ...current,
      [group]: current[group].filter((_, rowIndex) => rowIndex !== index),
    }));
  }

  function resetQualityRules() {
    setQualityRuleConfig(DEFAULT_QUALITY_RULES);
  }

  async function handleAnalyze(event) {
    event.preventDefault();

    if (!file) {
      setError("Please select a CSV file first.");
      return;
    }

    setLoading(true);
    setError("");
    setReport(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Analysis failed.");
      }

      setReport(data);
    } catch (err) {
      setError(
        err.message ||
          "Could not connect to DataSentinel. Is the backend running?"
      );
    } finally {
      setLoading(false);
    }
  }
  
  async function handleValidate() {
    if (!file) {
      setValidationError("Please select a CSV file first.");
      return;
    }

    setValidating(true);
    setValidationError("");
    setValidation(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("rules", qualityRules);

      const response = await fetch(`${API_URL}/validate`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Validation failed.");
      }

      setValidation(data);
    } catch (err) {
      setValidationError(
        err.message || "Could not connect to DataSentinel."
      );
    } finally {
      setValidating(false);
    }
  }
  
  async function handleDetectAnomalies() {
    if (!file) {
      setAnomalyError("Please select a CSV file first.");
      return;
    }

    setDetecting(true);
    setAnomalyError("");
    setAnomalyReport(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("contamination", contamination);
      formData.append("rules", qualityRules);

      const response = await fetch(
        `${API_URL}/detect-anomalies`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Anomaly detection failed."
        );
      }

      setAnomalyReport(data);
    } catch (err) {
      setAnomalyError(
        err.message || "Could not connect to DataSentinel."
      );
    } finally {
      setDetecting(false);
    }
  }


  function handleFileChange(event) {
    const selectedFile = event.target.files[0];

    setFile(selectedFile || null);
    setReport(null);
    setValidation(null);
    setAnomalyReport(null);
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

          <form onSubmit={handleAnalyze}>
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
                <button type="submit" className="analyze-button" disabled={!file || loading}>
                  {loading ? "Analyzing..." : "Run analysis →"}
                </button>
                <button type="button" className="validate-button" onClick={handleValidate} disabled={!file || validating}>
                  {validating ? "Validating..." : "Validate data"}
                </button>
              </div>
            </div>
          </form>

          {error && <div className="error-message">{error}</div>}
        </section>

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
            {report && <span className="success-badge">Analysis complete</span>}
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
              <span
                className={
                  validation.valid ? "validation-pass" : "validation-fail"
                }
              >
                {validation.valid ? "All checks passed" : "Issues detected"}
              </span>
            )}
          </div>

          {validationError && (
            <div className="error-message">{validationError}</div>
          )}

          {!validation ? (
            <div className="empty-state">
              <strong>No validation results yet</strong>
              <p>Upload a CSV and click Validate data.</p>
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

            <div className="quality-rule-manager">
              <div className="quality-rule-heading">
                <div>
                  <h3>Quality rules</h3>
                  <p>Rules are saved in this browser and used for validation and detection.</p>
                </div>
                <button type="button" className="rule-reset-button" onClick={resetQualityRules}>
                  Restore defaults
                </button>
              </div>

              <label htmlFor="required-columns">Required columns</label>
              <input
                id="required-columns"
                value={qualityRuleConfig.requiredColumns}
                onChange={(event) => updateQualityRuleConfig("requiredColumns", event.target.value)}
                placeholder="name, age"
              />

              <div className="rule-group-heading">
                <strong>Numeric ranges</strong>
                <button type="button" onClick={() => addRuleRow("numericRanges", { column: "", min: "", max: "" })}>+ Add range</button>
              </div>
              {qualityRuleConfig.numericRanges.map((rule, index) => (
                <div className="rule-editor-row" key={`range-${index}`}>
                  <input aria-label="Range column" placeholder="Column" value={rule.column} onChange={(event) => updateRuleRow("numericRanges", index, "column", event.target.value)} />
                  <input aria-label="Minimum value" type="number" placeholder="Min" value={rule.min} onChange={(event) => updateRuleRow("numericRanges", index, "min", event.target.value)} />
                  <input aria-label="Maximum value" type="number" placeholder="Max" value={rule.max} onChange={(event) => updateRuleRow("numericRanges", index, "max", event.target.value)} />
                  <button type="button" aria-label="Remove numeric range" onClick={() => removeRuleRow("numericRanges", index)}>Remove</button>
                </div>
              ))}

              <div className="rule-group-heading">
                <strong>Allowed values</strong>
                <button type="button" onClick={() => addRuleRow("allowedValues", { column: "", values: "" })}>+ Add allowed-values rule</button>
              </div>
              {qualityRuleConfig.allowedValues.map((rule, index) => (
                <div className="rule-editor-row allowed-rule-row" key={`allowed-${index}`}>
                  <input aria-label="Allowed-values column" placeholder="Column" value={rule.column} onChange={(event) => updateRuleRow("allowedValues", index, "column", event.target.value)} />
                  <input aria-label="Approved values, comma separated" placeholder="Approved values, comma separated" value={rule.values} onChange={(event) => updateRuleRow("allowedValues", index, "values", event.target.value)} />
                  <button type="button" aria-label="Remove allowed-values rule" onClick={() => removeRuleRow("allowedValues", index)}>Remove</button>
                </div>
              ))}

              <label htmlFor="unique-columns">Values that must be unique</label>
              <input
                id="unique-columns"
                value={qualityRuleConfig.uniqueColumns}
                onChange={(event) => updateQualityRuleConfig("uniqueColumns", event.target.value)}
                placeholder="email, customer_id"
              />
            </div>

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

              <h3 className="anomaly-subheading">
                Detected rows
              </h3>

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
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              )}

              <p className="anomaly-note">
                Isolation Forest flags unusual patterns, not
                necessarily incorrect data. Review flagged rows
                before taking action.
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
