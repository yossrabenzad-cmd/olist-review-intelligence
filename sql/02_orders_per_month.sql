-- How did orders grow? (stage 1, Q1)
-- Orders per month, the change from the month before, and a running total.
-- Reliable period: January 2017 to August 2018.

WITH monthly AS (
    SELECT strftime('%Y-%m', order_purchase_timestamp) AS month,
           COUNT(*)                                    AS orders
    FROM orders
    WHERE order_purchase_timestamp >= '2017-01-01'
      AND order_purchase_timestamp <  '2018-09-01'
    GROUP BY month
)
SELECT month,
       orders,
       orders - LAG(orders) OVER (ORDER BY month)           AS change_vs_last_month,
       SUM(orders) OVER (ORDER BY month)                    AS running_total
FROM monthly
ORDER BY month;
