# Review Radar: requirements

## Who it is for

A marketing or customer-experience manager at a Nordic webshop that receives reviews in several languages and has no time to read them all.

**The question it answers:** what are customers unhappy about, in any language, and what should we fix first?

## User stories

Each story lists what must be true for it to count as done.

| # | As a... | I want to... | Done when | Status |
| --- | --- | --- | --- | --- |
| R1 | CX manager | paste reviews or upload a CSV export in any language | Reviews are read from a text box (one per line) or a CSV; the text column is guessed if not named | Done |
| R2 | CX manager | see whether each review is negative, neutral or positive | Every review gets a label and a confidence score from the fine-tuned model; 200 Danish Trustpilot reviews are labelled correctly at least 90% of the time | Done (94%) |
| R3 | Marketing manager | see the share of complaints at a glance | A summary line and a bar chart show the share of each label | Done |
| R4 | CX manager | see what the complaints are about | Complaints are grouped into themes, largest first, each with typical words and example reviews | Done |
| R5 | CX manager | keep the results | Results can be downloaded as a CSV | Done |
| R6 | Marketing manager | ask a question in English and find relevant reviews in any language | The most similar reviews are returned in under 5 seconds, filtered by market and by complaints only | Done (tested on Danish refund complaints) |
| R7 | Marketing manager | get a short written answer to my question | An open language model answers using only the retrieved reviews, cites them by number, and says so when they do not answer the question | Built, not tested |
| R8 | CX manager | see how complaints change over time | Each analysis run is saved (date, number of reviews, complaint share, themes) and shown in a History view | Built; 3 tests pass; check in the app |
| R9 | Shop owner | trust that customer data is handled carefully | The history stores summaries, not full review text; database queries are parameterised; the database file is never published | Built; tests check no review text is stored and input cannot change the SQL |

## Constraints

- Runs on a laptop CPU, with no paid services or API keys.
- Up to 500 reviews per analysis; about 40 seconds for 200 reviews.
- All data stays on the computer running the app.
- Works in Danish, Swedish, Norwegian, Portuguese and English.

## Out of scope

- Collecting reviews from websites (scraping).
- Live connections to review platforms or shop systems.
- User accounts and logins.

## Known limits

- The fine-tuned model rarely labels mixed reviews as neutral.
- Theme quality depends on the number of complaints; fewer than 10 are not grouped.
- The language model is small (1.5 billion parameters) and may read Nordic languages less well than Portuguese; sources are always shown so answers can be checked.
