export default function TasksList({ data = [] }) {
  return (
    <div style={styles.container}>
      <h2>Active Tasks</h2>

      {data.length === 0 ? (
        <p>No tasks available</p>
      ) : (
        <ul style={styles.list}>
          {data.map((task, i) => (
            <li key={i} style={styles.item}>
              <strong>{task.task_type}</strong> — {task.status}
              <div style={styles.meta}>
                Assigned: {task.assignee_name} | Zone: {task.zone}
              </div>
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
  item: { borderBottom: "1px solid #eee", padding: "8px 0" },
  meta: { fontSize: 12, color: "#666" },
};
