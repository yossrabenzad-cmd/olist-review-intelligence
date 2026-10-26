import json
import sqlite3

from src.history import load_runs, save_run

SUMMARY = {"n_reviews": 200, "n_complaints": 30, "complaint_share": 15.0}
THEMES = [{"size": 20, "share": 66.7, "words": ["refund", "money", "email", "reply"],
           "examples": ["Private review text that must never be stored"]}]


def test_save_and_load_latest_first(tmp_path):
    db = tmp_path / "history.db"
    save_run(db, "text box", SUMMARY, THEMES, run_at="2026-10-01T10:00:00")
    save_run(db, "reviews.csv", {**SUMMARY, "complaint_share": 10.0}, [], run_at="2026-10-08T10:00:00")
    runs = load_runs(db)
    assert runs["run_at"].tolist() == ["2026-10-08T10:00:00", "2026-10-01T10:00:00"]
    assert runs["complaint_share"].tolist() == [10.0, 15.0]
    assert runs["top_theme"].tolist() == ["", "refund, money, email, reply"]


def test_review_text_is_never_stored(tmp_path):
    db = tmp_path / "history.db"
    save_run(db, "text box", SUMMARY, THEMES)
    raw = sqlite3.connect(db).execute("SELECT themes FROM runs").fetchone()[0]
    assert "Private review text" not in raw
    assert json.loads(raw) == [{"size": 20, "share": 66.7, "words": ["refund", "money", "email", "reply"]}]


def test_input_cannot_change_the_sql(tmp_path):
    db = tmp_path / "history.db"
    evil = "x'); DROP TABLE runs; --"
    save_run(db, evil, SUMMARY, [])
    assert load_runs(db)["source"].tolist() == [evil]
