"""Load the raw Olist CSV files and the Nordic Trustpilot reviews into one SQLite database: data/olist.db. Run once:
    python src/build_db.py

SQLite keeps a whole database in a single file and is built into Python,
so there is no server to install. The database file is never published.
"""
from pathlib import Path
import sqlite3

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
DB = BASE / "data" / "olist.db"

# table name in the database -> CSV file in data/raw
TABLES = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
    "leads": "marketing_funnel/olist_marketing_qualified_leads_dataset.csv",
    "deals": "marketing_funnel/olist_closed_deals_dataset.csv",
}

# Indexes make joins on these columns fast (like an index at the back of a book)
INDEXES = [
    ("orders", "order_id"), ("orders", "customer_id"),
    ("order_items", "order_id"), ("order_items", "seller_id"), ("order_items", "product_id"),
    ("reviews", "order_id"), ("payments", "order_id"),
    ("customers", "customer_id"), ("products", "product_id"),
    ("deals", "mql_id"), ("deals", "seller_id"),
]

with sqlite3.connect(DB) as con:
    for table, file in TABLES.items():
        df = pd.read_csv(RAW / file, encoding="utf-8-sig")   # utf-8-sig drops a hidden start-of-file mark
        df.to_sql(table, con, if_exists="replace", index=False)
        print(f"{table:22} {len(df):>9,} rows")
    # Nordic Trustpilot reviews (ScandiSent): one table for Denmark, Sweden and Norway
    nordic = []
    for lang, market in [("da", "Denmark"), ("sv", "Sweden"), ("no", "Norway")]:
        d = pd.read_csv(RAW / "scandisent" / "ScandiSent" / f"{lang}.csv")
        d["market"] = market
        d["sentiment"] = d["label"].map({0: "negative", 1: "positive"})
        nordic.append(d[["market", "sentiment", "text"]])
    nordic = pd.concat(nordic, ignore_index=True)
    nordic.insert(0, "review_id", range(1, len(nordic) + 1))
    nordic.to_sql("nordic_reviews", con, if_exists="replace", index=False)
    print(f"{'nordic_reviews':22} {len(nordic):>9,} rows")

    for table, column in INDEXES:
        con.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_{column} ON {table}({column})")

print(f"\nSaved {DB.name} ({DB.stat().st_size / 1e6:.0f} MB)")
