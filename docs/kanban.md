# Kanban

Move items between columns as work progresses. Detailed requirements: `requirements.md`.

## To do

- [ ] Test written answers in the app (R7; needs a one-time 3 GB model download)
- [ ] Decide on publishing: GitHub repository, model on the Hugging Face Hub, live demo

## Doing

- [ ] Publish on GitHub (needs a final file check and a yes)

## Done

- [x] BigQuery: 12 tables in a free sandbox project, 10 queries translated (`sql/bigquery/`), results match SQLite; Unicode fix in query 10
- [x] README: problem, key findings, how it was built, how to run, data, limits
- [x] Clean public notebooks in `notebooks_public/` (9): real names and local paths replaced, install logs removed, checked by `notebooks/make_public.py`
- [x] App split into components (`src/reviews.py`, `themes.py`, `search.py`, `history.py`); History tab with SQLite summaries (R8, R9); 18 pytest tests
- [x] Project structure: Git, `.gitignore` whitelist, `requirements.txt`, `AGENTS.md`, requirements spec, this board
- [x] SQL: 11 Olist tables in SQLite (`src/build_db.py`), 10 queries in `sql/`: 5 reproduce stage 1 and 3b findings, 5 new (payments, order timing, cohort retention, cross-sell, Nordic review topics); notebook 10
- [x] Stage 1: cleaning and EDA (10 business questions)
- [x] Stage 2: RFM segments, reusable toolkit, UK test, k-means check
- [x] Stage 3: bad-review prediction, feature importance, business case, delivery-time regression
- [x] Stage 3b: marketing funnel by channel
- [x] Stage 4: sentiment, complaint themes, NER, Danish and Nordic tests
- [x] Stage 5: fine-tuned multilingual model (macro F1 0.663, Danish 94.6%)
- [x] Stage 6: Review Radar tab 1 (analysis) and tab 2 search
