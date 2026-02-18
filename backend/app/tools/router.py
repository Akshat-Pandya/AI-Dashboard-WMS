from app.core.schemas import Intent
from app.tools.inbound import get_inbound_asns

def run_tool(intent: Intent, db):
    if intent == Intent.OVERVIEW:
        return get_inbound_asns(db)
    return {}
