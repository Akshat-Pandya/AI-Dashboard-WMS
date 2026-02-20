import React from "react";
import { R } from "@/tokens/brand";
import { Skeleton } from "./Skeleton";
import { DebugAccordion } from "./DebugAccordion";
import { WidgetRenderer } from "./widgets/WidgetRenderer";
import type { IntentTabResult } from "@/types";

interface Props {
  result: IntentTabResult;
  loading?: boolean;
}

export const IntentTabContent: React.FC<Props> = ({ result, loading = false }) => {
  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <Skeleton height={90} />
        <Skeleton height={200} />
        <Skeleton height={160} />
      </div>
    );
  }

  return (
    <div>
      {/* Tools executed */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
        {result.toolsExecuted.map((t, i) => (
          <span
            key={i}
            style={{
              fontFamily: "'Barlow', sans-serif",
              fontSize: 11,
              fontWeight: 700,
              background: R.black,
              color: "#CBD5E1",
              padding: "5px 10px",
              borderRadius: 2,
              letterSpacing: "0.05em",
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <span style={{ color: R.red, fontSize: 8 }}>▶</span>
            {t}
          </span>
        ))}
      </div>

      {/* Summary bullets */}
      <div
        style={{
          background: R.greenLight,
          borderLeft: `4px solid ${R.green}`,
          border: `1px solid #A7F3D0`,
          borderRadius: 3,
          padding: "14px 18px",
          marginBottom: 20,
        }}
      >
        {result.summary.map((s, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              gap: 10,
              marginBottom: i < result.summary.length - 1 ? 8 : 0,
            }}
          >
            <span
              style={{
                color: R.green,
                fontWeight: 800,
                fontSize: 16,
                lineHeight: 1.2,
                flexShrink: 0,
              }}
            >
              ·
            </span>
            <p
              style={{
                margin: 0,
                fontSize: 13,
                color: "#065F46",
                fontFamily: "'Barlow', sans-serif",
                lineHeight: 1.5,
              }}
            >
              {s}
            </p>
          </div>
        ))}
      </div>

      {/* Widgets */}
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {result.widgets.map((w, i) => (
          <WidgetRenderer key={i} widget={w} />
        ))}
      </div>

      <DebugAccordion data={result} />
    </div>
  );
};
