import React, { useState } from "react";
import { R } from "@/tokens/brand";
import { SAMPLE_QUERIES } from "@/data/mockResponse";

interface Props {
  history: string[];
  loading: boolean;
  onSubmit: (query: string) => void;
}

export const ChatPanel: React.FC<Props> = ({ history, loading, onSubmit }) => {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim() || loading) return;
    onSubmit(input.trim());
    setInput("");
  };

  return (
    <div
      style={{
        width: 290,
        minWidth: 260,
        background: R.black,
        display: "flex",
        flexDirection: "column",
        height: "100%",
        borderRight: `1px solid ${R.darkGray}`,
        flexShrink: 0,
      }}
    >
      {/* Addverb top red banner */}
      <div
        style={{
          background: R.red,
          padding: "6px 16px",
          fontFamily: "'Barlow', sans-serif",
          fontSize: 9,
          fontWeight: 700,
          color: "#fff",
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          flexShrink: 0,
        }}
      >
        GLOBAL ROBOTICS COMPANY · 24/7 AFTER SALES SUPPORT
      </div>

      {/* Logo */}
      <div
        style={{
          padding: "16px 20px 14px",
          borderBottom: `1px solid ${R.darkGray}`,
          flexShrink: 0,
        }}
      >
        <div style={{ marginBottom: 4 }}>
          <span
            style={{
              fontFamily: "'Barlow Condensed', sans-serif",
              fontSize: 28,
              fontWeight: 800,
              color: R.red,
              letterSpacing: "0.02em",
              lineHeight: 1,
            }}
          >
            ADDVERB
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
          <span
            style={{
              fontFamily: "'Barlow', sans-serif",
              fontSize: 10,
              color: R.textMuted,
              letterSpacing: "0.06em",
              textTransform: "uppercase",
            }}
          >
            WMS Generative Dashboard
          </span>
          {/* Live indicator */}
          <span
            style={{
              width: 5,
              height: 5,
              borderRadius: "50%",
              background: R.green,
              display: "inline-block",
              flexShrink: 0,
            }}
          />
        </div>
      </div>

      {/* History / Suggestions */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px" }}>
        {history.length === 0 ? (
          <div>
            <p
              style={{
                fontFamily: "'Barlow', sans-serif",
                fontSize: 10,
                fontWeight: 700,
                color: R.midGray,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                marginBottom: 12,
              }}
            >
              — Sample queries
            </p>
            {SAMPLE_QUERIES.map((q, i) => (
              <button
                key={i}
                onClick={() => !loading && onSubmit(q)}
                disabled={loading}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  background: "transparent",
                  border: `1px solid ${R.darkGray}`,
                  borderLeft: `3px solid ${R.red}`,
                  borderRadius: 2,
                  padding: "10px 14px",
                  marginBottom: 8,
                  cursor: loading ? "not-allowed" : "pointer",
                  fontFamily: "'Barlow', sans-serif",
                  fontSize: 12,
                  color: R.textMuted,
                  lineHeight: 1.4,
                }}
                onMouseEnter={(e) => {
                  if (!loading) {
                    (e.currentTarget as HTMLButtonElement).style.background = R.darkGray;
                    (e.currentTarget as HTMLButtonElement).style.color = "#E2E8F0";
                  }
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = "transparent";
                  (e.currentTarget as HTMLButtonElement).style.color = R.textMuted;
                }}
              >
                "{q}"
              </button>
            ))}
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {history.map((item, i) => (
              <div
                key={i}
                style={{
                  background: R.darkGray,
                  borderLeft: `3px solid ${i === history.length - 1 ? R.red : R.midGray}`,
                  borderRadius: 2,
                  padding: "10px 14px",
                }}
              >
                <p
                  style={{
                    margin: "0 0 4px",
                    fontFamily: "'Barlow', sans-serif",
                    fontSize: 9,
                    color: i === history.length - 1 ? R.red : R.midGray,
                    fontWeight: 700,
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                  }}
                >
                  QUERY
                </p>
                <p
                  style={{
                    margin: 0,
                    fontFamily: "'Barlow', sans-serif",
                    fontSize: 12,
                    color: "#CBD5E1",
                    lineHeight: 1.4,
                  }}
                >
                  {item}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Input area */}
      <div
        style={{
          padding: "14px 16px",
          borderTop: `1px solid ${R.darkGray}`,
          flexShrink: 0,
        }}
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Ask anything about your warehouse..."
          rows={3}
          style={{
            width: "100%",
            boxSizing: "border-box",
            background: R.darkGray,
            border: `1px solid ${R.midGray}`,
            borderRadius: 2,
            padding: "10px 12px",
            fontFamily: "'Barlow', sans-serif",
            fontSize: 12,
            color: "#E2E8F0",
            resize: "none",
            outline: "none",
            lineHeight: 1.5,
            transition: "border-color 0.2s",
          }}
          onFocus={(e) => (e.target.style.borderColor = R.red)}
          onBlur={(e) => (e.target.style.borderColor = R.midGray)}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          style={{
            width: "100%",
            marginTop: 8,
            padding: "11px 16px",
            background:
              loading ? R.midGray : !input.trim() ? R.darkGray : R.red,
            color: loading || !input.trim() ? R.midGray : "#fff",
            border: "none",
            borderRadius: 2,
            cursor: loading || !input.trim() ? "not-allowed" : "pointer",
            fontFamily: "'Barlow', sans-serif",
            fontSize: 12,
            fontWeight: 800,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
          }}
        >
          {loading ? "⟳  Processing..." : "Send Query  →"}
        </button>
      </div>
    </div>
  );
};
