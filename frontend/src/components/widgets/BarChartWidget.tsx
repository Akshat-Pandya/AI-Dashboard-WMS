import React from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
  type TooltipProps,
} from "recharts";
import { R } from "@/tokens/brand";

interface Props {
  data: unknown;
  props?: Record<string, unknown>;
}

const AUTO_COLORS = [
  "#E8001C", "#3B82F6", "#10B981", "#F59E0B",
  "#8B5CF6", "#EC4899", "#14B8A6", "#F97316",
];

// Human-readable label map for zone summary fields
const FIELD_LABEL: Record<string, string> = {
  total_on_hand:   "On Hand",
  total_available: "Available",
  total_reserved:  "Reserved",
  low_stock_skus:  "Low Stock",
  zero_stock_skus: "Zero Stock",
  total_skus:      "Total SKUs",
  avg_available:   "Avg Available",
  count:           "Count",
};

// ── Normalise any incoming shape into { bars, keys, xKey, colors } ─────────

interface Shaped {
  bars: Record<string, unknown>[];
  keys: string[];
  xKey: string;
  colors: string[];
}

function normalise(raw: unknown): Shaped | null {
  if (!raw || typeof raw !== "object") return null;
  const obj = raw as Record<string, unknown>;

  // ── Already shaped by WidgetRenderer: { bars, keys, colors } ───────────
  // keys may be raw field names (total_skus etc) — remap to FIELD_LABEL
  if (Array.isArray(obj.bars) && Array.isArray(obj.keys) && (obj.bars as unknown[]).length > 0) {
    const rawKeys  = obj.keys as string[];
    const bars     = obj.bars as Record<string, unknown>[];
    const colors   = (obj.colors as string[]) ?? AUTO_COLORS;

    // Detect xKey: first non-numeric key in bars[0] that isn't in rawKeys
    const firstBar = bars[0];
    const xKey =
      (typeof obj.xKey === "string" ? obj.xKey : undefined) ??
      Object.keys(firstBar).find((k) => !rawKeys.includes(k)) ??
      "name";

    // Remap bars: rename raw field keys to FIELD_LABEL versions
    const remappedBars = bars.map((bar) => {
      const out: Record<string, unknown> = { [xKey]: bar[xKey] };
      rawKeys.forEach((k) => {
        const label = FIELD_LABEL[k] ?? k;
        out[label] = bar[k];
      });
      return out;
    });

    const displayKeys = rawKeys.map((k) => FIELD_LABEL[k] ?? k);

    return { bars: remappedBars, keys: displayKeys, xKey, colors };
  }

  // ── Legacy: { zones: [{ zone, total_on_hand, ... }] } ──────────────────
  // Also handles direct zone array where values may be strings ("393")
  if (Array.isArray(obj.zones) && (obj.zones as unknown[]).length > 0) {
    const zones = obj.zones as Record<string, unknown>[];
    if (typeof zones[0].zone === "string") {
      const numericKeys = Object.keys(zones[0]).filter((k) => {
        if (k === "zone") return false;
        const v = zones[0][k];
        if (typeof v === "number") return true;
        if (typeof v === "string" && v.trim() !== "" && !isNaN(Number(v))) return true;
        return false;
      });
      const displayKeys = numericKeys.map((k) => FIELD_LABEL[k] ?? k);
      const bars = zones.map((z) => {
        const out: Record<string, unknown> = { zone: z.zone };
        numericKeys.forEach((k, i) => { out[displayKeys[i]] = Number(z[k]); });
        return out;
      });
      return { bars, keys: displayKeys, xKey: "zone", colors: AUTO_COLORS.slice(0, displayKeys.length) };
    }
  }

  return null;
}

// ── Tooltip ───────────────────────────────────────────────────────────────────
const CustomTooltip: React.FC<TooltipProps<number, string>> = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: R.white, border: `1px solid ${R.border}`,
      borderRadius: 3, padding: "10px 14px",
      boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
      fontFamily: "'Barlow', sans-serif",
    }}>
      <p style={{
        fontSize: 10, fontWeight: 700, color: R.textSecondary,
        marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.08em",
      }}>
        {label}
      </p>
      {payload.map((p, i) => (
        <p key={i} style={{ fontSize: 13, fontWeight: 600, marginBottom: 2 }}>
          <span style={{ color: p.fill }}>{p.name}</span>
          <span style={{ color: R.textPrimary }}>{": "}{(p.value ?? 0).toLocaleString()}</span>
        </p>
      ))}
    </div>
  );
};

// ── Component ─────────────────────────────────────────────────────────────────
export const BarChartWidget: React.FC<Props> = ({ data }) => {
  const shaped = normalise(data);

  if (!shaped || shaped.bars.length === 0) {
    return (
      <p style={{ color: R.textMuted, fontSize: 13, fontFamily: "'Barlow', sans-serif" }}>
        No chart data available.
      </p>
    );
  }

  const { bars, keys, xKey, colors } = shaped;

  // Scale height with number of metrics so bars don't get too cramped
  const chartHeight = keys.length > 3 ? 320 : 260;

  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <BarChart
        data={bars}
        margin={{ top: 8, right: 8, left: -10, bottom: 0 }}
        barCategoryGap="30%"
        barGap={3}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={R.borderLight} vertical={false} />
        <XAxis
          dataKey={xKey}
          tick={{ fontSize: 12, fill: R.textSecondary, fontFamily: "'Barlow', sans-serif", fontWeight: 600 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: R.textMuted, fontFamily: "'Barlow', sans-serif" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(0,0,0,0.04)" }} />
        <Legend
          wrapperStyle={{
            fontSize: 12, fontFamily: "'Barlow', sans-serif",
            paddingTop: 12, fontWeight: 600,
          }}
        />
        {keys.map((key, i) => (
          <Bar
            key={key}
            dataKey={key}
            fill={colors[i] ?? AUTO_COLORS[i % AUTO_COLORS.length]}
            radius={[3, 3, 0, 0]}
            maxBarSize={48}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
};