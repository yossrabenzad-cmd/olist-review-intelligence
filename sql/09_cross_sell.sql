-- Cross-sell: what category do repeat buyers choose for their second order?
-- Person = customer_unique_id; category = the order's first item; cancelled/unavailable excluded.
-- Second order must be at least 1 day after the first (same-day orders are usually split purchases).
-- Self-join: the ordered list of each person's orders is joined to itself, order n to order n + 1.

WITH order_category AS (
    SELECT oi.order_id,
           COALESCE(t.product_category_name_english, 'unknown') AS category
    FROM order_items AS oi
    LEFT JOIN products AS p ON p.product_id = oi.product_id
    LEFT JOIN category_translation AS t ON t.product_category_name = p.product_category_name
    WHERE oi.order_item_id = 1
),
person_orders AS (
    SELECT c.customer_unique_id       AS person,
           o.order_purchase_timestamp AS ts,
           oc.category
    FROM orders         AS o
    JOIN customers      AS c  ON c.customer_id = o.customer_id
    JOIN order_category AS oc ON oc.order_id   = o.order_id
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
           julianday(b.ts) - julianday(a.ts) AS days
    FROM sequenced AS a
    JOIN sequenced AS b ON b.person = a.person AND b.n = a.n + 1
    WHERE a.n = 1
      AND julianday(b.ts) - julianday(a.ts) >= 1
)
SELECT first_category,
       next_category,
       COUNT(*)          AS buyers,
       ROUND(AVG(days))  AS avg_days_between,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY first_category), 1)
                         AS share_of_category_repeaters_pct
FROM first_second
GROUP BY first_category, next_category
ORDER BY buyers DESC;
