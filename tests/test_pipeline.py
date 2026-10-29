import pandas as pd

from src.agent import connect
from src.approvals import setup
from src.pipeline import run_once
from test_approvals import GOOD, FakeNotion


def test_full_loop_then_nothing_new(tmp_path):
    db = tmp_path / "agent.db"
    csv = tmp_path / "r.csv"
    pd.DataFrame({"text": ["Ingen svar på mails", "Super service", "Svindel, jeg går til politiet"],
                  "rating": [1, 5, 1]}).to_csv(csv, index=False)
    notion = FakeNotion()
    setup(notion, "page1", db_path=db)

    first = run_once(csv, "Shop A", lambda m: GOOD, notion, db_path=db)
    assert (first["new_reviews"], first["queued"], first["drafted"], first["escalated"], first["pushed"]) == (3, 2, 1, 1, 2)

    pid = next(p for p, v in notion.pages.items() if v["Status"]["select"]["name"] == "Waiting")
    notion.decide(pid, "Approved")
    second = run_once(csv, "Shop A", lambda m: GOOD, notion, db_path=db)
    assert (second["approved"], second["new_reviews"], second["pushed"], second["status"]) == (1, 0, 0, "ok")

    with connect(db) as con:
        assert con.execute("SELECT COUNT(*) FROM pipeline_runs WHERE status = 'ok'").fetchone()[0] == 2


def test_a_failed_step_is_logged_not_hidden(tmp_path):
    db = tmp_path / "agent.db"
    notion = FakeNotion()
    setup(notion, "page1", db_path=db)
    s = run_once(tmp_path / "missing.csv", "Shop A", lambda m: GOOD, notion, db_path=db)
    assert s["status"] == "failed" and s["error"]
    with connect(db) as con:
        assert con.execute("SELECT status FROM pipeline_runs").fetchone()[0] == "failed"


def test_a_rate_limit_keeps_finished_drafts_and_still_sends_them(tmp_path):
    db = tmp_path / "agent.db"
    csv = tmp_path / "r.csv"
    pd.DataFrame({"text": ["Ingen svar på mails", "Pakken kom aldrig", "Forkert vare"],
                  "rating": [1, 1, 1]}).to_csv(csv, index=False)
    notion = FakeNotion()
    setup(notion, "page1", db_path=db)
    calls = iter([GOOD])

    def model(messages):
        try:
            return next(calls)
        except StopIteration:
            raise RuntimeError("Groq said 429")

    s = run_once(csv, "Shop A", model, notion, db_path=db)
    assert (s["status"], s["drafted"], s["pushed"]) == ("partial", 1, 1)
    assert "429" in s["error"]
    with connect(db) as con:
        assert con.execute("SELECT COUNT(*) FROM queue WHERE status = 'drafted'").fetchone()[0] == 1
        assert con.execute("SELECT COUNT(*) FROM queue WHERE status = 'new'").fetchone()[0] == 2
