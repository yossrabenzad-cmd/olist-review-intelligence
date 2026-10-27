import pandas as pd

from src.snapshot import analyse, label, render, themes, COMPLAINTS


def test_stars_decide_sentiment_without_a_model(tmp_path):
    f = tmp_path / "r.csv"
    pd.DataFrame({"text": ["Ingen svar på mine mails", "Hurtig levering, anbefales"],
                  "rating": [1, 5]}).to_csv(f, index=False)
    from src.snapshot import load
    df = label(load(f))
    assert df["sentiment"].tolist() == ["negative", "positive"]
    assert df["source"].iloc[0] == "star rating"


def test_lever_op_til_is_not_a_delivery_complaint():
    texts = pd.Series(["lever ikke op til forventningerne", "leveringen tog tre uger",
                       "pakken blev aldrig leveret"])
    rows = {r["theme"]: r["n"] for r in themes(texts, COMPLAINTS)}
    assert rows["Late or missing delivery"] == 2


def test_report_never_invents_ai_results():
    df = pd.DataFrame({"review": ["Ingen svar fra kundeservice, meget dårlig service"] * 3
                       + ["Super hurtig levering og god kvalitet, anbefales"] * 3,
                       "sentiment": ["negative"] * 3 + ["positive"] * 3, "source": "test"})
    page = render(analyse(df), "Test Shop", "Copenhagen", "rugs")
    assert "To be checked by hand" in page
    assert "Recommended in" not in page


def test_examples_are_not_repeated():
    texts = pd.Series(["Ingen svar og pengene er trukket, ingen levering endnu",
                       "Pengene er trukket men ingen refusion endnu efter flere uger",
                       "Ingen svar på mails i to uger, meget dårlig kundeservice her",
                       "Leveringen tog tre uger og ingen svar fra jer om pakken"])
    examples = [r["example"] for r in themes(texts, COMPLAINTS)]
    assert len(examples) == len(set(examples))
