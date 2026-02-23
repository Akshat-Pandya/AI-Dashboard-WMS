from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.intent_llm import classify_intent

router = APIRouter()


class QueryRequest(BaseModel):
    query: str


@router.post("/query")
def query_wms(req: QueryRequest):

    intent_result = classify_intent(req.query)

    return {
        "query": req.query,
        "intents": [
            {
                "intent": score.intent.value,
                "confidence": score.confidence
            }
            for score in intent_result.intents
        ]
    }