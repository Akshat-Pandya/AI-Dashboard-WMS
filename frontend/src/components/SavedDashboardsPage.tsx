import React, { useEffect, useState } from "react";
import { R } from "@/tokens/brand";
import { Skeleton } from "./Skeleton";

interface DashboardMeta {
  id:          string;
  query_text:  string;
  intent_name: string | null;
  label:       string | null;
  created_at:  string;
}

interface Props {
  onRunDashboard: (id: string, query: string) => void;
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const SavedDashboardsPage: React.FC<Props> = ({ onRunDashboard }) => {
  const [dashboards, setDashboards] = useState<DashboardMeta[]>([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState<string | null>(null);
  const [deleting, setDeleting]     = useState<string | null>(null);

  const fetchDashboards = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${BASE_URL}/dashboards`);
      if (!res.ok) throw new Error("Failed to fetch saved dashboards");
      const data = await res.json();
      setDashboards(data);
    } catch (e: any) {
      setError(e.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    setDeleting(id);
    try {
      await fetch(`${BASE_URL}/dashboards/${id}`, { method: "DELETE" });
      setDashboards((prev) => prev.filter((d) => d.id !== id));
    } catch {
      // fail silently — item stays in list
    } finally {
      setDeleting(null);
    }
  };

  useEffect(() => { fetchDashboards(); }, []);

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("en-IN", {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  };

  return (
    <div style={{
      flex: 1,
      display: "flex",
      flexDirection: "column",
      background: "#F9FAFB",
      overflow: "hidden",
    }}>
      {/* Header bar */}
      <div style={{
        background: "#fff",
        borderBottom: "1px solid #E5E7EB",
        padding: "14px 28px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexShrink: 0,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 4, height: 28, background: R.red, borderRadius: 2 }} />
          <div>
            <p style={{
              fontFamily: "'Barlow', sans-serif",
              fontSize: 9, fontWeight: 700,
              color: "#9CA3AF",
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              margin: "0 0 2px",
            }}>
              Navigation
            </p>
            <p style={{
              fontFamily: "'Barlow Condensed', sans-serif",
              fontSize: 20, fontWeight: 800,
              color: "#111827",
              margin: 0,
              letterSpacing: "0.04em",
            }}>
              SAVED DASHBOARDS
            </p>
          </div>
        </div>

        <button
          onClick={fetchDashboards}
          style={{
            background: "transparent",
            border: `1px solid #E5E7EB`,
            borderRadius: 2,
            padding: "7px 14px",
            fontFamily: "'Barlow', sans-serif",
            fontSize: 15,
            fontWeight: 700,
            color: "#6B7280",
            cursor: "pointer",
            letterSpacing: "0.06em",
            textTransform: "uppercase",
          }}
        >
          ↺ 
        </button>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: "auto", padding: 28 }}>

        {/* Loading */}
        {loading && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {[1, 2, 3].map((i) => <Skeleton key={i} height={80} />)}
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div style={{
            background: "#FEF2F2",
            border: "1px solid #FECACA",
            borderLeft: `4px solid ${R.red}`,
            borderRadius: 3,
            padding: "14px 18px",
            fontFamily: "'Barlow', sans-serif",
            fontSize: 13,
            color: "#991B1B",
          }}>
            {error}
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && dashboards.length === 0 && (
          <div style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "60%",
            gap: 16,
            opacity: 0.5,
          }}>
            <span style={{ fontSize: 48, lineHeight: 1 }}>⊟</span>
            <p style={{
              fontFamily: "'Barlow Condensed', sans-serif",
              fontSize: 20,
              fontWeight: 700,
              color: "#6B7280",
              margin: 0,
              letterSpacing: "0.04em",
            }}>
              NO SAVED DASHBOARDS
            </p>
            <p style={{
              fontFamily: "'Barlow', sans-serif",
              fontSize: 13,
              color: "#9CA3AF",
              margin: 0,
            }}>
              Run a query and click the bookmark icon to save it.
            </p>
          </div>
        )}

        {/* Dashboard list */}
        {!loading && !error && dashboards.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {dashboards.map((d) => (
              <div
                key={d.id}
                style={{
                  background: "#fff",
                  border: "1px solid #E5E7EB",
                  borderLeft: `4px solid ${R.red}`,
                  borderRadius: 3,
                  padding: "16px 20px",
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                  boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
                }}
              >
                {/* Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{
                    fontFamily: "'Barlow', sans-serif",
                    fontSize: 14,
                    fontWeight: 600,
                    color: "#111827",
                    margin: "0 0 4px",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}>
                    {d.label || d.query_text}
                  </p>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    {d.intent_name && (
                      <span style={{
                        fontFamily: "'Barlow', sans-serif",
                        fontSize: 10,
                        fontWeight: 700,
                        background: "#F3F4F6",
                        color: "#6B7280",
                        padding: "2px 8px",
                        borderRadius: 2,
                        letterSpacing: "0.06em",
                        textTransform: "uppercase",
                      }}>
                        {d.intent_name.replace(/_/g, " ")}
                      </span>
                    )}
                    <span style={{
                      fontFamily: "'Barlow', sans-serif",
                      fontSize: 11,
                      color: "#9CA3AF",
                    }}>
                      {formatDate(d.created_at)}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
                  <button
                    onClick={() => onRunDashboard(d.id, d.query_text)}
                    style={{
                      background: R.red,
                      border: "none",
                      borderRadius: 2,
                      padding: "8px 16px",
                      fontFamily: "'Barlow', sans-serif",
                      fontSize: 11,
                      fontWeight: 800,
                      color: "#fff",
                      cursor: "pointer",
                      letterSpacing: "0.08em",
                      textTransform: "uppercase",
                    }}
                  >
                    ▶ Run
                  </button>
                  <button
                    onClick={() => handleDelete(d.id)}
                    disabled={deleting === d.id}
                    style={{
                      background: "transparent",
                      border: "1px solid #E5E7EB",
                      borderRadius: 2,
                      padding: "8px 12px",
                      fontFamily: "'Barlow', sans-serif",
                      fontSize: 11,
                      fontWeight: 700,
                      color: deleting === d.id ? "#9CA3AF" : "#6B7280",
                      cursor: deleting === d.id ? "not-allowed" : "pointer",
                      letterSpacing: "0.06em",
                    }}
                  >
                    {deleting === d.id ? "…" : "✕"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
