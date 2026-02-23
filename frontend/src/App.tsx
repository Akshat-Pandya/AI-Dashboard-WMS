import React, { useState } from "react";
import { ChatPanel } from "./components/ChatPanel";
import { ResultsPanel } from "./components/ResultsPanel";
import { IntentTabs } from "./components/IntentTabs";
import { IntentTabContent } from "./components/IntentTabContent";
import { AllIntentsPanel } from "./components/AllIntentsPanel";
import { queryWMS } from "./services/api";
import type { WMSResponse } from "./types";

const App: React.FC = () => {
  const [response, setResponse]   = useState<WMSResponse | null>(null);
  const [loading, setLoading]     = useState(false);
  const [history, setHistory]     = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState(0);

  const handleSubmit = async (query: string) => {
    setLoading(true);
    setResponse(null);
    setActiveTab(0);
    setHistory((prev) => [...prev, query]);

    try {
      const result = await queryWMS(query);
      console.log("response:", result);
      console.log("resultsByIntent:", result.resultsByIntent);
      setResponse(result);
    } catch (err) {
      console.error("WMS query failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const results      = response?.resultsByIntent ?? [];
  const hasResults   = results.length > 0;

  // Tab labels: one per intent + "All Intents" at the end
  const tabLabels = hasResults
    ? [
        ...results.map(
          (r) => `${r.intent.replace(/_/g, " ")} (${Math.round(r.confidence * 100)}%)`
        ),
        "All Intents",
      ]
    : [];

  const isAllIntentsTab = hasResults && activeTab === tabLabels.length - 1;
  const activeResult    = !isAllIntentsTab ? results[activeTab] : undefined;

  // ── Empty / loading state — delegate entirely to ResultsPanel ────────────────
  if (!response && !loading) {
    return (
      <div style={{ display: "flex", height: "100vh", overflow: "hidden", width: "100%" }}>
        <ChatPanel history={history} loading={loading} onSubmit={handleSubmit} />
        <ResultsPanel response={null} loading={false} />
      </div>
    );
  }

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden", width: "100%" }}>
      <ChatPanel history={history} loading={loading} onSubmit={handleSubmit} />

      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: "#F9FAFB" }}>

        {/* Query + summary bar — reuse ResultsPanel's header by passing response */}
        {/* We render it in "header-only" mode by hiding its scroll area via a wrapper */}
        <div style={{ flexShrink: 0 }}>
          {loading ? (
            // Show the loading skeleton via ResultsPanel while fetching
            <ResultsPanel response={null} loading={true} />
          ) : (
            response && (
              <>
                {/* Active query bar */}
                <div style={{
                  background: "#fff",
                  borderBottom: "1px solid #E5E7EB",
                  padding: "12px 24px",
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                }}>
                  <div style={{ width: 4, height: 28, background: "#E8001C", borderRadius: 2, flexShrink: 0 }} />
                  <div>
                    <p style={{
                      fontFamily: "'Barlow', sans-serif",
                      fontSize: 9, fontWeight: 700,
                      color: "#9CA3AF",
                      letterSpacing: "0.1em",
                      textTransform: "uppercase",
                      margin: "0 0 3px",
                    }}>
                      Active Query
                    </p>
                    <p style={{
                      fontFamily: "'Barlow', sans-serif",
                      fontSize: 14, color: "#111827",
                      margin: 0, fontWeight: 600,
                    }}>
                      "{response.query}"
                    </p>
                  </div>
                </div>

                {/* Summary bar */}
                {response.summary && (
                  <div style={{
                    background: "#fff",
                    borderBottom: "1px solid #E5E7EB",
                    padding: "10px 24px",
                  }}>
                    <p style={{
                      fontFamily: "'Barlow', sans-serif",
                      fontSize: 13, color: "#111827",
                      margin: 0, lineHeight: 1.6,
                    }}>
                      {response.summary}
                    </p>
                  </div>
                )}

                {/* Intent tabs */}
                {tabLabels.length > 0 && (
                  <IntentTabs
                    tabs={tabLabels}
                    activeTab={activeTab}
                    onTabChange={setActiveTab}
                  />
                )}
              </>
            )
          )}
        </div>

        {/* Scrollable tab content */}
        {!loading && response && (
          <div style={{ flex: 1, overflowY: "auto", padding: 24 }}>
            {isAllIntentsTab ? (
              <AllIntentsPanel response={response} />
            ) : activeResult ? (
              <IntentTabContent result={activeResult} />
            ) : null}
          </div>
        )}

      </div>
    </div>
  );
};

export default App;