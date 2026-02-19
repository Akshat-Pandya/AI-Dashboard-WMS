import React from "react";
import { R } from "@/tokens/brand";

interface Props {
  title: string;
}

export const SectionHeader: React.FC<Props> = ({ title }) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: 12,
      marginBottom: 18,
    }}
  >
    <div
      style={{
        width: 4,
        height: 22,
        background: R.red,
        borderRadius: 2,
        flexShrink: 0,
      }}
    />
    <span
      style={{
        fontFamily: "'Barlow', sans-serif",
        fontSize: 13,
        fontWeight: 700,
        color: R.textPrimary,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
      }}
    >
      {title}
    </span>
  </div>
);
