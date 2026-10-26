-- BigQuery version of sql/08_cohort_retention.sql
-- Days between orders: DATETIME_DIFF in seconds / 86400 replaces SQLite's julianday difference
-- (both give fractional days, so "at least 1 day later" means the same in both).

WITH person_orders AS (
    SELECT c.customer_unique_id                       AS person,
           CAST(o.order_purchase_timestamp AS DATETIME) AS ts
    FROM olist.orders    AS o
    JOIN olist.customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
),
with_first AS (
    SELECT person, ts,
           MIN(ts) OVER (PARTITION BY person) AS first_ts
    FROM person_orders
),
per_person AS (
    SELECT person,
           FORMAT_DATETIME('%Y-%m', first_ts) AS cohort,
           MAX(CASE WHEN DATETIME_DIFF(ts, first_ts, SECOND) / 86400 BETWEEN 1 AND 90  THEN 1 ELSE 0 END) AS back_90,
           MAX(CASE WHEN DATETIME_DIFF(ts, first_ts, SECOND) / 86400 BETWEEN 1 AND 180 THEN 1 ELSE 0 END) AS back_180
    FROM with_first
    GROUP BY person, cohort
)
SELECT cohort,
       COUNT(*)                        AS new_customers,
       ROUND(100.0 * AVG(back_90), 2)  AS back_within_90d_pct,
       ROUND(100.0 * AVG(back_180), 2) AS back_within_180d_pct
FROM per_person
WHERE cohort BETWEEN '2017-01' AND '2018-02'
GROUP BY cohort
ORDER BY cohort;
