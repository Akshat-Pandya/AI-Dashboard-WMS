export default function OverviewKpiCards({ data = {} }) {
  const kpis = data.kpis || [];

  return (
    <div style={styles.container}>
      <h2>Warehouse Overview</h2>

      <div style={styles.grid}>
        {kpis.length === 0 ? (
          <p>No KPI data available</p>
        ) : (
          kpis.map((kpi, i) => (
            <div key={i} style={styles.card}>
              <h3>{kpi.label}</h3>
              <p style={styles.value}>{kpi.value}</p>
              <span>{kpi.unit}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

const styles = {
  container: { background: "#fff", padding: 20, borderRadius: 10 },
  grid: { display: "flex", gap: 16, flexWrap: "wrap" },
  card: {
    padding: 16,
    border: "1px solid #eee",
    borderRadius: 8,
    minWidth: 150,
  },
  value: { fontSize: 24, fontWeight: "bold" },
};
