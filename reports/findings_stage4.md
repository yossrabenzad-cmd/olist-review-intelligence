# Stage 4 findings: what customers complain about and praise, in Portuguese and Danish

Notebook: `notebooks/07_nlp.ipynb`.
Data: Olist reviews with a comment (40,775, Portuguese) and ScandiSent Trustpilot reviews (10,000 each in Danish, Swedish and Norwegian, labelled positive or negative; Språkbanken, University of Gothenburg, CC BY 4.0).
Goal: a review analysis pipeline for webshops that receive reviews in several languages. Analysis runs in the original language; translations here are for presentation only.

## Top findings

1. **One ready-made multilingual model reads both Portuguese and Danish reviews:** 90.3% accuracy on Portuguese and 92.8% on Danish for positive vs negative, although it was never trained on Danish sentiment.
2. **Its weak spot is factual complaints.** A third of 1-star Olist comments read as "neutral" because they state facts ("I still haven't received the product") without emotional words. Three-way accuracy is 69.9% (macro F1 0.571): the baseline for stage 5.
3. **Olist complaints are mostly about delivery** (about 54%), and the text independently found the stage 3 problem: incomplete multi-item orders (12.8% of complaints, 68% of them multi-item orders).
4. **For a real share of orders, "delivered" does not mean delivered:** at least a quarter of delivery complaints on orders recorded as delivered on time say the order never arrived.
5. **Danish complaints are mostly about communication:** no reply and bad customer service together are 31.9% of negative reviews; delivery is 13.9%.
6. **Across Denmark, Sweden and Norway the pattern is the same:** speed drives praise, while missing replies and money or refund problems drive complaints.

## Part 1: Olist (Portuguese)

### Sentiment checked against the stars

Model: Cardiff NLP XLM-T (`cardiffnlp/twitter-xlm-roberta-base-sentiment`), trained for sentiment in 8 languages including Portuguese. Full run: 40,775 comments in 30 minutes on a laptop CPU.

| Stars | Negative | Neutral | Positive |
| --- | --- | --- | --- |
| 1 | 64.0% | 34.7% | 1.4% |
| 2 | 56.5% | 38.0% | 5.5% |
| 3 | 40.8% | 37.7% | 21.5% |
| 4 | 15.3% | 25.9% | 58.8% |
| 5 | 3.6% | 13.8% | 82.7% |

- Three labels (1 to 2 stars negative, 3 neutral, 4 to 5 positive): accuracy 69.9%, macro F1 0.571.
- A sample of 1-star comments labelled neutral: all 10 were clear complaints written as facts, half of them about incomplete orders.
- **Hidden complaints:** 448 reviews with 4 to 5 stars (1.7%) have text the model calls negative with at least 80% confidence. In a sample of 10, 9 described real problems (cancellation, last-mile delivery, defects, damage, shipping costs, split deliveries without warning). A star dashboard would miss them.

### Complaint themes (10,839 comments with 1 to 2 stars)

Method: multilingual sentence embeddings (`paraphrase-multilingual-MiniLM-L12-v2`) grouped with k-means (k = 8, silhouette 0.038; text themes overlap). Three clusters said the same thing in different writing styles (capital letters, no accents) and were merged by reading.

| Theme | Share | Never delivered | Late (delivered) | Multi-item |
| --- | --- | --- | --- | --- |
| Not delivered or late | 40.6% | 19.2% | 41.1% | 14.6% |
| Product quality / not as pictured | 18.5% | 1.4% | 4.0% | 9.6% |
| Lost trust in the shop | 14.2% | 21.2% | 25.3% | 12.6% |
| Not delivered + no answer from support | 13.9% | 24.8% | 25.7% | 18.7% |
| Incomplete order | 12.8% | 2.2% | 5.7% | 68.0% |

- The order data confirms the themes: the incomplete-order theme is 68% multi-item orders (10 to 19% elsewhere); product-quality complaints arrive on time.
- Among 1,749 delivery complaints on orders recorded as delivered on time, only 0.5% were written before the recorded delivery date; 24.9% explicitly say the order was not received (a minimum, from keywords) and 9.4% say it was slow.

### Names in complaints

- spaCy's Portuguese NER model (`pt_core_news_sm`) performs poorly on informal reviews: most "entities" were ordinary verbs. Domain mismatch, as with sentiment.
- Counting known names directly: refunds or cancellations 5.5%, returns 4.3%, the national postal carrier 4.5%, invoices 2.8%, customer service 1.1% (undercounted; the "no answer" theme catches more).
- Customers mostly blame the shop, not the carrier: delivery is part of the brand experience.
- Shop names in the Olist data are anonymised with invented names; no real company names are used in this report.

### Actions for a webshop

- A "did everything arrive?" message at delivery catches both incomplete orders and false delivery statuses.
- Answer customers whose delivery failed: the "no answer" theme is the cheapest to fix.
- Product-quality complaints need better photos, descriptions and quality checks, not logistics.

## Part 2: Danish and Nordic Trustpilot reviews

### Does the model work in Danish?

Both datasets scored the same way: positive vs negative (Olist: 1 to 2 vs 4 to 5 stars).

| | Olist (Portuguese) | Trustpilot (Danish) |
| --- | --- | --- |
| Reviews | 2,000 | 10,000 |
| Accuracy | 90.3% | 92.8% |
| Macro F1 | 0.888 | 0.928 |
| "Neutral" as top choice | 21.3% | 20.9% |

- The base model (XLM-RoBERTa) was pre-trained on about 100 languages including Danish, so sentiment learned in other languages transfers (cross-lingual transfer).
- The Danish test is easier (reviews about twice as long, balanced classes), so the fair claim is "works about as well in Danish".

### What Danish customers complain about (5,000 negative reviews)

| Theme | Share |
| --- | --- |
| No reply to emails | 17.7% |
| Money and refunds | 14.4% |
| Bad customer service | 14.2% |
| Late or missing delivery vs the promise | 13.9% |
| Product not as described | 11.8% |
| Non-retail: other services 14.1%, car dealers 7.2%, restaurants 6.7% | 28.0% |

### What Danish customers praise (5,000 positive reviews)

| Theme | Share |
| --- | --- |
| Expert advice and professional treatment | 16.1% |
| Product quality | 13.0% |
| Fast, good service | 12.5% |
| Delivery faster than expected | 12.3% |
| Nice webshop and prices | 12.2% |
| Fast delivery | 11.2% |
| General satisfaction | 11.2% |
| Non-retail: car dealers and physical shops | 11.4% |

Service is both the largest complaint and the largest praise in Danish reviews.

### Denmark, Sweden and Norway (share of reviews mentioning each topic)

| Topic | Negative DK | Negative SE | Negative NO | Positive DK | Positive SE | Positive NO |
| --- | --- | --- | --- | --- | --- | --- |
| Speed | 6.8 | 4.7 | 5.6 | 36.4 | 49.5 | 42.7 |
| Delivery | 21.1 | 24.8 | 27.6 | 28.6 | 39.9 | 40.9 |
| Service | 25.6 | 21.9 | 23.8 | 32.8 | 16.4 | 20.5 |
| Reply | 29.7 | 27.7 | 23.5 | 5.1 | 3.7 | 3.7 |
| Money / refund | 30.7 | 18.2 | 13.3 | 3.4 | 1.9 | 1.4 |
| Price | 9.4 | 6.6 | 7.1 | 11.4 | 10.4 | 9.7 |
| Quality | 5.1 | 2.1 | 4.2 | 8.0 | 3.8 | 6.8 |

- **The same pattern in all three countries:** speed is mentioned in 36 to 50% of positive reviews but only 5 to 7% of negative ones; replies (24 to 30% vs 4 to 5%) and money or refunds (13 to 31% vs 1 to 3%) are complaint topics.
- **Do not read too much into country differences.** Danish reviews are about twice as long as Swedish and Norwegian ones (median 219 vs about 110 characters), so they mention more topics in general, and the same idea uses different words in each language. Comparing negative vs positive within each country is reliable; comparing levels between countries is not.

### Actions for a Nordic webshop

- Reply fast: missing replies are a top complaint in every country.
- Make refunds and cancellations quick and visible: money is the most complaint-only topic.
- Promise realistic delivery times and beat them: speed is what happy customers write about.
- Use these themes in marketing ("answer within X hours", "order today, here tomorrow").

## Limits

- ScandiSent covers all Trustpilot businesses (including car dealers, restaurants and services) and contains only text and a positive/negative label: no company, date or star rating.
- Theme shares depend on where k-means draws boundaries; keyword counts are approximate and miss other wordings.
- Olist is one Brazilian marketplace (2016 to 2018); Brazil vs Denmark comparisons are indicative only.
- The sentiment model was trained on tweets; it misses factual complaints and misread one positive review written in capital letters.
- Sentiment was tested in Danish only; Swedish and Norwegian were compared with keywords.

## Next

Stage 5: fine-tune a multilingual model on review text so it catches factual complaints, and beat the baseline (three-way macro F1 0.571).
