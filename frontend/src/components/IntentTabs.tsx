import React from "react";
import { R } from "@/tokens/brand";

interface Props {
  tabs: string[];
  activeTab: number;
  onTabChange: (index: number) => void;
}

export const IntentTabs: React.FC<Props> = ({ tabs, activeTab, onTabChange }) => (
  <div
    style={{
      background: R.white,
      borderBottom: `1px solid ${R.border}`,
      padding: "0 24px",
      display: "flex",
      flexShrink: 0,
    }}
  >
    {tabs.map((tab, i) => (
      <button
        key={i}
        onClick={() => onTabChange(i)}
        style={{
          padding: "12px 18px",
          border: "none",
          borderBottom:
            activeTab === i ? `3px solid ${R.red}` : "3px solid transparent",
          background: "transparent",
          cursor: "pointer",
          fontFamily: "'Barlow', sans-serif",
          fontSize: 11,
          fontWeight: activeTab === i ? 800 : 600,
          color: activeTab === i ? R.red : R.textMuted,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          transition: "all 0.15s ease",
        }}
      >
        {tab}
      </button>
    ))}
  </div>
);
