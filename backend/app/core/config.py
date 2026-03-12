# app/core/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Explicit path — works regardless of where uvicorn is launched from
BASE_DIR = Path(__file__).resolve().parent.parent.parent  
load_dotenv(BASE_DIR / ".env")

# ── LLM / Ollama ─────────────────────────────────────────────────────────────
OLLAMA_URL  = os.getenv("OLLAMA_URL",  "http://localhost:11434/api/generate")
MODEL_NAME  = os.getenv("MODEL_NAME",  "llama3.1:8b")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "45"))   

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")             

# ── App behaviour ─────────────────────────────────────────────────────────────
CORS_ORIGINS            = os.getenv("CORS_ORIGINS", "http://localhost:5173")
QUERY_CACHE_SIZE        = int(os.getenv("QUERY_CACHE_SIZE", "15"))
INTENT_CONFIDENCE_THRESHOLD = float(os.getenv("INTENT_CONFIDENCE_THRESHOLD", "0.6"))

# ── Tool defaults (overridable without code changes) ──────────────────────────
DEFAULT_ALERT_LIMIT     = int(os.getenv("DEFAULT_ALERT_LIMIT",    "20"))
DEFAULT_TASK_LIMIT      = int(os.getenv("DEFAULT_TASK_LIMIT",     "50"))
DEFAULT_ORDER_LIMIT     = int(os.getenv("DEFAULT_ORDER_LIMIT",    "25"))
DEFAULT_INVENTORY_LIMIT = int(os.getenv("DEFAULT_INVENTORY_LIMIT","100"))
DEFAULT_ASN_LIMIT       = int(os.getenv("DEFAULT_ASN_LIMIT",      "25"))
DEFAULT_KPI_LIMIT       = int(os.getenv("DEFAULT_KPI_LIMIT",      "10"))


# ── Startup validation ────────────────────────────────────────────────────────
# Catches missing required vars at boot, not buried inside a request.
_REQUIRED = {
    "DATABASE_URL": DATABASE_URL,
    "OLLAMA_URL":   OLLAMA_URL,
    "MODEL_NAME":   MODEL_NAME,
}

def validate_config() -> None:
    missing = [k for k, v in _REQUIRED.items() if not v]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Set them in your .env file or as system environment variables."
        )