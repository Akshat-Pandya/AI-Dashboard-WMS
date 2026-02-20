from fastapi import FastAPI
from app.api.chat import router as chat_router

app = FastAPI(title="WMS GenUI Backend")

# ----------------------
# API Routes
# ----------------------
app.include_router(chat_router)

# ----------------------
# Health Check
# ----------------------
@app.get("/health")
def health():
    return {"status": "ok"}