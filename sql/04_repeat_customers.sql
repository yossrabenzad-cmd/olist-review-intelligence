-- Do customers come back? (stage 1, Q10)
-- A person can have several customer_id values (one per order), so people are counted
-- with customer_unique_id.

WITH per_person AS (
    SELECT c.customer_unique_id,
           COUNT(DISTINCT o.order_id) AS n_orders
    FROM orders    AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
)
SELECT COUNT(*)                                AS people,
       SUM(n_orders >= 2)                      AS repeat_buyers,
       ROUND(100.0 * AVG(n_orders >= 2), 1)    AS repeat_pct,
       MAX(n_orders)                           AS most_orders_by_one_person
FROM per_person;
