"""Review-to-Action Agent: the whole loop in one run, for a daily schedule.

Order of one run:
  1. pull     record yesterday's Approved / Rejected decisions from Notion
  2. collect  read the review export, keep only reviews not seen before
  3. draft    write Danish replies for new complaints (with guardrails and escalation)
  4. push     send new drafts and escalations to Notion for a human to decide
Each run is logged in data/agent.db (table pipeline_runs) and in data/agent_runs.log.

Run from the project folder, with the virtual environment active:
    python src/pipeline.py --csv data/demo/demo_reviews_da.csv --shop "Example Shop" --model groq
Needs GROQ_API_KEY (for --model groq) and NOTION_TOKEN as environment variables.
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from src.agent import DB_PATH, connect, run as collect  # noqa: E402
from src.approvals import Notion, pull, push  # noqa: E402
from src.drafts import draft_queue, groq_llm, local_llm  # noqa: E402

LOG_FILE = BASE / "data" / "agent_runs.log"

SCHEMA = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL, shop TEXT NOT NULL,
    approved INTEGER, rejected INTEGER, new_reviews INTEGER, queued INTEGER,
    drafted INTEGER, flagged INTEGER, escalated INTEGER, pushed INTEGER,
    status TEXT NOT NULL, error TEXT
);
"""


def run_once(csv, shop, generate, notion, db_path=DB_PATH, limit=50):
    """One full loop. Returns a summary dict; errors are logged, never hidden."""
    started = datetime.now().isoformat(timespec="seconds")
    s = {"approved": 0, "rejected": 0, "new_reviews": 0, "queued": 0,
         "drafted": 0, "flagged": 0, "escalated": 0, "pushed": 0, "status": "ok", "error": None}
    try:
        s.update(pull(notion, shop, db_path=db_path))
        c = collect(csv, shop, db_path=db_path)
        s["new_reviews"], s["queued"] = c["new"], c["queued"]
        results = draft_queue(shop, limit=limit, generate=generate, db_path=db_path)
        for r in results:
            s[r["status"]] += 1
        s["pushed"] = push(notion, shop, db_path=db_path)
    except (Exception, SystemExit) as e:          # keep a record even when a step fails
        s["status"], s["error"] = "failed", str(e)[:500]
    with connect(db_path) as con:
        con.executescript(SCHEMA)
        con.execute("INSERT INTO pipeline_runs (started_at, shop, approved, rejected, new_reviews, queued, "
                    "drafted, flagged, escalated, pushed, status, error) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (started, shop, s["approved"], s["rejected"], s["new_reviews"], s["queued"], s["drafted"],
                     s["flagged"], s["escalated"], s["pushed"], s["status"], s["error"]))
    return s


def summary_line(shop, s):
    line = (f"{datetime.now():%Y-%m-%d %H:%M} {shop}: {s['status']} | decisions in: {s['approved']} approved, "
            f"{s['rejected']} rejected | {s['new_reviews']} new reviews, {s['queued']} complaints | "
            f"{s['drafted']} drafted, {s['flagged']} flagged, {s['escalated']} escalated | {s['pushed']} sent to Notion")
    return line + (f" | ERROR: {s['error']}" if s["error"] else "")


def main():
    ap = argparse.ArgumentParser(description="Run the Review-to-Action loop once.")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--shop", required=True)
    ap.add_argument("--model", choices=["local", "groq"], default="groq")
    ap.add_argument("--limit", type=int, default=50, help="max complaints to draft per run")
    a = ap.parse_args()
    generate = groq_llm() if a.model == "groq" else local_llm()
    s = run_once(a.csv, a.shop, generate, Notion(), limit=a.limit)
    line = summary_line(a.shop, s)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)
    sys.exit(0 if s["status"] == "ok" else 1)


if __name__ == "__main__":
    main()
