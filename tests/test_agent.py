import pandas as pd

from src.agent import complaint_themes, fingerprint, queue_summary, run


def make_csv(path, texts, stars):
    pd.DataFrame({"text": texts, "rating": stars}).to_csv(path, index=False)
    return path


def test_second_run_finds_nothing_new(tmp_path):
    db = tmp_path / "agent.db"
    csv = make_csv(tmp_path / "r.csv",
                   ["Ingen svar på mine mails", "Hurtig levering, tak", "Pakken kom aldrig"], [1, 5, 2])
    first = run(csv, "Shop A", db_path=db)
    second = run(csv, "Shop A", db_path=db)
    assert (first["new"], first["queued"]) == (3, 2)
    assert (second["new"], second["queued"]) == (0, 0)
    assert queue_summary(db, "Shop A") == {"new": 2}


def test_only_added_reviews_are_new(tmp_path):
    db = tmp_path / "agent.db"
    run(make_csv(tmp_path / "a.csv", ["Ingen svar", "Super service"], [1, 5]), "Shop A", db_path=db)
    res = run(make_csv(tmp_path / "b.csv", ["Ingen svar", "Super service", "Varen var i stykker"],
                       [1, 5, 1]), "Shop A", db_path=db)
    assert (res["new"], res["queued"]) == (1, 1)


def test_fingerprint_ignores_case_and_spacing_but_not_shop():
    assert fingerprint("Shop", "Ingen  svar ") == fingerprint("shop", "ingen svar")
    assert fingerprint("Shop A", "Ingen svar") != fingerprint("Shop B", "Ingen svar")


def test_themes():
    assert "No reply" in complaint_themes("De svarer ikke på mails")
    assert complaint_themes("Meh") == ["Other"]
