# app/api/chat.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.schemas import IntentRequest, ChatResponse, TabResponse
from app.core.db_session import get_db

from app.ai.intent_llm import classify_intent
from app.ai.thresholds import filter_intents
from app.ai.param_llm import extract_params
from app.ai.intent_registry import INTENT_REGISTRY
from app.ai.tool_selector import select_tool

from app.ai.presentation_rules import INTENT_WIDGETS
from app.ai.summary_llm import choose_widget_and_summary

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(req: IntentRequest, db: Session = Depends(get_db)):

    intent_result = classify_intent(req.query)
    intents = filter_intents(intent_result)

    tabs: list[TabResponse] = []

    for intent_score in intents:
        intent = intent_score.intent

        tools = INTENT_REGISTRY.get(intent)
        if not tools:
            continue

        params = extract_params(req.query, intent)

        tool = select_tool(intent, tools, params)
        if not tool:
            continue

        data = tool(db=db, params=params)

        allowed_widgets = INTENT_WIDGETS.get(intent, [])
        presentation = choose_widget_and_summary(
            query=req.query,
            data=data,
            allowed_widgets=allowed_widgets
        )

        tabs.append(
            TabResponse(
                intent=intent.value,
                widget=presentation["widget"],
                data=data,
                summary=presentation["summary"]
            )
        )
    
    if not intents:
        return ChatResponse(
            tabs=[
                TabResponse(
                    intent="unknown",
                    widget="TEXT",
                    data={},
                    summary=["I can help with warehouse operational data."]
                )
            ]
        )

    return ChatResponse(tabs=tabs)