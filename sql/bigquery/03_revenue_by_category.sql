-- BigQuery version of sql/03_revenue_by_category.sql (same SQL, tables prefixed with the dataset)
-- Revenue = sum of item prices, delivered orders only; each item counts in its own category.

WITH item_revenue AS (
    SELECT COALESCE(t.product_category_name_english, 'unknown') AS category,
           oi.price
    FROM olist.order_items AS oi
    JOIN olist.orders      AS o ON o.order_id   = oi.order_id
    LEFT JOIN olist.products AS p ON p.product_id = oi.product_id
    LEFT JOIN olist.category_translation AS t
           ON t.product_category_name = p.product_category_name
    WHERE o.order_status = 'delivered'
)
SELECT category,
       ROUND(SUM(price))                                       AS revenue_brl,
       ROUND(100.0 * SUM(price) / SUM(SUM(price)) OVER (), 1)  AS share_pct
FROM item_revenue
GROUP BY category
ORDER BY revenue_brl DESC
LIMIT 10;
