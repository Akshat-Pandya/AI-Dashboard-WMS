import React from "react";
import { AlertListWidget } from "./widgets/AlertListWidget";
import { TableWidget } from "./widgets/TableWidget";
import { BarChartWidget } from "./widgets/BarChartWidget";
import { LineChartWidget } from "./widgets/LineChartWidget";
import { KPICardsWidget } from "./widgets/KPICardsWidget";
import type { WidgetConfig } from "@/types";

interface Props {
  widgets: WidgetConfig[];
  data: Record<string, unknown>;
}

const WIDGET_MAP: Record<string, React.FC<{ data: any; props?: any }>> = {
  ALERT_LIST:         AlertListWidget,
  TABLE:              TableWidget,
  BAR_CHART:          BarChartWidget,
  ZONE_COMPARE_CHART: BarChartWidget,
  LINE_CHART:         LineChartWidget,
  KPI_CARDS:          KPICardsWidget,
  INBOUND_SUMMARY:    TableWidget,
};

// ─── Dot-path resolver ────────────────────────────────────────────────────────
// Resolves "low_stock.items" → data["low_stock"]["items"]

function resolvePath(obj: Record<string, unknown>, path: string): unknown {
  return path.split(".").reduce<unknown>((acc, key) => {
    if (acc && typeof acc === "object" && !Array.isArray(acc)) {
      return (acc as Record<string, unknown>)[key];
    }
    return undefined;
  }, obj);
}

// ─── Array → TableData transformer ───────────────────────────────────────────
// TableWidget expects { columns: string[], rows: any[][] }
// Backend tools return arrays of objects like { sku, name, zone, quantity, ... }
// This auto-converts so you never have to manually shape data for TABLE widgets.

function toTableData(raw: unknown): { columns: string[]; rows: unknown[][] } | null {
  if (!Array.isArray(raw) || raw.length === 0) return null;
  const first = raw[0];
  if (typeof first !== "object" || first === null) return null;

  const columns = Object.keys(first);
  const rows = raw.map((item) =>
    columns.map((col) => (item as Record<string, unknown>)[col] ?? "—")
  );
  return { columns, rows };
}

// ─── Data adapter per widget type ────────────────────────────────────────────
// Shapes resolved data into what each component actually expects.

function adaptData(type: string, resolved: unknown): unknown {
  switch (type) {
    case "TABLE":
    case "INBOUND_SUMMARY": {
      // Already shaped correctly (has .columns + .rows)
      if (
        resolved &&
        typeof resolved === "object" &&
        "columns" in (resolved as object) &&
        "rows" in (resolved as object)
      ) {
        return resolved;
      }
      // It's an array of objects — auto-convert
      if (Array.isArray(resolved)) {
        return toTableData(resolved) ?? resolved;
      }
      // It's an object with a nested array (e.g. { items: [...] }) — unwrap first array found
      if (resolved && typeof resolved === "object") {
        const obj = resolved as Record<string, unknown>;
        const arrayKey = Object.keys(obj).find((k) => Array.isArray(obj[k]));
        if (arrayKey) return toTableData(obj[arrayKey] as unknown[]) ?? resolved;
      }
      return resolved;
    }

    case "ALERT_LIST": {
      // Expects { alerts: AlertRow[] }
      if (Array.isArray(resolved)) return { alerts: resolved };
      return resolved;
    }

    case "BAR_CHART":
    case "ZONE_COMPARE_CHART": {
      // Pass through — BarChartWidget handles raw arrays or shaped objects
      return resolved;
    }

    case "KPI_CARDS": {
      // Expects { kpis: KPICard[] }
      if (Array.isArray(resolved)) return { kpis: resolved };
      return resolved;
    }

    default:
      return resolved;
  }
}

// ─── Renderer ─────────────────────────────────────────────────────────────────

export const WidgetRenderer: React.FC<Props> = ({ widgets, data }) => {
  if (!widgets || widgets.length === 0) return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      {widgets.map((widget, idx) => {
        const Component = WIDGET_MAP[widget.type];

        if (!Component) {
          console.warn(`[WidgetRenderer] Unknown widget type: "${widget.type}"`);
          return null;
        }

        const resolved = resolvePath(data, widget.data_key);

        if (resolved === undefined) {
          console.warn(
            `[WidgetRenderer] data_key "${widget.data_key}" not found in data`,
            data
          );
          return null;
        }

        const adapted = adaptData(widget.type, resolved);

        return (
          <div key={idx}>
            {widget.title && (
              <h3
                style={{
                  fontFamily: "'Barlow Condensed', sans-serif",
                  fontSize: 14,
                  fontWeight: 700,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  color: "#6B7280",
                  margin: "0 0 10px 0",
                }}
              >
                {widget.title}
              </h3>
            )}
            <Component data={adapted} props={widget.props} />
          </div>
        );
      })}
    </div>
  );
};