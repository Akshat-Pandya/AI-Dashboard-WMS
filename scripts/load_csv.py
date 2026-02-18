import os
import pandas as pd
from sqlalchemy import create_engine, text

# -----------------------
# DB CONFIG
# -----------------------
DB_URL = "mysql+pymysql://root:root@localhost:3307/wms"
CSV_DIR = "db/seed/csv"

engine = create_engine(DB_URL)

# -----------------------
# Helpers
# -----------------------
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def normalize_values(df: pd.DataFrame) -> pd.DataFrame:
    df = df.where(pd.notnull(df), None)

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(
                lambda x: None if x in ("NULL", "null", "") else x
            )
    return df

# -----------------------
# Main loader
# -----------------------
def load_csvs():
    with engine.begin() as conn:
        for file in os.listdir(CSV_DIR):
            if not file.endswith(".csv"):
                continue

            table_name = file.replace(".csv", "")
            file_path = os.path.join(CSV_DIR, file)

            print(f"\n📥 Loading {file} → {table_name}")

            df = pd.read_csv(file_path)
            df = normalize_columns(df)
            df = normalize_values(df)

            # Truncate table for deterministic reload
            conn.execute(text(f"TRUNCATE TABLE {table_name}"))

            # Bulk insert
            df.to_sql(
                table_name,
                con=conn,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=500
            )

            print(f"✅ Inserted {len(df)} rows into {table_name}")

    print("\n🎉 All CSV data loaded successfully.")

# -----------------------
# Entry point
# -----------------------
if __name__ == "__main__":
    load_csvs()
