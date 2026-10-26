"""Build the search index for Review Radar's "Ask the reviews" tab. Run once:
    python app/build_index.py

It stores every review with its market and sentiment, plus an embedding
(a numeric representation of its meaning), so the app can find the reviews
closest in meaning to a question, in any language.
- Brazil: the 34,912 unique Olist comments, reusing the stage 5 embeddings.
- Denmark, Sweden, Norway: 10,000 ScandiSent Trustpilot reviews each (newly embedded).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed"
SCANDI = BASE / "data" / "raw" / "scandisent" / "ScandiSent"

# Brazil: reuse the embeddings computed in stage 5 (same model, same order as the files)
train = pd.read_parquet(PROC / "s5_train.parquet")
test = pd.read_parquet(PROC / "s5_test.parquet")
olist = pd.concat([train, test], ignore_index=True)
olist_emb = np.vstack([np.load(PROC / "s5_X_train.npy"), np.load(PROC / "s5_X_test.npy")])
assert len(olist) == len(olist_emb), "Olist texts and embeddings do not line up"

parts = [pd.DataFrame({"text": olist["review_comment_message"], "market": "Brazil (Olist)",
                       "sentiment": olist["star_label"], "stars": olist["review_score"]})]
embeddings = [olist_emb]

# Nordics: embed the Trustpilot reviews
embedder = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
for lang, market in [("da", "Denmark"), ("sv", "Sweden"), ("no", "Norway")]:
    d = pd.read_csv(SCANDI / f"{lang}.csv")
    print(f"Embedding {market}: {len(d):,} reviews")
    parts.append(pd.DataFrame({"text": d["text"], "market": market,
                               "sentiment": d["label"].map({0: "negative", 1: "positive"}),
                               "stars": np.nan}))
    embeddings.append(embedder.encode(d["text"].tolist(), batch_size=64,
                                      show_progress_bar=True, normalize_embeddings=True))

index = pd.concat(parts, ignore_index=True)
emb = np.vstack(embeddings).astype(np.float32)
index.to_parquet(PROC / "rag_index.parquet")
np.save(PROC / "rag_embeddings.npy", emb)
print(f"Saved {len(index):,} reviews | embeddings {emb.shape}")
print(index.groupby(["market", "sentiment"]).size())
