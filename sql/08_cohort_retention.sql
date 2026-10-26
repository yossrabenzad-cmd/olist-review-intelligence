-- Cohort retention: of customers who first ordered in month X, what share ordered again
-- within 90 and 180 days? Person = customer_unique_id. Cancelled/unavailable orders excluded.
-- "Again" means at least 1 day after the first order (same-day orders are usually split purchases).
-- Cohorts up to Feb 2018, so each has a full 180 days before the data ends (Sep 2018).

WITH person_orders AS (
    SELECT c.customer_unique_id      AS person,
           o.order_purchase_timestamp AS ts
    FROM orders    AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
),
with_first AS (
    SELECT person, ts,
           MIN(ts) OVER (PARTITION BY person) AS first_ts
    FROM person_orders
),
per_person AS (
    SELECT person,
           strftime('%Y-%m', first_ts) AS cohort,
           MAX(CASE WHEN julianday(ts) - julianday(first_ts) BETWEEN 1 AND 90  THEN 1 ELSE 0 END) AS back_90,
           MAX(CASE WHEN julianday(ts) - julianday(first_ts) BETWEEN 1 AND 180 THEN 1 ELSE 0 END) AS back_180
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
