import React from "react";
import { R } from "@/tokens/brand";

interface WidgetCardProps {
  title: string;
  children: React.ReactNode;
}

export const WidgetCard: React.FC<WidgetCardProps> = ({ title, children }) => (
  <div
    style={{
      background: R.white,
      border: `1px solid ${R.border}`,
      borderRadius: 4,
      overflow: "hidden",
      boxShadow: "0 1px 6px rgba(0,0,0,0.05)",
    }}
  >
    {/* Card Header */}
    <div
      style={{
        padding: "13px 20px",
        borderBottom: `1px solid ${R.borderLight}`,
        display: "flex",
        alignItems: "center",
        gap: 10,
        background: "#FAFBFC",
      }}
    >
      <div
        style={{
          width: 3,
          height: 16,
          background: R.red,
          borderRadius: 2,
          flexShrink: 0,
        }}
      />
      <span
        style={{
          fontFamily: "'Barlow', sans-serif",
          fontSize: 11,
          fontWeight: 700,
          color: R.textPrimary,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
        }}
      >
        {title}
      </span>
    </div>

    {/* Card Body */}
    <div style={{ padding: "20px" }}>{children}</div>
  </div>
);
