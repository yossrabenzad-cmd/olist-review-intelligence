"""Review-to-Action Agent, piece 1: pick up only NEW reviews and queue the complaints.

Each run:
  1. reads a reviews CSV (a Trustpilot export or any CSV with a text column);
  2. gives every review a fingerprint, so a review already seen is skipped next time;
  3. labels the new reviews (star rating if present, otherwise the fine-tuned model);
  4. tags each complaint with its themes (the same Danish and English keywords as the snapshot);
  5. saves complaints to a queue with status "new", ready for reply drafting (piece 2).

Privacy: review text is kept only in data/agent.db on this laptop. data/ is never published.

Run from the project folder, with the virtual environment active:
    python src/agent.py data/demo/demo_reviews_da.csv --shop "Example Shop"
Run it twice: the second run should find 0 new reviews.
"""
import argparse
import hashlib
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from src.snapshot import COMPLAINTS, label, load  # noqa: E402

DB_PATH = BASE / "data" / "agent.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    review_id   TEXT PRIMARY KEY,          -- fingerprint of shop + text
    shop        TEXT NOT NULL,
    first_seen  TEXT NOT NULL,
    text        TEXT NOT NULL,
    sentiment   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS queue (
    review_id   TEXT PRIMARY KEY REFERENCES reviews(review_id),
    themes      TEXT NOT NULL,             -- comma-separated complaint themes
    status      TEXT NOT NULL DEFAULT 'new',   -- new, drafted, approved, rejected
    draft       TEXT,
    updated_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
    run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at      TEXT NOT NULL,
    shop        TEXT NOT NULL,
    source      TEXT NOT NULL,
    n_read      INTEGER NOT NULL,
    n_new       INTEGER NOT NULL,
    n_queued    INTEGER NOT NULL
);
"""


def connect(db_path=DB_PATH):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    return con


def fingerprint(shop, text):
    """Same shop and same text (ignoring case and spacing) give the same id."""
    norm = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(f"{shop.lower()}|{norm}".encode("utf-8")).hexdigest()[:16]


def complaint_themes(text):
    low = text.lower()
    found = [name for name, pat in COMPLAINTS.items() if re.search(pat, low)]
    return found or ["Other"]


def new_only(con, shop, df):
    """Keep the rows whose fingerprint is not in the database yet (and drop duplicates in the file)."""
    df = df.copy()
    df["review_id"] = [fingerprint(shop, t) for t in df["review"]]
    df = df.drop_duplicates("review_id")
    seen = {r[0] for r in con.execute("SELECT review_id FROM reviews WHERE shop = ?", (shop,))}
    return df[~df["review_id"].isin(seen)].reset_index(drop=True)


def run(csv_path, shop, db_path=DB_PATH, model=None):
    """One agent run. Returns a small summary dict."""
    now = datetime.now().isoformat(timespec="seconds")
    df = load(csv_path)
    with connect(db_path) as con:
        new = new_only(con, shop, df)
        n_queued = 0
        if len(new):
            new = label(new, model)
            for row in new.itertuples():
                con.execute("INSERT INTO reviews (review_id, shop, first_seen, text, sentiment) "
                            "VALUES (?, ?, ?, ?, ?)",
                            (row.review_id, shop, now, row.review, row.sentiment))
                if row.sentiment == "negative":
                    con.execute("INSERT INTO queue (review_id, themes, updated_at) VALUES (?, ?, ?)",
                                (row.review_id, ", ".join(complaint_themes(row.review)), now))
                    n_queued += 1
        con.execute("INSERT INTO runs (run_at, shop, source, n_read, n_new, n_queued) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (now, shop, Path(csv_path).name, len(df), len(new), n_queued))
    return {"read": len(df), "new": len(new), "queued": n_queued}


def queue_summary(db_path=DB_PATH, shop=None):
    """Queue size per status, for a quick look."""
    with connect(db_path) as con:
        sql = ("SELECT q.status, COUNT(*) FROM queue q JOIN reviews r USING (review_id) "
               + ("WHERE r.shop = ? " if shop else "") + "GROUP BY q.status")
        return dict(con.execute(sql, (shop,) if shop else ()).fetchall())


def main():
    ap = argparse.ArgumentParser(description="Review-to-Action Agent: queue new complaints.")
    ap.add_argument("csv")
    ap.add_argument("--shop", required=True)
    a = ap.parse_args()
    res = run(a.csv, a.shop)
    print(f"Read {res['read']} reviews: {res['new']} new, {res['queued']} complaints queued.")
    print(f"Queue for {a.shop}: {queue_summary(shop=a.shop)}")


if __name__ == "__main__":
    main()
