-- Do late orders get worse reviews? (stage 1, Q4)
-- One review per order (the latest answered), delivered orders with a delivery date only.
-- Late = delivered on a later calendar day than the estimated delivery date.
-- Comparing dates, not timestamps, matters: the estimate has no time of day (00:00),
-- so a parcel arriving in the afternoon of the promised day would wrongly count as late.

WITH latest_review AS (
    SELECT order_id,
           review_score,
           ROW_NUMBER() OVER (PARTITION BY order_id
                              ORDER BY review_answer_timestamp DESC) AS rn
    FROM reviews
),
delivered AS (
    SELECT order_id,
           CASE WHEN DATE(order_delivered_customer_date) > DATE(order_estimated_delivery_date)
                THEN 1 ELSE 0 END AS is_late
    FROM orders
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
)
SELECT CASE d.is_late WHEN 1 THEN 'Late' ELSE 'On time' END AS delivery,
       COUNT(*)                                     AS orders,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_of_orders_pct,
       ROUND(100.0 * AVG(r.review_score <= 2), 1)   AS bad_review_pct,
       ROUND(AVG(r.review_score), 2)                AS avg_score
FROM delivered AS d
JOIN latest_review AS r
  ON r.order_id = d.order_id AND r.rn = 1
GROUP BY d.is_late
ORDER BY d.is_late DESC;
