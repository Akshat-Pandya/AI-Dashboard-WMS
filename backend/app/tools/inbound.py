from sqlalchemy import text

def get_inbound_asns(db):
    query = text("SELECT * FROM inbound_asns")
    result = db.execute(query)
    return [dict(row._mapping) for row in result]
