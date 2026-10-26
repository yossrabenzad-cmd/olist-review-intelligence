"""Read reviews from a text box or a CSV file, and label them with a sentiment model.

No Gradio here: errors are raised as ValueError, and the app shows them to the user.
"""
import pandas as pd

MAX_REVIEWS = 500   # keeps an analysis fast on a laptop


def read_reviews(text_box=None, csv_file=None, column=None, max_reviews=MAX_REVIEWS):
    """Return a list of reviews from an uploaded CSV, or from the text box (one per line)."""
    if csv_file is not None:
        df = pd.read_csv(csv_file)
        if column and column in df.columns:
            col = column
        else:   # guess: the text column with the longest average entries
            text_cols = df.select_dtypes(include=["object", "string"]).columns
            if len(text_cols) == 0:
                raise ValueError("No text column found in the CSV.")
            col = max(text_cols, key=lambda c: df[c].astype(str).str.len().mean())
        reviews = df[col].dropna().astype(str).tolist()
    else:
        reviews = [line.strip() for line in (text_box or "").splitlines() if line.strip()]
    if not reviews:
        raise ValueError("Paste some reviews (one per line) or upload a CSV.")
    return reviews[:max_reviews]


def classify(reviews, model):
    """Label each review negative, neutral or positive, with the model's confidence.

    `model` is any function that takes a list of texts and returns, per text, a list of
    {"label": ..., "score": ...} (the format of a Hugging Face pipeline with top_k=None).
    """
    out = model(reviews, batch_size=32)
    rows = []
    for text, scores in zip(reviews, out):
        best = max(scores, key=lambda s: s["score"])
        rows.append({"review": text, "sentiment": best["label"].lower(),
                     "confidence": round(best["score"], 3)})
    return pd.DataFrame(rows)


def summarise(results):
    """Counts and complaint share for one analysis."""
    n = len(results)
    n_neg = int((results["sentiment"] == "negative").sum())
    return {"n_reviews": n, "n_complaints": n_neg,
            "complaint_share": round(n_neg / n * 100, 1) if n else 0.0}
