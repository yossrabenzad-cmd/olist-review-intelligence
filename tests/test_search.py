import numpy as np
import pandas as pd

from src.search import retrieve

INDEX = pd.DataFrame({
    "market": ["Denmark", "Denmark", "Sweden", "Brazil (Olist)"],
    "sentiment": ["negative", "positive", "negative", "negative"],
    "text": ["refund missing", "great service", "refund slow", "entrega atrasada"],
})
EMB = np.array([[1.0, 0.0], [0.9, 0.436], [0.95, 0.312], [0.0, 1.0]])
QUESTION = np.array([1.0, 0.0])          # "refunds"


def test_most_similar_first():
    hits = retrieve(QUESTION, INDEX, EMB, k=2)
    assert hits["text"].tolist() == ["refund missing", "refund slow"]
    assert hits["similarity"].iloc[0] == 1.0


def test_market_filter():
    hits = retrieve(QUESTION, INDEX, EMB, market="Sweden", k=5)
    assert hits["text"].tolist() == ["refund slow"]


def test_complaints_only_filter():
    hits = retrieve(QUESTION, INDEX, EMB, market="Denmark", only_negative=True, k=5)
    assert hits["text"].tolist() == ["refund missing"]
