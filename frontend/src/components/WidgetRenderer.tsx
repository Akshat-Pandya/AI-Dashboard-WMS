import React from "react";
import { AlertListWidget }   from "./widgets/AlertListWidget";
import { TableWidget }       from "./widgets/TableWidget";
import { BarChartWidget }    from "./widgets/BarChartWidget";
import { LineChartWidget }   from "./widgets/LineChartWidget";
import { KPICardsWidget }    from "./widgets/KPICardsWidget";
import { OverviewPanelWidget } from "./widgets/OverviewPanelWidget";
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
  OVERVIEW_PANEL:     OverviewPanelWidget,
};

const CHART_COLORS = [
  "#E8001C", "#3B82F6", "#10B981", "#F59E0B",
  "#8B5CF6", "#EC4899", "#06B6D4", "#84CC16",
];

const STATUS_COLORS: Record<string, string> = {
  pending:   "#F59E0B",
  picking:   "#3B82F6",
  packed:    "#8B5CF6",
  shipped:   "#10B981",
  cancelled: "#E8001C",
  completed: "#10B981",
  blocked:   "#E8001C",
  active:    "#3B82F6",
};

// ─── resolvePath ──────────────────────────────────────────────────────────────

function resolvePath(obj: Record<string, unknown>, path: string): unknown {
  const parts = path.split(".");

  const full = parts.reduce<unknown>((acc, key) => {
    if (acc && typeof acc === "object" && !Array.isArray(acc))
      return (acc as Record<string, unknown>)[key];
    return undefined;
  }, obj);

  if (full !== undefined) return full;

  // 3-part path fallback
  if (parts.length >= 3) {
    const parentPath = parts.slice(0, -1).join(".");
    const parent = parentPath.split(".").reduce<unknown>((acc, key) => {
      if (acc && typeof acc === "object" && !Array.isArray(acc))
        return (acc as Record<string, unknown>)[key];
      return undefined;
    }, obj);
    if (parent !== undefined) {
      console.warn(`[WidgetRenderer] "${path}" not found — falling back to "${parentPath}"`);
      return parent;
    }
  }

  return undefined;
}

// ─── Table ────────────────────────────────────────────────────────────────────

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

// ─── Bar chart ────────────────────────────────────────────────────────────────

function isNumericValue(v: unknown): boolean {
  if (typeof v === "number") return true;
  if (typeof v === "string" && v.trim() !== "" && !isNaN(Number(v))) return true;
  return false;
}

function toBarChartData(
  raw: unknown[],
  propsKeys?: string[]
): { bars: unknown[]; keys: string[]; colors: string[] } | null {
  if (raw.length === 0) return null;
  const first = raw[0];
  if (typeof first !== "object" || first === null) return null;

  const allKeys     = Object.keys(first as object);
  const numericKeys = allKeys.filter((k) => isNumericValue((first as Record<string, unknown>)[k]));
  const keys        = propsKeys ?? numericKeys;

  if (keys.length === 0) {
    const fallbackKeys = allKeys.slice(1);
    return { bars: raw, keys: fallbackKeys, colors: fallbackKeys.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]) };
  }

  const bars = raw.map((item) => {
    const obj = { ...(item as Record<string, unknown>) };
    keys.forEach((k) => { if (typeof obj[k] === "string") obj[k] = Number(obj[k]); });
    return obj;
  });

  return { bars, keys, colors: keys.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]) };
}

function numericObjectToBars(
  obj: Record<string, unknown>
): { bars: unknown[]; keys: string[]; colors: string[] } | null {
  const entries = Object.entries(obj);
  if (entries.length === 0) return null;
  if (!entries.every(([, v]) => typeof v === "number" || (typeof v === "string" && !isNaN(Number(v)))))
    return null;
  const bars   = entries.map(([name, value]) => ({ name, count: Number(value) }));
  const colors = bars.map((b) => STATUS_COLORS[(b as any).name] ?? CHART_COLORS[0]);
  return { bars, keys: ["count"], colors };
}

/**
 * Zone compare: tool returns { zones: string[], summary: ZoneInventorySummary[] }
 * We use `summary` (has per-zone numeric metrics), NOT `zones` (just name strings).
 * Each row: { zone, total_skus, total_on_hand, total_available, low_stock_skus, zero_stock_skus }
 */
function zoneCompareToBarData(
  obj: Record<string, unknown>
): { bars: unknown[]; keys: string[]; colors: string[] } | null {
  // Accept obj.zones (actual tool output) OR obj.summary (legacy)
  const rows = Array.isArray(obj.zones) ? obj.zones
             : Array.isArray(obj.summary) ? obj.summary
             : null;
  if (!rows || rows.length === 0) return null;

  const first   = rows[0] as Record<string, unknown>;
  const allKeys = Object.keys(first);

  // Coerce strings to numbers — backend serialises aggregated fields as strings ("393")
  const numericKeys = allKeys.filter((k) => {
    if (k === "zone") return false;
    const v = first[k];
    if (typeof v === "number") return true;
    if (typeof v === "string" && v.trim() !== "" && !isNaN(Number(v))) return true;
    return false;
  });

  if (numericKeys.length === 0) return null;

  const bars = rows.map((item: any) => {
    const row: Record<string, unknown> = { zone: item.zone ?? "?" };
    numericKeys.forEach((k) => { row[k] = Number(item[k]); });
    return row;
  });

  return { bars, keys: numericKeys, colors: numericKeys.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]) };
}

// ─── adaptData ────────────────────────────────────────────────────────────────

function adaptData(
  type: string,
  resolved: unknown,
  props?: Record<string, unknown>
): unknown {
  switch (type) {

    case "TABLE":
    case "INBOUND_SUMMARY": {
      if (resolved && typeof resolved === "object" && "columns" in (resolved as object) && "rows" in (resolved as object))
        return resolved;
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

    case "BAR_CHART": {
      if (resolved && typeof resolved === "object" && !Array.isArray(resolved) &&
          "bars" in (resolved as object) && "keys" in (resolved as object) &&
          Array.isArray((resolved as any).keys))
        return resolved;

      const propsKeys = Array.isArray(props?.keys) ? (props!.keys as string[]) : undefined;

      if (Array.isArray(resolved)) return toBarChartData(resolved, propsKeys) ?? resolved;

      if (resolved && typeof resolved === "object") {
        const obj = resolved as Record<string, unknown>;

        const directNumeric = numericObjectToBars(obj);
        if (directNumeric) return directNumeric;

        if (obj.by_status && typeof obj.by_status === "object" && !Array.isArray(obj.by_status)) {
          const nested = numericObjectToBars(obj.by_status as Record<string, unknown>);
          if (nested) return nested;
        }

        const arrayKey = Object.keys(obj).find((k) => Array.isArray(obj[k]));
        if (arrayKey) return toBarChartData(obj[arrayKey] as unknown[], propsKeys) ?? resolved;
      }

      return resolved;
    }

    // Zone compare MUST use the `summary` sub-array, not `zones` (which is just names)
    case "ZONE_COMPARE_CHART": {
      if (resolved && typeof resolved === "object" && !Array.isArray(resolved) &&
          "bars" in (resolved as object) && "keys" in (resolved as object) &&
          Array.isArray((resolved as any).keys))
        return resolved;

      if (resolved && typeof resolved === "object" && !Array.isArray(resolved)) {
        const result = zoneCompareToBarData(resolved as Record<string, unknown>);
        if (result) return result;
      }

      if (Array.isArray(resolved)) {
        const propsKeys = Array.isArray(props?.keys) ? (props!.keys as string[]) : undefined;
        return toBarChartData(resolved, propsKeys) ?? resolved;
      }

      return resolved;
    }

    case "LINE_CHART": {
      if (resolved && typeof resolved === "object" && !Array.isArray(resolved) &&
          "points" in (resolved as object) && "keys" in (resolved as object) &&
          Array.isArray((resolved as any).keys))
        return resolved;

      const propsKeys = Array.isArray(props?.keys) ? (props!.keys as string[]) : undefined;

      const toLineData = (arr: unknown[]) => {
        if (arr.length === 0) return null;
        const first   = arr[0] as Record<string, unknown>;
        const allKeys = Object.keys(first);

        const numericKeys = propsKeys ?? allKeys.filter((k) => {
          const v = first[k];
          if (typeof v === "boolean") return false;
          if (typeof v === "number")  return true;
          if (typeof v === "string" && v.trim() !== "" && !isNaN(Number(v))) return true;
          return false;
        });

        if (numericKeys.length === 0) return null;

        // Prefer a field literally named "date", then fall back to any date-like name
        const dateKey =
          allKeys.find((k) => k === "date") ??
          allKeys.find((k) => /date|time|timestamp|created|updated/i.test(k) && typeof first[k] === "string");

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
          keys:   numericKeys,
          colors: numericKeys.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]),
          xKey:   dateKey,  // passed through to LineChartWidget
        };
      };

      if (Array.isArray(resolved)) {
        const r = toLineData(resolved);
        if (r) return r;
      }

      if (resolved && typeof resolved === "object") {
        const obj      = resolved as Record<string, unknown>;
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

    case "OVERVIEW_PANEL": {
      if (resolved && typeof resolved === "object" && !Array.isArray(resolved)) return resolved;
      console.warn("[WidgetRenderer] OVERVIEW_PANEL unexpected shape:", resolved);
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
          console.warn(`[WidgetRenderer] data_key "${widget.data_key}" not found in data`, data);
          return null;
        }

        const adapted = adaptData(widget.type, resolved, widget.props as Record<string, unknown>);

        return (
          <div key={idx}>
            {widget.title && (
              <h3 style={{
                fontFamily:    "'Barlow Condensed', sans-serif",
                fontSize:      14,
                fontWeight:    700,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                color:         "#6B7280",
                margin:        "0 0 10px 0",
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