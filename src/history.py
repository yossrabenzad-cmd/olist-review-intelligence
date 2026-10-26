"""Save a summary of every Review Radar analysis, so complaints can be followed over time.

Privacy by design (requirement R9):
- only summaries are stored: counts, complaint share, theme sizes and typical words;
  never the review text itself;
- every query uses placeholders (?), so input can never change the SQL;
- the database file lives in data/, which is never published.
"""
import json
import sqlite3
from datetime import datetime

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at          TEXT    NOT NULL,
    source          TEXT    NOT NULL,
    n_reviews       INTEGER NOT NULL,
    n_complaints    INTEGER NOT NULL,
    complaint_share REAL    NOT NULL,
    themes          TEXT    NOT NULL
)
"""


def connect(db_path):
    con = sqlite3.connect(db_path)
    con.execute(SCHEMA)
    return con


def save_run(db_path, source, summary, themes, run_at=None):
    """Store one analysis. `themes` is the list from find_themes; examples are dropped."""
    theme_summary = [{"size": t["size"], "share": t["share"], "words": t["words"]} for t in themes]
    run_at = run_at or datetime.now().isoformat(timespec="seconds")
    with connect(db_path) as con:
        cur = con.execute(
            "INSERT INTO runs (run_at, source, n_reviews, n_complaints, complaint_share, themes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (run_at, source, summary["n_reviews"], summary["n_complaints"],
             summary["complaint_share"], json.dumps(theme_summary, ensure_ascii=False)))
        return cur.lastrowid


def load_runs(db_path, limit=50):
    """Latest runs first, with the top words of the biggest theme for a quick read."""
    with connect(db_path) as con:
        df = pd.read_sql_query(
            "SELECT run_id, run_at, source, n_reviews, n_complaints, complaint_share, themes "
            "FROM runs ORDER BY run_id DESC LIMIT ?", con, params=(limit,))
    df["top_theme"] = df["themes"].map(
        lambda s: ", ".join(json.loads(s)[0]["words"][:4]) if json.loads(s) else "")
    return df.drop(columns="themes")
