import pandas as pd

from src.agent import queue_summary, run
from src.approvals import db, pull, push, setup
from src.drafts import draft_queue

GOOD = ("Tak for din anmeldelse, og undskyld, at du ikke har fået svar på dine mails. "
        "Skriv til os med dit ordrenummer, så ser vi på sagen. Venlig hilsen, Shop A")


class FakeNotion:
    """Stands in for the Notion API: remembers pages and lets a test play the human."""

    def __init__(self):
        self.pages = {}

    def post(self, path, body):
        if path == "/databases":
            return {"id": "db1"}
        if path == "/pages":
            pid = f"p{len(self.pages) + 1}"
            self.pages[pid] = body["properties"]
            return {"id": pid}
        if path.endswith("/query"):
            done = [{"id": pid, "properties": {
                        "Review ID": {"rich_text": [{"plain_text": p["Review ID"]["rich_text"][0]["text"]["content"]}]},
                        "Status": {"select": {"name": p["Status"]["select"]["name"]}},
                        "Draft": {"rich_text": [{"plain_text": p["Draft"]["rich_text"][0]["text"]["content"]}]}}}
                    for pid, p in self.pages.items() if p["Status"]["select"]["name"] in ("Approved", "Rejected")]
            return {"results": done, "has_more": False}
        raise AssertionError(path)

    def decide(self, pid, status, draft=None):
        self.pages[pid]["Status"]["select"]["name"] = status
        if draft:
            self.pages[pid]["Draft"]["rich_text"][0]["text"]["content"] = draft


def prepared(tmp_path):
    db_path = tmp_path / "agent.db"
    csv = tmp_path / "r.csv"
    pd.DataFrame({"text": ["Ingen svar på mails", "Pakken kom aldrig", "Svindel, jeg går til politiet"],
                  "rating": [1, 1, 1]}).to_csv(csv, index=False)
    run(csv, "Shop A", db_path=db_path)
    draft_queue("Shop A", generate=lambda m: GOOD, db_path=db_path)
    notion = FakeNotion()
    setup(notion, "page1", db_path=db_path)
    return db_path, notion


def test_push_sends_each_complaint_once(tmp_path):
    db_path, notion = prepared(tmp_path)
    assert push(notion, "Shop A", db_path=db_path) == 3
    assert push(notion, "Shop A", db_path=db_path) == 0
    statuses = sorted(p["Status"]["select"]["name"] for p in notion.pages.values())
    assert statuses == ["Escalated", "Waiting", "Waiting"]


def test_pull_records_decisions_and_edits(tmp_path):
    db_path, notion = prepared(tmp_path)
    push(notion, "Shop A", db_path=db_path)
    waiting = [pid for pid, p in notion.pages.items() if p["Status"]["select"]["name"] == "Waiting"]
    notion.decide(waiting[0], "Approved", draft="Redigeret svar. Venlig hilsen, Shop A")
    notion.decide(waiting[1], "Rejected")
    assert pull(notion, "Shop A", db_path=db_path) == {"approved": 1, "rejected": 1}
    assert pull(notion, "Shop A", db_path=db_path) == {"approved": 0, "rejected": 0}
    assert queue_summary(db_path, "Shop A") == {"approved": 1, "rejected": 1, "escalated": 1}
    with db(db_path) as con:
        rows = con.execute("SELECT decision, final_text FROM decisions ORDER BY decision").fetchall()
    assert rows == [("approved", "Redigeret svar. Venlig hilsen, Shop A"), ("rejected", None)]
