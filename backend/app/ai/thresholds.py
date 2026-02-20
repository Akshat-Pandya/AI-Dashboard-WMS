from app.core.schemas import IntentResult, IntentScore

INTENT_CONFIDENCE_THRESHOLD = 0.6
MAX_INTENTS_PER_QUERY = 3

def filter_intents(result: IntentResult) -> list[IntentScore]:
    intents = [
        s for s in result.intents
        if s.confidence >= INTENT_CONFIDENCE_THRESHOLD
    ]

    intents = sorted(intents, key=lambda s: s.confidence, reverse=True)
    return intents[:MAX_INTENTS_PER_QUERY]