import React, { useState } from "react";
import { R } from "@/tokens/brand";

interface Props {
  data: unknown;
}

export const DebugAccordion: React.FC<Props> = ({ data }) => {
  const [open, setOpen] = useState(false);

  return (
    <div
      style={{
        marginTop: 20,
        border: `1px solid ${R.border}`,
        borderRadius: 4,
        overflow: "hidden",
      }}
    >
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          width: "100%",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "10px 16px",
          background: R.bg,
          border: "none",
          cursor: "pointer",
          fontFamily: "'Barlow', sans-serif",
          fontSize: 10,
          fontWeight: 700,
          color: R.textMuted,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
        }}
      >
        <span>Debug — Raw JSON Response</span>
        <span style={{ fontSize: 9 }}>{open ? "▲ HIDE" : "▼ SHOW"}</span>
      </button>

      {open && (
        <pre
          style={{
            margin: 0,
            padding: "16px",
            background: R.black,
            color: "#7DD3FC",
            fontFamily: "'Barlow Condensed', monospace",
            fontSize: 12,
            lineHeight: 1.7,
            overflowX: "auto",
            maxHeight: 300,
          }}
        >
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
};
