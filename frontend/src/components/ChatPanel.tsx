import React, { useState, useEffect } from "react";
import { R } from "@/tokens/brand";

interface DashboardMeta {
  id:          string;
  query_text:  string;
  intent_name: string | null;
  label:       string | null;
  created_at:  string;
}

interface Props {
  history:          string[];
  activeQuery:      string;                                              // ← new
  loading:          boolean;
  onSubmit:         (query: string) => void | Promise<void>;
  mode?:            "history" | "saved";
  onRunSaved?:      (id: string, queryText: string) => void | Promise<void>;
  savedRefreshKey?: number;
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const SAMPLE_QUERIES = [
  "Show warehouse overview",
  "Which items are low on stock?",
  "Show active alerts",
  "Compare inventory across zones",
];

export const ChatPanel: React.FC<Props> = ({
  history,
  activeQuery,
  loading,
  onSubmit,
  mode = "history",
  onRunSaved,
  savedRefreshKey = 0,
}) => {
  const [input, setInput]           = useState("");
  const [dashboards, setDashboards] = useState<DashboardMeta[]>([]);
  const [fetching, setFetching]     = useState(false);
  const [deleting, setDeleting]     = useState<string | null>(null);

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
      if (input.trim()) { onSubmit(input.trim()); setInput(""); }
    }
  };

  const panelStyle: React.CSSProperties = {
    width: 320,
    background: R.black,
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    flexShrink: 0,
    borderRight: `1px solid ${R.darkGray}`,
  };

  const Header = () => (
    <div style={{ background: R.red, padding: "6px 16px", flexShrink: 0 }}>
      <p style={{
        fontFamily: "'Barlow', sans-serif", fontSize: 9, fontWeight: 700,
        color: "#fff", letterSpacing: "0.1em", textTransform: "uppercase", margin: 0,
      }}>
        Global Robotics Company · 24/7 After Sales Support
      </p>
    </div>
  );

  const Brand = () => (
    <div style={{ padding: "16px 16px 12px", borderBottom: `1px solid ${R.darkGray}`, flexShrink: 0 }}>
      <span style={{
        fontFamily: "'Barlow Condensed', sans-serif", fontSize: 28, fontWeight: 800,
        color: R.red, letterSpacing: "0.02em", display: "block",
      }}>ADDVERB</span>
      <span style={{
        fontFamily: "'Barlow', sans-serif", fontSize: 10, color: R.textMuted,
        letterSpacing: "0.06em", textTransform: "uppercase",
        display: "flex", alignItems: "center", gap: 6, marginTop: 2,
      }}>
        WMS Generative Dashboard
        <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22C55E", display: "inline-block" }} />
      </span>
    </div>
  );

  const InputArea = (rows = 3) => (
    <div style={{ padding: 12, borderTop: `1px solid ${R.darkGray}`, flexShrink: 0 }}>
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKey}
        placeholder="Ask anything about your warehouse..."
        rows={rows}
        style={{
          width: "100%", background: R.darkGray, border: `1px solid ${R.midGray}`,
          borderRadius: 3, padding: "8px 10px", fontFamily: "'Barlow', sans-serif",
          fontSize: 12, color: "#E5E7EB", resize: "none", boxSizing: "border-box", outline: "none",
        }}
      />
      <button
        onClick={() => { if (input.trim()) { onSubmit(input.trim()); setInput(""); } }}
        disabled={loading || !input.trim()}
        style={{
          marginTop: 8, width: "100%", background: R.red, border: "none", borderRadius: 3,
          padding: "9px", fontFamily: "'Barlow', sans-serif", fontSize: 11, fontWeight: 800,
          color: "#fff", cursor: loading || !input.trim() ? "not-allowed" : "pointer",
          letterSpacing: "0.1em", textTransform: "uppercase", opacity: loading || !input.trim() ? 0.5 : 1,
        }}
      >
        {loading ? "Running…" : "Send Query →"}
      </button>
    </div>
  );

  // ── Saved dashboards mode ─────────────────────────────────────────────────
  if (mode === "saved") {
    return (
      <div style={panelStyle}>
        <Header />
        <Brand />

        <div style={{ padding: "14px 16px 8px", flexShrink: 0 }}>
          <p style={{
            fontFamily: "'Barlow', sans-serif", fontSize: 9, fontWeight: 700,
            color: R.textMuted, letterSpacing: "0.1em", textTransform: "uppercase", margin: 0,
          }}>
            Saved Dashboards
          </p>
        </div>

        <div style={{ flex: 1, overflowY: "auto" }}>
          {fetching && [1,2,3].map((i) => (
            <div key={i} style={{
              height: 52, background: R.darkGray, borderRadius: 3,
              margin: "0 12px 8px", opacity: 0.5,
            }} />
          ))}

          {!fetching && dashboards.length === 0 && (
            <div style={{
              padding: "32px 16px", textAlign: "center",
              fontFamily: "'Barlow', sans-serif", fontSize: 12,
              color: R.midGray, lineHeight: 1.6,
            }}>
              No saved dashboards yet.<br />Run a query and click Save.
            </div>
          )}

          {!fetching && dashboards.map((d) => {
            const isActive = activeQuery === d.query_text;
            return (
              <div
                key={d.id}
                onClick={() => onRunSaved?.(d.id, d.query_text)}
                style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "10px 12px 10px 16px", cursor: "pointer",
                  borderLeft: `3px solid ${isActive ? R.red : "transparent"}`,
                  borderBottom: `1px solid ${R.darkGray}`,
                  background: isActive ? "rgba(232,0,28,0.08)" : "transparent",
                  transition: "all 0.15s",
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    const el = e.currentTarget as HTMLDivElement;
                    el.style.background = R.darkGray;
                    el.style.borderLeftColor = R.red;
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    const el = e.currentTarget as HTMLDivElement;
                    el.style.background = "transparent";
                    el.style.borderLeftColor = "transparent";
                  }
                }}
              >
                <span style={{ color: R.red, fontSize: 10, flexShrink: 0, fontFamily: "monospace" }}>▶</span>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{
                    fontFamily: "'Barlow', sans-serif", fontSize: 12,
                    fontWeight: isActive ? 700 : 600,
                    color: isActive ? "#fff" : "#E5E7EB",
                    margin: 0,
                    whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                  }}>
                    {d.label || d.query_text}
                  </p>
                  {d.intent_name && (
                    <p style={{
                      fontFamily: "'Barlow', sans-serif", fontSize: 9, fontWeight: 700,
                      color: R.midGray, margin: "2px 0 0",
                      letterSpacing: "0.06em", textTransform: "uppercase",
                    }}>
                      {d.intent_name.replace(/_/g, " ")}
                    </p>
                  )}
                </div>

                <button
                  onClick={(e) => handleDelete(e, d.id)}
                  disabled={deleting === d.id}
                  title="Remove"
                  style={{
                    flexShrink: 0, background: "transparent", border: "none",
                    color: "#6B7280", cursor: deleting === d.id ? "not-allowed" : "pointer",
                    fontSize: 12, padding: "2px 4px", lineHeight: 1, borderRadius: 2,
                  }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.color = "#EF4444"; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.color = "#6B7280"; }}
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

  // ── History mode ──────────────────────────────────────────────────────────
  return (
    <div style={panelStyle}>
      <Header />
      <Brand />

      <div style={{ flex: 1, overflowY: "auto" }}>
        {history.length === 0 ? (
          <div style={{ padding: "16px 16px 8px" }}>
            <p style={{
              fontFamily: "'Barlow', sans-serif", fontSize: 9, fontWeight: 700,
              color: R.textMuted, letterSpacing: "0.1em", textTransform: "uppercase", margin: "0 0 10px",
            }}>Sample Queries</p>
            {SAMPLE_QUERIES.map((q, i) => (
              <button key={i} onClick={() => onSubmit(q)} style={{
                display: "block", width: "100%", textAlign: "left",
                background: "transparent", border: `1px solid ${R.darkGray}`,
                borderRadius: 3, padding: "8px 10px", marginBottom: 6,
                fontFamily: "'Barlow', sans-serif", fontSize: 12, color: R.textMuted, cursor: "pointer",
              }}>
                {q}
              </button>
            ))}
          </div>
        ) : (
          <div style={{ padding: "14px 16px 8px" }}>
            <p style={{
              fontFamily: "'Barlow', sans-serif", fontSize: 9, fontWeight: 700,
              color: R.textMuted, letterSpacing: "0.1em", textTransform: "uppercase", margin: "0 0 10px",
            }}>Query</p>
            {/* Show newest first, highlight the active one */}
            {[...history].reverse().map((q, i) => {
              const isActive = q === activeQuery;
              return (
                <div key={i} onClick={() => onSubmit(q)} style={{
                  padding: "10px 12px", marginBottom: 6, cursor: "pointer",
                  background: isActive ? "rgba(232,0,28,0.08)" : "transparent",
                  border: `1px solid ${isActive ? R.red : R.darkGray}`,
                  borderRadius: 3, fontFamily: "'Barlow', sans-serif", fontSize: 12,
                  color: isActive ? "#E5E7EB" : R.textMuted,
                  fontWeight: isActive ? 600 : 400,
                  transition: "all 0.15s",
                }}>
                  {q}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {InputArea(3)}
    </div>
  );
};