import React from "react";
import { Skeleton } from "./Skeleton";
import { WidgetRenderer } from "./WidgetRenderer";
import type { IntentTabResult } from "@/types";

interface Props {
  result: IntentTabResult;
  loading?: boolean;
}

export const IntentTabContent: React.FC<Props> = ({ result, loading = false }) => {
  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <Skeleton height={90} />
        <Skeleton height={200} />
        <Skeleton height={160} />
      </div>
    );
  }

  return (
    <WidgetRenderer widgets={result.widgets} data={result.data} />
  );
};