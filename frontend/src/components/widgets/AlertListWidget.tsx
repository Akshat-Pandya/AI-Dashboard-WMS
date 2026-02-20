import React from "react";
import { R } from "@/tokens/brand";
import type { AlertListData, AlertSeverity } from "@/types";

interface Props {
  data: AlertListData;
}

const ALERT_CFG: Record<AlertSeverity, { bg: string; border: string; stripe: string; text: string }> = {
  CRITICAL: { bg: R.redLight,    border: "#FFB3BB", stripe: R.red,    text: R.red      },
  HIGH:     { bg: R.amberLight,  border: "#FCD34D", stripe: R.amber,  text: "#92400E"  },
  MEDIUM:   { bg: "#EFF6FF",     border: "#BFDBFE", stripe: "#3B82F6",text: "#1D4ED8"  },
};

export const AlertListWidget: React.FC<Props> = ({ data }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
    {data.alerts.map((alert, i) => {
      const cfg = ALERT_CFG[alert.severity] ?? ALERT_CFG.MEDIUM;
      return (
        <div
          key={i}
          style={{
            display: "flex",
            alignItems: "stretch",
            background: cfg.bg,
            border: `1px solid ${cfg.border}`,
            borderRadius: 3,
            overflow: "hidden",
          }}
        >
          {/* Left severity stripe */}
          <div style={{ width: 4, background: cfg.stripe, flexShrink: 0 }} />

          <div style={{ flex: 1, padding: "12px 16px" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 5,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                {/* Severity badge */}
                <span
                  style={{
                    background: cfg.stripe,
                    color: "#fff",
                    fontFamily: "'Barlow', sans-serif",
                    fontSize: 9,
                    fontWeight: 800,
                    padding: "2px 7px",
                    borderRadius: 2,
                    letterSpacing: "0.1em",
                  }}
                >
                  {alert.severity}
                </span>
                <span
                  style={{
                    fontFamily: "'Barlow Condensed', sans-serif",
                    fontSize: 13,
                    fontWeight: 700,
                    color: cfg.text,
                    letterSpacing: "0.04em",
                  }}
                >
                  {alert.id}
                </span>
              </div>

              <span
                style={{
                  fontFamily: "'Barlow', sans-serif",
                  fontSize: 11,
                  color: R.textMuted,
                  fontWeight: 600,
                }}
              >
                {alert.time}
              </span>
            </div>

            <p
              style={{
                margin: 0,
                fontSize: 13,
                color: R.textPrimary,
                fontFamily: "'Barlow', sans-serif",
                lineHeight: 1.4,
              }}
            >
              {alert.message}
            </p>
          </div>
        </div>
      );
    })}
  </div>
);
