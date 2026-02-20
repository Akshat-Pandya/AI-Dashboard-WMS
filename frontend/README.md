# Addverb WMS — Generative UI Dashboard

A chat-driven warehouse management dashboard with multi-intent analysis, built with React + TypeScript + Vite + Recharts.

---

## Project Setup

### 1. Prerequisites

- Node.js >= 18
- npm >= 9

### 2. Create the project (from scratch)

```bash
npm create vite@latest wms-dashboard -- --template react-ts
cd wms-dashboard
```

### 3. Install dependencies

```bash
npm install recharts
npm install --save-dev @types/react @types/react-dom
```

### 4. Replace generated files with this project structure

Copy all files from this repository into the project root.

### 5. Configure path aliases (vite.config.ts already set)

The `@/` alias maps to `src/`. TypeScript is configured via `tsconfig.json`.

### 6. Run locally

```bash
npm run dev
```

Open: http://localhost:5173

### 7. Build for production

```bash
npm run build
npm run preview
```

---

## Folder Structure

```
wms-dashboard/
├── index.html                          # HTML entry point (loads Google Fonts)
├── vite.config.ts                      # Vite config with @ alias
├── tsconfig.json                       # TypeScript config
├── tsconfig.node.json                  # TypeScript config for Vite node env
├── package.json                        # Dependencies and scripts
├── .env.example                        # Environment variable template
├── .gitignore
│
└── src/
    ├── main.tsx                        # ReactDOM.createRoot entry
    ├── App.tsx                         # Root component — state + layout
    ├── index.css                       # Global reset, fonts, scrollbar, keyframes
    │
    ├── tokens/
    │   └── brand.ts                    # Addverb brand color tokens (single source of truth)
    │
    ├── types/
    │   └── index.ts                    # All TypeScript interfaces (ChatResponse, WidgetSpec, etc.)
    │
    ├── data/
    │   └── mockResponse.ts             # Hardcoded MOCK_RESPONSE + SAMPLE_QUERIES
    │
    ├── services/
    │   └── api.ts                      # queryWMS() — mock now, real fetch() scaffolded
    │
    └── components/
        ├── ChatPanel.tsx               # Left sidebar: logo, history, textarea, send button
        ├── ResultsPanel.tsx            # Right panel: query bar, chips, tabs, content
        ├── IntentChips.tsx             # Detected intent chips strip
        ├── IntentTabs.tsx              # Tab bar (ALL INTENTS + one per candidate)
        ├── AllIntentsPanel.tsx         # Overview of all candidates with confidence bars
        ├── IntentTabContent.tsx        # Single intent: tools + summary + widgets
        ├── SectionHeader.tsx           # Red-bar section title (Addverb style)
        ├── Skeleton.tsx                # Shimmer loading placeholder
        ├── DebugAccordion.tsx          # Collapsible raw JSON viewer
        │
        └── widgets/
            ├── WidgetCard.tsx          # Shared card shell with red-bar header
            ├── WidgetRenderer.tsx      # Switch dispatcher → correct widget
            ├── KPICardsWidget.tsx      # 3-column KPI metric cards
            ├── TableWidget.tsx         # Generic sortable table (status badges, red numbers)
            ├── BarChartWidget.tsx      # Recharts BarChart (zone comparison)
            ├── LineChartWidget.tsx     # Recharts LineChart (trend over time)
            └── AlertListWidget.tsx     # Severity-colored alert rows
```

---

## Switching to Real Backend

In `src/services/api.ts`:

```typescript
const useMock = false; // ← change this

// Set your API URL in .env:
# VITE_API_BASE_URL=http://your-backend.com/api
```

The backend must accept:
```
POST /api/query
Content-Type: application/json

{ "query": "..." }
```

And return a `ChatResponse` object matching the types in `src/types/index.ts`.

---

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| React | 18 | UI framework |
| TypeScript | 5 | Type safety |
| Vite | 5 | Dev server + bundler |
| Recharts | 2.10 | Bar + Line charts |
| Google Fonts | — | Barlow + Barlow Condensed |

No Tailwind, no paid APIs, no UI component libraries — pure inline styles for zero-dependency portability.
