-- BigQuery version of sql/06_payment_types.sql (same SQL, tables prefixed with the dataset)
-- Share of all orders using each payment type; the base is a subquery over all orders.

SELECT payment_type,
       COUNT(DISTINCT order_id)                                 AS orders,
       ROUND(100.0 * COUNT(DISTINCT order_id)
             / (SELECT COUNT(DISTINCT order_id) FROM olist.payments), 1) AS share_of_orders_pct,
       ROUND(AVG(payment_installments), 1)                      AS avg_installments,
       ROUND(AVG(payment_value))                                AS avg_payment_brl
FROM olist.payments
GROUP BY payment_type
ORDER BY orders DESC;
