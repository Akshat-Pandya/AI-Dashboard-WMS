import type { ChatResponse, QueryResponse } from "@/types";

// ─── Legacy mock (kept for existing tab/intent UI components) ─────────────────

export const MOCK_RESPONSE: ChatResponse = {
  query: "compare inventory of zone A vs zone B and highlight low stock",
  candidates: [
    { name: "INVENTORY", confidence: 0.86 },
    { name: "OVERVIEW",  confidence: 0.63 },
    { name: "TASKS",     confidence: 0.22 },
  ],
  selectedIntent: "INVENTORY",
  resultsByIntent: [
    // ── INVENTORY ──────────────────────────────────────────────────────────
    {
      intent: "INVENTORY",
      confidence: 0.86,
      toolsExecuted: ["get_inventory_by_zone", "get_low_stock_items"],
      summary: [
        "Zone A has 1,240 available units across 34 SKUs; Zone B has 890 units across 28 SKUs.",
        "12 SKUs are below reorder point — 8 in Zone A, 4 in Zone B.",
        "Immediate replenishment recommended for SKU-1042, SKU-2087, and SKU-3301.",
      ],
      widgets: [
        {
          type: "KPI_CARDS",
          title: "Inventory Overview",
          data: {
            cards: [
              { label: "Total SKUs",            value: "62",    unit: "",  trend: "+3 this week",       up: true,  icon: "📦" },
              { label: "Low Stock Items",        value: "12",    unit: "",  trend: "▲ 4 vs yesterday",  up: false, icon: "⚠️" },
              { label: "Total Available Units",  value: "2,130", unit: "units", trend: "−210 vs yesterday", up: false, icon: "🏭" },
            ],
          },
        },
        {
          type: "BAR_CHART",
          title: "Zone-wise Available Units",
          data: {
            bars: [
              { zone: "Zone A", available: 1240, reserved: 310 },
              { zone: "Zone B", available: 890,  reserved: 175 },
            ],
            keys: ["available", "reserved"],
            colors: ["#E8001C", "#3A3F47"],
          },
        },
        {
          type: "TABLE",
          title: "Low Stock Items — Top 10",
          data: {
            columns: ["SKU", "Product", "Zone", "Available", "Reorder Point"],
            rows: [
              ["SKU-1042", "Bolt M8×25",        "Zone A", 5,  50],
              ["SKU-2087", "Gasket Ring 40mm",   "Zone A", 8,  100],
              ["SKU-3301", "Hex Nut M10",        "Zone B", 3,  75],
              ["SKU-0821", "Cable Tie 200mm",    "Zone A", 12, 150],
              ["SKU-4412", "Pipe Elbow 90°",     "Zone B", 6,  40],
              ["SKU-1153", "Bearing 6205",       "Zone A", 2,  30],
              ["SKU-2340", "O-Ring 25×3",        "Zone B", 9,  80],
              ["SKU-0509", "Spring Washer M6",   "Zone A", 14, 200],
              ["SKU-3874", "Valve Seat",         "Zone B", 1,  20],
              ["SKU-1660", "Shaft Sleeve 50mm",  "Zone A", 7,  60],
            ],
          },
        },
      ],
    },

    // ── OVERVIEW ───────────────────────────────────────────────────────────
    {
      intent: "OVERVIEW",
      confidence: 0.63,
      toolsExecuted: ["get_kpis", "get_critical_alerts", "get_overdue_asns"],
      summary: [
        "974 orders fulfilled today with 99.1% pick accuracy — within SLA.",
        "3 critical alerts require immediate attention (2 equipment, 1 safety).",
        "7 ASNs are overdue; oldest is 5 days past expected date.",
      ],
      widgets: [
        {
          type: "KPI_CARDS",
          title: "Warehouse KPIs",
          data: {
            cards: [
              { label: "Orders Fulfilled Today", value: "974",  unit: "",  trend: "+12% vs avg",          up: true,  icon: "✅" },
              { label: "Pick Accuracy",           value: "99.1", unit: "%", trend: "↓ 0.2pp vs yesterday", up: false, icon: "🎯" },
              { label: "Overdue ASNs",            value: "7",    unit: "",  trend: "+2 since morning",     up: false, icon: "🚨" },
            ],
          },
        },
        {
          type: "ALERT_LIST",
          title: "Critical Alerts",
          data: {
            alerts: [
              { id: "ALT-001", severity: "CRITICAL", message: "Forklift FL-04 reported fault — Zone C aisle 3",     time: "09:14 AM" },
              { id: "ALT-002", severity: "CRITICAL", message: "Conveyor belt CB-07 jam detected — dispatch bay",    time: "10:02 AM" },
              { id: "ALT-003", severity: "HIGH",     message: "Fire suppression system low pressure — Rack Row 12", time: "11:47 AM" },
            ],
          },
        },
        {
          type: "TABLE",
          title: "Overdue ASNs",
          data: {
            columns: ["ASN Number", "Supplier", "Expected Date", "Status"],
            rows: [
              ["ASN-20481", "Acme Parts Co.",   "2025-01-14", "In Transit"],
              ["ASN-20455", "Delta Supply",     "2025-01-13", "Customs Hold"],
              ["ASN-20397", "Precision Goods",  "2025-01-12", "Delayed"],
              ["ASN-20341", "Fast Freight Ltd", "2025-01-11", "In Transit"],
              ["ASN-20312", "Global Parts Hub", "2025-01-10", "Missing ETA"],
              ["ASN-20289", "UniSource",        "2025-01-09", "Delayed"],
              ["ASN-20201", "TechComp Inc.",    "2025-01-08", "Customs Hold"],
            ],
          },
        },
      ],
    },

    // ── TASKS ──────────────────────────────────────────────────────────────
    {
      intent: "TASKS",
      confidence: 0.22,
      toolsExecuted: ["get_blocked_tasks"],
      summary: [
        "9 tasks are currently blocked across warehouse zones.",
        "Most blockers are related to missing equipment or unresolved putaway conflicts.",
      ],
      widgets: [
        {
          type: "TABLE",
          title: "Blocked Tasks",
          data: {
            columns: ["Task ID", "Type", "Zone", "Assignee", "Block Reason"],
            rows: [
              ["TSK-4401", "Putaway",       "Zone A", "Rahul M.",  "Location occupied"],
              ["TSK-4387", "Pick",          "Zone B", "Sneha K.",  "Forklift unavailable"],
              ["TSK-4362", "Cycle Count",   "Zone C", "Arjun S.",  "System discrepancy"],
              ["TSK-4341", "Replenishment", "Zone A", "Priya L.",  "Stock not received"],
              ["TSK-4320", "Dispatch",      "Dock 3", "Dev P.",    "Carrier delay"],
              ["TSK-4298", "Pick",          "Zone B", "Meera T.",  "Label missing"],
              ["TSK-4271", "Putaway",       "Zone D", "Kiran R.",  "Aisle blocked"],
              ["TSK-4255", "Receiving",     "Dock 1", "Anil V.",   "PO mismatch"],
              ["TSK-4230", "Pick",          "Zone A", "Fatima N.", "Inventory discrepancy"],
            ],
          },
        },
      ],
    },
  ],
};

// ─── New mock matching QueryResponse (used when useMock=true in api.ts) ────────

export const MOCK_QUERY_RESPONSE: QueryResponse = {
  query: "compare inventory of zone A vs zone B and highlight low stock",
  summary:
    "Zone A has 1,240 units across 34 SKUs vs Zone B's 890 units across 28 SKUs. " +
    "12 SKUs are below reorder point — 8 in Zone A and 4 in Zone B. " +
    "2 unacknowledged critical alerts require immediate attention.",
  widgets: [
    {
      type: "ZONE_COMPARE_CHART",
      title: "Zone A vs Zone B — Available Units",
      data_key: "zone_comparison.zones",
      props: { highlightKey: "low_stock_count" },
    },
    {
      type: "TABLE",
      title: "Low Stock Items",
      data_key: "low_stock.items",
      props: { highlight: "quantity" },
    },
    {
      type: "ALERT_LIST",
      title: "Active Alerts",
      data_key: "alerts.alerts",
    },
  ],
  data: {
    zone_comparison: {
      zones: [
        { zone: "Zone A", total_skus: 34, total_units: 1240, low_stock_count: 8,  avg_quantity: 36.5 },
        { zone: "Zone B", total_skus: 28, total_units: 890,  low_stock_count: 4,  avg_quantity: 31.8 },
      ],
    },
    low_stock: {
      count: 10,
      threshold: 10,
      items: [
        { sku: "SKU-1042", name: "Bolt M8×25",       zone: "Zone A", quantity: 5,  reorder_point: 50,  unit: "pcs" },
        { sku: "SKU-2087", name: "Gasket Ring 40mm",  zone: "Zone A", quantity: 8,  reorder_point: 100, unit: "pcs" },
        { sku: "SKU-3301", name: "Hex Nut M10",       zone: "Zone B", quantity: 3,  reorder_point: 75,  unit: "pcs" },
        { sku: "SKU-0821", name: "Cable Tie 200mm",   zone: "Zone A", quantity: 12, reorder_point: 150, unit: "pcs" },
        { sku: "SKU-4412", name: "Pipe Elbow 90°",    zone: "Zone B", quantity: 6,  reorder_point: 40,  unit: "pcs" },
        { sku: "SKU-1153", name: "Bearing 6205",      zone: "Zone A", quantity: 2,  reorder_point: 30,  unit: "pcs" },
        { sku: "SKU-2340", name: "O-Ring 25×3",       zone: "Zone B", quantity: 9,  reorder_point: 80,  unit: "pcs" },
        { sku: "SKU-0509", name: "Spring Washer M6",  zone: "Zone A", quantity: 14, reorder_point: 200, unit: "pcs" },
        { sku: "SKU-3874", name: "Valve Seat",        zone: "Zone B", quantity: 1,  reorder_point: 20,  unit: "pcs" },
        { sku: "SKU-1660", name: "Shaft Sleeve 50mm", zone: "Zone A", quantity: 7,  reorder_point: 60,  unit: "pcs" },
      ],
    },
    alerts: {
      count: 2,
      alerts: [
        { id: "ALT-001", severity: "CRITICAL", title: "Forklift Fault",          message: "Forklift FL-04 reported fault — Zone C aisle 3",     timestamp: "2025-01-15T09:14:00", acknowledged: false, zone: "C" },
        { id: "ALT-002", severity: "CRITICAL", title: "Conveyor Jam",            message: "Conveyor belt CB-07 jam detected — dispatch bay",    timestamp: "2025-01-15T10:02:00", acknowledged: false, zone: "DOCK" },
      ],
    },
  },
};

// ─── Sample queries ───────────────────────────────────────────────────────────

export const SAMPLE_QUERIES: string[] = [
  "compare inventory of zone A vs zone B and highlight low stock",
  "show me warehouse KPIs and critical alerts",
  "list all blocked tasks by zone",
];