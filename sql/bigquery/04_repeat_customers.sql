-- BigQuery version of sql/04_repeat_customers.sql
-- People are counted with customer_unique_id (customer_id is created per order).
-- COUNTIF replaces SQLite's SUM(condition).

WITH per_person AS (
    SELECT c.customer_unique_id,
           COUNT(DISTINCT o.order_id) AS n_orders
    FROM olist.orders    AS o
    JOIN olist.customers AS c ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
)
SELECT COUNT(*)                                          AS people,
       COUNTIF(n_orders >= 2)                            AS repeat_buyers,
       ROUND(100.0 * COUNTIF(n_orders >= 2) / COUNT(*), 1) AS repeat_pct,
       MAX(n_orders)                                     AS most_orders_by_one_person
FROM per_person;
