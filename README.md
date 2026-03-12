# ADDVERB — AI-Powered WMS Dashboard

> Natural language queries → live warehouse data → dynamic widgets

---

## Overview

Addverb WMS Dashboard is a full-stack, AI-powered warehouse management interface. Users type plain English queries which are classified by intent, executed against a live MySQL warehouse database, and rendered as dynamic UI widgets — tables, charts, alerts, KPIs, and trend lines.

---

## Architecture

| Layer | Stack |
|---|---|
| **Frontend** | React 18 + TypeScript + Vite · Recharts |
| **Backend** | FastAPI (Python 3.12) + SQLAlchemy 2 + PyMySQL |
| **AI Layer** | Ollama (local LLM) — intent, param, summary, free-SQL |
| **Database** | MySQL 8.0+ |
| **Model** | Configurable via `.env` — default `qwen2.5:7b` |

### AI Query Pipeline

Every query flows through 6 stages:

```
User Query
    │
    ▼
1. Intent LLM        → classifies into warehouse intents
    │
    ▼
2. Param LLM         → extracts filters (zone, SKU, severity, limit)
    │
    ▼
3. Tool Runner       → executes DB tools in parallel per intent
    │
    ▼
4. Trend Aggregator  → groups rows by date for trend queries
    │
    ▼
5. Summary LLM       → selects widgets + writes factual summary
    │
    ▼
6. Widget Renderer   → React frontend renders the result
```

---

## Project Structure

```
AI_WMS_NEW/
├── backend/
│   ├── app/
│   │   ├── ai/                  # LLM modules
│   │   │   ├── intent_llm.py
│   │   │   ├── param_llm.py
│   │   │   ├── summary_llm.py
│   │   │   ├── orchestrator.py
│   │   │   ├── widget_registry.py
│   │   │   ├── keyword_fallback.py
│   │   │   ├── free_query_llm.py
│   │   │   └── thresholds.py
│   │   ├── api/                 # FastAPI routes
│   │   ├── core/                # DB session, schemas, models
│   │   ├── tools/               # Tool functions per intent
│   │   └── main.py
│   ├── .env                     # Backend environment variables
│   ├── requirements.txt
│   └── venv/
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── widgets/         # AlertList, Table, BarChart, LineChart, etc.
    │   │   ├── ChatPanel.tsx
    │   │   ├── WidgetRenderer.tsx
    │   │   └── ...
    │   ├── services/
    │   │   ├── api.ts
    │   │   └── buildTabResults.ts
    │   ├── tokens/brand.ts
    │   └── types.ts
    ├── .env                     # Frontend environment variables
    └── package.json
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.12+ |
| Node.js | 18+ (20+ recommended) |
| MySQL | 8.0+ |
| Ollama | Latest — https://ollama.ai |
| Git | Any recent version |

> **Note:** Ollama must be running before starting the backend. The model is downloaded on first use (~4–8 GB depending on model).

---

## Backend Setup

### 1. Clone and navigate

```bash
git clone <your-repo-url>
cd AI_WMS_NEW/backend
```

### 2. Create virtual environment

```bash
python3 -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Create `backend/.env`:

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=wms_db
DB_USER=root
DB_PASSWORD=your_password

# Ollama
OLLAMA_URL=http://localhost:11434/api/generate
MODEL_NAME=qwen2.5:7b
```

### 5. Pull the Ollama model

```bash
# Start Ollama
ollama serve

# In a new terminal — pull the model
ollama pull qwen2.5:7b

# Or alternatively
ollama pull llama3.1:8b
```

### 6. Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

API available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

---

## Frontend Setup

### 1. Navigate to frontend

```bash
cd AI_WMS_NEW/frontend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Configure environment

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 4. Start the dev server

```bash
npm run dev
```

Frontend available at `http://localhost:5173`

---

## Running the Full Stack

Three terminals required, started in this order:

| Terminal | Command |
|---|---|
| **1 — Ollama** | `ollama serve` |
| **2 — Backend** | `cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000` |
| **3 — Frontend** | `cd frontend && npm run dev` |

> **Tip:** Always start Ollama first. The backend connects to Ollama on startup.

---

## Environment Variables

### Backend — `backend/.env`

| Variable | Description |
|---|---|
| `DB_HOST` | MySQL host (default: `localhost`) |
| `DB_PORT` | MySQL port (default: `3306`) |
| `DB_NAME` | Database name |
| `DB_USER` | Database user |
| `DB_PASSWORD` | Database password |
| `OLLAMA_URL` | Ollama API endpoint |
| `MODEL_NAME` | Ollama model name (e.g. `qwen2.5:7b`) |

### Frontend — `frontend/.env`

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Backend API base URL (default: `http://localhost:8000`) |

---

## Supported Query Types

| Intent | Example Queries |
|---|---|
| Warehouse Overview | "Show warehouse overview", "Morning briefing" |
| Alerts | "Show active alerts", "What's critical right now?" |
| Order Status | "Show all orders", "Distribution of orders by status" |
| Inventory Lookup | "Show inventory in Zone A", "Find SKU X" |
| Zone Comparison | "Compare Zone A and Zone B", "Compare all zones" |
| Low Stock | "Which items are running low?", "Show reorder items" |
| Inbound Activity | "Show inbound shipments", "ASN status" |
| Trend Queries | "Alert trend last 7 days", "Inbound shipments over time" |
| Active Tasks | "Show active tasks", "What's being picked right now?" |
| Blocked Tasks | "What tasks are blocked?", "Show stuck tasks" |
| KPIs | "Show KPIs", "Warehouse performance metrics" |
| Free-form | Any warehouse question not covered by the above intents |

---

## Key Dependencies

### Backend

| Package | Version | Purpose |
|---|---|---|
| `fastapi` | 0.129 | Web framework |
| `uvicorn` | 0.41 | ASGI server |
| `sqlalchemy` | 2.0 | ORM and DB sessions |
| `pymysql` | 1.1 | MySQL driver |
| `pydantic` | 2.12 | Data validation |
| `requests` | 2.32 | HTTP calls to Ollama |
| `pandas` | 2.3 | Data manipulation |
| `python-dotenv` | 1.0 | Env variable loading |

### Frontend

| Package | Version | Purpose |
|---|---|---|
| `react` | 18 | UI framework |
| `typescript` | 5 | Type safety |
| `vite` | 7 | Build tool |
| `recharts` | 2.10 | Charts (Bar, Line, etc.) |

---

## Build for Production

### Frontend

```bash
cd frontend
npm run build
# Output in frontend/dist/
```

### Backend

```bash
# Run without --reload for production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Ollama timeout errors | Ensure `ollama serve` is running. Check `OLLAMA_URL` in `.env` matches the Ollama port. |
| DB connection refused | Verify MySQL is running. Check `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` in `backend/.env`. |
| Frontend can't reach backend | Check `VITE_API_BASE_URL` in `frontend/.env`. Ensure backend is on port 8000. Check CORS in `app/main.py`. |
| Model not found | Run `ollama pull <model-name>` where model-name matches `MODEL_NAME` in `.env`. |
| Widgets not rendering | Open browser DevTools console — check for `[WidgetRenderer]` warnings about unresolved `data_key`. |
| Slow LLM responses | Smaller models (`qwen2.5:7b`) are faster. Ensure Ollama has GPU acceleration enabled if available. |
| Only one bar in zone chart | Confirm backend returns `zones[]` with numeric or string-numeric fields in `zone_comparison`. |
