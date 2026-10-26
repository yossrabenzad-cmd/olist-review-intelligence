-- Payment types: what share of orders uses each checkout option? (stage 1, Q9)
-- One row in payments = one payment; an order can have several payments,
-- so orders are counted with COUNT(DISTINCT order_id).
-- The share uses all orders as the base (subquery). Shares add to more than 100%
-- because some orders use two payment types (for example voucher + card).

SELECT payment_type,
       COUNT(DISTINCT order_id)                       AS orders,
       ROUND(100.0 * COUNT(DISTINCT order_id)
             / (SELECT COUNT(DISTINCT order_id) FROM payments), 1) AS share_of_orders_pct,
       ROUND(AVG(payment_installments), 1)            AS avg_installments,
       ROUND(AVG(payment_value))                      AS avg_payment_brl
FROM payments
GROUP BY payment_type
ORDER BY orders DESC;
