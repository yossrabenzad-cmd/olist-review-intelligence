-- Which categories earn most? (stage 1, Q2)
-- Revenue = sum of item prices, delivered orders only, categories in English.
-- Each item counts in its own category (the pandas version used the first item's category per order).

WITH item_revenue AS (
    SELECT COALESCE(t.product_category_name_english, 'unknown') AS category,
           oi.price
    FROM order_items AS oi
    JOIN orders   AS o ON o.order_id   = oi.order_id
    LEFT JOIN products AS p ON p.product_id = oi.product_id
    LEFT JOIN category_translation AS t
           ON t.product_category_name = p.product_category_name
    WHERE o.order_status = 'delivered'
)
SELECT category,
       ROUND(SUM(price))                                        AS revenue_brl,
       ROUND(100.0 * SUM(price) / SUM(SUM(price)) OVER (), 1)   AS share_pct
FROM item_revenue
GROUP BY category
ORDER BY revenue_brl DESC
LIMIT 10;
