// components/widgets/OverviewPanelWidget.tsx
//
// Renders the warehouse_overview intent data.
// Data shape received (data_key = "overview"):
// {
//   inventory: { total_skus, low_stock_items, zero_stock_items }
//   orders:    { orders_by_status: { pending, processing, shipped, ... }, stuck_orders }
//   tasks:     { active_tasks, blocked_tasks }
//   alerts:    { unacknowledged_critical_alerts }
//   kpis:      { kpis: [{ label, value, unit, trend, is_on_target }] }
//   zones:     { zones_near_capacity: string[] }
// }

import React from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface KPIItem {
  label: string;
  value: number | string;
  unit?: string;
  trend?: "up" | "down" | "stable";
  is_on_target?: boolean;
}

interface OverviewData {
  inventory?: {
    total_skus?: number;
    low_stock_items?: number;
    zero_stock_items?: number;
  };
  orders?: {
    orders_by_status?: Record<string, number>;
    stuck_orders?: number;
  };
  tasks?: {
    active_tasks?: number;
    blocked_tasks?: number;
  };
  alerts?: {
    unacknowledged_critical_alerts?: number;
  };
  kpis?: {
    kpis?: KPIItem[];
  };
  zones?: {
    zones_near_capacity?: string[];
  };
}

interface Props {
  data: OverviewData | null | undefined;
  props?: Record<string, unknown>;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function num(v: number | string | undefined, fallback = 0): number {
  if (v === undefined || v === null) return fallback;
  const n = Number(v);
  return isNaN(n) ? fallback : n;
}

function TrendArrow({ trend }: { trend?: string }) {
  if (trend === "up")
    return <span style={{ color: "#10B981", fontSize: 12, marginLeft: 4 }}>▲</span>;
  if (trend === "down")
    return <span style={{ color: "#E8001C", fontSize: 12, marginLeft: 4 }}>▼</span>;
  return <span style={{ color: "#6B7280", fontSize: 12, marginLeft: 4 }}>—</span>;
}

// ─── Sub-sections ─────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  accent,
  sub,
}: {
  label: string;
  value: number | string;
  accent?: string;
  sub?: string;
}) {
  return (
    <div
      style={{
        background: "#111827",
        border: "1px solid #1F2937",
        borderRadius: 8,
        padding: "14px 18px",
        minWidth: 120,
        flex: 1,
      }}
    >
      <div
        style={{
          fontFamily: "'Barlow Condensed', sans-serif",
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          color: "#6B7280",
          marginBottom: 6,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: "'Barlow Condensed', sans-serif",
          fontSize: 28,
          fontWeight: 700,
          color: accent ?? "#F9FAFB",
          lineHeight: 1,
        }}
      >
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 11, color: "#6B7280", marginTop: 4 }}>
          {sub}
        </div>
      )}
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontFamily: "'Barlow Condensed', sans-serif",
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: "0.12em",
        textTransform: "uppercase",
        color: "#4B5563",
        marginBottom: 8,
        marginTop: 20,
        borderBottom: "1px solid #1F2937",
        paddingBottom: 4,
      }}
    >
      {children}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export const OverviewPanelWidget: React.FC<Props> = ({ data }) => {
  // Guard: handle null/undefined or non-object gracefully
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return (
      <div style={{ color: "#6B7280", fontSize: 13, padding: 16 }}>
        No overview data available.
      </div>
    );
  }

  const inv    = data.inventory   ?? {};
  const orders = data.orders      ?? {};
  const tasks  = data.tasks       ?? {};
  const alerts = data.alerts      ?? {};
  const kpis   = data.kpis?.kpis  ?? [];
  const zones  = data.zones?.zones_near_capacity ?? [];

  const totalOrders = Object.values(orders.orders_by_status ?? {}).reduce(
    (s, v) => s + num(v),
    0
  );

  const criticalAlerts = num(alerts.unacknowledged_critical_alerts);
  const blockedTasks   = num(tasks.blocked_tasks);

  return (
    <div
      style={{
        background: "#0D1117",
        border: "1px solid #1F2937",
        borderRadius: 10,
        padding: "20px 24px",
        fontFamily: "'Barlow Condensed', sans-serif",
      }}
    >

      {/* ── Row 1: Inventory + Orders + Tasks + Alerts ── */}
      <SectionLabel>Inventory</SectionLabel>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard
          label="Total SKUs"
          value={num(inv.total_skus)}
        />
        <StatCard
          label="Low Stock"
          value={num(inv.low_stock_items)}
          accent={num(inv.low_stock_items) > 0 ? "#F59E0B" : undefined}
          sub="items at/below reorder point"
        />
        <StatCard
          label="Zero Stock"
          value={num(inv.zero_stock_items)}
          accent={num(inv.zero_stock_items) > 0 ? "#E8001C" : undefined}
          sub="completely out of stock"
        />
      </div>

      <SectionLabel>Orders</SectionLabel>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard label="Total Orders" value={totalOrders} />
        <StatCard
          label="Stuck Orders"
          value={num(orders.stuck_orders)}
          accent={num(orders.stuck_orders) > 0 ? "#F59E0B" : undefined}
          sub="pending/picking — incomplete"
        />
        {/* Per-status breakdown */}
        {Object.entries(orders.orders_by_status ?? {}).map(([status, count]) => (
          <StatCard
            key={status}
            label={status}
            value={num(count)}
          />
        ))}
      </div>

      <SectionLabel>Tasks</SectionLabel>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard
          label="Active Tasks"
          value={num(tasks.active_tasks)}
          accent="#3B82F6"
        />
        <StatCard
          label="Blocked Tasks"
          value={blockedTasks}
          accent={blockedTasks > 0 ? "#E8001C" : undefined}
          sub={blockedTasks > 0 ? "require immediate attention" : undefined}
        />
      </div>

      <SectionLabel>Alerts</SectionLabel>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard
          label="Critical Unacknowledged"
          value={criticalAlerts}
          accent={criticalAlerts > 0 ? "#E8001C" : "#10B981"}
          sub={criticalAlerts === 0 ? "all clear" : "need acknowledgement"}
        />
      </div>

      {/* ── KPIs ── */}
      {kpis.length > 0 && (
        <>
          <SectionLabel>KPIs</SectionLabel>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
              gap: 10,
            }}
          >
            {kpis.map((kpi, i) => (
              <div
                key={i}
                style={{
                  background: "#111827",
                  border: `1px solid ${kpi.is_on_target ? "#065F46" : "#7F1D1D"}`,
                  borderRadius: 8,
                  padding: "12px 14px",
                }}
              >
                <div
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                    color: "#6B7280",
                    marginBottom: 4,
                  }}
                >
                  {kpi.label}
                </div>
                <div
                  style={{
                    fontSize: 22,
                    fontWeight: 700,
                    color: kpi.is_on_target ? "#10B981" : "#F59E0B",
                    lineHeight: 1,
                  }}
                >
                  {kpi.value}
                  {kpi.unit && (
                    <span style={{ fontSize: 12, color: "#6B7280", marginLeft: 3 }}>
                      {kpi.unit}
                    </span>
                  )}
                  <TrendArrow trend={kpi.trend} />
                </div>
                <div style={{ fontSize: 10, color: kpi.is_on_target ? "#059669" : "#D97706", marginTop: 4 }}>
                  {kpi.is_on_target ? "On target" : "Off target"}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ── Zones Near Capacity ── */}
      {zones.length > 0 && (
        <>
          <SectionLabel>Zones Near Capacity (≥85%)</SectionLabel>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {zones.map((zone, i) => (
              <div
                key={i}
                style={{
                  background: "#431407",
                  border: "1px solid #9A3412",
                  borderRadius: 6,
                  padding: "4px 12px",
                  fontSize: 12,
                  fontWeight: 700,
                  color: "#FB923C",
                  letterSpacing: "0.05em",
                }}
              >
                {zone}
              </div>
            ))}
          </div>
        </>
      )}

    </div>
  );
};