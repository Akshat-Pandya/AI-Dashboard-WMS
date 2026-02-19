import { useState } from "react";

export default function QueryBar({ onResult }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!query.trim()) return;

    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/nl-query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });

      const data = await res.json();
      onResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <input
        style={styles.input}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask something like 'Show warehouse overview'"
        onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
      />

      <button style={styles.button} onClick={handleSubmit}>
        {loading ? "Loading..." : "Ask"}
      </button>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    gap: "10px",
    maxWidth: "800px",
    margin: "0 auto",
  },
  input: {
    flex: 1,
    padding: "12px",
    borderRadius: "8px",
    border: "1px solid #d1d5db",
  },
  button: {
    padding: "12px 20px",
    borderRadius: "8px",
    border: "none",
    backgroundColor: "#2563eb",
    color: "#fff",
    cursor: "pointer",
  },
};
