from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.schemas import IntentRequest, WidgetResponse
from app.core.db_session import get_db

from app.ai.intent_llm import classify_intent
from app.ai.fallback import keyword_fallback
from app.tools.router import run_tool
from app.ai.summary_llm import choose_widget_and_summary

app = FastAPI()  

@app.post("/chat", response_model=WidgetResponse)
def chat(req: IntentRequest, db: Session = Depends(get_db)):
    intent_result = classify_intent(req.query)

    if intent_result.intent.name == "UNKNOWN":
        intent_result.intent = keyword_fallback(req.query)

    if intent_result.intent.name == "UNKNOWN":
        return {
            "type": "TEXT",
            "summary": ["I can answer warehouse data questions only."]
        }

    data = run_tool(intent_result.intent, db)
    presentation = choose_widget_and_summary(req.query, data)

    return {
        "type": "WIDGET",
        "widget": presentation["widget"],
        "data": data,
        "summary": presentation["summary"]
    }


# ======================
# DEBUG ENDPOINTS
# ======================

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
