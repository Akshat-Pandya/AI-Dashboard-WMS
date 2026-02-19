import { useState } from "react";
import QueryBar from "../components/QueryBar";
import Renderer from "../components/Renderer";

export default function Dashboard() {
  const [response, setResponse] = useState(null);

  return (
    <div style={styles.page}>
      {/* ---------- Top Query Section ---------- */}
      <div style={styles.header}>
        <QueryBar onResult={setResponse} />
      </div>

      {/* ---------- Rendered Components Section ---------- */}
      <div style={styles.content}>
        {response ? (
          <Renderer
            components={response.components}
            data={response.data}
          />
        ) : (
          <div style={styles.placeholder}>
            <h2>Ask something about your warehouse</h2>
            <p>
              Example: <em>“Show me warehouse overview”</em>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  page: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    backgroundColor: "#f7f9fc",
  },

  header: {
    position: "sticky",
    top: 0,
    zIndex: 10,
    backgroundColor: "#ffffff",
    padding: "16px 24px",
    borderBottom: "1px solid #e5e7eb",
  },

  content: {
    flex: 1,
    overflowY: "auto",
    padding: "24px",
    maxWidth: "1200px",
    margin: "0 auto",
    width: "100%",
  },

  placeholder: {
    textAlign: "center",
    marginTop: "80px",
    color: "#6b7280",
  },
};
