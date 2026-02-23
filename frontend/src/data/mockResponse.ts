import type { WMSResponse } from "@/types";

export const SAMPLE_QUERIES = [
  "Show me all active warehouse alerts",
  "Which items are low on stock?",
  "Compare inventory across zones",
  "Show blocked tasks and stuck orders",
  "Give me the KPI summary",
];

export const MOCK_RESPONSE: WMSResponse = {
  query: "",
  summary: "5 active alerts detected. 3 items are below reorder threshold.",
  intents: [
    { intent: "warehouse_alerts", confidence: 1.0 },
    { intent: "low_stock",        confidence: 0.95 },
  ],
  widgets: [
    { type: "ALERT_LIST", title: "Active Alerts",   data_key: "alerts.alerts",   props: {} },
    { type: "TABLE",      title: "Low Stock Items", data_key: "low_stock.items", props: {} },
  ],
  data: {
    alerts: {
      count: 2,
      alerts: [
        {
          id: "ALT-001",
          severity: "CRITICAL",
          title: "Zone A overstock",
          message: "Zone A capacity at 98%",
          category: "CAPACITY",
          timestamp: "2025-01-15T09:30:00",
          acknowledged: false,
          zone: "A",
        },
        {
          id: "ALT-002",
          severity: "HIGH",
          title: "Low stock: SKU-XYZ",
          message: "Only 3 units remaining",
          category: "INVENTORY",
          timestamp: "2025-01-15T10:00:00",
          acknowledged: false,
          zone: "B",
        },
      ],
    },
    low_stock: {
      count: 3,
      items: [
        { sku: "SKU-001", name: "Widget A", zone: "A", quantity: 2, reorder_point: 10, unit: "pcs" },
        { sku: "SKU-045", name: "Gadget B", zone: "B", quantity: 5, reorder_point: 15, unit: "pcs" },
        { sku: "SKU-089", name: "Part C",   zone: "A", quantity: 1, reorder_point: 8,  unit: "pcs" },
      ],
    },
  },
};