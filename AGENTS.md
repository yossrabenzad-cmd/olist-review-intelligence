# Project guide for AI coding assistants and new contributors

Read this first. It explains what the project is, where things are, how to run it, and the rules for changing it.

## What this project is

**Olist Review Intelligence**: turning e-commerce data into marketing and customer-experience decisions, and a review analysis tool for webshops that receive reviews in several languages.

- Data analysis on the Olist Brazilian e-commerce dataset (about 100,000 orders, 2016 to 2018): cleaning, EDA, customer segments (RFM), bad-review prediction, marketing funnel.
- NLP on review text: sentiment, complaint themes, a fine-tuned multilingual model, and a test on Danish, Swedish and Norwegian Trustpilot reviews (ScandiSent).
- **Review Radar**: a Gradio app that labels reviews in any language, groups complaints into themes, and searches reviews by meaning.

Owner: Yossra Benzad. Status and next steps: `docs/kanban.md`. What the app must do: `docs/requirements.md`.

## Folder map

| Folder | Contents | Published |
| --- | --- | --- |
| `notebooks/` | Working notebooks, numbered in order (01 cleaning to 08 fine-tuning) | No |
| `notebooks_public/` | Clean copies of the notebooks for GitHub | Yes |
| `src/` | Reusable code: `rfm_toolkit.py` (RFM segments and action plans), `reviews.py`, `themes.py`, `search.py`, `history.py` (Review Radar logic), `build_db.py` | Yes |
| `app/` | Review Radar (`app.py`) and its search index builder (`build_index.py`) | Yes |
| `reports/` | Findings per stage (`findings_stage*.md`), the Danish insights one-pager, charts in `figures/` | Yes, except `review_radar_results.csv` |
| `docs/` | Requirements spec and Kanban board | Yes |
| `sql/`, `tests/` | SQL queries and pytest tests (`python -m pytest`) | Yes |
| `data/raw/`, `data/processed/` | Datasets and derived files | No |
| `models/` | The fine-tuned sentiment model (about 1.1 GB) | No |

`.gitignore` is a whitelist: nothing is published unless it is listed there.

## How to run

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download pt_core_news_sm
```

- Notebooks: `jupyter lab`, then run them in order. Raw data comes from Kaggle (Olist) and Språkbanken (ScandiSent); see the links below.
- App: build the search index once with `python app/build_index.py`, then `python app/app.py` and open the local address it prints.
- The fine-tuned model must be in `models/olist-review-sentiment/` (trained in Google Colab, stage 5).

## Data sources and licences

- Olist Brazilian E-Commerce Public Dataset and Olist Marketing Funnel (Kaggle). Store names in the data are anonymised. Check the Kaggle licence before redistributing anything derived from the raw data.
- ScandiSent: Trustpilot reviews in Danish, Swedish, Norwegian, Finnish and English (Språkbanken, University of Gothenburg, CC BY 4.0; credit required).
- UCI Online Retail II (CC BY 4.0), used to test the RFM toolkit on a second market.

Raw data is never committed; link to the sources instead.

## Rules

**Never commit:** datasets, models, embeddings, databases, `.zip` files, `.venv`, API keys or tokens, or output files containing raw review text.

**Never publish real company names from review text.** ScandiSent reviews name real Danish businesses. Replace them with `[company]` in anything public (notebook outputs, screenshots, README examples).

**Analysis standards used throughout:**
- Time-based train/test splits for anything predicting the future; no information from after the prediction moment (no leakage).
- Duplicate texts removed before splitting text data.
- The test set is used once; settings are chosen on a validation set.
- Every result is reported with its limits; assumptions are labelled as assumptions.
- `random_state=42` for reproducibility.

**Code style:** paths are built from the project folder (`BASE`), never hard-coded to one computer; functions have a one-line docstring; Markdown cells explain each step in plain language.

**Writing style for reports:** plain English, short sentences, no em dashes.

## Key results (details in `reports/`)

- Late orders get a 1 to 2 star review 61% of the time, against 9% on time.
- Multi-item orders often arrive incomplete: about 10% of orders, about a fifth of bad reviews.
- Fine-tuned XLM-T: macro F1 0.663 (baseline 0.579 on the same test set), catches 90% of complaints (baseline 64%), 94.6% accuracy on Danish reviews.
