// Characters that make Excel/Sheets treat a cell as a formula.
const FORMULA_START = /^[=+\-@\t\r]/;

export function escapeCsvCell(value) {
  if (value === null || value === undefined) return "";

  let text = typeof value === "object" ? JSON.stringify(value) : String(value);

  // CSV injection protection: neutralize text that looks like a formula.
  // Real numbers are left alone, so -5 stays -5.
  if (typeof value === "string" && FORMULA_START.test(text)) {
    text = `'${text}`;
  }

  if (/[",\n\r]/.test(text)) {
    text = `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

export function toCsv(headers, rows) {
  const lines = [headers, ...rows].map((row) => row.map(escapeCsvCell).join(","));
  return "\uFEFF" + lines.join("\r\n"); // BOM so Excel reads UTF-8 correctly
}

export function downloadFile(filename, content, mime) {
  const blob = new Blob([content], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function baseName(fileName) {
  return (fileName || "dataset").replace(/\.csv$/i, "");
}

export function exportValidationIssues(validation, fileName) {
  const rows = validation.issues.map((issue) => [
    issue.column,
    issue.rule,
    issue.message,
    issue.affected_rows,
    (issue.row_numbers || []).join(" "),
  ]);
  downloadFile(
    `${baseName(fileName)}_validation_issues.csv`,
    toCsv(["column", "rule", "message", "affected_rows", "row_numbers"], rows),
    "text/csv"
  );
}

export function exportFlaggedRows(anomalyReport, fileName) {
  const flagged = anomalyReport.results.filter((row) => row.status !== "Normal");
  if (flagged.length === 0) return false;

  const valueColumns = Object.keys(flagged[0].values);
  const rows = flagged.map((row) => [
    row.row_number,
    row.status,
    row.anomaly_score,
    row.detection_methods.join("; "),
    row.reasons.join(" | "),
    ...valueColumns.map((column) => row.values[column]),
  ]);

  downloadFile(
    `${baseName(fileName)}_flagged_rows.csv`,
    toCsv(
      ["row_number", "status", "anomaly_score", "detection_methods", "reasons", ...valueColumns],
      rows
    ),
    "text/csv"
  );
  return true;
}

export function exportReportJson({ fileName, qualityScore, report, validation, anomalyReport }) {
  const payload = {
    generated_at: new Date().toISOString(),
    file_name: fileName,
    quality_score: qualityScore,
    profile: report,
    validation,
    anomalies: anomalyReport && {
      ...anomalyReport,
      results: anomalyReport.results.filter((row) => row.status !== "Normal"),
    },
  };
  downloadFile(
    `${baseName(fileName)}_report.json`,
    JSON.stringify(payload, null, 2),
    "application/json"
  );
}
