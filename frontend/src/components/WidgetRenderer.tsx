import React from "react";
import { AlertListWidget } from "./widgets/AlertListWidget";
import { TableWidget } from "./widgets/TableWidget";
import { BarChartWidget } from "./widgets/BarChartWidget";
import { LineChartWidget } from "./widgets/LineChartWidget";
import { KPICardsWidget } from "./widgets/KPICardsWidget";
import { OverviewPanelWidget } from "./widgets/OverviewPanelWidget"; // ← NEW
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
  OVERVIEW_PANEL:     OverviewPanelWidget, // ← NEW — was missing, caused blank render
};

const CHART_COLORS = [
  "#E8001C", "#3B82F6", "#10B981", "#F59E0B",
  "#8B5CF6", "#EC4899", "#06B6D4", "#84CC16",
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function resolvePath(obj: Record<string, unknown>, path: string): unknown {
  const parts = path.split(".");

  // Try full path first
  const full = parts.reduce<unknown>((acc, key) => {
    if (acc && typeof acc === "object" && !Array.isArray(acc)) {
      return (acc as Record<string, unknown>)[key];
    }
    return undefined;
  }, obj);

  if (full !== undefined) return full;

  // If full path failed and has 3+ parts, fall back to parent path
  if (parts.length >= 3) {
    const parentPath = parts.slice(0, -1).join(".");
    const parent = parentPath.split(".").reduce<unknown>((acc, key) => {
      if (acc && typeof acc === "object" && !Array.isArray(acc)) {
        return (acc as Record<string, unknown>)[key];
      }
      return undefined;
    }, obj);

    if (parent !== undefined) {
      console.warn(`[WidgetRenderer] "${path}" not found — falling back to "${parentPath}"`);
      return parent;
    }
  }

  return undefined;
}

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

function isNumericValue(v: unknown): boolean {
  if (typeof v === "number") return true;
  if (typeof v === "string" && v.trim() !== "" && !isNaN(Number(v))) return true;
  return false;
}

/**
 * Converts array of objects → BarChartData.
 * Handles numeric values stored as strings (common from MySQL).
 */
function toBarChartData(
  raw: unknown[],
  propsKeys?: string[]
): { bars: unknown[]; keys: string[]; colors: string[] } | null {
  if (raw.length === 0) return null;
  const first = raw[0];
  if (typeof first !== "object" || first === null) return null;

  const allKeys = Object.keys(first as object);

  const numericKeys = allKeys.filter((k) => {
    const val = (first as Record<string, unknown>)[k];
    return isNumericValue(val);
  });

  const keys = propsKeys ?? numericKeys;

  if (keys.length === 0) {
    const fallbackKeys = allKeys.slice(1);
    const colors = fallbackKeys.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]);
    return { bars: raw, keys: fallbackKeys, colors };
  }

  const bars = raw.map((item) => {
    const obj = { ...(item as Record<string, unknown>) };
    keys.forEach((k) => {
      if (typeof obj[k] === "string") obj[k] = Number(obj[k]);
    });
    return obj;
  });

  const colors = keys.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]);
  return { bars, keys, colors };
}

// ─── Data adapter ─────────────────────────────────────────────────────────────

function adaptData(type: string, resolved: unknown, props?: Record<string, unknown>): unknown {
  switch (type) {

    case "TABLE":
    case "INBOUND_SUMMARY": {
      if (
        resolved &&
        typeof resolved === "object" &&
        "columns" in (resolved as object) &&
        "rows" in (resolved as object)
      ) return resolved;
      if (Array.isArray(resolved)) return toTableData(resolved) ?? resolved;
      if (resolved && typeof resolved === "object") {
        const obj = resolved as Record<string, unknown>;
        const arrayKey = Object.keys(obj).find((k) => Array.isArray(obj[k]));
        if (arrayKey) return toTableData(obj[arrayKey] as unknown[]) ?? resolved;
      }
      return resolved;
    }

    case "ALERT_LIST": {
      if (Array.isArray(resolved)) return { alerts: resolved };
      return resolved;
    }

    case "BAR_CHART":
    case "ZONE_COMPARE_CHART": {
      if (
        resolved &&
        typeof resolved === "object" &&
        !Array.isArray(resolved) &&
        "bars" in (resolved as object) &&
        "keys" in (resolved as object) &&
        Array.isArray((resolved as any).keys)
      ) return resolved;

      const propsKeys = Array.isArray(props?.keys) ? (props!.keys as string[]) : undefined;

      if (Array.isArray(resolved)) {
        return toBarChartData(resolved, propsKeys) ?? resolved;
      }
      if (resolved && typeof resolved === "object") {
        const obj = resolved as Record<string, unknown>;
        const arrayKey = Object.keys(obj).find((k) => Array.isArray(obj[k]));
        if (arrayKey) return toBarChartData(obj[arrayKey] as unknown[], propsKeys) ?? resolved;
      }
      return resolved;
    }

    case "LINE_CHART": {
      if (
        resolved &&
        typeof resolved === "object" &&
        !Array.isArray(resolved) &&
        "points" in (resolved as object) &&
        "keys" in (resolved as object) &&
        Array.isArray((resolved as any).keys)
      ) return resolved;

      const propsKeys = Array.isArray(props?.keys) ? (props!.keys as string[]) : undefined;

      const toLineData = (arr: unknown[]) => {
        if (arr.length === 0) return null;
        const first = arr[0] as Record<string, unknown>;
        const allKeys = Object.keys(first);
        const numericKeys = propsKeys ?? allKeys.filter((k) => {
          const v = first[k];
          if (typeof v === "boolean") return false;
          if (typeof v === "number") return true;
          if (typeof v === "string" && v.trim() !== "" && !isNaN(Number(v))) return true;
          return false;
        });
        if (numericKeys.length === 0) return null;
        const dateKey = allKeys.find(
          (k) => typeof first[k] === "string" && /date|time|timestamp|created|updated/i.test(k)
        );
        let points: unknown[] = dateKey
          ? [...arr].sort((a, b) => {
              const av = (a as Record<string, unknown>)[dateKey] as string;
              const bv = (b as Record<string, unknown>)[dateKey] as string;
              return av < bv ? -1 : av > bv ? 1 : 0;
            })
          : arr;
        points = points.map((item) => {
          const obj = { ...(item as Record<string, unknown>) };
          numericKeys.forEach((k) => { if (typeof obj[k] === "string") obj[k] = Number(obj[k]); });
          return obj;
        });
        return {
          points,
          keys: numericKeys,
          colors: numericKeys.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]),
        };
      };

      if (Array.isArray(resolved)) {
        const r = toLineData(resolved);
        if (r) return r;
      }
      if (resolved && typeof resolved === "object") {
        const obj = resolved as Record<string, unknown>;
        const arrayKey = Object.keys(obj).find((k) => Array.isArray(obj[k]));
        if (arrayKey) {
          const r = toLineData(obj[arrayKey] as unknown[]);
          if (r) return r;
        }
      }
      return { points: [], keys: [], colors: [] };
    }

    case "KPI_CARDS": {
      if (resolved && typeof resolved === "object" && !Array.isArray(resolved)) return resolved;
      if (Array.isArray(resolved)) return { kpis: resolved };
      return resolved;
    }

    // ── OVERVIEW_PANEL ─────────────────────────────────────────────────────────
    // The backend sends a nested object:
    //   { inventory: {...}, orders: {...}, tasks: {...}, alerts: {...}, kpis: {...}, zones: {...} }
    // OverviewPanelWidget reads it directly — no transformation needed.
    // We still validate it's an object and not an accidental array.
    case "OVERVIEW_PANEL": {
      if (resolved && typeof resolved === "object" && !Array.isArray(resolved)) {
        return resolved; // pass through as-is — OverviewPanelWidget handles the shape
      }
      // Shouldn't happen, but guard gracefully
      console.warn("[WidgetRenderer] OVERVIEW_PANEL received unexpected data shape:", resolved);
      return {};
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

        const adapted = adaptData(widget.type, resolved, widget.props);

        return (
          <div key={idx}>
            {widget.title && (
              <h3 style={{
                fontFamily: "'Barlow Condensed', sans-serif",
                fontSize: 14,
                fontWeight: 700,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                color: "#6B7280",
                margin: "0 0 10px 0",
              }}>
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