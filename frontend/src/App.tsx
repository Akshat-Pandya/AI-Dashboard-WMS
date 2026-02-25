import React, { useState } from "react";
import { ChatPanel }        from "./components/ChatPanel";
import { ResultsPanel }     from "./components/ResultsPanel";
import { IntentTabs }       from "./components/IntentTabs";
import { IntentTabContent } from "./components/IntentTabContent";
import { AllIntentsPanel }  from "./components/AllIntentsPanel";
import { NavDrawer }        from "./components/NavDrawer";
import { SaveButton }       from "./components/SaveButton";
import { queryWMS }         from "./services/api";
import { buildTabResults }  from "./services/buildTabResults";
import type { WMSResponse } from "./types";
import { R }                from "./tokens/brand";

type Page = "query" | "saved";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const App: React.FC = () => {
  const [response, setResponse]               = useState<WMSResponse | null>(null);
  const [loading, setLoading]                 = useState(false);
  const [history, setHistory]                 = useState<string[]>([]);
  const [activeQuery, setActiveQuery]         = useState<string>("");   // ← tracks which query is active
  const [activeTab, setActiveTab]             = useState(0);
  const [drawerOpen, setDrawerOpen]           = useState(false);
  const [page, setPage]                       = useState<Page>("query");
  const [savedRefreshKey, setSavedRefreshKey] = useState(0);

  // ── FIX 1: only add to history if query is new ────────────────────────────
  const addToHistory = (query: string) => {
    setActiveQuery(query);
    setHistory((prev) => prev.includes(query) ? prev : [...prev, query]);
  };

  const handleSubmit = async (query: string) => {
    setPage("query");
    setLoading(true);
    setResponse(null);
    setActiveTab(0);
    addToHistory(query);   // deduplicates
    try {
      const result = await queryWMS(query);
      setResponse(result);
    } catch (err) {
      console.error("WMS query failed:", err);
    } finally {
      setLoading(false);
    }
  };

  // ── FIX 2 & 3: stay on saved page, don't add to history ──────────────────
  const handleRunSaved = async (id: string, queryText: string) => {
    // Stay on saved page — do NOT call setPage("query")
    setLoading(true);
    setResponse(null);
    setActiveTab(0);
    setActiveQuery(queryText);
    // Do NOT add to history for saved runs
    try {
      const res = await fetch(`${BASE_URL}/dashboards/${id}/run`);
      if (!res.ok) throw new Error("Failed to run dashboard");
      const raw = await res.json();
      setResponse(buildTabResults(raw));
    } catch (err) {
      console.error("Dashboard run failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleNavigate = (p: string) => {
    setPage(p as Page);
    if (p === "saved") {
      setSavedRefreshKey((k) => k + 1);
      setResponse(null);   // clear result when switching to saved page
      setActiveQuery("");
    }
  };

  const results         = response?.resultsByIntent ?? [];
  const hasResults      = results.length > 0;
  const tabLabels       = hasResults
    ? [...results.map((r) => `${r.intent.replace(/_/g, " ")} (${Math.round(r.confidence * 100)}%)`), "All Intents"]
    : [];
  const isAllIntentsTab = hasResults && activeTab === tabLabels.length - 1;
  const activeResult    = !isAllIntentsTab ? results[activeTab] : undefined;

  const HamburgerBtn = () => (
    <button
      onClick={() => setDrawerOpen(true)}
      style={{
        position: "fixed", top: 12, right: 16, zIndex: 99,
        background: "transparent", border: `1px solid ${R.darkGray}`,
        borderRadius: 2, width: 36, height: 36, cursor: "pointer",
        display: "flex", flexDirection: "column", alignItems: "center",
        justifyContent: "center", gap: 5, padding: 0,
      }}
      aria-label="Open navigation"
    >
      {[0,1,2].map((i) => (
        <span key={i} style={{ display: "block", width: 16, height: 2, background: "#9CA3AF", borderRadius: 1 }} />
      ))}
    </button>
  );

  const ResultArea = () => (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: "#F9FAFB" }}>
      {loading ? (
        <ResultsPanel response={null} loading={true} />
      ) : response ? (
        <>
          <div style={{
            background: "#fff", borderBottom: "1px solid #E5E7EB",
            padding: "12px 24px", display: "flex", alignItems: "center", gap: 14, flexShrink: 0,
          }}>
            <div style={{ width: 4, height: 28, background: R.red, borderRadius: 2, flexShrink: 0 }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{
                fontFamily: "'Barlow', sans-serif", fontSize: 9, fontWeight: 700,
                color: "#9CA3AF", letterSpacing: "0.1em", textTransform: "uppercase", margin: "0 0 3px",
              }}>Active Query</p>
              <p style={{
                fontFamily: "'Barlow', sans-serif", fontSize: 14, color: "#111827",
                margin: 0, fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
              }}>"{response.query}"</p>
            </div>
            <SaveButton
              query={response.query}
              intentName={response.selectedIntent}
              onSaved={() => setSavedRefreshKey((k) => k + 1)}
            />
            <div style={{ width: 44 }} />
          </div>

          {response.summary && (
            <div style={{ background: "#fff", borderBottom: "1px solid #E5E7EB", padding: "10px 24px", flexShrink: 0 }}>
              <p style={{ fontFamily: "'Barlow', sans-serif", fontSize: 13, color: "#111827", margin: 0, lineHeight: 1.6 }}>
                {response.summary}
              </p>
            </div>
          )}

          {tabLabels.length > 0 && (
            <IntentTabs tabs={tabLabels} activeTab={activeTab} onTabChange={setActiveTab} />
          )}

          <div style={{ flex: 1, overflowY: "auto", padding: 24 }}>
            {isAllIntentsTab
              ? <AllIntentsPanel response={response} />
              : activeResult ? <IntentTabContent result={activeResult} /> : null}
          </div>
        </>
      ) : (
        page === "saved" ? (
          <div style={{
            flex: 1, display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center", gap: 12, opacity: 0.45,
          }}>
            <span style={{ fontSize: 40 }}>⊟</span>
            <p style={{
              fontFamily: "'Barlow Condensed', sans-serif", fontSize: 18, fontWeight: 700,
              color: "#6B7280", margin: 0, letterSpacing: "0.04em",
            }}>SELECT A SAVED DASHBOARD</p>
            <p style={{ fontFamily: "'Barlow', sans-serif", fontSize: 13, color: "#9CA3AF", margin: 0 }}>
              Click any query from the panel to run it
            </p>
          </div>
        ) : (
          <ResultsPanel response={null} loading={false} />
        )
      )}
    </div>
  );

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden", width: "100%" }}>
      <ChatPanel
        history={history}
        activeQuery={activeQuery}
        loading={loading}
        onSubmit={handleSubmit}
        mode={page === "saved" ? "saved" : "history"}
        onRunSaved={handleRunSaved}
        savedRefreshKey={savedRefreshKey}
      />

      <ResultArea />

      <HamburgerBtn />
      <NavDrawer
        open={drawerOpen}
        activePage={page}
        onNavigate={handleNavigate}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  );
};

export default App;