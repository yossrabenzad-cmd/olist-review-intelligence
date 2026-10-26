-- BigQuery version of sql/09_cross_sell.sql
-- Self-join of each person's ordered list of orders: order 1 next to order 2.
-- DATETIME_DIFF in seconds / 86400 replaces SQLite's julianday difference.

WITH order_category AS (
    SELECT oi.order_id,
           COALESCE(t.product_category_name_english, 'unknown') AS category
    FROM olist.order_items AS oi
    LEFT JOIN olist.products AS p ON p.product_id = oi.product_id
    LEFT JOIN olist.category_translation AS t ON t.product_category_name = p.product_category_name
    WHERE oi.order_item_id = 1
),
person_orders AS (
    SELECT c.customer_unique_id                       AS person,
           CAST(o.order_purchase_timestamp AS DATETIME) AS ts,
           oc.category
    FROM olist.orders    AS o
    JOIN olist.customers AS c  ON c.customer_id = o.customer_id
    JOIN order_category  AS oc ON oc.order_id   = o.order_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
),
sequenced AS (
    SELECT person, ts, category,
           ROW_NUMBER() OVER (PARTITION BY person ORDER BY ts) AS n
    FROM person_orders
),
first_second AS (
    SELECT a.category AS first_category,
           b.category AS next_category,
           DATETIME_DIFF(b.ts, a.ts, SECOND) / 86400 AS days
    FROM sequenced AS a
    JOIN sequenced AS b ON b.person = a.person AND b.n = a.n + 1
    WHERE a.n = 1
      AND DATETIME_DIFF(b.ts, a.ts, SECOND) / 86400 >= 1
)
SELECT first_category,
       next_category,
       COUNT(*)         AS buyers,
       ROUND(AVG(days)) AS avg_days_between,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY first_category), 1)
                        AS share_of_category_repeaters_pct
FROM first_second
GROUP BY first_category, next_category
ORDER BY buyers DESC, first_category, next_category;
