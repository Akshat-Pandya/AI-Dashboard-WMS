import React from "react";
import type { WidgetSpec, KPICardsData, TableData, BarChartData, LineChartData, AlertListData } from "@/types";
import { WidgetCard }       from "./WidgetCard";
import { KPICardsWidget }   from "./KPICardsWidget";
import { TableWidget }      from "./TableWidget";
import { BarChartWidget }   from "./BarChartWidget";
import { LineChartWidget }  from "./LineChartWidget";
import { AlertListWidget }  from "./AlertListWidget";

interface Props {
  widget: WidgetSpec;
}

export const WidgetRenderer: React.FC<Props> = ({ widget }) => {
  const { type, title, data } = widget;

  const content = (() => {
    switch (type) {
      case "KPI_CARDS":  return <KPICardsWidget  data={data as KPICardsData}  />;
      case "TABLE":      return <TableWidget      data={data as TableData}     />;
      case "BAR_CHART":  return <BarChartWidget   data={data as BarChartData}  />;
      case "LINE_CHART": return <LineChartWidget  data={data as LineChartData} />;
      case "ALERT_LIST": return <AlertListWidget  data={data as AlertListData} />;
      default:           return <p style={{ color: "#9BA3AE", fontSize: 13 }}>Unknown widget type: {type}</p>;
    }
  })();

  return <WidgetCard title={title}>{content}</WidgetCard>;
};
