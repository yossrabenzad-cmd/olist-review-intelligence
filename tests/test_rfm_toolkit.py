import pandas as pd

from src.rfm_toolkit import build_rfm

ORDERS = pd.DataFrame({
    "customer": ["a", "a", "b"],
    "order_id": [1, 2, 3],
    "date": pd.to_datetime(["2026-01-01", "2026-01-10", "2026-01-05"]),
    "amount": [100.0, 50.0, 80.0],
})


def test_recency_frequency_monetary():
    rfm = build_rfm(ORDERS, "customer", "date", "amount", "order_id",
                    ref_date=pd.Timestamp("2026-01-11"))
    assert rfm.loc["a", ["recency", "frequency", "monetary"]].tolist() == [1, 2, 150.0]
    assert rfm.loc["b", ["recency", "frequency", "monetary"]].tolist() == [6, 1, 80.0]


def test_segments_follow_the_rules():
    from src.rfm_toolkit import assign_segments
    scored = pd.DataFrame({"R": [5, 2, 5, 1], "F": [2, 2, 1, 1], "M": [3, 3, 5, 2]},
                          index=["champ", "slipping", "new_high", "lost"])
    seg = assign_segments(scored)["segment"].tolist()
    assert seg == ["Champions", "Loyal, slipping", "New, high value", "Lost"]
