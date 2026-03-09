import React, { useEffect, useState } from "react";
import { R } from "@/tokens/brand";

interface Props {
  query: string;
}

export const QueryLoadingState: React.FC<Props> = ({ query }) => {
  const [dots, setDots] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setDots((d) => (d + 1) % 4), 500);
    return () => clearInterval(t);
  }, []);

  const dotStr = "●".repeat(dots) + "○".repeat(3 - dots);

  return (
    <div style={{
      flex: 1,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      background: "#F9FAFB",
      gap: 24,
    }}>

      {/* Spinning ring */}
      <div style={{ position: "relative", width: 56, height: 56 }}>
        {/* Outer ring */}
        <div style={{
          position: "absolute", inset: 0,
          borderRadius: "50%",
          border: `2px solid #E5E7EB`,
        }} />
        {/* Spinning arc */}
        <div style={{
          position: "absolute", inset: 0,
          borderRadius: "50%",
          border: `2px solid transparent`,
          borderTopColor: R.red,
          borderRightColor: R.red,
          animation: "spin 0.9s linear infinite",
        }} />
        {/* Center dot
        <div style={{
          position: "absolute",
          top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          width: 6, height: 6,
          borderRadius: "50%",
          background: R.red,
        }} /> */}
      </div>

      {/* Query text */}
      <div style={{ textAlign: "center", maxWidth: 400, padding: "0 24px" }}>
        <p style={{
          fontFamily: "'Barlow Condensed', sans-serif",
          fontSize: 13, fontWeight: 700,
          color: "#9CA3AF",
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          margin: "0 0 8px",
        }}>
          Analysing
        </p>
        <p style={{
          fontFamily: "'Barlow', sans-serif",
          fontSize: 15, fontWeight: 500,
          color: "#374151",
          margin: 0,
          lineHeight: 1.5,
          overflow: "hidden",
          textOverflow: "ellipsis",
          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
        } as React.CSSProperties}>
          "{query}"
        </p>
      </div>

      {/* Dot rhythm */}
      <p style={{
        fontFamily: "monospace",
        fontSize: 12,
        color: "#D1D5DB",
        letterSpacing: "0.3em",
        margin: 0,
      }}>
        {dotStr}
      </p>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
