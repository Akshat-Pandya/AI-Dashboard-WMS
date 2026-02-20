import React from "react";
import { R } from "@/tokens/brand";
import type { KPICardsData } from "@/types";

interface Props {
  data: KPICardsData;
}

export const KPICardsWidget: React.FC<Props> = ({ data }) => (
  <div
    style={{
      display: "grid",
      gridTemplateColumns: "repeat(3, 1fr)",
      gap: 12,
    }}
  >
    {data.cards.map((c, i) => (
      <div
        key={i}
        style={{
          background: R.bg,
          border: `1px solid ${R.border}`,
          borderTop: `3px solid ${c.up ? R.midGray : R.red}`,
          borderRadius: 3,
          padding: "18px 20px",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Ghost icon */}
        <div
          style={{
            position: "absolute",
            right: 14,
            top: 12,
            fontSize: 24,
            opacity: 0.12,
            userSelect: "none",
          }}
        >
          {c.icon}
        </div>

        <p
          style={{
            fontFamily: "'Barlow', sans-serif",
            fontSize: 10,
            fontWeight: 700,
            color: R.textMuted,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            marginBottom: 8,
          }}
        >
          {c.label}
        </p>

        <p
          style={{
            fontFamily: "'Barlow Condensed', sans-serif",
            fontSize: 36,
            fontWeight: 700,
            color: R.textPrimary,
            lineHeight: 1,
            marginBottom: 6,
          }}
        >
          {c.value}
          {c.unit && (
            <span
              style={{
                fontSize: 13,
                fontWeight: 500,
                color: R.textSecondary,
                marginLeft: 4,
                fontFamily: "'Barlow', sans-serif",
              }}
            >
              {c.unit}
            </span>
          )}
        </p>

        <p
          style={{
            fontFamily: "'Barlow', sans-serif",
            fontSize: 11,
            fontWeight: 600,
            color: c.up ? R.green : R.red,
          }}
        >
          {c.trend}
        </p>
      </div>
    ))}
  </div>
);
