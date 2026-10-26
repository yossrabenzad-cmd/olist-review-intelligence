-- BigQuery version of sql/02_orders_per_month.sql
-- Orders per month, the change from the month before (LAG), and a running total.
-- FORMAT_DATETIME replaces SQLite's strftime. Reliable period: Jan 2017 to Aug 2018.

WITH monthly AS (
    SELECT FORMAT_DATETIME('%Y-%m', CAST(order_purchase_timestamp AS DATETIME)) AS month,
           COUNT(*)                                                            AS orders
    FROM olist.orders
    WHERE CAST(order_purchase_timestamp AS DATETIME) >= '2017-01-01'
      AND CAST(order_purchase_timestamp AS DATETIME) <  '2018-09-01'
    GROUP BY month
)
SELECT month,
       orders,
       orders - LAG(orders) OVER (ORDER BY month) AS change_vs_last_month,
       SUM(orders) OVER (ORDER BY month)          AS running_total
FROM monthly
ORDER BY month;
