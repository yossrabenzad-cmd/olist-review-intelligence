-- Marketing funnel by channel: lead -> signed seller -> active seller (stage 3b)
-- Active = the seller appears in at least one order. Empty channels are grouped with 'unknown'.
-- SUM over only empty values gives NULL, so COALESCE turns 'no active sellers' into 0.

WITH seller_orders AS (
    SELECT seller_id,
           COUNT(DISTINCT order_id) AS n_orders
    FROM order_items
    GROUP BY seller_id
)
SELECT COALESCE(l.origin, 'unknown')                                   AS channel,
       COUNT(*)                                                        AS leads,
       COUNT(d.seller_id)                                              AS sellers,
       COALESCE(SUM(so.n_orders > 0), 0)                               AS active_sellers,
       ROUND(100.0 * COUNT(d.seller_id) / COUNT(*), 1)                 AS conversion_pct,
       ROUND(100.0 * COALESCE(SUM(so.n_orders > 0), 0) / NULLIF(COUNT(d.seller_id), 0), 1) AS activation_pct,
       ROUND(100.0 * COALESCE(SUM(so.n_orders > 0), 0) / COUNT(*), 1)  AS active_per_100_leads
FROM leads AS l
LEFT JOIN deals         AS d  ON d.mql_id     = l.mql_id
LEFT JOIN seller_orders AS so ON so.seller_id = d.seller_id
GROUP BY channel
ORDER BY leads DESC;
