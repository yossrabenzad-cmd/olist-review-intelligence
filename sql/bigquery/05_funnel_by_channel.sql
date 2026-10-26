-- BigQuery version of sql/05_funnel_by_channel.sql
-- Lead -> signed seller -> active seller, by channel. COUNTIF returns 0 (not NULL)
-- when there are no matches, so the COALESCE needed in SQLite is not needed here.

WITH seller_orders AS (
    SELECT seller_id,
           COUNT(DISTINCT order_id) AS n_orders
    FROM olist.order_items
    GROUP BY seller_id
)
SELECT COALESCE(l.origin, 'unknown')                                         AS channel,
       COUNT(*)                                                              AS leads,
       COUNT(d.seller_id)                                                    AS sellers,
       COUNTIF(so.n_orders > 0)                                              AS active_sellers,
       ROUND(100.0 * COUNT(d.seller_id) / COUNT(*), 1)                       AS conversion_pct,
       ROUND(100.0 * COUNTIF(so.n_orders > 0) / NULLIF(COUNT(d.seller_id), 0), 1) AS activation_pct,
       ROUND(100.0 * COUNTIF(so.n_orders > 0) / COUNT(*), 1)                 AS active_per_100_leads
FROM olist.leads AS l
LEFT JOIN olist.deals AS d  ON d.mql_id     = l.mql_id
LEFT JOIN seller_orders AS so ON so.seller_id = d.seller_id
GROUP BY channel
ORDER BY leads DESC;
