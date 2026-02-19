export default function OrdersTable({ data = [] }) {
  return (
    <div style={styles.container}>
      <h2>Outbound Orders</h2>

      {data.length === 0 ? (
        <p>No orders available</p>
      ) : (
        <table style={styles.table}>
          <thead>
            <tr>
              <th>Order #</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Customer</th>
              <th>Total Units</th>
            </tr>
          </thead>
          <tbody>
            {data.map((order, i) => (
              <tr key={i}>
                <td>{order.order_number}</td>
                <td>{order.status}</td>
                <td>{order.priority}</td>
                <td>{order.customer_name}</td>
                <td>{order.total_units}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const styles = {
  container: { background: "#fff", padding: 20, borderRadius: 10 },
  table: { width: "100%", borderCollapse: "collapse" },
};
