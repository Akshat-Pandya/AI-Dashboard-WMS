from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.schemas import IntentRequest, WidgetResponse
from app.core.db_session import get_db

from app.ai.intent_llm import classify_intent
from app.ai.keyword_fallback import keyword_fallback

# ✅ import router correctly
from app.api.query import router as query_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="WMS Generative API")

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register API router
app.include_router(query_router, prefix="/api", tags=["Query"])


# =====================================================
# MAIN CHAT ENDPOINT (existing)
# =====================================================
@app.post("/chat", response_model=WidgetResponse)
def chat(req: IntentRequest, db: Session = Depends(get_db)):

    intent_result = classify_intent(req.query)

    # 🔹 pick primary intent (highest confidence)
    primary_intent = intent_result.intents[0].intent

    if primary_intent.name == "UNKNOWN":
        fallback_intent = keyword_fallback(req.query)
        primary_intent = fallback_intent

    if primary_intent.name == "UNKNOWN":
        return {
            "type": "TEXT",
            "summary": ["I can answer warehouse data questions only."]
        }

    return {
        "type": "TEXT",
        "summary": [
            f"Intent detected: {primary_intent.name}. Tool execution not enabled yet."
        ]
    }


# =====================================================
# DEBUG ENDPOINTS
# =====================================================

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