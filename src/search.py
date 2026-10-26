"""Find the reviews closest in meaning to a question (the retrieval step of RAG)."""
import numpy as np


def retrieve(query_vec, index_df, index_emb, market="All markets", only_negative=False, k=8):
    """Return the k most similar reviews, after filtering by market and sentiment.

    Embeddings are normalised, so a dot product equals cosine similarity.
    """
    mask = np.ones(len(index_df), dtype=bool)
    if market != "All markets":
        mask &= (index_df["market"] == market).values
    if only_negative:
        mask &= (index_df["sentiment"] == "negative").values
    scores = index_emb @ np.asarray(query_vec)
    scores = np.where(mask, scores, -np.inf)       # rule out reviews outside the filters
    top = np.argsort(scores)[::-1][:min(k, int(mask.sum()))]
    hits = index_df.iloc[top].copy()
    hits["similarity"] = scores[top].astype(float).round(3)
    return hits
