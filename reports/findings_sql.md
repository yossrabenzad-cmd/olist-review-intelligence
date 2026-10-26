# SQL check: the Olist analysis in a database

The 11 Olist tables (99,441 orders, 112,650 order items, 99,224 reviews, 8,000 leads, 842 deals and more) were loaded into one SQLite database with `src/build_db.py`. Ten SQL queries in `sql/`: five reproduce key findings independently of the pandas notebooks, and five answer new questions for CRM, marketing and Nordic teams. The database also holds the 30,000 Danish, Swedish and Norwegian Trustpilot reviews. Notebook: `notebooks/10_sql.ipynb`.

## Results compared with the pandas analysis

| Query | SQL result | pandas result (stages 1 and 3b) |
| --- | --- | --- |
| 01 Late vs on-time reviews | 6.7% of reviewed deliveries late; 62.4% vs 9.3% bad reviews; average score 2.27 vs 4.29 | 6.8% late; 61% vs 9.2%; 2.27 vs 4.29 |
| 02 Orders per month | Peak 7,544 in November 2017 (+2,913); growth flattens from March 2018 | Peak 7,544 in November 2017 |
| 03 Revenue by category | Health & beauty 1.23M BRL; top 5 = 39.7% of revenue | 1.23M BRL; top 5 = 39.8% |
| 04 Repeat customers | 96,096 people, 3.1% repeat; most orders by one person: 17 | 96,096 people, 3.1% repeat |
| 05 Funnel by channel | Paid search: 12.3% conversion, 51.8% activation, 6.4 active sellers per 100 leads | Identical |

## New questions answered in SQL

| Query | Question | Result | Use for a webshop |
| --- | --- | --- | --- |
| 06 Payment types | Which checkout options do customers use? | Credit card in 76.9% of orders (3.5 instalments on average, 163 BRL), boleto 19.9%, vouchers 3.9% (small top-ups); 2,246 orders combine two types | Test pay-later options for higher-priced items |
| 07 Order timing | When do customers order? | Monday busiest (16,196), Saturday quietest (10,887); plateau 10:00 to 22:00; Sunday evening as busy as a weekday evening; top slots Tuesday 14:00 and Monday 21:00 | Send campaigns early in the week, midday or early evening; Sunday evening for weekend sends |
| 08 Cohort retention | Do new customers come back? | 0.9% to 1.8% within 90 days, 1.6% to 2.5% within 180 days; lower from October 2017 as cohorts grew; the Black Friday cohort (7,190) came back no more often than others | Retention needs its own programme; discount campaigns bring volume, not loyalty |
| 09 Cross-sell | What do repeat buyers buy next? | 1,991 repeat buyers, second order after about 117 days; 61.8% switch category; a home cluster (bed, bath & table, furniture & decor, housewares) leads to each other (10 to 21 people per pair) | Cross-sell email with related home categories a few months after a home purchase |
| 10 Nordic review topics | What do Danish, Swedish and Norwegian reviews mention? | Same results as stage 4: speed in 36 to 50% of positive reviews vs 5 to 7% of negative; replies and money/refunds are complaint topics | Reply fast, make refunds quick, promise realistic delivery and beat it |

## What the differences show

The conclusions are the same; small gaps come from definitions, not errors:
- Query 01 counts only delivered orders that have a review and keeps the latest answered review per order.
- Query 03 counts each item in its own category; stage 1 used each order's first item.
- Query 10 matches stage 4 except Sweden, service, negative: 21.8% vs 21.9%. SQLite's LOWER only lowercases plain English letters, so a word written in capitals with Swedish letters (KUNDTJÄNST) is missed.
- Comparing calendar dates matters: comparing timestamps counted afternoon deliveries on the promised day as late (8.0% instead of 6.7%).

## The same queries in BigQuery

All 12 tables were loaded into Google BigQuery (free sandbox, EU location) as Parquet files made by `src/export_bigquery.py`, and the 10 queries were rewritten in BigQuery's SQL dialect (`sql/bigquery/`). Row counts match the source files for every table.

| Change | SQLite | BigQuery |
| --- | --- | --- |
| Month from a date | `strftime('%Y-%m', ts)` | `FORMAT_DATETIME('%Y-%m', ts)` |
| Days between two timestamps | `julianday(b) - julianday(a)` | `DATETIME_DIFF(b, a, SECOND) / 86400` |
| Weekday and hour | `strftime('%w')`, `strftime('%H')` | `EXTRACT(DAYOFWEEK) - 1`, `EXTRACT(HOUR)` |
| Counting rows that meet a condition | `SUM(condition)` | `COUNTIF(condition)` |
| Lookup table written in the query | `VALUES (...)` | `UNNEST([STRUCT(...)])` |
| Joining text | `'%' \|\| word \|\| '%'` | `CONCAT('%', word, '%')` |

**Results:** queries 01 to 09 give identical results in BigQuery and SQLite (every value compared; queries 07 and 09 by row count, totals and a weighted checksum). Query 10 differs in two cells, and BigQuery is right: its `LOWER` handles Å, Ä and Ö, so words in capitals such as KUNDTJÄNST are found. Sweden, service, negative becomes 21.9%, the same as the pandas result in stage 4 (SQLite: 21.8%).

**Simplification:** geolocation is stored with one point per zip prefix (19,015 rows instead of 1,000,163, average position); no query uses it.

## SQL techniques used

Joins across up to four tables (`JOIN`, `LEFT JOIN`), filtering (`WHERE`), grouping and aggregation (`GROUP BY`, `COUNT`, `SUM`, `AVG`), conditional logic (`CASE WHEN`), handling empty values (`COALESCE`, `NULLIF`), step-by-step queries (`WITH`), and window functions (`ROW_NUMBER`, `LAG`, `MIN ... OVER`, running totals and shares with `SUM ... OVER`), subqueries, self-joins, cohort analysis with date arithmetic (`julianday`), text search (`LIKE`) and lookup tables written in the query (`VALUES`).
