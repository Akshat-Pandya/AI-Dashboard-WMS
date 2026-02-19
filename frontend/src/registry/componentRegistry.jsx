// src/registry/componentRegistry.js

import OverviewKpiCards from "../components/widgets/OverviewKpiCards";
import LowStockTable from "../components/widgets/LowStockTable";
import OrdersTable from "../components/widgets/OrdersTable";
import TasksList from "../components/widgets/TasksList";
import AlertsFeed from "../components/widgets/AlertsFeed";

// --------------------------------------------------
// Registry mapping string → component
// --------------------------------------------------
export const componentRegistry = {
  OverviewKpiCards,
  LowStockTable,
  OrdersTable,
  TasksList,
  AlertsFeed,
};

// --------------------------------------------------
// Helper: get component by name safely
// --------------------------------------------------
export function getComponent(name) {
  return componentRegistry[name] || null;
}
