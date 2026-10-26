-- BigQuery version of sql/07_order_timing.sql
-- EXTRACT(DAYOFWEEK) gives 1 = Sunday to 7 = Saturday, so 1 is subtracted
-- to match SQLite's strftime('%w') (0 = Sunday).

WITH t AS (
    SELECT CAST(order_purchase_timestamp AS DATETIME) AS ts
    FROM olist.orders
)
SELECT EXTRACT(DAYOFWEEK FROM ts) - 1                      AS weekday_num,
       ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][OFFSET(EXTRACT(DAYOFWEEK FROM ts) - 1)] AS weekday,
       EXTRACT(HOUR FROM ts)                               AS hour,
       COUNT(*)                                            AS orders
FROM t
GROUP BY weekday_num, weekday, hour
ORDER BY weekday_num, hour;
