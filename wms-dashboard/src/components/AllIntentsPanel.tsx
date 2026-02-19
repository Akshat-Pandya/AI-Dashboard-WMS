import React from "react";
import { R } from "@/tokens/brand";
import { SectionHeader } from "./SectionHeader";
import type { ChatResponse } from "@/types";

interface Props {
  response: ChatResponse;
}

export const AllIntentsPanel: React.FC<Props> = ({ response }) => (
  <div>
    <SectionHeader title="Candidate Intents Detected" />

    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {response.candidates.map((c, i) => {
        const result = response.resultsByIntent.find((r) => r.intent === c.name);
        const isSelected = c.name === response.selectedIntent;
        const pct = Math.round(c.confidence * 100);
        const confidenceColor = pct > 70 ? R.green : pct > 40 ? R.amber : R.red;

        return (
          <div
            key={i}
            style={{
              background: R.white,
              border: `1px solid ${isSelected ? R.red : R.border}`,
              borderLeft: `5px solid ${isSelected ? R.red : R.border}`,
              borderRadius: 4,
              padding: "18px 20px",
              boxShadow: isSelected
                ? "0 2px 16px rgba(232,0,28,0.08)"
                : "0 1px 4px rgba(0,0,0,0.04)",
            }}
          >
            {/* Header row */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                marginBottom: 12,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span
                  style={{
                    fontFamily: "'Barlow Condensed', sans-serif",
                    fontSize: 18,
                    fontWeight: 800,
                    color: isSelected ? R.red : R.textPrimary,
                    letterSpacing: "0.04em",
                  }}
                >
                  {c.name}
                </span>
                {isSelected && (
                  <span
                    style={{
                      background: R.red,
                      color: "#fff",
                      fontFamily: "'Barlow', sans-serif",
                      fontSize: 9,
                      fontWeight: 800,
                      padding: "2px 7px",
                      borderRadius: 2,
                      letterSpacing: "0.1em",
                    }}
                  >
                    SELECTED
                  </span>
                )}
              </div>

              <span
                style={{
                  fontFamily: "'Barlow Condensed', sans-serif",
                  fontSize: 28,
                  fontWeight: 800,
                  color: confidenceColor,
                  lineHeight: 1,
                }}
              >
                {pct}%
              </span>
            </div>

            {/* Confidence bar */}
            <div
              style={{
                background: R.bg,
                borderRadius: 2,
                height: 5,
                marginBottom: 14,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  height: "100%",
                  borderRadius: 2,
                  width: `${pct}%`,
                  background: confidenceColor,
                  transition: "width 1s cubic-bezier(0.4,0,0.2,1)",
                }}
              />
            </div>

            {/* Tools */}
            {result && (
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {result.toolsExecuted.map((t, j) => (
                  <span
                    key={j}
                    style={{
                      fontFamily: "'Barlow', sans-serif",
                      fontSize: 10,
                      fontWeight: 600,
                      background: R.bg,
                      color: R.textSecondary,
                      border: `1px solid ${R.border}`,
                      borderRadius: 2,
                      padding: "2px 8px",
                    }}
                  >
                    {t}
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  </div>
);
