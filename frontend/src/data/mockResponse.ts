import type { ChatResponse } from "@/types";

export const MOCK_RESPONSE: ChatResponse = {
  query: "compare inventory of zone A vs zone B and highlight low stock",
  candidates: [
    { name: "INVENTORY", confidence: 0.86 },
    { name: "OVERVIEW", confidence: 0.63 },
    { name: "TASKS", confidence: 0.22 },
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
              { label: "Total SKUs", value: "62", unit: "", trend: "+3 this week", up: true, icon: "📦" },
              { label: "Low Stock Items", value: "12", unit: "", trend: "▲ 4 vs yesterday", up: false, icon: "⚠️" },
              { label: "Total Available Units", value: "2,130", unit: "units", trend: "−210 vs yesterday", up: false, icon: "🏭" },
            ],
          },
        },
        {
          type: "BAR_CHART",
          title: "Zone-wise Available Units",
          data: {
            bars: [
              { zone: "Zone A", available: 1240, reserved: 310 },
              { zone: "Zone B", available: 890, reserved: 175 },
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
              ["SKU-1042", "Bolt M8×25",       "Zone A", 5,  50],
              ["SKU-2087", "Gasket Ring 40mm",  "Zone A", 8,  100],
              ["SKU-3301", "Hex Nut M10",       "Zone B", 3,  75],
              ["SKU-0821", "Cable Tie 200mm",   "Zone A", 12, 150],
              ["SKU-4412", "Pipe Elbow 90°",    "Zone B", 6,  40],
              ["SKU-1153", "Bearing 6205",      "Zone A", 2,  30],
              ["SKU-2340", "O-Ring 25×3",       "Zone B", 9,  80],
              ["SKU-0509", "Spring Washer M6",  "Zone A", 14, 200],
              ["SKU-3874", "Valve Seat",        "Zone B", 1,  20],
              ["SKU-1660", "Shaft Sleeve 50mm", "Zone A", 7,  60],
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
              { label: "Orders Fulfilled Today", value: "974",  unit: "",  trend: "+12% vs avg",         up: true,  icon: "✅" },
              { label: "Pick Accuracy",          value: "99.1", unit: "%", trend: "↓ 0.2pp vs yesterday", up: false, icon: "🎯" },
              { label: "Overdue ASNs",           value: "7",    unit: "",  trend: "+2 since morning",     up: false, icon: "🚨" },
            ],
          },
        },
        {
          type: "ALERT_LIST",
          title: "Critical Alerts",
          data: {
            alerts: [
              { id: "ALT-001", severity: "CRITICAL", message: "Forklift FL-04 reported fault — Zone C aisle 3",          time: "09:14 AM" },
              { id: "ALT-002", severity: "CRITICAL", message: "Conveyor belt CB-07 jam detected — dispatch bay",         time: "10:02 AM" },
              { id: "ALT-003", severity: "HIGH",     message: "Fire suppression system low pressure — Rack Row 12",      time: "11:47 AM" },
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
              ["TSK-4401", "Putaway",      "Zone A", "Rahul M.",  "Location occupied"],
              ["TSK-4387", "Pick",         "Zone B", "Sneha K.",  "Forklift unavailable"],
              ["TSK-4362", "Cycle Count",  "Zone C", "Arjun S.",  "System discrepancy"],
              ["TSK-4341", "Replenishment","Zone A", "Priya L.",  "Stock not received"],
              ["TSK-4320", "Dispatch",     "Dock 3", "Dev P.",    "Carrier delay"],
              ["TSK-4298", "Pick",         "Zone B", "Meera T.",  "Label missing"],
              ["TSK-4271", "Putaway",      "Zone D", "Kiran R.",  "Aisle blocked"],
              ["TSK-4255", "Receiving",    "Dock 1", "Anil V.",   "PO mismatch"],
              ["TSK-4230", "Pick",         "Zone A", "Fatima N.", "Inventory discrepancy"],
            ],
          },
        },
      ],
    },
  ],
};

export const SAMPLE_QUERIES: string[] = [
  "compare inventory of zone A vs zone B and highlight low stock",
  "show me warehouse KPIs and critical alerts",
  "list all blocked tasks by zone",
];
