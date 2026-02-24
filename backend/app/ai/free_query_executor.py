# app/ai/free_query_executor.py
import re
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import text

# Block any mutating or dangerous SQL
BLOCKED_PATTERNS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|EXEC|EXECUTE|GRANT|REVOKE)\b",
    re.IGNORECASE
)

def execute_free_sql(db: Session, sql: str) -> Dict[str, Any]:
    """Execute LLM-generated SQL safely. Returns {columns, rows} or {error}."""
    if BLOCKED_PATTERNS.search(sql):
        return {"error": "Query blocked: only SELECT statements are allowed."}

    if not sql.strip().upper().startswith("SELECT"):
        return {"error": "Only SELECT queries are permitted."}

    try:
        result = db.execute(text(sql))
        columns: List[str] = list(result.keys())
        rows: List[List[Any]] = [list(row) for row in result.fetchall()]
        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }
    except Exception as e:
        print(f"⚠️ Free SQL execution error: {e}")
        return {"error": str(e)}