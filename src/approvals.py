"""Review-to-Action Agent, piece 3: human approval in Notion.

  setup  creates a "Review Approvals" database inside a Notion page you shared with the integration.
  push   sends every drafted or escalated complaint to Notion with Status "Waiting" or "Escalated".
  pull   reads your decisions back: "Approved" or "Rejected". If you edited the Draft in Notion,
         the edited text is what gets saved. Every decision is logged with its time.

Nothing is ever posted to a customer from here: approval only marks a reply as ready.

Set once per PowerShell window (the token stays out of every file):
    $env:NOTION_TOKEN = "your integration secret"
Then, from the project folder with the virtual environment active:
    python src/approvals.py setup --page <page id>
    python src/approvals.py push --shop "Example Shop"
    (approve or reject in Notion)
    python src/approvals.py pull --shop "Example Shop"
"""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from src.agent import DB_PATH, connect  # noqa: E402

API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
MAX_TEXT = 1900   # Notion allows 2,000 characters per text block

EXTRA_SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS notion_pages (
    review_id   TEXT PRIMARY KEY REFERENCES queue(review_id),
    page_id     TEXT NOT NULL,
    pushed_at   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id   TEXT NOT NULL REFERENCES queue(review_id),
    decision    TEXT NOT NULL,          -- approved or rejected
    final_text  TEXT,
    decided_at  TEXT NOT NULL
);
"""


def db(db_path=DB_PATH):
    con = connect(db_path)
    con.executescript(EXTRA_SCHEMA)
    return con


def now():
    return datetime.now().isoformat(timespec="seconds")


class Notion:
    """Tiny Notion client. `post` and `patch` can be replaced in tests."""

    def __init__(self, token=None, session=None):
        import requests
        self.token = token or os.environ.get("NOTION_TOKEN")
        if not self.token:
            raise SystemExit('Set your token first, in PowerShell:  $env:NOTION_TOKEN = "your secret"')
        self.s = session or requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {self.token}",
                               "Notion-Version": NOTION_VERSION, "Content-Type": "application/json"})

    def _call(self, method, path, body=None):
        r = self.s.request(method, f"{API}{path}", json=body, timeout=30)
        if r.status_code >= 300:
            raise SystemExit(f"Notion said {r.status_code}: {r.text[:400]}")
        return r.json()

    def post(self, path, body):
        return self._call("POST", path, body)

    def patch(self, path, body):
        return self._call("PATCH", path, body)


def text(value):
    return [{"type": "text", "text": {"content": (value or "")[:MAX_TEXT]}}]


def plain(prop):
    """Read the plain text of a Notion title or rich_text property."""
    items = prop.get("title") or prop.get("rich_text") or []
    return "".join(i.get("plain_text") or i.get("text", {}).get("content", "") for i in items)


def setup(notion, page_id, db_path=DB_PATH):
    """Create the approvals database under the shared page and remember its id."""
    res = notion.post("/databases", {
        "parent": {"type": "page_id", "page_id": page_id},
        "title": text("Review Approvals"),
        "properties": {
            "Review": {"title": {}},
            "Draft": {"rich_text": {}},
            "Status": {"select": {"options": [
                {"name": "Waiting", "color": "yellow"}, {"name": "Approved", "color": "green"},
                {"name": "Rejected", "color": "red"}, {"name": "Escalated", "color": "orange"}]}},
            "Themes": {"rich_text": {}},
            "Shop": {"rich_text": {}},
            "Review ID": {"rich_text": {}},
        }})
    with db(db_path) as con:
        con.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('notion_database_id', ?)", (res["id"],))
    return res["id"]


def database_id(con):
    row = con.execute("SELECT value FROM settings WHERE key = 'notion_database_id'").fetchone()
    if not row:
        raise SystemExit("Run setup first:  python src/approvals.py setup --page <page id>")
    return row[0]


def push(notion, shop, db_path=DB_PATH):
    """Send drafted and escalated complaints that are not in Notion yet. Returns how many."""
    with db(db_path) as con:
        dbid = database_id(con)
        rows = con.execute(
            "SELECT q.review_id, r.text, q.draft, q.themes, q.status FROM queue q "
            "JOIN reviews r USING (review_id) LEFT JOIN notion_pages n USING (review_id) "
            "WHERE r.shop = ? AND q.status IN ('drafted', 'escalated') AND n.page_id IS NULL",
            (shop,)).fetchall()
        for review_id, review, draft, themes, status in rows:
            page = notion.post("/pages", {"parent": {"database_id": dbid}, "properties": {
                "Review": {"title": text(review)},
                "Draft": {"rich_text": text(draft)},
                "Status": {"select": {"name": "Escalated" if status == "escalated" else "Waiting"}},
                "Themes": {"rich_text": text(themes)},
                "Shop": {"rich_text": text(shop)},
                "Review ID": {"rich_text": text(review_id)},
            }})
            con.execute("INSERT INTO notion_pages (review_id, page_id, pushed_at) VALUES (?, ?, ?)",
                        (review_id, page["id"], now()))
    return len(rows)


def pull(notion, shop, db_path=DB_PATH):
    """Record Approved and Rejected decisions made in Notion. Returns {'approved': n, 'rejected': n}."""
    counts = {"approved": 0, "rejected": 0}
    with db(db_path) as con:
        dbid = database_id(con)
        body = {"filter": {"and": [
            {"property": "Shop", "rich_text": {"equals": shop}},
            {"or": [{"property": "Status", "select": {"equals": "Approved"}},
                    {"property": "Status", "select": {"equals": "Rejected"}}]}]}}
        pages, cursor = [], None
        while True:
            if cursor:
                body["start_cursor"] = cursor
            res = notion.post(f"/databases/{dbid}/query", body)
            pages += res.get("results", [])
            if not res.get("has_more"):
                break
            cursor = res.get("next_cursor")
        for page in pages:
            props = page["properties"]
            review_id = plain(props["Review ID"])
            decision = props["Status"]["select"]["name"].lower()
            current = con.execute("SELECT status FROM queue WHERE review_id = ?", (review_id,)).fetchone()
            if not current or current[0] == decision:
                continue                      # unknown review, or already recorded
            final = plain(props["Draft"]) if decision == "approved" else None
            con.execute("UPDATE queue SET status = ?, draft = COALESCE(?, draft), updated_at = ? "
                        "WHERE review_id = ?", (decision, final, now(), review_id))
            con.execute("INSERT INTO decisions (review_id, decision, final_text, decided_at) "
                        "VALUES (?, ?, ?, ?)", (review_id, decision, final, now()))
            counts[decision] += 1
    return counts


def main():
    ap = argparse.ArgumentParser(description="Human approval of reply drafts in Notion.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("setup")
    s.add_argument("--page", required=True, help="id of the Notion page shared with the integration")
    for name in ("push", "pull"):
        sub.add_parser(name).add_argument("--shop", required=True)
    a = ap.parse_args()
    notion = Notion()
    if a.cmd == "setup":
        print(f"Created the Review Approvals database: {setup(notion, a.page)}")
    elif a.cmd == "push":
        print(f"Sent {push(notion, a.shop)} complaints to Notion. Approve or reject them there.")
    else:
        c = pull(notion, a.shop)
        print(f"Recorded {c['approved']} approved and {c['rejected']} rejected replies.")


if __name__ == "__main__":
    main()
