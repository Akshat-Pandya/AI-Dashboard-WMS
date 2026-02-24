import React, { useState } from "react";
import { ChatPanel }            from "./components/ChatPanel";
import { ResultsPanel }         from "./components/ResultsPanel";
import { IntentTabs }           from "./components/IntentTabs";
import { IntentTabContent }     from "./components/IntentTabContent";
import { AllIntentsPanel }      from "./components/AllIntentsPanel";
import { NavDrawer }            from "./components/NavDrawer";
import { SavedDashboardsPage }  from "./components/SavedDashboardsPage";
import { SaveButton }           from "./components/SaveButton";
import { queryWMS }             from "./services/api";
import type { WMSResponse }     from "./types";
import { R }                    from "./tokens/brand";

type Page = "query" | "saved";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const App: React.FC = () => {
  const [response, setResponse]     = useState<WMSResponse | null>(null);
  const [loading, setLoading]       = useState(false);
  const [history, setHistory]       = useState<string[]>([]);
  const [activeTab, setActiveTab]   = useState(0);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [page, setPage]             = useState<Page>("query");

  const handleSubmit = async (query: string) => {
    // Always switch to query page when a query is submitted
    setPage("query");
    setLoading(true);
    setResponse(null);
    setActiveTab(0);
    setHistory((prev) => [...prev, query]);

    try {
      const result = await queryWMS(query);
      setResponse(result);
    } catch (err) {
      console.error("WMS query failed:", err);
    } finally {
      setLoading(false);
    }
  };

  // Re-run a saved dashboard by its ID via /dashboards/{id}/run
  const handleRunSaved = async (id: string, queryText: string) => {
    setPage("query");
    setLoading(true);
    setResponse(null);
    setActiveTab(0);
    setHistory((prev) => [...prev, queryText]);

    try {
      const res = await fetch(`${BASE_URL}/dashboards/${id}/run`);
      if (!res.ok) throw new Error("Failed to run dashboard");
      const raw = await res.json();
      // buildTabResults is called inside queryWMS for normal queries,
      // but for saved dashboards we get raw QueryResponse — import buildTabResults
      const { buildTabResults } = await import("./services/buildTabResults");
      setResponse(buildTabResults(raw));
    } catch (err) {
      console.error("Dashboard run failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const results         = response?.resultsByIntent ?? [];
  const hasResults      = results.length > 0;
  const tabLabels       = hasResults
    ? [
        ...results.map(
          (r) => `${r.intent.replace(/_/g, " ")} (${Math.round(r.confidence * 100)}%)`
        ),
        "All Intents",
      ]
    : [];
  const isAllIntentsTab = hasResults && activeTab === tabLabels.length - 1;
  const activeResult    = !isAllIntentsTab ? results[activeTab] : undefined;

  // ── Hamburger button (always visible top-right) ───────────────────────────
  const HamburgerBtn = () => (
    <button
      onClick={() => setDrawerOpen(true)}
      style={{
        position:   "fixed",
        top:        12,
        right:      16,
        zIndex:     99,
        background: "transparent",
        border:     `1px solid ${R.darkGray}`,
        borderRadius: 2,
        width:      36,
        height:     36,
        cursor:     "pointer",
        display:    "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap:        5,
        padding:    0,
      }}
      aria-label="Open navigation"
    >
      {[0, 1, 2].map((i) => (
        <span key={i} style={{
          display:    "block",
          width:      16,
          height:     2,
          background: "#9CA3AF",
          borderRadius: 1,
          transition: "background 0.15s",
        }} />
      ))}
    </button>
  );

  // ── Saved Dashboards page ─────────────────────────────────────────────────
  if (page === "saved") {
    return (
      <div style={{ display: "flex", height: "100vh", overflow: "hidden", width: "100%" }}>
        <ChatPanel history={history} loading={loading} onSubmit={handleSubmit} />
        <SavedDashboardsPage onRunDashboard={handleRunSaved} />
        <HamburgerBtn />
        <NavDrawer
          open={drawerOpen}
          activePage={page}
          onNavigate={(p) => setPage(p as Page)}
          onClose={() => setDrawerOpen(false)}
        />
      </div>
    );
  }

  // ── Query page — empty / loading ──────────────────────────────────────────
  if (!response && !loading) {
    return (
      <div style={{ display: "flex", height: "100vh", overflow: "hidden", width: "100%" }}>
        <ChatPanel history={history} loading={loading} onSubmit={handleSubmit} />
        <ResultsPanel response={null} loading={false} />
        <HamburgerBtn />
        <NavDrawer
          open={drawerOpen}
          activePage={page}
          onNavigate={(p) => setPage(p as Page)}
          onClose={() => setDrawerOpen(false)}
        />
      </div>
    );
  }

  // ── Query page — with results ─────────────────────────────────────────────
  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden", width: "100%" }}>
      <ChatPanel history={history} loading={loading} onSubmit={handleSubmit} />

      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: "#F9FAFB" }}>

        <div style={{ flexShrink: 0 }}>
          {loading ? (
            <ResultsPanel response={null} loading={true} />
          ) : (
            response && (
              <>
                {/* Active query bar + Save button */}
                <div style={{
                  background: "#fff",
                  borderBottom: "1px solid #E5E7EB",
                  padding: "12px 24px",
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                }}>
                  <div style={{ width: 4, height: 28, background: R.red, borderRadius: 2, flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
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
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}>
                      "{response.query}"
                    </p>
                  </div>

                  {/* Save Dashboard button */}
                  <SaveButton
                    query={response.query}
                    intentName={response.selectedIntent}
                  />

                  {/* Space for hamburger */}
                  <div style={{ width: 44 }} />
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

      <HamburgerBtn />
      <NavDrawer
        open={drawerOpen}
        activePage={page}
        onNavigate={(p) => setPage(p as Page)}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  );
};

export default App;