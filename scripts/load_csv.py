import os
import pandas as pd
from sqlalchemy import create_engine, text

DB_URL = "mysql+pymysql://root:root@localhost:3307/wms"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_DIR = os.path.join(BASE_DIR, "db", "seed", "csv")


def camel_to_snake(col):
    out = []
    for c in col:
        if c.isupper():
            out.append("_" + c.lower())
        else:
            out.append(c)
    return "".join(out).lstrip("_")


TABLE_CONFIG = {
    "inbound_asns.csv": "inbound_asns",
    "inventory_items.csv": "inventory_items",
    "outbound_orders.csv": "outbound_orders",
    "warehouse_alerts.csv": "warehouse_alerts",
    "warehouse_kpis.csv": "warehouse_kpis",
    "warehouse_tasks.csv": "warehouse_tasks",
    "zone_utilization.csv": "zone_utilization",
}


def normalize_datetimes(df):
    for col in df.columns:
        if "date" in col or "time" in col or col.endswith("_at"):
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
    return df


def load_csvs():
    engine = create_engine(DB_URL)

    with engine.begin() as conn:
        for file, table in TABLE_CONFIG.items():
            csv_path = os.path.join(CSV_DIR, file)

            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"❌ CSV not found: {csv_path}")

            print(f"📥 Loading {file} → {table}")

            df = pd.read_csv(csv_path)

            # camelCase → snake_case
            df.columns = [camel_to_snake(c) for c in df.columns]

            # 🔥 FIX DATETIME FORMAT
            df = normalize_datetimes(df)

            # idempotent reload
            conn.execute(text(f"DELETE FROM {table}"))

            df.to_sql(
                table,
                con=conn,
                if_exists="append",
                index=False,
                method="multi"
            )

            print(f"✅ {table}: {len(df)} rows inserted")

    print("\n🎉 All CSVs loaded successfully")


if __name__ == "__main__":
    load_csvs()
