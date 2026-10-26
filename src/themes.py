"""Group complaints into themes by meaning, and describe each theme."""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

MIN_COMPLAINTS = 10


def find_themes(texts, embed, stop_words=None, max_themes=6, n_words=6, n_examples=3):
    """Return a list of themes, largest first.

    `embed` is any function that turns a list of texts into normalised vectors
    (in the app: a multilingual sentence-transformer). Each theme is a dict with
    its size, share, typical words and the reviews closest to its centre.
    """
    if len(texts) < MIN_COMPLAINTS:
        return []
    k = min(max_themes, max(2, len(texts) // 15))
    emb = np.asarray(embed(texts))
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(emb)

    vec = TfidfVectorizer(stop_words=stop_words, min_df=2, ngram_range=(1, 2))
    tf = vec.fit_transform([t.lower() for t in texts])
    terms = np.array(vec.get_feature_names_out())
    dist = km.transform(emb)

    themes = []
    for c in np.argsort(np.bincount(km.labels_))[::-1]:          # largest theme first
        mask = km.labels_ == c
        top = terms[np.asarray(tf[mask].mean(axis=0)).ravel().argsort()[::-1][:n_words]]
        themes.append({
            "size": int(mask.sum()),
            "share": round(float(mask.mean()) * 100, 1),
            "words": [str(w) for w in top],
            "examples": [texts[i] for i in np.argsort(dist[:, c])[:n_examples]],
        })
    return themes


def themes_to_markdown(themes):
    """Readable text for the app."""
    if not themes:
        return f"Fewer than {MIN_COMPLAINTS} complaints: too few to group into themes."
    parts = []
    for rank, t in enumerate(themes, start=1):
        parts.append(f"### Theme {rank}: {t['size']} complaints ({t['share']:.0f}%)\n"
                     f"**Typical words:** {', '.join(t['words'])}\n\n"
                     + "\n".join(f"- {e[:200]}" for e in t["examples"]))
    return "\n\n".join(parts)
