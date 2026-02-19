import React from "react";
import { R } from "@/tokens/brand";
import type { TableData } from "@/types";

interface Props {
  data: TableData;
}

const STATUS_STYLES: Record<string, { bg: string; color: string; border: string }> = {
  Delayed:       { bg: R.redLight,    color: R.red,      border: "#FFB3BB" },
  "Customs Hold":{ bg: R.amberLight,  color: "#92400E",  border: "#FCD34D" },
  "Missing ETA": { bg: "#F3F4F6",     color: R.midGray,  border: R.border  },
  "In Transit":  { bg: "#EFF6FF",     color: "#1D4ED8",  border: "#BFDBFE" },
};

export const TableWidget: React.FC<Props> = ({ data }) => (
  <div style={{ overflowX: "auto", margin: "-20px" }}>
    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
      <thead>
        <tr style={{ background: R.bg }}>
          {data.columns.map((col, i) => (
            <th
              key={i}
              style={{
                textAlign: "left",
                padding: "10px 20px",
                fontFamily: "'Barlow', sans-serif",
                fontWeight: 700,
                fontSize: 10,
                color: R.textMuted,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                borderBottom: `2px solid ${R.border}`,
                whiteSpace: "nowrap",
              }}
            >
              {col}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.rows.map((row, ri) => (
          <tr
            key={ri}
            style={{ borderBottom: `1px solid ${R.borderLight}`, transition: "background 0.1s" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = R.bg)}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          >
            {row.map((cell, ci) => {
              const isNum = typeof cell === "number";
              const statusStyle = typeof cell === "string" ? STATUS_STYLES[cell] : undefined;

              return (
                <td
                  key={ci}
                  style={{
                    padding: "10px 20px",
                    fontFamily: ci === 0 ? "'Barlow Condensed', sans-serif" : "'Barlow', sans-serif",
                    fontSize: 13,
                    color: R.textPrimary,
                    whiteSpace: "nowrap",
                    fontWeight: ci === 0 ? 700 : 400,
                    letterSpacing: ci === 0 ? "0.04em" : 0,
                  }}
                >
                  {isNum ? (
                    <span
                      style={{
                        fontFamily: "'Barlow Condensed', sans-serif",
                        fontWeight: 700,
                        fontSize: 15,
                        color: (cell as number) < 15 ? R.red : R.textPrimary,
                      }}
                    >
                      {(cell as number) < 15 && (
                        <span style={{ marginRight: 3, fontSize: 10 }}>▼</span>
                      )}
                      {cell}
                    </span>
                  ) : statusStyle ? (
                    <span
                      style={{
                        background: statusStyle.bg,
                        color: statusStyle.color,
                        border: `1px solid ${statusStyle.border}`,
                        borderRadius: 2,
                        padding: "2px 8px",
                        fontSize: 10,
                        fontWeight: 700,
                        fontFamily: "'Barlow', sans-serif",
                        letterSpacing: "0.06em",
                      }}
                    >
                      {cell}
                    </span>
                  ) : (
                    cell
                  )}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
