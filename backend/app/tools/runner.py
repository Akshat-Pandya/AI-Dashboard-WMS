import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.schemas import Intent, IntentScore
from app.core.database import SessionLocal
from app.ai.thresholds import MAX_INTENTS_PER_QUERY
from app.tools.registry import INTENT_TOOL_MAP, INTENT_DATA_KEY, INTENT_PARAM_HINTS


def run_tools(
    intents: List[IntentScore],
    db: Session,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    params = params or {}
    results: Dict[str, Any] = {}

    # ── Cap total intents to avoid overloading the DB ────────────────────────
    # Sort by confidence descending so we run the most relevant tools first
    sorted_intents = sorted(intents, key=lambda s: s.confidence, reverse=True)
    sorted_intents = sorted_intents[:MAX_INTENTS_PER_QUERY]

    # ── Build task list ──────────────────────────────────────────────────────
    # FIX: deduplicate by (tool_fn, data_key) pair, NOT just tool_fn.
    # This allows INVENTORY_LOOKUP and ZONE_INVENTORY_COMPARE to both run
    # get_inventory_by_zone but store results under different keys.
    seen_pairs = set()
    tasks: List[tuple] = []   # (data_key, tool_fn, merged_params)

    for score in sorted_intents:
        intent = score.intent

        if intent == Intent.UNKNOWN:
            continue

        tool_fn = INTENT_TOOL_MAP.get(intent)
        if tool_fn is None:
            print(f"⚠️  No tool registered for intent: {intent.value}")
            continue

        data_key = INTENT_DATA_KEY[intent]
        pair = (tool_fn, data_key)

        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        # Merge intent-specific param hints on top of caller-supplied params
        # Caller params win if there's a conflict (explicit > implicit)
        hint = INTENT_PARAM_HINTS.get(intent, {})
        merged_params = {**hint, **params}   # caller params override hints

        tasks.append((data_key, tool_fn, merged_params))

    if not tasks:
        return results

    # ── Execute tools in parallel ─────────────────────────────────────────────
    def _run(data_key: str, tool_fn, merged_params: Dict) -> tuple:
        """Each thread gets its own DB session — SQLAlchemy sessions are not thread-safe."""
        thread_db = SessionLocal()
        try:
            output = tool_fn(db=thread_db, params=merged_params)
            return data_key, output, None
        except Exception:
            return data_key, None, traceback.format_exc()
        finally:
            thread_db.close()

    with ThreadPoolExecutor(max_workers=min(len(tasks), 8)) as pool:
        futures = {
            pool.submit(_run, dk, fn, mp): dk
            for dk, fn, mp in tasks
        }
        for future in as_completed(futures):
            data_key, output, error = future.result()
            if error:
                print(f"❌ Tool error [{data_key}]:\n{error}")
                # FIX: Return structured error so summary LLM can acknowledge it
                # instead of silently omitting the widget
                results[data_key] = {
                    "error": "Tool execution failed",
                    "detail": error.splitlines()[-1],  # last line of traceback
                }
            else:
                results[data_key] = output

    return results