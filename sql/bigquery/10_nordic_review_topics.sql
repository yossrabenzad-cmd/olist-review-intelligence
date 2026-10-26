-- BigQuery version of sql/10_nordic_review_topics.sql
-- The topic word list is an array of STRUCTs (UNNEST) instead of SQLite's VALUES list,
-- and CONCAT replaces ||. BigQuery's LOWER handles all letters, including Å, Ä and Ö,
-- so capitalised words such as KUNDTJÄNST are matched (SQLite's LOWER missed them).

WITH topic_words AS (
    SELECT * FROM UNNEST([
        STRUCT('Denmark' AS market, 'Delivery' AS topic, 'lever' AS word),
        ('Sweden', 'Delivery', 'lever'), ('Norway', 'Delivery', 'lever'),
        ('Denmark', 'Speed', 'hurtig'), ('Sweden', 'Speed', 'snabb'), ('Norway', 'Speed', 'rask'),
        ('Norway', 'Speed', 'kjapp'),
        ('Denmark', 'Service', 'service'), ('Sweden', 'Service', 'service'), ('Norway', 'Service', 'service'),
        ('Sweden', 'Service', 'kundtjänst'),
        ('Denmark', 'Reply', 'svar'), ('Sweden', 'Reply', 'svar'), ('Norway', 'Reply', 'svar'),
        ('Denmark', 'Money / refund', 'penge'), ('Sweden', 'Money / refund', 'pengar'),
        ('Denmark', 'Money / refund', 'refunder'), ('Sweden', 'Money / refund', 'återbetal'),
        ('Denmark', 'Money / refund', 'retur'), ('Sweden', 'Money / refund', 'retur'),
        ('Norway', 'Money / refund', 'penger'), ('Norway', 'Money / refund', 'refusjon'),
        ('Norway', 'Money / refund', 'retur'),
        ('Denmark', 'Price', 'pris'), ('Sweden', 'Price', 'pris'), ('Norway', 'Price', 'pris'),
        ('Denmark', 'Quality', 'kvalitet'), ('Sweden', 'Quality', 'kvalitet'), ('Norway', 'Quality', 'kvalitet')
    ])
),
hits AS (
    SELECT DISTINCT r.review_id, r.market, r.sentiment, w.topic
    FROM olist.nordic_reviews AS r
    JOIN topic_words          AS w
      ON w.market = r.market
     AND LOWER(r.text) LIKE CONCAT('%', w.word, '%')
),
totals AS (
    SELECT market, sentiment, COUNT(*) AS reviews
    FROM olist.nordic_reviews
    GROUP BY market, sentiment
)
SELECT h.market,
       h.topic,
       h.sentiment,
       COUNT(*)                                AS reviews_mentioning,
       ROUND(100.0 * COUNT(*) / t.reviews, 1)  AS pct_of_reviews
FROM hits   AS h
JOIN totals AS t ON t.market = h.market AND t.sentiment = h.sentiment
GROUP BY h.market, h.topic, h.sentiment, t.reviews
ORDER BY h.topic, h.market, h.sentiment;
