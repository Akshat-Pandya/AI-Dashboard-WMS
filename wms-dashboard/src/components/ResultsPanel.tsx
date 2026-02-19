import React, { useState, useEffect } from "react";
import { R } from "@/tokens/brand";
import { Skeleton } from "./Skeleton";
import { IntentChips } from "./IntentChips";
import { IntentTabs } from "./IntentTabs";
import { AllIntentsPanel } from "./AllIntentsPanel";
import { IntentTabContent } from "./IntentTabContent";
import type { ChatResponse } from "@/types";

interface Props {
  response: ChatResponse | null;
  loading: boolean;
}

export const ResultsPanel: React.FC<Props> = ({ response, loading }) => {
  const [activeTab, setActiveTab] = useState(0);

  // Reset to first tab on each new response
  useEffect(() => {
    setActiveTab(0);
  }, [response]);

  // ── Empty State ─────────────────────────────────────────────────────────────
  if (!response && !loading) {
    return (
      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: R.bg,
          flexDirection: "column",
          gap: 24,
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Background watermark */}
        <div
          style={{
            position: "absolute",
            fontFamily: "'Barlow Condensed', sans-serif",
            fontSize: "18vw",
            fontWeight: 800,
            color: "rgba(232,0,28,0.04)",
            letterSpacing: "0.04em",
            userSelect: "none",
            whiteSpace: "nowrap",
            pointerEvents: "none",
          }}
        >
          ADDVERB
        </div>

        {/* Central message */}
        <div style={{ textAlign: "center", position: "relative" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              justifyContent: "center",
              marginBottom: 16,
            }}
          >
            <div style={{ height: 2, width: 40, background: R.red }} />
            <span
              style={{
                fontFamily: "'Barlow', sans-serif",
                fontSize: 11,
                fontWeight: 700,
                color: R.textMuted,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
              }}
            >
              WMS Intelligence
            </span>
            <div style={{ height: 2, width: 40, background: R.red }} />
          </div>

          <p
            style={{
              fontFamily: "'Barlow Condensed', sans-serif",
              fontSize: 28,
              color: R.textPrimary,
              margin: 0,
              fontWeight: 700,
            }}
          >
            Ask a question to generate
          </p>
          <p
            style={{
              fontFamily: "'Barlow Condensed', sans-serif",
              fontSize: 28,
              color: R.red,
              margin: "0 0 12px",
              fontWeight: 700,
            }}
          >
            warehouse insights
          </p>
          <p
            style={{
              fontFamily: "'Barlow', sans-serif",
              fontSize: 12,
              color: R.textMuted,
              margin: 0,
            }}
          >
            Multi-intent analysis · Generative UI · Real-time data
          </p>
        </div>

        {/* Stats row */}
        <div style={{ display: "flex", gap: 32, position: "relative" }}>
          {[
            ["350+", "Clients Globally"],
            ["500+", "Warehouses Automated"],
            ["24/7", "Support"],
          ].map(([val, label], i) => (
            <div key={i} style={{ textAlign: "center" }}>
              <p
                style={{
                  fontFamily: "'Barlow Condensed', sans-serif",
                  fontSize: 28,
                  fontWeight: 800,
                  color: R.red,
                  margin: "0 0 2px",
                }}
              >
                {val}
              </p>
              <p
                style={{
                  fontFamily: "'Barlow', sans-serif",
                  fontSize: 10,
                  fontWeight: 700,
                  color: R.textMuted,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  margin: 0,
                }}
              >
                {label}
              </p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const tabs = response
    ? ["ALL INTENTS", ...response.candidates.map((c) => c.name)]
    : [];

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        background: R.bg,
        overflow: "hidden",
      }}
    >
      {/* Active query bar */}
      {response && (
        <div
          style={{
            background: R.white,
            borderBottom: `1px solid ${R.border}`,
            padding: "12px 24px",
            display: "flex",
            alignItems: "center",
            gap: 14,
            flexShrink: 0,
          }}
        >
          <div
            style={{
              width: 4,
              height: 28,
              background: R.red,
              borderRadius: 2,
              flexShrink: 0,
            }}
          />
          <div>
            <p
              style={{
                fontFamily: "'Barlow', sans-serif",
                fontSize: 9,
                fontWeight: 700,
                color: R.textMuted,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                margin: "0 0 3px",
              }}
            >
              Active Query
            </p>
            <p
              style={{
                fontFamily: "'Barlow', sans-serif",
                fontSize: 14,
                color: R.textPrimary,
                margin: 0,
                fontWeight: 600,
              }}
            >
              "{response.query}"
            </p>
          </div>
        </div>
      )}

      {/* Intent chips */}
      {response && (
        <IntentChips
          candidates={response.candidates}
          selectedIntent={response.selectedIntent}
        />
      )}

      {/* Tabs */}
      {response && (
        <IntentTabs
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
      )}

      {/* Tab content */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
        {loading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <Skeleton height={80} />
            <Skeleton height={220} />
            <Skeleton height={170} />
          </div>
        ) : response ? (
          activeTab === 0 ? (
            <AllIntentsPanel response={response} />
          ) : (
            <IntentTabContent
              result={response.resultsByIntent[activeTab - 1]}
            />
          )
        ) : null}
      </div>
    </div>
  );
};
