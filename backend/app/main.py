from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

from app.core.schemas     import IntentRequest, WidgetResponse, QueryResponse
from app.core.db_session  import get_db
from app.core.database    import engine, Base
from app.core.models      import SavedDashboard          # ← NEW: registers ORM model

from app.ai.intent_llm       import classify_intent
from app.ai.keyword_fallback  import keyword_fallback

from app.api.query       import router as query_router
from app.api.dashboards  import router as dashboards_router   # ← NEW

# Auto-create saved_dashboards table if it doesn't exist (idempotent)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="WMS Generative API")

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(query_router)
app.include_router(dashboards_router)    # ← NEW: /dashboards/* endpoints


# ── Legacy chat endpoint (kept for compatibility) ─────────────────────────────
@app.post("/chat", response_model=WidgetResponse)
def chat(req: IntentRequest, db: Session = Depends(get_db)):
    intent_result  = classify_intent(req.query)
    primary_intent = intent_result.intents[0].intent

    if primary_intent.name == "UNKNOWN":
        primary_intent = keyword_fallback(req.query)

    if primary_intent.name == "UNKNOWN":
        return WidgetResponse(
            type="TEXT",
            summary=["I can answer warehouse data questions only."]
        )

    return WidgetResponse(
        type="TEXT",
        summary=[f"Intent detected: {primary_intent.name}. Tool execution not enabled yet."]
    )


# ── Debug endpoints ───────────────────────────────────────────────────────────
@app.get("/debug/inventory")
def debug_inventory(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM inventory_items LIMIT 10"))
    return [dict(row._mapping) for row in result]

@app.get("/debug/outbound")
def debug_outbound(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM outbound_orders LIMIT 10"))
    return [dict(row._mapping) for row in result]

@app.get("/debug/inbound")
def debug_inbound(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM inbound_asns LIMIT 10"))
    return [dict(row._mapping) for row in result]

@app.get("/debug/tasks")
def debug_tasks(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM warehouse_tasks LIMIT 10"))
    return [dict(row._mapping) for row in result]

@app.get("/debug/kpis")
def debug_kpis(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM warehouse_kpis"))
    return [dict(row._mapping) for row in result]

@app.get("/debug/zones")
def debug_zones(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM zone_utilization"))
    return [dict(row._mapping) for row in result]

@app.get("/debug/alerts")
def debug_alerts(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM warehouse_alerts"))
    return [dict(row._mapping) for row in result]