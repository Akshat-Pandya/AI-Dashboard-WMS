import React, { useState } from "react";
import { R } from "@/tokens/brand";

interface Props {
  query:      string;
  intentName?: string;
  params?:    Record<string, unknown>;
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const SaveButton: React.FC<Props> = ({ query, intentName, params }) => {
  const [state, setState] = useState<"idle" | "saving" | "saved" | "error">("idle");

  const handleSave = async () => {
    if (state === "saving" || state === "saved") return;
    setState("saving");
    try {
      const res = await fetch(`${BASE_URL}/dashboards/save`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          intent_name: intentName ?? null,
          params:      params     ?? null,
          label:       query.slice(0, 80),
        }),
      });
      if (!res.ok) throw new Error("Save failed");
      setState("saved");
      // Reset to idle after 2.5s
      setTimeout(() => setState("idle"), 2500);
    } catch {
      setState("error");
      setTimeout(() => setState("idle"), 2000);
    }
  };

  const labels = {
    idle:   "⊟  Save Dashboard",
    saving: "…  Saving",
    saved:  "✓  Saved",
    error:  "✕  Failed",
  };

  const colors = {
    idle:   { bg: "transparent", color: "#6B7280", border: "#E5E7EB" },
    saving: { bg: "transparent", color: "#9CA3AF", border: "#E5E7EB" },
    saved:  { bg: "#ECFDF5",     color: "#065F46", border: "#A7F3D0" },
    error:  { bg: "#FEF2F2",     color: "#991B1B", border: "#FECACA" },
  };

  const c = colors[state];

  return (
    <button
      onClick={handleSave}
      disabled={state === "saving"}
      style={{
        background:   c.bg,
        border:       `1px solid ${c.border}`,
        borderRadius: 2,
        padding:      "7px 14px",
        fontFamily:   "'Barlow', sans-serif",
        fontSize:     11,
        fontWeight:   700,
        color:        c.color,
        cursor:       state === "saving" ? "not-allowed" : "pointer",
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        transition:   "all 0.2s",
        whiteSpace:   "nowrap",
      }}
    >
      {labels[state]}
    </button>
  );
};
