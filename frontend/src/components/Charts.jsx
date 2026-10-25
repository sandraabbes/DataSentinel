export function MissingValuesChart({ columns }) {
  const missing = columns
    .filter((column) => column.missing_percentage > 0)
    .sort((a, b) => b.missing_percentage - a.missing_percentage)
    .slice(0, 12);

  if (missing.length === 0) {
    return <div className="validation-success">No missing values in any column.</div>;
  }

  return (
    <div className="chart-bars" role="img" aria-label="Missing values by column">
      {missing.map((column) => (
        <div className="chart-bar-row" key={column.name}>
          <span className="chart-bar-label" title={column.name}>{column.name}</span>
          <div className="score-bar">
            <div
              className="score-bar-fill warning-fill"
              style={{ width: `${Math.min(column.missing_percentage, 100)}%` }}
            />
          </div>
          <span className="chart-bar-value">
            {column.missing_percentage}% ({column.missing_values})
          </span>
        </div>
      ))}
    </div>
  );
}

export function ScoreHistogram({ histogram }) {
  if (!histogram) return null;

  const { bin_edges: edges, normal, flagged } = histogram;
  const width = 480;
  const height = 150;
  const barWidth = width / normal.length;
  const peak = Math.max(...normal.map((n, i) => n + flagged[i]), 1);
  const scale = (count) => (count / peak) * height;

  return (
    <figure className="histogram">
      <svg
        viewBox={`0 0 ${width} ${height + 4}`}
        role="img"
        aria-label="Distribution of anomaly scores"
      >
        {normal.map((count, i) => {
          const normalHeight = scale(count);
          const flaggedHeight = scale(flagged[i]);
          return (
            <g key={i}>
              <rect
                x={i * barWidth + 1}
                y={height - normalHeight}
                width={barWidth - 2}
                height={normalHeight}
                fill="#6366f1"
              />
              <rect
                x={i * barWidth + 1}
                y={height - normalHeight - flaggedHeight}
                width={barWidth - 2}
                height={flaggedHeight}
                fill="#ef4444"
              />
            </g>
          );
        })}
      </svg>
      <div className="histogram-axis">
        <span>{edges[0]} (more unusual)</span>
        <span>{edges[edges.length - 1]} (more typical)</span>
      </div>
      <figcaption className="histogram-legend">
        <span><i style={{ background: "#6366f1" }} /> Normal</span>
        <span><i style={{ background: "#ef4444" }} /> Flagged</span>
      </figcaption>
    </figure>
  );
}
