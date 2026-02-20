import React, { useState } from "react";
import { ChatPanel } from "./components/ChatPanel";
import { ResultsPanel } from "./components/ResultsPanel";
import { queryWMS } from "./services/api";
import type { ChatResponse } from "./types";

const App: React.FC = () => {
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<string[]>([]);

  const handleSubmit = async (query: string) => {
    setLoading(true);
    setResponse(null);
    setHistory((prev) => [...prev, query]);

    try {
      const result = await queryWMS(query);
      setResponse(result);
    } catch (err) {
      console.error("WMS query failed:", err);
      // TODO: surface error state in UI
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        overflow: "hidden",
        width: "100%",
      }}
    >
      <ChatPanel
        history={history}
        loading={loading}
        onSubmit={handleSubmit}
      />
      <ResultsPanel response={response} loading={loading} />
    </div>
  );
};

export default App;
