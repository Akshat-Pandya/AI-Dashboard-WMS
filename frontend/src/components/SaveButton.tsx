import React, { useState, useEffect } from "react";

interface Props {
  query:        string;
  intentName?:  string;
  params?:      Record<string, unknown>;
  onSaved?:     () => void;   // called after a successful save (not on unsave)
}

const BASE_URL = "";

export const SaveButton: React.FC<Props> = ({ query, intentName, params, onSaved }) => {
  const [status, setStatus]     = useState<"checking" | "unsaved" | "saved">("checking");
  const [busy, setBusy]         = useState(false);
  const [hovering, setHovering] = useState(false);
  const [savedId, setSavedId]   = useState<string | null>(null);

  useEffect(() => {
    if (!query) return;
    setStatus("checking");
    setSavedId(null);
    fetch(`${BASE_URL}/dashboards/check?query=${encodeURIComponent(query)}`)
      .then((r) => r.json())
      .then((data) => {
        setStatus(data.saved ? "saved" : "unsaved");
        setSavedId(data.id ?? null);
      })
      .catch(() => setStatus("unsaved"));
  }, [query]);

  const handleToggle = async () => {
    if (busy || status === "checking") return;
    setBusy(true);
    try {
      if (status === "unsaved") {
        const res = await fetch(`${BASE_URL}/dashboards/save`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query, intent_name: intentName ?? null, params: params ?? null, label: query.slice(0, 80) }),
        });
        if (!res.ok) throw new Error();
        const data = await res.json();
        setSavedId(data.id);
        setStatus("saved");
        onSaved?.();   // notify parent so side panel can refresh
      } else {
        if (!savedId) return;
        const res = await fetch(`${BASE_URL}/dashboards/${savedId}`, { method: "DELETE" });
        if (!res.ok && res.status !== 404) throw new Error();
        setSavedId(null);
        setStatus("unsaved");
      }
    } catch {
      // revert silently
    } finally {
      setBusy(false);
    }
  };

  const isChecking = status === "checking";
  const isSaved    = status === "saved";

  const label = isChecking ? "…"
    : busy          ? "…"
    : isSaved && hovering ? "✕  Unsave"
    : isSaved       ? "✓  Saved"
    : "⊟  Save";

  const bg     = isSaved ? (hovering ? "#FEF2F2" : "#ECFDF5") : "transparent";
  const color  = isSaved ? (hovering ? "#991B1B" : "#065F46") : "#6B7280";
  const border = isSaved ? (hovering ? "#FECACA" : "#A7F3D0") : "#E5E7EB";

  return (
    <button
      onClick={handleToggle}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
      disabled={busy || isChecking}
      title={isSaved ? "Click to unsave" : "Save this dashboard"}
      style={{
        background: bg, border: `1px solid ${border}`, borderRadius: 2,
        padding: "7px 14px", fontFamily: "'Barlow', sans-serif",
        fontSize: 11, fontWeight: 700, color,
        cursor: busy || isChecking ? "not-allowed" : "pointer",
        letterSpacing: "0.06em", textTransform: "uppercase",
        transition: "all 0.18s ease", whiteSpace: "nowrap", minWidth: 90,
      }}
    >
      {label}
    </button>
  );
};
