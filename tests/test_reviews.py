import io

import pandas as pd
import pytest

from src.reviews import classify, read_reviews, summarise


def test_text_box_one_review_per_line_and_blank_lines_skipped():
    assert read_reviews("Great shop\n\n  Slow delivery  \n") == ["Great shop", "Slow delivery"]


def test_csv_text_column_is_guessed():
    csv = io.StringIO("id,stars,text\n1,5,Fast delivery and friendly service\n2,1,Never got my refund\n")
    assert read_reviews(csv_file=csv) == ["Fast delivery and friendly service", "Never got my refund"]


def test_csv_named_column_is_used():
    csv = io.StringIO("title,body\nShort,A much longer review text here\n")
    assert read_reviews(csv_file=csv, column="title") == ["Short"]


def test_max_reviews_limit():
    assert len(read_reviews("\n".join(f"review {i}" for i in range(20)), max_reviews=5)) == 5


def test_empty_input_raises_a_clear_error():
    with pytest.raises(ValueError, match="Paste some reviews"):
        read_reviews("   \n  ")


def fake_model(texts, batch_size=32):
    """Stands in for the fine-tuned model: 'refund' or 'late' means negative."""
    out = []
    for t in texts:
        neg = 0.9 if ("refund" in t or "late" in t) else 0.1
        out.append([{"label": "NEGATIVE", "score": neg},
                    {"label": "POSITIVE", "score": round(1 - neg, 1)}])
    return out


def test_classify_picks_the_most_likely_label():
    df = classify(["no refund yet", "lovely rug"], fake_model)
    assert df["sentiment"].tolist() == ["negative", "positive"]
    assert df["confidence"].tolist() == [0.9, 0.9]


def test_summarise_counts_complaints():
    df = pd.DataFrame({"sentiment": ["negative", "positive", "negative", "neutral"]})
    assert summarise(df) == {"n_reviews": 4, "n_complaints": 2, "complaint_share": 50.0}
