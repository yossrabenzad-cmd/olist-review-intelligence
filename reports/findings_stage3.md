# Stage 3 findings: predicting bad reviews and delivery time

Data: Olist delivered orders with a review, 95,830 orders. Notebook: `notebooks/05_model.ipynb`.
Time-based split: training = orders up to 27 May 2018 (76,664), test = later orders (19,166).
Bad review = 1 or 2 stars: 13.6% in training, 9.7% in test.

## Top findings for a manager

1. **The model finds at-risk orders at delivery, before the review is written.** The riskiest 5% of orders contain 26% of all bad reviews, and half of those flagged really do leave one (50.2%, against 9.7% on average).
2. **Multi-item orders arrive incomplete.** Bad reviews rise from 11.3% (1 item) to 25.4% (2 items) and 34.1% (4+). It is not lateness (multi-item orders are late less often) and not mixed sellers (single-seller orders show the same pattern). In bad reviews, comments about missing or undelivered items rise from 14.4% (1 item) to 37 to 42% (2+ items).
3. **Multi-item orders are about 10% of orders but roughly a fifth of bad reviews.** A cheap rule (a "did everything arrive?" message) reaches them without any model.
4. **Two tiers reach 38% of bad reviews while contacting 12% of orders:** an automated message for 2+ item orders and a personal check-in for the model's riskiest 5%.
5. **Better information beat bigger models.** Logistic regression, gradient boosting and neural networks all scored about the same; adding seller history was what improved the result.
6. **Delivery time is hard to predict at checkout, and Olist's promise is a buffer, not a forecast.** Orders arrive a median 12 days before the promised date.

## Model 1: will this order get a bad review? (classification)

Score: ROC-AUC, the chance that a random bad-review order is ranked riskier than a random good one (0.5 = coin flip, 1.0 = perfect).

| Model | ROC-AUC | Riskiest 5%: share of bad reviews caught | Riskiest 5%: precision |
| --- | --- | --- | --- |
| Logistic regression | 0.693 | 23.5% | 45.4% |
| Gradient boosting | 0.693 | 25.4% | 49.3% |
| Logistic regression + seller history | 0.710 | 23.4% | 45.3% |
| **Gradient boosting + seller history (final)** | **0.720** | **25.9%** | **50.2%** |
| Neural network (32) | 0.705 | 23.3% | 45.1% |
| Neural network (64, 32) | 0.706 | 23.7% | 45.9% |
| Neural network (128, 64, 32) | 0.697 | 24.3% | 47.0% |

- Baseline rule "flag every late order": precision 46.9%, but it catches only 16.6% of bad reviews.
- Bigger neural networks did not help; the largest did slightly worse (overfitting with limited signal).
- Final model: gradient boosting with seller history, best on every measure. Logistic regression is kept as the explainable reference.

### What drives the predictions (permutation importance, drop in ROC-AUC)

| Clue | Drop |
| --- | --- |
| Number of items | 0.051 |
| Delay in days | 0.042 |
| Seller's past bad-review rate | 0.039 |
| Delivery days | 0.015 |
| Seller's past late rate | 0.007 |
| Seller's past order count | 0.007 |

Price, freight, installments, approval time, state and month add almost nothing (under 0.001), consistent with stage 1 (freight has a small effect). Permutation importance understates clues that share information (is_late overlaps with delay_days).

Chart: `figures/s3_feature_importance.png`.

### Checking the surprise: number of items

| Items | Orders | Bad reviews | Late | More than one seller | Bad reviews, single-seller only | Bad reviews mentioning missing items |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 86,301 | 11.3% | 6.8% | 0% | 11.3% | 14.4% |
| 2 | 7,320 | 25.4% | 5.2% | 12.9% | 22.4% | 38.1% |
| 3 | 1,286 | 29.1% | 4.8% | 15.6% | 25.7% | 37.4% |
| 4+ | 923 | 34.1% | 5.0% | 12.4% | 30.5% | 42.2% |

Keywords searched (Portuguese): faltou, falta, faltando, só recebi, apenas um, não recebi, incompleto/a. This is approximate, and reviews without a comment count as "no mention", so the real share is likely higher.

## Business case (test period, about 3 months)

Value is measured in bad reviews prevented, not money: in stage 1, customers came back at the same rate after good and bad orders, so repeat sales cannot be claimed. The share of contacted customers support can save is unknown, so three scenarios are shown.

| Contact | Contacts a month | Bad reviews reached | Prevented at 10% / 25% / 40% save rate | Contacts per prevented review |
| --- | --- | --- | --- | --- |
| Riskiest 5% | 319 | 481 | 48 / 120 / 192 | 19.9 / 8.0 / 5.0 |
| Riskiest 10% | 639 | 673 | 67 / 168 / 269 | 28.5 / 11.4 / 7.1 |
| Riskiest 20% | 1,278 | 918 | 92 / 230 / 367 | 41.8 / 16.7 / 10.4 |

Diminishing returns: the first 5% of contacts hits 50%, the next 5% only 20%, and the 10 to 20% band 13% (close to the 9.7% average).

### Recommended plan: two tiers

| Tier | Who | How | Per month (approx.) |
| --- | --- | --- | --- |
| 1 | Orders with 2+ items, not in tier 2 | Automated "did everything arrive?" message at delivery | 450 |
| 2 | Model's riskiest 5% | Personal support check-in at delivery | 320 |

- Tier 1 alone: 1,816 orders, 426 bad reviews, hit rate 23.5% (2.4 times the average).
- Tier 2 alone: 958 orders, 481 bad reviews.
- Overlap: 467 orders (they get the personal check-in only).
- Together: 708 of about 1,850 bad reviews in the test period (38.2%).
- Measure the real effect in month one with a 10% control group per tier.

## Model 2: how long will delivery take? (regression)

Only information known at checkout is used. Score: MAE, the average number of days the prediction is off.

| Approach | MAE (days) | Average bias (days) |
| --- | --- | --- |
| Olist's promised date | 13.20 | promise is a median 12 days early |
| Median for every order (no skill) | 5.10 | |
| Linear regression | 4.46 | +2.51 |
| Gradient boosting | 4.62 | +2.93 |
| Linear regression + distance | 4.45 | +2.59 |
| Gradient boosting + distance | 4.79 | +3.28 |
| **Linear regression, last 12 months of training (final)** | **4.42** | **+2.37** |
| Linear regression, last 6 months | 6.04 | +4.89 |
| Linear regression, last 3 months | 6.18 | +5.08 |

- Olist's promise is a buffer, so beating its error is not a fair claim.
- Seller-to-customer distance (median 434 km, available for 98.7% of orders) added nothing: it correlates 0.54 with the promised time, which already carries the route.
- Most of the error is drift: delivery got faster (median 11 days in training, 7 in test), so the models over-predict.

### Delivery swings by month

| Month | Orders | Median days | Late |
| --- | --- | --- | --- |
| 2017-10 | 4,446 | 10 | 4.0% |
| 2017-11 | 7,237 | 12 | 12.3% |
| 2017-12 | 5,461 | 13 | 7.3% |
| 2018-01 | 7,013 | 11 | 5.6% |
| 2018-02 | 6,508 | 14 | 14.0% |
| 2018-03 | 6,948 | 13 | 18.7% |
| 2018-04 | 6,752 | 9 | 4.4% |
| 2018-05 | 6,722 | 9 | 6.5% |
| 2018-06 | 6,072 | 7 | 1.2% |
| 2018-07 | 6,118 | 7 | 3.3% |
| 2018-08 | 6,330 | 7 | 6.1% |

- The slow patches are November 2017 (Black Friday peak) and February to March 2018. Training on the last 3 or 6 months put those slow months at the centre, which is why it made predictions worse.
- The data does not show why February and March 2018 were slow.
- Lesson: "most recent" data is not automatically "most representative". A delivery model needs monthly error monitoring and recalibration.

## Ethics and limits

- The model prioritises help; nobody is denied a service, price or delivery option because of a score.
- Support fixes problems and never asks for a better or removed review or rewards positive ones. Misrepresenting consumer reviews is a banned practice under the EU Unfair Commercial Practices Directive, as amended by Directive (EU) 2019/2161.
- Scoring customers is profiling under GDPR; the privacy notice should say orders are scored to prioritise support.
- Customer state adds almost nothing and should be removed, so no region is treated differently.
- Brazilian marketplace data, 2016 to 2018: the method transfers, the numbers do not.
- New sellers have no history, so seller features cannot judge them yet.
- The bad-review model scores at delivery, not at checkout.
- Save rates are assumptions, not measurements.
- Links in the data are not proof of cause; keyword matching is approximate.
- ROC-AUC 0.72 is useful for ranking but far from certain: half of the riskiest 5% will not leave a bad review.

## Next

Stage 3b: the Olist marketing funnel (which lead sources turn into sellers). Then stage 4 onward as per the plan.
