// components/widgets/OverviewPanelWidget.tsx
import React from "react";
import { R } from "@/tokens/brand";

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
  if (trend === "up")   return <span style={{ color: R.green,   fontSize: 11, marginLeft: 4 }}>▲</span>;
  if (trend === "down") return <span style={{ color: R.red,     fontSize: 11, marginLeft: 4 }}>▼</span>;
  return                       <span style={{ color: R.textMuted, fontSize: 11, marginLeft: 4 }}>—</span>;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      fontFamily: "'Barlow', sans-serif",
      fontSize: 9,
      fontWeight: 700,
      letterSpacing: "0.1em",
      textTransform: "uppercase",
      color: R.textMuted,
      marginBottom: 8,
      marginTop: 24,
      paddingBottom: 6,
      borderBottom: `1px solid ${R.border}`,
    }}>
      {children}
    </div>
  );
}

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
    <div style={{
      background: R.white,
      border: `1px solid ${R.border}`,
      borderTop: `3px solid ${accent ?? R.border}`,
      borderRadius: 3,
      padding: "14px 16px",
      minWidth: 110,
      flex: 1,
      boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
    }}>
      <div style={{
        fontFamily: "'Barlow', sans-serif",
        fontSize: 9,
        fontWeight: 700,
        letterSpacing: "0.1em",
        textTransform: "uppercase",
        color: R.textMuted,
        marginBottom: 6,
      }}>
        {label}
      </div>
      <div style={{
        fontFamily: "'Barlow Condensed', sans-serif",
        fontSize: 30,
        fontWeight: 800,
        color: accent ?? R.textPrimary,
        lineHeight: 1,
      }}>
        {value}
      </div>
      {sub && (
        <div style={{
          fontFamily: "'Barlow', sans-serif",
          fontSize: 10,
          color: R.textMuted,
          marginTop: 5,
        }}>
          {sub}
        </div>
      )}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export const OverviewPanelWidget: React.FC<Props> = ({ data }) => {
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return (
      <div style={{ color: R.textMuted, fontSize: 13, padding: 16 }}>
        No overview data available.
      </div>
    );
  }

  const inv    = data.inventory  ?? {};
  const orders = data.orders     ?? {};
  const tasks  = data.tasks      ?? {};
  const alerts = data.alerts     ?? {};
  const kpis   = data.kpis?.kpis ?? [];
  const zones  = data.zones?.zones_near_capacity ?? [];

  const totalOrders    = Object.values(orders.orders_by_status ?? {}).reduce((s, v) => s + num(v), 0);
  const criticalAlerts = num(alerts.unacknowledged_critical_alerts);
  const blockedTasks   = num(tasks.blocked_tasks);

  return (
    <div style={{
      background: R.bg,
      border: `1px solid ${R.border}`,
      borderRadius: 4,
      padding: "20px 24px",
    }}>

      {/* ── Inventory ── */}
      <SectionLabel>Inventory</SectionLabel>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard
          label="Total SKUs"
          value={num(inv.total_skus)}
          accent={R.midGray}
        />
        <StatCard
          label="Low Stock"
          value={num(inv.low_stock_items)}
          accent={num(inv.low_stock_items) > 0 ? R.amber : R.green}
          sub="at or below reorder point"
        />
        <StatCard
          label="Zero Stock"
          value={num(inv.zero_stock_items)}
          accent={num(inv.zero_stock_items) > 0 ? R.red : R.green}
          sub="completely out of stock"
        />
      </div>

      {/* ── Orders ── */}
      <SectionLabel>Orders</SectionLabel>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard label="Total Orders" value={totalOrders} accent={R.midGray} />
        <StatCard
          label="Stuck Orders"
          value={num(orders.stuck_orders)}
          accent={num(orders.stuck_orders) > 0 ? R.amber : R.green}
          sub="pending / picking — incomplete"
        />
        {Object.entries(orders.orders_by_status ?? {}).map(([status, count]) => (
          <StatCard key={status} label={status} value={num(count)} />
        ))}
      </div>

      {/* ── Tasks ── */}
      <SectionLabel>Tasks</SectionLabel>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard
          label="Active Tasks"
          value={num(tasks.active_tasks)}
          accent={R.midGray}
        />
        <StatCard
          label="Blocked Tasks"
          value={blockedTasks}
          accent={blockedTasks > 0 ? R.red : R.green}
          sub={blockedTasks > 0 ? "require immediate attention" : undefined}
        />
      </div>

      {/* ── Alerts ── */}
      <SectionLabel>Alerts</SectionLabel>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard
          label="Critical Unacknowledged"
          value={criticalAlerts}
          accent={criticalAlerts > 0 ? R.red : R.green}
          sub={criticalAlerts === 0 ? "all clear" : "need acknowledgement"}
        />
      </div>

      {/* ── KPIs ── */}
      {kpis.length > 0 && (
        <>
          <SectionLabel>KPIs</SectionLabel>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
            gap: 10,
          }}>
            {kpis.map((kpi, i) => (
              <div key={i} style={{
                background: R.white,
                border: `1px solid ${R.border}`,
                borderTop: `3px solid ${kpi.is_on_target ? R.green : R.amber}`,
                borderRadius: 3,
                padding: "12px 14px",
                boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
              }}>
                <div style={{
                  fontFamily: "'Barlow', sans-serif",
                  fontSize: 9,
                  fontWeight: 700,
                  letterSpacing: "0.1em",
                  textTransform: "uppercase",
                  color: R.textMuted,
                  marginBottom: 6,
                }}>
                  {kpi.label}
                </div>
                <div style={{
                  fontFamily: "'Barlow Condensed', sans-serif",
                  fontSize: 24,
                  fontWeight: 800,
                  color: kpi.is_on_target ? R.green : R.amber,
                  lineHeight: 1,
                }}>
                  {kpi.value}
                  {kpi.unit && (
                    <span style={{
                      fontFamily: "'Barlow', sans-serif",
                      fontSize: 11,
                      color: R.textMuted,
                      marginLeft: 3,
                      fontWeight: 400,
                    }}>
                      {kpi.unit}
                    </span>
                  )}
                  <TrendArrow trend={kpi.trend} />
                </div>
                <div style={{
                  fontFamily: "'Barlow', sans-serif",
                  fontSize: 10,
                  color: kpi.is_on_target ? R.green : R.amber,
                  marginTop: 5,
                  fontWeight: 600,
                }}>
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
              <div key={i} style={{
                background: R.amberLight,
                border: `1px solid ${R.amber}`,
                borderRadius: 3,
                padding: "4px 12px",
                fontFamily: "'Barlow', sans-serif",
                fontSize: 11,
                fontWeight: 700,
                color: R.amber,
                letterSpacing: "0.06em",
                textTransform: "uppercase",
              }}>
                {zone}
              </div>
            ))}
          </div>
        </>
      )}

    </div>
  );
};