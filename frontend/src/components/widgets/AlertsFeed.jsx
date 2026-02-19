export default function AlertsFeed({ data = [] }) {
  return (
    <div style={styles.container}>
      <h2>Warehouse Alerts</h2>

      {data.length === 0 ? (
        <p>No alerts 🎉</p>
      ) : (
        <ul style={styles.list}>
          {data.map((alert, i) => (
            <li key={i} style={styles.item}>
              <strong>{alert.title}</strong>
              <p>{alert.message}</p>
              <span style={styles.meta}>
                {alert.severity} • {alert.timestamp}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

const styles = {
  container: { background: "#fff", padding: 20, borderRadius: 10 },
  list: { listStyle: "none", padding: 0 },
  item: { borderBottom: "1px solid #eee", padding: "10px 0" },
  meta: { fontSize: 12, color: "#888" },
};
