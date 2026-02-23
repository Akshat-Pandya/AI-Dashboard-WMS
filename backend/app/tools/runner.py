"""
runner.py
Executes the tools that correspond to the detected intents.

Design decisions:
  - Tools run in parallel via ThreadPoolExecutor (they are I/O bound DB calls)
  - Intent.UNKNOWN is silently skipped
  - If a tool raises, the error is captured and stored so one failure never
    kills the whole response
  - Results are keyed by INTENT_DATA_KEY so the frontend / summary LLM always
    gets a stable, predictable structure
"""
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.schemas import Intent, IntentScore
from app.tools.registry import INTENT_TOOL_MAP, INTENT_DATA_KEY


def run_tools(
    intents: List[IntentScore],
    db: Session,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute the tools for every detected intent in parallel.

    Returns a flat dict keyed by INTENT_DATA_KEY values, e.g.
    {
        "alerts":          { "count": 3, "alerts": [...] },
        "low_stock":       { "count": 5, "items": [...] },
        "zone_comparison": { "zones": [...] },
    }
    """
    params = params or {}
    results: Dict[str, Any] = {}

    # Deduplicate: multiple intents might map to the same tool
    seen_tools = set()
    tasks: List[tuple] = []   # (data_key, callable)

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
        try:
            output = tool_fn(db=db, params=params)
            return data_key, output, None
        except Exception:
            tb = traceback.format_exc()
            print(f"❌ FULL ERROR [{data_key}]:\n{tb}")  # already there
            return data_key, None, tb

    with ThreadPoolExecutor(max_workers=min(len(tasks), 8)) as pool:
        futures = {pool.submit(_run, dk, fn): dk for dk, fn in tasks}
        for future in as_completed(futures):
            data_key, output, error = future.result()
            if error:
                print(f"⚠️  Tool error [{data_key}]:\n{error}")
                results[data_key] = {"error": "Tool execution failed"}
            else:
                results[data_key] = output

    return results
