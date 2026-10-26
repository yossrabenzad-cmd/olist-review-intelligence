# Stage 3b findings: marketing funnel, from lead to active seller

Data: Olist marketing funnel dataset. 8,000 marketing-qualified leads (businesses that showed interest in selling on Olist), first contact 14 Jun 2017 to 31 May 2018, and 842 closed deals. Linked to the main Olist orders data by seller_id.
Notebook: `notebooks/06_funnel.ipynb`.

Funnel: lead → signed seller → active seller (made at least one sale in the orders data).

## Top findings for a marketing manager

1. **More than half of signed sellers never sold anything.** Only 380 of 842 (45%) made a sale; 112 reached 10 or more orders. Activation is 33 to 55% in every channel, so this is an onboarding problem, not a channel problem, and the biggest lever in the funnel.
2. **Paid search is the strongest known channel end to end:** 6.4 active sellers per 100 leads, against 4.9 for organic search and 2.3 for social. Conversion to seller is similar for paid and organic (12.3% vs 11.8%); the difference is activation (51.8% vs 41.7%, two-proportion z-test p = 0.031: modest evidence of a real gap).
3. **Social brings volume, not sellers.** The third-largest source (1,350 leads) converts at 5.6% (95% range 4.3 to 6.8%), half the rate of search, and takes a median 30 days to close against 14 to 15 for search.
4. **The best-converting leads cannot be attributed.** 1,159 leads (14.5%) have no recorded channel, and they convert best (16.7%, range 14.5 to 18.8%). Fixing lead-source tracking comes before moving budget.

## Funnel by channel

| Channel | Leads | Sellers | Conversion | Active sellers | Activation | Active per 100 leads | Median days to close |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Organic search | 2,296 | 271 | 11.8% | 113 | 41.7% | 4.9 | 14 |
| Paid search | 1,586 | 195 | 12.3% | 101 | 51.8% | 6.4 | 15 |
| Social | 1,350 | 75 | 5.6% | 31 | 41.3% | 2.3 | 30 |
| Unknown (incl. 60 empty) | 1,159 | 193 | 16.7% | 85 | 44.0% | 7.3 | 11 |
| Direct traffic | 499 | 56 | 11.2% | 31 | 55.4% | 6.2 | 10 |
| Email | 493 | 15 | 3.0% | 6 | 40.0% | 1.2 | |
| Referral | 284 | 24 | 8.5% | 9 | 37.5% | 3.2 | |
| Other | 150 | 4 | 2.7% | 2 | 50.0% | 1.3 | |
| Display | 118 | 6 | 5.1% | 2 | 33.3% | 1.7 | |
| Other publicities | 65 | 3 | 4.6% | 0 | 0.0% | 0.0 | |

Overall: 10.52% of leads became sellers; 4.75 active sellers per 100 leads.
Channels with fewer than about 30 sellers (email and below) are too small to judge.

### How sure are we? (95% ranges, five largest channels)

| Channel | Conversion | Range | Activation | Range |
| --- | --- | --- | --- | --- |
| Organic search | 11.8% | 10.5 to 13.1 | 41.7% | 35.8 to 47.6 |
| Paid search | 12.3% | 10.7 to 13.9 | 51.8% | 44.8 to 58.8 |
| Social | 5.6% | 4.3 to 6.8 | 41.3% | 30.2 to 52.5 |
| Unknown | 16.7% | 14.5 to 18.8 | 44.0% | 37.0 to 51.0 |
| Direct traffic | 11.2% | 8.5 to 14.0 | 55.4% | 42.3 to 68.4 |

Chart: `figures/s3b_active_per_100_leads.png`.

## Recommendations

1. **Fix attribution first:** record the source of every lead. The unattributed 14.5% are the best converters, so any budget decision without them is partly blind.
2. **Build seller onboarding:** a first-sale programme for newly signed sellers (setup help, first listing review, a check-in if no sale after a set period). It addresses the 55% who never sell, in every channel.
3. **Favour search over social per lead,** but only after checking cost: social produces about a third as many active sellers per lead as paid search (2.3 vs 6.4), so it pays off only if its leads cost less than roughly a third as much.
4. **Treat direct traffic and unknown as warm leads:** they close fastest (median 10 to 11 days). Why is not visible in the data; a likely explanation (they already knew Olist) is a hypothesis to test.

## Limits

- **No cost data:** the dataset has no cost per lead or spend per channel, so this measures yield per lead, not return on spend.
- **Activation is measured only until the orders data ends (Aug 2018).** Sellers signed late had less time to make a first sale, so activation is understated for them.
- **Customer experience by channel was not analysed:** only 380 sellers ever sold (4,518 orders, about 4.5% of Olist orders), too few per channel for reliable review comparisons.
- The z-test is a single comparison with p = 0.031: modest evidence, not proof.
- Brazilian B2B marketplace data, 2017 to 2018. The funnel method (lead → signed → active, per channel, with uncertainty ranges) transfers to any market; the numbers do not.

## Next

k-means clustering on the stage 2 customer data (course module 4, unsupervised learning), then stage 4 (NLP on the review text).
