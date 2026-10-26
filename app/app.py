"""Review Radar: what are customers unhappy about, in any language?

Tab 1, "Analyse your reviews": paste or upload reviews, get sentiment per review
(fine-tuned multilingual model), the share of complaints, and complaint themes.
Every analysis is saved as a summary (no review text) for the History tab.
Tab 2, "Ask the reviews": ask a question in English; the app finds the reviews closest
in meaning (Brazil, Denmark, Sweden, Norway) and a small open language model writes
a short answer that cites them (retrieval-augmented generation, RAG).
Tab 3, "History": complaint share and top theme for every past analysis.

The logic lives in src/ (reviews, themes, search, history); this file builds the page.

Before the first run of tab 2, build the search index once:
    python app/build_index.py

Run from the project folder, with the virtual environment active:
    python app/app.py
Then open the address it prints (usually http://127.0.0.1:7860).
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent          # the project folder
sys.path.insert(0, str(BASE))                           # so "from src..." works

import gradio as gr
import matplotlib
matplotlib.use("Agg")                      # draw charts without opening windows
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from spacy.lang.da.stop_words import STOP_WORDS as DA
from spacy.lang.en.stop_words import STOP_WORDS as EN
from spacy.lang.nb.stop_words import STOP_WORDS as NB
from spacy.lang.pt.stop_words import STOP_WORDS as PT
from spacy.lang.sv.stop_words import STOP_WORDS as SV
from transformers import pipeline

from src.history import load_runs, save_run
from src.reviews import MAX_REVIEWS, classify, read_reviews, summarise
from src.search import retrieve
from src.themes import find_themes, themes_to_markdown

# ---------- Paths and settings ----------
MODEL_DIR = BASE / "models" / "olist-review-sentiment"  # fine-tuned in stage 5
SAMPLE_FILE = BASE / "data" / "raw" / "scandisent" / "ScandiSent" / "da.csv"
STOP_WORDS = list(DA | SV | NB | PT | EN)               # filler words, 5 languages
INDEX_FILE = BASE / "data" / "processed" / "rag_index.parquet"
EMB_FILE = BASE / "data" / "processed" / "rag_embeddings.npy"
HISTORY_DB = BASE / "data" / "review_radar_history.db"  # never published (data/ is ignored)
LLM_NAME = "Qwen/Qwen2.5-1.5B-Instruct"                  # small open model, Apache 2.0
MARKETS = ["All markets", "Brazil (Olist)", "Denmark", "Sweden", "Norway"]

# ---------- Load the models once, when the app starts ----------
print("Loading models...")
sentiment = pipeline("text-classification", model=str(MODEL_DIR),
                     truncation=True, max_length=256, top_k=None)
embedder = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
index_df = pd.read_parquet(INDEX_FILE) if INDEX_FILE.exists() else None
index_emb = np.load(EMB_FILE) if EMB_FILE.exists() else None
_llm = None   # the language model loads on the first question, to keep start-up fast
print("Ready." if index_df is not None else "Ready (tab 2 needs: python app/build_index.py).")


def embed(texts):
    return embedder.encode(texts, batch_size=64, normalize_embeddings=True)


# ---------- Charts ----------
def sentiment_chart(results):
    """Bar chart of the share of each sentiment."""
    share = (results["sentiment"].value_counts(normalize=True) * 100) \
        .reindex(["negative", "neutral", "positive"]).fillna(0)
    fig, ax = plt.subplots(figsize=(5, 2.5))
    ax.barh(share.index, share.values, color=["#c0504d", "#a5a5a5", "#4f81bd"])
    for i, v in enumerate(share.values):
        ax.text(v + 1, i, f"{v:.0f}%", va="center")
    ax.set_xlim(0, 100)
    ax.set_xlabel("% of reviews")
    ax.invert_yaxis()
    fig.tight_layout()
    return fig


def history_chart(runs):
    """Complaint share per analysis, oldest to newest."""
    fig, ax = plt.subplots(figsize=(6, 2.5))
    if len(runs):
        r = runs.iloc[::-1]
        ax.plot(range(len(r)), r["complaint_share"], marker="o", color="#c0504d")
        ax.set_xticks(range(len(r)), [s[:10] for s in r["run_at"]], rotation=45, ha="right")
    ax.set_ylabel("% complaints")
    ax.set_ylim(0, 100)
    fig.tight_layout()
    return fig


# ---------- Tab 1: analyse ----------
def analyse(text_box, csv_file, column):
    try:
        reviews = read_reviews(text_box, csv_file, column)
    except ValueError as e:
        raise gr.Error(str(e))
    results = classify(reviews, sentiment)
    s = summarise(results)
    summary = (f"**{s['n_reviews']} reviews analysed.** {s['n_complaints']} are complaints "
               f"({s['complaint_share']:.0f}%)."
               + (f" Only the first {MAX_REVIEWS} reviews were used." if s["n_reviews"] == MAX_REVIEWS else ""))

    complaints = results.loc[results["sentiment"] == "negative", "review"].tolist()
    themes = find_themes(complaints, embed, stop_words=STOP_WORDS)

    source = Path(csv_file).name if csv_file is not None else "text box"
    save_run(HISTORY_DB, source, s, themes)                 # summary only, no review text

    out_path = BASE / "reports" / "review_radar_results.csv"
    results.to_csv(out_path, index=False)
    return summary, sentiment_chart(results), themes_to_markdown(themes), results, str(out_path)


def load_sample():
    """200 random Danish Trustpilot reviews, so the app can be shown without a file."""
    da = pd.read_csv(SAMPLE_FILE).sample(200, random_state=1)
    return "\n".join(da["text"].str.replace("\n", " "))


# ---------- Tab 2: ask the reviews (RAG) ----------
def get_llm():
    """Load the language model the first time it is needed (about 3 GB download, once)."""
    global _llm
    if _llm is None:
        import torch
        _llm = pipeline("text-generation", model=LLM_NAME, torch_dtype=torch.bfloat16)
    return _llm


def ask(question, market, only_negative, k, use_llm):
    if not (question or "").strip():
        raise gr.Error("Type a question.")
    if index_df is None:
        raise gr.Error("Search index missing. Run: python app/build_index.py")
    hits = retrieve(embed([question])[0], index_df, index_emb, market, only_negative, int(k))
    numbered = "\n".join(f"[{i}] ({r.market}, {r.sentiment}) {r.text[:400]}"
                         for i, r in enumerate(hits.itertuples(), start=1))
    if use_llm:
        messages = [
            {"role": "system", "content":
                "You analyse customer reviews for a webshop. Answer the question in English "
                "using ONLY the numbered reviews provided. Cite reviews like [2]. "
                "If the reviews do not answer the question, say so. Maximum 120 words."},
            {"role": "user", "content": f"Question: {question}\n\nReviews:\n{numbered}"},
        ]
        out = get_llm()(messages, max_new_tokens=220, do_sample=False)
        answer_text = out[0]["generated_text"][-1]["content"]
    else:
        answer_text = "_Answer writing is off: showing the most relevant reviews only._"
    sources = hits[["similarity", "market", "sentiment", "text"]].reset_index(drop=True)
    sources.index = sources.index + 1          # number sources from 1, matching the citations
    return answer_text, sources.reset_index(names="#")


# ---------- Tab 3: history ----------
def show_history():
    runs = load_runs(HISTORY_DB)
    return history_chart(runs), runs


# ---------- The page ----------
with gr.Blocks(title="Review Radar") as demo:
    gr.Markdown("# Review Radar\nWhat are customers unhappy about, in any language? "
                "Paste reviews (one per line) or upload a CSV export.")
    with gr.Tab("Analyse your reviews"):
        with gr.Row():
            with gr.Column():
                text_box = gr.Textbox(lines=10, label="Reviews, one per line")
                sample_btn = gr.Button("Load 200 Danish Trustpilot reviews (example)")
            with gr.Column():
                csv_file = gr.File(label="...or upload a CSV", file_types=[".csv"])
                column = gr.Textbox(label="Text column name (optional, guessed if empty)")
                run_btn = gr.Button("Analyse", variant="primary")
        summary = gr.Markdown()
        chart = gr.Plot(label="Sentiment")
        themes = gr.Markdown()
        table = gr.Dataframe(label="Every review with its label", wrap=True)
        download = gr.File(label="Download results (CSV)")

        sample_btn.click(load_sample, outputs=text_box)
        run_btn.click(analyse, inputs=[text_box, csv_file, column],
                      outputs=[summary, chart, themes, table, download])

    with gr.Tab("Ask the reviews"):
        gr.Markdown("Ask in English. The app finds the most relevant reviews by meaning, in any "
                    "language, and a small language model answers using only those reviews. "
                    "Always check the quoted sources below the answer.")
        question = gr.Textbox(label="Question", lines=2)
        with gr.Row():
            market = gr.Dropdown(MARKETS, value="All markets", label="Market")
            only_negative = gr.Checkbox(value=True, label="Complaints only")
            k = gr.Slider(3, 15, value=8, step=1, label="Number of reviews to use")
            use_llm = gr.Checkbox(value=True, label="Write an answer (slower, first time downloads the model)")
        ask_btn = gr.Button("Ask", variant="primary")
        gr.Examples([["Why do customers complain about refunds?", "Denmark"],
                     ["What goes wrong when customers order several items?", "Brazil (Olist)"],
                     ["What do customers say about customer service replies?", "All markets"]],
                    inputs=[question, market])
        answer_box = gr.Markdown()
        sources_table = gr.Dataframe(label="Sources used (cited by number)", wrap=True)
        ask_btn.click(ask, inputs=[question, market, only_negative, k, use_llm],
                      outputs=[answer_box, sources_table])

    with gr.Tab("History"):
        gr.Markdown("Every analysis is saved as a summary: date, number of reviews, complaint share "
                    "and the words of the biggest theme. Review text is never stored.")
        refresh_btn = gr.Button("Refresh")
        history_plot = gr.Plot(label="Complaint share per analysis")
        history_table = gr.Dataframe(label="Past analyses, newest first")
        refresh_btn.click(show_history, outputs=[history_plot, history_table])
        demo.load(show_history, outputs=[history_plot, history_table])

    gr.Markdown("Sentiment: XLM-T fine-tuned on 28,000 Olist reviews (stage 5). "
                "Themes and search: multilingual sentence embeddings (+ k-means for themes). "
                "Answers: Qwen2.5-1.5B-Instruct. "
                "Example data: ScandiSent (Språkbanken, University of Gothenburg, CC BY 4.0).")

if __name__ == "__main__":
    demo.launch()
