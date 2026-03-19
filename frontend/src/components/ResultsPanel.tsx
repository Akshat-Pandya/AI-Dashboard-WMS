import React from "react";
import { R } from "@/tokens/brand";

export const ResultsPanel: React.FC = () => (
  <div
    style={{
      flex: 1,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: R.bg,
      flexDirection: "column",
      gap: 24,
      position: "relative",
      overflow: "hidden",
    }}
  >
    {/* Background watermark */}
    <div
      style={{
        position: "absolute",
        fontFamily: "'Barlow Condensed', sans-serif",
        fontSize: "18vw",
        fontWeight: 800,
        color: "rgba(232,0,28,0.04)",
        letterSpacing: "0.04em",
        userSelect: "none",
        whiteSpace: "nowrap",
        pointerEvents: "none",
      }}
    >
      ADDVERB
    </div>

    {/* Central message */}
    <div style={{ textAlign: "center", position: "relative" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          justifyContent: "center",
          marginBottom: 16,
        }}
      >
        <div style={{ height: 2, width: 40, background: R.red }} />
        <span
          style={{
            fontFamily: "'Barlow', sans-serif",
            fontSize: 11,
            fontWeight: 700,
            color: R.textMuted,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
          }}
        >
          WMS Intelligence
        </span>
        <div style={{ height: 2, width: 40, background: R.red }} />
      </div>

      <p
        style={{
          fontFamily: "'Barlow Condensed', sans-serif",
          fontSize: 28,
          color: R.textPrimary,
          margin: 0,
          fontWeight: 700,
        }}
      >
        Ask a question to generate
      </p>
      <p
        style={{
          fontFamily: "'Barlow Condensed', sans-serif",
          fontSize: 28,
          color: R.red,
          margin: "0 0 12px",
          fontWeight: 700,
        }}
      >
        warehouse insights
      </p>
      <p
        style={{
          fontFamily: "'Barlow', sans-serif",
          fontSize: 12,
          color: R.textMuted,
          margin: 0,
        }}
      >
        Multi-intent analysis · Generative UI · Real-time data
      </p>
    </div>

    {/* Stats row */}
    <div style={{ display: "flex", gap: 32, position: "relative" }}>
      {[
        ["350+", "Clients Globally"],
        ["500+", "Warehouses Automated"],
        ["24/7", "Support"],
      ].map(([val, label], i) => (
        <div key={i} style={{ textAlign: "center" }}>
          <p
            style={{
              fontFamily: "'Barlow Condensed', sans-serif",
              fontSize: 28,
              fontWeight: 800,
              color: R.red,
              margin: "0 0 2px",
            }}
          >
            {val}
          </p>
          <p
            style={{
              fontFamily: "'Barlow', sans-serif",
              fontSize: 10,
              fontWeight: 700,
              color: R.textMuted,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              margin: 0,
            }}
          >
            {label}
          </p>
        </div>
      ))}
    </div>
  </div>
);