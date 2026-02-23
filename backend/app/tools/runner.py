"""
runner.py
Executes the tools that correspond to the detected intents.

FIX: SQLAlchemy sessions are not thread-safe. Each tool now gets its own
session created from the engine, rather than sharing the request session.
"""
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.schemas import Intent, IntentScore
from app.core.database import SessionLocal          # ← your session factory
from app.tools.registry import INTENT_TOOL_MAP, INTENT_DATA_KEY


def run_tools(
    intents: List[IntentScore],
    db: Session,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    params = params or {}
    results: Dict[str, Any] = {}

    # Deduplicate tools
    seen_tools = set()
    tasks: List[tuple] = []

    for score in intents:
        intent = score.intent
        if intent == Intent.UNKNOWN:
            continue
        tool_fn = INTENT_TOOL_MAP.get(intent)
        if tool_fn is None:
            continue
        if tool_fn in seen_tools:
            continue
        seen_tools.add(tool_fn)
        data_key = INTENT_DATA_KEY[intent]
        tasks.append((data_key, tool_fn))

    if not tasks:
        return results

    def _run(data_key: str, tool_fn) -> tuple:
        # Each thread gets its own independent session
        thread_db = SessionLocal()
        try:
            output = tool_fn(db=thread_db, params=params)
            return data_key, output, None
        except Exception:
            return data_key, None, traceback.format_exc()
        finally:
            thread_db.close()   # always release the connection

    with ThreadPoolExecutor(max_workers=min(len(tasks), 8)) as pool:
        futures = {pool.submit(_run, dk, fn): dk for dk, fn in tasks}
        for future in as_completed(futures):
            data_key, output, error = future.result()
            if error:
                print(f"❌ FULL ERROR [{data_key}]:\n{error}")
                results[data_key] = {"error": "Tool execution failed"}
            else:
                results[data_key] = output

    return results