"""Convert the raw Olist CSV files and the Nordic reviews to Parquet for BigQuery. Run once:
    python src/export_bigquery.py

Writes data/bigquery/<table>.parquet (never published). Then, in the BigQuery console,
create a dataset called olist and upload each file as a table with the same name
(Create table > Upload > Parquet). The queries in sql/bigquery/ run on those tables.

Parquet keeps column types (dates stay dates) and is compressed, so every file
is under the 10 MB limit for uploads from the browser.
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
OUT = BASE / "data" / "bigquery"

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
DATE_COLUMNS = {
    "orders": ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
               "order_delivered_customer_date", "order_estimated_delivery_date"],
    "order_items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
    "leads": ["first_contact_date"],
    "deals": ["won_date"],
}

OUT.mkdir(parents=True, exist_ok=True)
for table, file in TABLES.items():
    df = pd.read_csv(RAW / file, encoding="utf-8-sig")
    for col in DATE_COLUMNS.get(table, []):
        df[col] = pd.to_datetime(df[col]).astype("datetime64[us]")
    if table == "geolocation":
        # 1 million rows with many duplicates: keep one point per zip prefix (average position)
        df = (df.groupby("geolocation_zip_code_prefix", as_index=False)
                .agg(geolocation_lat=("geolocation_lat", "mean"),
                     geolocation_lng=("geolocation_lng", "mean"),
                     geolocation_city=("geolocation_city", "first"),
                     geolocation_state=("geolocation_state", "first")))
    df.to_parquet(OUT / f"{table}.parquet", index=False, compression="gzip")
    print(f"{table:22} {len(df):>9,} rows")

nordic = []
for lang, market in [("da", "Denmark"), ("sv", "Sweden"), ("no", "Norway")]:
    d = pd.read_csv(RAW / "scandisent" / "ScandiSent" / f"{lang}.csv")
    d["market"] = market
    d["sentiment"] = d["label"].map({0: "negative", 1: "positive"})
    nordic.append(d[["market", "sentiment", "text"]])
nordic = pd.concat(nordic, ignore_index=True)
nordic.insert(0, "review_id", range(1, len(nordic) + 1))
nordic.to_parquet(OUT / "nordic_reviews.parquet", index=False, compression="gzip")
print(f"{'nordic_reviews':22} {len(nordic):>9,} rows")
