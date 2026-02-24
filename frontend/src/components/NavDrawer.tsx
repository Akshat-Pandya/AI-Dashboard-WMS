import React from "react";
import { R } from "@/tokens/brand";

interface NavItem {
  id: string;
  label: string;
  icon: string;
  implemented: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { id: "query",     label: "Query",            icon: "◈", implemented: true  },
  { id: "saved",     label: "Saved Dashboards", icon: "⊟", implemented: true  },
  { id: "settings",  label: "Settings",         icon: "⊙", implemented: false },
  { id: "profile",   label: "Profile",          icon: "◎", implemented: false },
];

interface Props {
  open: boolean;
  activePage: string;
  onNavigate: (page: string) => void;
  onClose: () => void;
}

export const NavDrawer: React.FC<Props> = ({ open, activePage, onNavigate, onClose }) => {
  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          onClick={onClose}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.45)",
            zIndex: 100,
            backdropFilter: "blur(2px)",
          }}
        />
      )}

      {/* Drawer */}
      <div
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          height: "100vh",
          width: 280,
          background: R.black,
          borderLeft: `1px solid ${R.darkGray}`,
          zIndex: 101,
          display: "flex",
          flexDirection: "column",
          transform: open ? "translateX(0)" : "translateX(100%)",
          transition: "transform 0.25s cubic-bezier(0.4,0,0.2,1)",
          boxShadow: open ? "-8px 0 40px rgba(0,0,0,0.5)" : "none",
        }}
      >
        {/* Header */}
        <div style={{
          background: R.red,
          padding: "6px 16px",
          fontFamily: "'Barlow', sans-serif",
          fontSize: 9,
          fontWeight: 700,
          color: "#fff",
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexShrink: 0,
        }}>
          <span>Navigation</span>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              color: "#fff",
              cursor: "pointer",
              fontSize: 16,
              lineHeight: 1,
              padding: "2px 4px",
              opacity: 0.8,
            }}
          >
            ✕
          </button>
        </div>

        {/* Brand */}
        <div style={{
          padding: "20px 20px 16px",
          borderBottom: `1px solid ${R.darkGray}`,
          flexShrink: 0,
        }}>
          <span style={{
            fontFamily: "'Barlow Condensed', sans-serif",
            fontSize: 26,
            fontWeight: 800,
            color: R.red,
            letterSpacing: "0.02em",
          }}>
            ADDVERB
          </span>
          <div style={{
            fontFamily: "'Barlow', sans-serif",
            fontSize: 10,
            color: R.textMuted,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            marginTop: 2,
          }}>
            WMS Generative Dashboard
          </div>
        </div>

        {/* Nav items */}
        <nav style={{ flex: 1, padding: "12px 0" }}>
          {NAV_ITEMS.map((item) => {
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  if (item.implemented) {
                    onNavigate(item.id);
                    onClose();
                  }
                }}
                disabled={!item.implemented}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  width: "100%",
                  padding: "14px 20px",
                  background: isActive ? "rgba(232,0,28,0.12)" : "transparent",
                  borderLeft: isActive ? `3px solid ${R.red}` : "3px solid transparent",
                  border: "none",
                  borderRadius: 0,
                  cursor: item.implemented ? "pointer" : "not-allowed",
                  textAlign: "left",
                  transition: "background 0.15s",
                  opacity: item.implemented ? 1 : 0.35,
                }}
                onMouseEnter={(e) => {
                  if (item.implemented && !isActive)
                    (e.currentTarget as HTMLButtonElement).style.background = R.darkGray;
                }}
                onMouseLeave={(e) => {
                  if (!isActive)
                    (e.currentTarget as HTMLButtonElement).style.background = "transparent";
                }}
              >
                <span style={{
                  fontFamily: "monospace",
                  fontSize: 16,
                  color: isActive ? R.red : R.textMuted,
                  width: 20,
                  textAlign: "center",
                  flexShrink: 0,
                }}>
                  {item.icon}
                </span>
                <span style={{
                  fontFamily: "'Barlow', sans-serif",
                  fontSize: 13,
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? "#fff" : R.textMuted,
                  letterSpacing: "0.04em",
                }}>
                  {item.label}
                </span>
                {!item.implemented && (
                  <span style={{
                    marginLeft: "auto",
                    fontFamily: "'Barlow', sans-serif",
                    fontSize: 9,
                    fontWeight: 700,
                    color: R.midGray,
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                  }}>
                    Soon
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        <div style={{
          padding: "16px 20px",
          borderTop: `1px solid ${R.darkGray}`,
          fontFamily: "'Barlow', sans-serif",
          fontSize: 10,
          color: R.midGray,
          letterSpacing: "0.06em",
          flexShrink: 0,
        }}>
          WMS Intelligence v1.0
        </div>
      </div>
    </>
  );
};
