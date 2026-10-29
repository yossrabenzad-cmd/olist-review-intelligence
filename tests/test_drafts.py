import pandas as pd

from src.agent import queue_summary, run
from src.drafts import check, draft_queue

GOOD = ("Tak for din anmeldelse, og vi beklager, at du ikke har fået svar på dine mails. "
        "Det er ikke godt nok. Skriv til os med dit ordrenummer, så kigger vi på sagen med det samme. "
        "Venlig hilsen, Shop A")


def test_good_draft_passes():
    assert check(GOOD, "Shop A") == []


def test_promises_are_flagged():
    bad = GOOD.replace("så kigger vi på sagen", "så får du pengene tilbage og en rabat")
    problems = check(bad, "Shop A")
    assert "promises a refund" in problems and "promises compensation" in problems


def test_english_and_missing_signoff_are_flagged():
    problems = check("Sorry for the trouble, we will look into it.", "Shop A")
    assert "does not look Danish" in problems and "missing the shop's sign-off" in problems


def test_draft_queue_updates_status(tmp_path):
    db = tmp_path / "agent.db"
    csv = tmp_path / "r.csv"
    pd.DataFrame({"text": ["Ingen svar på mine mails", "Pakken kom aldrig"], "rating": [1, 1]}).to_csv(csv, index=False)
    run(csv, "Shop A", db_path=db)
    replies = iter([GOOD, "Du får pengene tilbage i morgen. Venlig hilsen, Shop A"])
    results = draft_queue("Shop A", generate=lambda messages: next(replies), db_path=db)
    assert [r["status"] for r in results] == ["drafted", "flagged"]
    assert queue_summary(db, "Shop A") == {"drafted": 1, "flagged": 1}


def test_real_failures_from_the_local_model_are_caught():
    # Drafts the 1.5B model actually wrote in the first test run
    for bad, reason in [
        ("Tak for din anmodning! Vi ser på dette. Venlig hilsen, Shop A", "calls the complaint a request"),
        ("Vi håber at kunne hjelpe med noget godt og ikke for dig. Venlig hilsen, Shop A", "uses Norwegian"),
        ("Kjøbnummer: [Dit ordrenummer]. Vi ser på det og din sag. Venlig hilsen, Shop A", "contains a [placeholder]"),
        ("Hvis du har ordrenummer, ville vi være happy til at hjælpe dig. Venlig hilsen, Shop A", "uses English"),
    ]:
        assert reason in check(bad, "Shop A")


def test_echo_of_the_review_is_caught():
    review = "Nu svarer de ikke længere på henvendelser og pengene er trukket"
    draft = "Nu svarer de ikke længere på henvendelser og pengene er trukket. Venlig hilsen, Shop A"
    assert "repeats the review" in check(draft, "Shop A", review)


def test_redo_never_touches_human_decisions(tmp_path):
    db = tmp_path / "agent.db"
    csv = tmp_path / "r.csv"
    pd.DataFrame({"text": ["Ingen svar", "Pakken kom aldrig"], "rating": [1, 1]}).to_csv(csv, index=False)
    run(csv, "Shop A", db_path=db)
    draft_queue("Shop A", generate=lambda m: GOOD, db_path=db)
    from src.agent import connect
    with connect(db) as con:
        con.execute("UPDATE queue SET status = 'approved' WHERE rowid = 1")
    again = draft_queue("Shop A", generate=lambda m: GOOD, db_path=db, redo=True)
    assert len(again) == 1
    assert queue_summary(db, "Shop A") == {"approved": 1, "drafted": 1}


def test_empty_draft_is_flagged():
    assert check("", "Shop A") == ["empty draft"]


def test_reasoning_models_get_room_to_answer():
    from src import drafts
    body = drafts.payload([{"role": "user", "content": "hej"}])
    assert body["max_tokens"] >= 1000


def test_fraud_and_police_go_to_a_human(tmp_path):
    db = tmp_path / "agent.db"
    csv = tmp_path / "r.csv"
    pd.DataFrame({"text": ["Vi endte med indsigelse i banken. Politianmeldelse er eneste udvej mod svindleren."],
                  "rating": [1]}).to_csv(csv, index=False)
    run(csv, "Shop A", db_path=db)
    called = []
    results = draft_queue("Shop A", generate=lambda m: called.append(m) or GOOD, db_path=db)
    assert results[0]["status"] == "escalated" and not called
    assert queue_summary(db, "Shop A") == {"escalated": 1}


def test_theme_labels_are_not_sent_to_the_model():
    from src.drafts import build_messages
    msg = build_messages("Batteriet virkede ikke", "Late or missing delivery", "Shop A")[1]["content"]
    assert "Late or missing delivery" not in msg


class _Response:
    def __init__(self, text, headers=None):
        self.text, self.headers = text, headers or {}


def test_retry_wait_reads_groq_rate_limit_messages():
    from src.drafts import retry_wait
    assert retry_wait(_Response("", {"retry-after": "4"})) == 5
    assert abs(retry_wait(_Response("Please try again in 2.325s.")) - 3.325) < 1e-9
    assert abs(retry_wait(_Response("Please try again in 640ms.")) - 1.64) < 1e-9
    assert retry_wait(_Response("no hint")) == 20
