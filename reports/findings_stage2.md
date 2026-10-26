# Stage 2 findings: customer segments and a reusable RFM toolkit

Data: Olist delivered orders, 93,356 customers (2016 to 2018). Recency is measured from the end of the data (30 Aug 2018).
Notebooks: `notebooks/03_segments.ipynb` (Olist) and `notebooks/04_toolkit_uk.ipynb` (UK test). Toolkit: `src/rfm_toolkit.py`.

## Top findings for a marketing manager

1. **More than half of revenue sits with one-time high spenders.** The two "high value" segments are 30.4% of customers but 54.8% of revenue.
2. **New, high value is the most valuable segment:** 14,442 customers (15.5%) bring 28.3% of revenue, spend a median 204 BRL and bought about 3 months ago. They still remember the shop.
3. **At risk, high value is slipping away:** 13,868 customers (14.9%), 26.5% of revenue, median spend 205 BRL, last order about 9 months ago.
4. **Repeat customers are rare but valuable:** Champions (1,209) and Loyal, slipping (1,592) are 3% of customers. Champions spend a median 235 BRL, about twice an average customer's share.
5. **Customers did not leave because of bad experiences.** Lost customers had the fewest late deliveries (3.6%) and few bad reviews (10.9%). Retention is a marketing gap, not a service problem.
6. **Reorder reminders do not fit this shop.** Orders per customer are 1.01 to 1.09 in every category, so cross-sell is the better tactic.

## Segment profile (Olist)

| Segment | Customers | % of customers | % of revenue | Median spend (BRL) | Days since last order |
| --- | --- | --- | --- | --- | --- |
| New, high value | 14,442 | 15.5 | 28.3 | 204 | 93 |
| At risk, high value | 13,868 | 14.9 | 26.5 | 205 | 269 |
| Lost | 18,208 | 19.5 | 18.9 | 103 | 466 |
| Hibernating | 22,261 | 23.8 | 10.5 | 69 | 268 |
| New | 21,776 | 23.3 | 10.3 | 70 | 92 |
| Loyal, slipping | 1,592 | 1.7 | 3.1 | 217 | 295 |
| Champions | 1,209 | 1.3 | 2.5 | 235 | 89 |

Cut-offs: "recent" = bought within the last 177 days (top 40%); "high value" = spent 133 BRL or more (top 40%); top tier = 209 BRL or more (top 20%).

## Action plan decisions

- **Priority:** both high-value segments, with a starting budget split of 60/40 (an assumption to test, not a fact).
- **Earn it, then reward it:** first contact without a discount (personal email, care tips, cross-sell, early access); a reward (free shipping or 10%) only after 14 days without an order.
- **Effort in proportion to value:** personal, tailored messages for the high-value segments and Champions; automated messages for New, Hibernating and Lost.
- **Experience first:** check a high-value customer's last experience; if it was bad, start with an apology or service follow-up, not an offer.
- **Cross-sell, not reorder reminders,** because customers rarely rebuy the same category.
- **Measure it:** keep 10 to 15% of each segment as a control group. For small segments (Champions, about 120 people in a 10% control) results are indicative only.

## The reusable toolkit

`src/rfm_toolkit.py` turns the analysis into functions that work on any shop's orders:
`build_rfm`, `score_rfm`, `assign_segments`, `profile_segments`, `build_action_plan`, and `run_rfm`, which does everything in one call.
Market-specific actions live in playbooks (Brazil, Denmark, UK), so the same segmentation produces a different plan per market.
Every function was tested against the manual Olist results (99.7% to 100% identical).

## Test on a second market: UK online retailer

Data: UCI Online Retail II, a UK online gift retailer, Dec 2009 to Dec 2011 (CC BY 4.0). After cleaning: 805,549 rows, 5,878 customers, 36,969 invoices.

- **The shops are opposites.** Olist: 97% one-time buyers. UK: median 3 orders per customer, up to 398.
- **With settings adapted to repeat buyers** (frequency groups 1, 2-3, 4-10, 11+; repeat = 4+ orders): Champions are 27.1% of customers and 70.0% of revenue.
- **Limitation found:** the segment rules were designed for a one-time-buyer business. In a repeat-buyer business the high spenders are repeat buyers, so the "high value" one-time segments stay small (149 and 82 customers).
- **Next improvement:** split Champions by value (VIP vs regular) for repeat-buyer businesses.

## Applying this to a Danish webshop

- The behaviour numbers are Brazilian (2016 to 2018) and cannot be claimed for Denmark; the method and playbook transfer.
- Payments: MobilePay and Apple Pay rather than boleto and installments.
- Marketing email and SMS need consent; check the Danish Marketing Practices Act before launching campaigns.
- Trustpilot reviews are highly visible, so bad experiences are more public.
- Delivery expectations are 1 to 3 days; whether lateness hurts reviews as much as in Brazil is a hypothesis to test.

## Next

Stage 3: a model that predicts which orders will get a 1 to 2 star review, so support can act before the review is written.
