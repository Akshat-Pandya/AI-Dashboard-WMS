import React from "react";
import { R } from "@/tokens/brand";
import type { CandidateIntent } from "@/types";

interface Props {
  candidates: CandidateIntent[];
  selectedIntent: string;
}

export const IntentChips: React.FC<Props> = ({ candidates, selectedIntent }) => (
  <div
    style={{
      background: R.white,
      borderBottom: `1px solid ${R.border}`,
      padding: "10px 24px",
      display: "flex",
      gap: 8,
      alignItems: "center",
      flexWrap: "wrap",
      flexShrink: 0,
    }}
  >
    <span
      style={{
        fontFamily: "'Barlow', sans-serif",
        fontSize: 9,
        fontWeight: 700,
        color: R.textMuted,
        letterSpacing: "0.1em",
        textTransform: "uppercase",
        marginRight: 4,
      }}
    >
      Detected Intents
    </span>

    {candidates.map((c, i) => {
      const isSelected = c.name === selectedIntent;
      const pct = Math.round(c.confidence * 100);
      const confidenceColor =
        pct > 70 ? R.green : pct > 40 ? R.amber : R.red;

      return (
        <div
          key={i}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 7,
            background: isSelected ? R.red : R.bg,
            border: `1px solid ${isSelected ? R.red : R.border}`,
            borderRadius: 2,
            padding: "5px 12px",
          }}
        >
          <span
            style={{
              fontFamily: "'Barlow', sans-serif",
              fontSize: 11,
              fontWeight: 700,
              color: isSelected ? "#fff" : R.textSecondary,
              letterSpacing: "0.06em",
            }}
          >
            {c.name}
          </span>
          <span
            style={{
              fontFamily: "'Barlow Condensed', sans-serif",
              fontSize: 14,
              fontWeight: 800,
              color: isSelected ? "rgba(255,255,255,0.85)" : confidenceColor,
            }}
          >
            {pct}%
          </span>
        </div>
      );
    })}
  </div>
);
