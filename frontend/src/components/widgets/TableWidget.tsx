import React from "react";
import { R } from "@/tokens/brand";
import type { TableData } from "@/types";

interface Props {
  data: TableData;
}

const STATUS_STYLES: Record<string, { bg: string; color: string; border: string }> = {
  Delayed:        { bg: R.redLight,   color: R.red,     border: "#FFB3BB" },
  "Customs Hold": { bg: R.amberLight, color: "#92400E", border: "#FCD34D" },
  "Missing ETA":  { bg: "#F3F4F6",   color: R.midGray, border: R.border  },
  "In Transit":   { bg: "#EFF6FF",   color: "#1D4ED8", border: "#BFDBFE" },
  expected:       { bg: "#EFF6FF",   color: "#1D4ED8", border: "#BFDBFE" },
  receiving:      { bg: "#ECFDF5",   color: "#065F46", border: "#6EE7B7" },
  received:       { bg: "#ECFDF5",   color: "#065F46", border: "#6EE7B7" },
  in_transit:     { bg: "#EFF6FF",   color: "#1D4ED8", border: "#BFDBFE" },
  overdue:        { bg: R.redLight,   color: R.red,     border: "#FFB3BB" },
};

/** Render any cell value safely — handles booleans, null, numbers, strings */
function renderCell(cell: unknown, _colIndex: number): React.ReactNode {
  // ── Null / undefined ─────────────────────────────────────────────────────
  if (cell === null || cell === undefined) {
    return <span style={{ color: R.textMuted, fontSize: 12 }}>—</span>;
  }

  // ── Boolean ───────────────────────────────────────────────────────────────
  if (typeof cell === "boolean") {
    return cell ? (
      <span style={{
        background: "#ECFDF5", color: "#065F46", border: "1px solid #6EE7B7",
        borderRadius: 2, padding: "2px 8px",
        fontSize: 10, fontWeight: 700,
        fontFamily: "'Barlow', sans-serif", letterSpacing: "0.06em",
      }}>
        YES
      </span>
    ) : (
      <span style={{
        background: "#F3F4F6", color: R.midGray, border: `1px solid ${R.border}`,
        borderRadius: 2, padding: "2px 8px",
        fontSize: 10, fontWeight: 700,
        fontFamily: "'Barlow', sans-serif", letterSpacing: "0.06em",
      }}>
        NO
      </span>
    );
  }

  // ── Number ────────────────────────────────────────────────────────────────
  if (typeof cell === "number") {
    return (
      <span style={{
        fontFamily: "'Barlow Condensed', sans-serif",
        fontWeight: 700, fontSize: 15,
        // color: cell < 15 ? R.red : R.textPrimary,
        color: R.textPrimary,

      }}>
        {/* {cell < 15 && <span style={{ marginRight: 3, fontSize: 10 }}>▼</span>} */}
        {cell}
      </span>
    );
  }

  // ── String with status badge ──────────────────────────────────────────────
  if (typeof cell === "string") {
    const statusStyle = STATUS_STYLES[cell];
    if (statusStyle) {
      return (
        <span style={{
          background: statusStyle.bg, color: statusStyle.color,
          border: `1px solid ${statusStyle.border}`,
          borderRadius: 2, padding: "2px 8px",
          fontSize: 10, fontWeight: 700,
          fontFamily: "'Barlow', sans-serif", letterSpacing: "0.06em",
        }}>
          {cell}
        </span>
      );
    }
    return cell;
  }

  // ── Anything else (arrays, objects) ──────────────────────────────────────
  return String(cell);
}

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
                fontSize: 12.5,
                color: R.textPrimary,
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
            {row.map((cell, ci) => (
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
                {renderCell(cell, ci)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
