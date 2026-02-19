export default function LowStockTable({ data = [] }) {
  return (
    <div style={styles.container}>
      <h2>Low Stock Items</h2>

      {data.length === 0 ? (
        <p>No low stock items 🎉</p>
      ) : (
        <table style={styles.table}>
          <thead>
            <tr>
              <th>SKU</th>
              <th>Product</th>
              <th>Available</th>
              <th>Reorder Point</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, i) => (
              <tr key={i}>
                <td>{item.sku}</td>
                <td>{item.product_name}</td>
                <td>{item.quantity_available}</td>
                <td>{item.reorder_point}</td>
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
