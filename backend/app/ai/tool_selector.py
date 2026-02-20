from typing import List, Callable
from sqlalchemy.orm import Session

from app.core.schemas import Intent


def select_tool(
    intent: Intent,
    tools: List[Callable],
    params: dict
) -> Callable:
    """
    Decide which tool to run for an intent.
    Rule-based for now (NO AI).
    """

    # Most intents currently have 1 tool
    if len(tools) == 1:
        return tools[0]

    # Future-proof examples
    if intent == Intent.WAREHOUSE_OVERVIEW:
        return tools[0]

    if intent == Intent.LOW_STOCK:
        return tools[0]

    return tools[0]  # safe default