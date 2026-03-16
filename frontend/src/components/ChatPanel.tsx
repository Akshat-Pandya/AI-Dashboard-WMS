import React, { useState, useEffect } from "react";
import { R } from "@/tokens/brand";

interface DashboardMeta {
  id: string;
  query_text: string;
  intent_name: string | null;
  label: string | null;
  created_at: string;
}

interface Props {
  history: string[];
  activeQuery: string;
  loading: boolean;
  onSubmit: (query: string) => void | Promise<void>;
  mode?: "history" | "saved";
  onRunSaved?: (id: string, queryText: string) => void | Promise<void>;
  savedRefreshKey?: number;
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const SAMPLE_QUERIES = [
  "Show warehouse overview",
  "Which items are low on stock?",
  "Show active alerts",
  "Compare inventory across zones",
];

const INTENT_LABELS: Record<string, string> = {
  order_status: "Orders",
  warehouse_alerts: "Alerts",
  low_stock: "Low Stock",
  inventory_lookup: "Inventory",
  zone_inventory_compare: "Zone Compare",
  warehouse_overview: "Overview",
  active_tasks: "Tasks",
  blocked_tasks: "Blocked",
  inbound_activity: "Inbound",
  overdue_asn: "Overdue ASN",
  kpi_summary: "KPIs",
};

const INTENT_COLORS: Record<string, string> = {
  warehouse_alerts: "#EF4444",
  low_stock: "#F59E0B",
  order_status: "#3B82F6",
  warehouse_overview: "#8B5CF6",
  active_tasks: "#10B981",
  blocked_tasks: "#EF4444",
  inbound_activity: "#06B6D4",
  kpi_summary: "#F97316",
};

export const ChatPanel: React.FC<Props> = ({
  history,
  activeQuery,
  loading,
  onSubmit,
  mode = "history",
  onRunSaved,
  savedRefreshKey = 0,
}) => {
  const [input, setInput] = useState("");
  const [dashboards, setDashboards] = useState<DashboardMeta[]>([]);
  const [fetching, setFetching] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    if (mode !== "saved") return;
    setFetching(true);
    fetch(`${BASE_URL}/dashboards`)
      .then((r) => r.json())
      .then(setDashboards)
      .catch(() => setDashboards([]))
      .finally(() => setFetching(false));
  }, [mode, savedRefreshKey]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (loading) return;
    setDeleting(id);
    try {
      await fetch(`${BASE_URL}/dashboards/${id}`, { method: "DELETE" });
      setDashboards((prev) => prev.filter((d) => d.id !== id));
    } finally {
      setDeleting(null);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !loading) { onSubmit(input.trim()); setInput(""); }
    }
  };

  const panelStyle: React.CSSProperties = {
    width: 300,
    background: "#0A0B0D",
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    flexShrink: 0,
    borderRight: "1px solid #1A1D22",
  };

  // Shared style applied to the scrollable list area when loading
  const listLockStyle: React.CSSProperties = loading
    ? { pointerEvents: "none", opacity: 0.4, transition: "opacity 0.2s" }
    : { pointerEvents: "auto", opacity: 1, transition: "opacity 0.2s" };

  // ── Header ────────────────────────────────────────────────────────────────
  const Header = () => (
    <div style={{
      background: R.red,
      padding: "7px 16px",
      flexShrink: 0,
      display: "flex",
      alignItems: "center",
      gap: 7,
    }}>
      <div style={{ width: 5, height: 5, borderRadius: "50%", background: "rgba(255,255,255,0.45)" }} />
      <p style={{
        fontFamily: "'Barlow', sans-serif",
        fontSize: 9, fontWeight: 800,
        color: "#FFFFFF", letterSpacing: "0.14em",
        textTransform: "uppercase", margin: 0,
      }}>
        Global Robotics · After Sales
      </p>
    </div>
  );

  // ── Brand ─────────────────────────────────────────────────────────────────
  const Brand = () => (
    <div style={{
      padding: "18px 16px 15px",
      borderBottom: "1px solid #1A1D22",
      flexShrink: 0,
    }}>
      <span style={{
        fontFamily: "'Barlow Condensed', sans-serif",
        fontSize: 32, fontWeight: 900,
        color: R.red, letterSpacing: "0.02em",
        display: "block", lineHeight: 1,
      }}>
        ADDVERB
      </span>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 6 }}>
        <span style={{
          fontFamily: "'Barlow', sans-serif",
          fontSize: 10, fontWeight: 600,
          color: "#D1D5DB",
          letterSpacing: "0.1em",
          textTransform: "uppercase",
        }}>
          WMS Dashboard
        </span>
        <div style={{
          display: "flex", alignItems: "center", gap: 5,
          background: "#0F2A1A",
          border: "1px solid #1A4D2E",
          borderRadius: 20,
          padding: "2px 8px",
        }}>
          <div style={{
            width: 5, height: 5, borderRadius: "50%",
            background: loading ? "#F59E0B" : "#22C55E",
            boxShadow: loading ? "0 0 5px #F59E0B88" : "0 0 5px #22C55E88",
            transition: "background 0.3s, box-shadow 0.3s",
          }} />
          <span style={{
            fontFamily: "'Barlow', sans-serif",
            fontSize: 9, fontWeight: 800,
            color: loading ? "#F59E0B" : "#22C55E",
            letterSpacing: "0.1em",
            transition: "color 0.3s",
          }}>
            {loading ? "RUNNING" : "LIVE"}
          </span>
        </div>
      </div>
    </div>
  );

  // ── Section divider ────────────────────────────────────────────────────────
  const SectionLabel = ({ children }: { children: React.ReactNode }) => (
    <div style={{
      padding: "14px 16px 8px",
      display: "flex", alignItems: "center", gap: 8, flexShrink: 0,
    }}>
      <div style={{ flex: 1, height: 1, background: "#1A1D22" }} />
      <span style={{
        fontFamily: "'Barlow', sans-serif",
        fontSize: 9, fontWeight: 800,
        color: "#D1D5DB",
        letterSpacing: "0.14em",
        textTransform: "uppercase",
        whiteSpace: "nowrap",
      }}>
        {children}
      </span>
      <div style={{ flex: 1, height: 1, background: "#1A1D22" }} />
    </div>
  );

  // ── Input area ─────────────────────────────────────────────────────────────
  const InputArea = (rows = 3) => (
    <div style={{
      padding: "12px 14px 16px",
      borderTop: "1px solid #1A1D22",
      flexShrink: 0,
    }}>
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKey}
        disabled={loading}
        placeholder="Ask anything about your warehouse..."
        rows={rows}
        style={{
          width: "100%",
          background: "#111417",
          border: "1px solid #252A32",
          borderRadius: 4,
          padding: "10px 12px",
          fontFamily: "'Barlow', sans-serif",
          fontSize: 13, lineHeight: 1.5,
          color: loading ? "#4A5260" : "#F3F4F6",
          resize: "none",
          boxSizing: "border-box",
          outline: "none",
          transition: "border-color 0.15s, color 0.15s",
          cursor: loading ? "not-allowed" : "text",
        }}
        onFocus={(e) => { if (!loading) e.currentTarget.style.borderColor = R.red; }}
        onBlur={(e) => { e.currentTarget.style.borderColor = "#252A32"; }}
      />
      <button
        onClick={() => { if (input.trim() && !loading) { onSubmit(input.trim()); setInput(""); } }}
        disabled={loading || !input.trim()}
        style={{
          marginTop: 8, width: "100%",
          background: loading || !input.trim() ? "#141619" : R.red,
          border: `1px solid ${loading || !input.trim() ? "#1E2125" : R.red}`,
          borderRadius: 4, padding: "10px",
          fontFamily: "'Barlow', sans-serif",
          fontSize: 11, fontWeight: 800,
          color: loading || !input.trim() ? "#B0B8C4" : "#fff",
          cursor: loading || !input.trim() ? "not-allowed" : "pointer",
          letterSpacing: "0.12em", textTransform: "uppercase",
          transition: "all 0.15s",
        }}
      >
        {loading ? "Running…" : "Send Query →"}
      </button>
      <p style={{
        fontFamily: "'Barlow', sans-serif",
        fontSize: 9, color: loading ? "#2A2F38" : "#B0B8C4",
        margin: "7px 0 0", textAlign: "center",
        letterSpacing: "0.06em",
        transition: "color 0.2s",
      }}>
        ENTER · SHIFT+ENTER for new line
      </p>
    </div>
  );

  // ══════════════════════════════════════════════════
  // SAVED MODE
  // ══════════════════════════════════════════════════
  if (mode === "saved") {
    return (
      <div style={panelStyle}>
        <Header />
        <Brand />
        <SectionLabel>Saved Dashboards</SectionLabel>

        {/* Lock overlay on the list — blocks all clicks while loading */}
        <div style={{ flex: 1, overflowY: "auto", ...listLockStyle }}>

          {fetching && [1, 2, 3].map((i) => (
            <div key={i} style={{
              margin: "0 14px 6px", height: 56,
              background: "#111417", borderRadius: 4, opacity: 0.5,
            }} />
          ))}

          {!fetching && dashboards.length === 0 && (
            <div style={{ padding: "40px 20px", textAlign: "center" }}>
              <div style={{ fontSize: 26, opacity: 0.2, marginBottom: 10 }}>⊟</div>
              <p style={{
                fontFamily: "'Barlow', sans-serif", fontSize: 13, fontWeight: 600,
                color: "#D1D5DB", margin: "0 0 4px",
              }}>No saved dashboards</p>
              <p style={{
                fontFamily: "'Barlow', sans-serif", fontSize: 11,
                color: "#D1D5DB", margin: 0, lineHeight: 1.5,
              }}>Run a query and click Save</p>
            </div>
          )}

          {!fetching && dashboards.map((d) => {
            const isActive = activeQuery === d.query_text;
            const intentColor = INTENT_COLORS[d.intent_name ?? ""] ?? "#B0B8C4";
            const intentLabel = INTENT_LABELS[d.intent_name ?? ""] ?? d.intent_name?.replace(/_/g, " ") ?? "";

            return (
              <div
                key={d.id}
                onClick={() => !loading && onRunSaved?.(d.id, d.query_text)}
                style={{
                  display: "flex", alignItems: "center", gap: 10,
                  padding: "12px 12px 12px 0",
                  cursor: loading ? "not-allowed" : "pointer",
                  borderLeft: `3px solid ${isActive ? R.red : "transparent"}`,
                  borderBottom: "1px solid #111417",
                  background: isActive ? "rgba(232,0,28,0.07)" : "transparent",
                  transition: "all 0.15s",
                }}
                onMouseEnter={(e) => {
                  if (!isActive && !loading) {
                    const el = e.currentTarget as HTMLDivElement;
                    el.style.background = "#0F1114";
                    el.style.borderLeftColor = "#B0B8C4";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    const el = e.currentTarget as HTMLDivElement;
                    el.style.background = isActive ? "rgba(232,0,28,0.07)" : "transparent";
                    el.style.borderLeftColor = isActive ? R.red : "transparent";
                  }
                }}
              >
                <div style={{
                  paddingLeft: 14, flexShrink: 0,
                  color: isActive ? R.red : "#D1D5DB",
                  fontSize: 9, fontFamily: "monospace",
                }}>▶</div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{
                    fontFamily: "'Barlow', sans-serif",
                    fontSize: 13, fontWeight: isActive ? 700 : 500,
                    color: isActive ? "#FFFFFF" : "#F3F4F6",
                    margin: "0 0 4px",
                    whiteSpace: "normal",
                    wordBreak: "break-word",
                    lineHeight: 1.3,
                  }}>
                    {d.label || d.query_text}
                  </p>
                  {intentLabel && (
                    <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                      <div style={{
                        width: 5, height: 5, borderRadius: "50%",
                        background: intentColor, flexShrink: 0,
                      }} />
                      <span style={{
                        fontFamily: "'Barlow', sans-serif",
                        fontSize: 9, fontWeight: 700, color: "#B0B8C4",
                        letterSpacing: "0.1em", textTransform: "uppercase",
                      }}>
                        {intentLabel}
                      </span>
                    </div>
                  )}
                </div>

                <button
                  onClick={(e) => handleDelete(e, d.id)}
                  disabled={deleting === d.id || loading}
                  title="Remove"
                  style={{
                    flexShrink: 0, background: "transparent", border: "none",
                    color: "#D1D5DB",
                    cursor: deleting === d.id || loading ? "not-allowed" : "pointer",
                    fontSize: 13, padding: "4px 8px 4px 4px",
                    lineHeight: 1, borderRadius: 3, transition: "color 0.15s",
                  }}
                  onMouseEnter={(e) => { if (!loading) (e.currentTarget as HTMLButtonElement).style.color = "#EF4444"; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.color = "#D1D5DB"; }}
                >
                  {deleting === d.id ? "…" : "✕"}
                </button>
              </div>
            );
          })}
        </div>

        {InputArea(2)}
      </div>
    );
  }

  // ══════════════════════════════════════════════════
  // HISTORY MODE
  // ══════════════════════════════════════════════════
  return (
    <div style={panelStyle}>
      <Header />
      <Brand />

      <div style={{ flex: 1, overflowY: "auto", ...listLockStyle }}>
        {history.length === 0 ? (
          <>
            <SectionLabel>Try asking</SectionLabel>
            <div style={{ padding: "0 14px 8px" }}>
              {SAMPLE_QUERIES.map((q, i) => (
                <button
                  key={i}
                  onClick={() => !loading && onSubmit(q)}
                  disabled={loading}
                  style={{
                    display: "block", width: "100%", textAlign: "left",
                    background: "#111417",
                    border: "1px solid #1A1D22",
                    borderRadius: 4,
                    padding: "10px 12px",
                    marginBottom: 6,
                    fontFamily: "'Barlow', sans-serif",
                    fontSize: 12, fontWeight: 500,
                    color: "#F3F4F6",
                    cursor: loading ? "not-allowed" : "pointer",
                    lineHeight: 1.4,
                    transition: "all 0.15s",
                  }}
                  onMouseEnter={(e) => {
                    if (!loading) {
                      const el = e.currentTarget as HTMLButtonElement;
                      el.style.borderColor = "#B0B8C4";
                      el.style.color = "#D1D5DB";
                      el.style.background = "#141619";
                    }
                  }}
                  onMouseLeave={(e) => {
                    const el = e.currentTarget as HTMLButtonElement;
                    el.style.borderColor = "#1A1D22";
                    el.style.color = "#D1D5DB";
                    el.style.background = "#111417";
                  }}
                >
                  <span style={{ color: "#D1D5DB", marginRight: 8, fontSize: 10 }}>→</span>
                  {q}
                </button>
              ))}
            </div>
          </>
        ) : (
          <>
            <SectionLabel>History</SectionLabel>
            <div style={{ padding: "0 14px 8px" }}>
              {[...history].reverse().map((q, i) => {
                const isActive = q === activeQuery;
                const num = history.length - i;
                return (
                  <div
                    key={i}
                    onClick={() => !loading && onSubmit(q)}
                    style={{
                      display: "flex", alignItems: "flex-start", gap: 10,
                      padding: "10px 12px",
                      marginBottom: 5,
                      cursor: loading ? "not-allowed" : "pointer",
                      background: isActive ? "rgba(232,0,28,0.08)" : "#111417",
                      border: `1px solid ${isActive ? R.red : "#1A1D22"}`,
                      borderRadius: 4,
                      fontFamily: "'Barlow', sans-serif",
                      fontSize: 13,
                      fontWeight: isActive ? 600 : 400,
                      color: isActive ? "#FFFFFF" : "#E5E7EB",
                      lineHeight: 1.4,
                      transition: "all 0.15s",
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive && !loading) {
                        const el = e.currentTarget as HTMLDivElement;
                        el.style.borderColor = "#B0B8C4";
                        el.style.color = "#D1D5DB";
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) {
                        const el = e.currentTarget as HTMLDivElement;
                        el.style.borderColor = "#1A1D22";
                        el.style.color = "#B0B8C4";
                      }
                    }}
                  >
                    <span style={{
                      fontFamily: isActive ? "monospace" : "'Barlow Condensed', sans-serif",
                      fontSize: isActive ? 9 : 11,
                      fontWeight: 700,
                      color: isActive ? R.red : "#D1D5DB",
                      marginTop: isActive ? 2 : 1,
                      flexShrink: 0,
                      minWidth: 14,
                      textAlign: "right",
                    }}>
                      {isActive ? "▶" : num}
                    </span>
                    <span style={{ flex: 1 }}>{q}</span>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>

      {InputArea(3)}
    </div>
  );
};