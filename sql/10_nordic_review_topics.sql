-- Nordic Trustpilot reviews (ScandiSent): what share of negative and positive reviews
-- mention each topic, per country? Same word stems as stage 4 (step 5d).
-- A review counts once per topic, even if it uses several words for it.
-- Topic words live in this file (a VALUES list), so they are easy to read and change.

WITH topic_words(market, topic, word) AS (
    VALUES
    ('Denmark', 'Delivery', 'lever'),  ('Sweden', 'Delivery', 'lever'),   ('Norway', 'Delivery', 'lever'),
    ('Denmark', 'Speed', 'hurtig'),    ('Sweden', 'Speed', 'snabb'),      ('Norway', 'Speed', 'rask'),
                                                                          ('Norway', 'Speed', 'kjapp'),
    ('Denmark', 'Service', 'service'), ('Sweden', 'Service', 'service'), ('Norway', 'Service', 'service'),
                                       ('Sweden', 'Service', 'kundtjänst'),
    ('Denmark', 'Reply', 'svar'),      ('Sweden', 'Reply', 'svar'),       ('Norway', 'Reply', 'svar'),
    ('Denmark', 'Money / refund', 'penge'),    ('Sweden', 'Money / refund', 'pengar'),
    ('Denmark', 'Money / refund', 'refunder'), ('Sweden', 'Money / refund', 'återbetal'),
    ('Denmark', 'Money / refund', 'retur'),    ('Sweden', 'Money / refund', 'retur'),
    ('Norway',  'Money / refund', 'penger'),   ('Norway', 'Money / refund', 'refusjon'),
    ('Norway',  'Money / refund', 'retur'),
    ('Denmark', 'Price', 'pris'),      ('Sweden', 'Price', 'pris'),       ('Norway', 'Price', 'pris'),
    ('Denmark', 'Quality', 'kvalitet'),('Sweden', 'Quality', 'kvalitet'), ('Norway', 'Quality', 'kvalitet')
),
hits AS (
    SELECT DISTINCT r.review_id, r.market, r.sentiment, w.topic
    FROM nordic_reviews AS r
    JOIN topic_words    AS w
      ON w.market = r.market
     AND LOWER(r.text) LIKE '%' || w.word || '%'
),
totals AS (
    SELECT market, sentiment, COUNT(*) AS reviews
    FROM nordic_reviews
    GROUP BY market, sentiment
)
SELECT h.market,
       h.topic,
       h.sentiment,
       COUNT(*)                                  AS reviews_mentioning,
       ROUND(100.0 * COUNT(*) / t.reviews, 1)    AS pct_of_reviews
FROM hits   AS h
JOIN totals AS t ON t.market = h.market AND t.sentiment = h.sentiment
GROUP BY h.market, h.topic, h.sentiment
ORDER BY h.topic, h.market, h.sentiment;
