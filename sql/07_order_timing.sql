-- When do customers order? Orders by weekday and hour of purchase.
-- strftime('%w') gives 0 = Sunday to 6 = Saturday; '%H' gives the hour 00 to 23.

SELECT CAST(strftime('%w', order_purchase_timestamp) AS INTEGER) AS weekday_num,
       CASE strftime('%w', order_purchase_timestamp)
            WHEN '0' THEN 'Sun' WHEN '1' THEN 'Mon' WHEN '2' THEN 'Tue'
            WHEN '3' THEN 'Wed' WHEN '4' THEN 'Thu' WHEN '5' THEN 'Fri'
            ELSE 'Sat' END                                       AS weekday,
       CAST(strftime('%H', order_purchase_timestamp) AS INTEGER) AS hour,
       COUNT(*)                                                  AS orders
FROM orders
GROUP BY weekday_num, hour
ORDER BY weekday_num, hour;
