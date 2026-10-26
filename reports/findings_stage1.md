# Stage 1 findings: Olist orders, deliveries and reviews

Data: Olist Brazilian e-commerce dataset, 99,441 orders (Sep 2016 to Oct 2018), cleaned in `notebooks/01_cleaning.ipynb`, analysed in `notebooks/02_eda.ipynb`.
Reliable period for trends: January 2017 to August 2018 (earlier and later months are incomplete).

## Top 5 findings for a marketing manager

1. **Late delivery is the strongest driver of bad reviews.** 61% of late orders get a 1 or 2 star review, against 9.2% of on-time orders: a late order is 6.6 times more likely to be reviewed badly. The average score drops from 4.29 to 2.27. Late orders are 6.8% of delivered orders but account for roughly a third of bad reviews.
2. **Every day of delay makes it worse, and early delivery barely helps.** Bad reviews stay at 9% to 12% while orders arrive early or on the day, then rise to 32% at 1 to 3 days late, 66% at 4 to 7 days and 77% at 8+ days.
3. **Customers punish broken promises, not slow delivery.** Amazonas is the slowest state (median 25 days) but has only 2.8% late orders and a 4.2 average score. Alagoas takes 22 days, has 21.4% late orders and the lowest score (3.8). Across states, late share and score correlate at -0.88; delivery time and score only at -0.40.
4. **Some categories disappoint even when delivery is on time.** Office furniture gets 18.4% bad reviews on on-time orders, double the 9.2% average. Products listed with no category, description or photos get 12.8%. Food and drink (2.4%) and books (3.5%) do best.
5. **Almost nobody comes back.** Only 3.1% of 96,096 customers ordered twice, and the rate is the same after a good or a bad first order. Retention is missing, not broken.

## All 10 questions

| # | Question | Finding | For a shop |
| --- | --- | --- | --- |
| Q1 | How did orders grow? | From 800 orders in Jan 2017 to a peak of 7,544 in Nov 2017 (Black Friday), then 6,000 to 7,000 a month in 2018 | Plan stock and delivery capacity for November |
| Q2 | Which categories earn most? | Health & beauty (about 1.23M BRL), watches & gifts (1.16M), bed, bath & table (1.02M); top 5 of 74 categories = 39.8% of revenue | Focus budget and delivery quality on the top 5 |
| Q3 | How are scores distributed? | 59.2% five stars, 12.8% one or two stars (delivered orders); J-shaped | A 1-star review signals a specific failure worth tracing |
| Q4 | Do late orders get worse reviews? | 61% bad vs 9.2%; score 2.27 vs 4.29 | Prevent delays or warn customers early |
| Q5 | Does a longer delay hurt more? | 12% on the day, 32% at 1-3 days late, 66% at 4-7, 77% at 8+ | Aim for "never late", act before day 4 |
| Q6 | Where is delivery slowest? | SP 7 days (42% of orders), AM about 25 days; lateness, not slowness, links to scores | Set honest delivery estimates per region |
| Q7 | Does expensive freight matter? | Bad reviews 12.2% to 13.4% across freight groups: small effect | Cheaper shipping will not fix reviews much |
| Q8 | Which categories get bad reviews when on time? | Office furniture 18.4%; empty listings 12.8%; food and drink 2.4% | Better product info, photos, packaging; require complete listings |
| Q9 | How do customers pay? | Credit card 75.4%, boleto 19.9%; 51.5% use installments; median 79 BRL paid at once vs 207 BRL over 7-24 installments | Offer boleto and installments on higher-priced items |
| Q10 | Do customers come back? | 3.1% repeat, same after good or bad first order | Build retention: post-purchase emails, reorder reminders, loyalty offers |

## Cleaning decisions that affect these numbers

- 2,957 orders never delivered and 8 "delivered" orders with no date are excluded from delivery and review analysis.
- One review per order (latest kept); 551 duplicate review rows removed.
- Category = category of the first item in each order (75%+ of orders have one item).
- Months before Jan 2017 and after Aug 2018 excluded from trend charts.

## Limits

- These are links in the data, not proof of cause. Stage 3 tests the delivery effect with a model.
- Brazilian marketplace data from 2016 to 2018; patterns may differ in other markets.

## Next

Stage 2: customer segments (RFM) and a retention plan per segment.
