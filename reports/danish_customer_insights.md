# What Danish customers write about webshops: insights from Trustpilot reviews

One-page summary from the Olist Review Intelligence project (`notebooks/07_nlp.ipynb`).
Data: 10,000 Danish Trustpilot reviews (5,000 positive, 5,000 negative), plus 10,000 each in Swedish and Norwegian, from ScandiSent (Språkbanken, University of Gothenburg, CC BY 4.0). Reviews cover all Trustpilot businesses, not only webshops; non-retail themes were set aside.

## Key insights

1. **Service decides Danish reviews, both ways.** No reply (17.7%) and bad customer service (14.2%) are the largest complaint themes; expert advice (16.1%) and fast, good service (12.5%) are among the largest praise themes.
2. **Being ignored hurts more than being late.** Late or missing delivery is 13.9% of complaints, less than missing replies and customer service together (31.9%).
3. **Money is a complaint-only topic.** Refunds, charges and returns are mentioned in 30.7% of negative Danish reviews and 3.4% of positive ones.
4. **Speed is what happy customers write about.** "Hurtig" (fast) appears in 36.4% of positive reviews and 6.8% of negative ones; delivery faster than expected is told as a story ("ordered yesterday afternoon, here today").
5. **The pattern holds in Sweden and Norway:** speed drives praise; missing replies and money problems drive complaints.

## What a Danish webshop can do

| Insight | Action |
| --- | --- |
| Missing replies are the top complaint | Answer every customer email fast, and send status updates before customers have to ask |
| Refunds cause complaints | Make refunds and cancellations quick, and confirm them by email |
| Speed drives praise | Promise realistic delivery times and beat them |
| Praise themes are what customers value | Use them in marketing: "we answer within X hours", "order today, here tomorrow", expert advice |

## Complaint themes (5,000 negative Danish reviews)

| Theme | Share |
| --- | --- |
| No reply to emails | 17.7% |
| Money and refunds | 14.4% |
| Bad customer service | 14.2% |
| Late or missing delivery vs the promise | 13.9% |
| Product not as described | 11.8% |
| Non-retail (services, car dealers, restaurants) | 28.0% |

## Praise themes (5,000 positive Danish reviews)

| Theme | Share |
| --- | --- |
| Expert advice and professional treatment | 16.1% |
| Product quality | 13.0% |
| Fast, good service | 12.5% |
| Delivery faster than expected | 12.3% |
| Nice webshop and prices | 12.2% |
| Fast delivery | 11.2% |
| General satisfaction | 11.2% |
| Non-retail (car dealers, physical shops) | 11.4% |

## How it was done

- **Sentiment:** a multilingual AI model (Cardiff NLP XLM-T) never trained on Danish sentiment classified Danish reviews as positive or negative with 92.8% accuracy. After fine-tuning it on Portuguese e-commerce reviews, Danish accuracy rose to 94.6%.
- **Themes:** each review was turned into an embedding (a numeric representation of its meaning) with a multilingual model and grouped with k-means clustering. The same pipeline works on Portuguese, Danish, Swedish and Norwegian without changes.
- **Country comparison:** share of reviews mentioning each topic, using the matching word in each language.

## Limits

- Trustpilot reviews from all sectors, not only webshops; no company names, dates or star ratings in the data.
- Theme shares depend on clustering choices; keyword counts are approximate.
- Danish reviews are about twice as long as Swedish and Norwegian ones, so levels between countries are not directly comparable; the within-country positive vs negative pattern is reliable.
