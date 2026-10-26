# Stage 5 findings: fine-tuning a multilingual model on reviews

Notebooks: `notebooks/08_finetune.ipynb` (split, baseline, quick model) and `09_finetune_colab` (Google Colab, free T4 GPU).
Data: Olist comments with star-based labels (1 to 2 stars negative, 3 neutral, 4 to 5 positive). 5,863 duplicate texts removed (14.4%) so no sentence appears in both training and test. Stratified 80/20 split: train 27,929, test 6,983 (positive 61.5%, negative 29.4%, neutral 9.1%). 10% of training held out for validation; the test set was used once.

## Top findings

1. **Fine-tuning on real reviews catches 9 in 10 complaints.** Negative recall rose from 0.638 (off-the-shelf) to 0.897: about 1,839 of 2,050 complaints in the test set, against 1,308.
2. **Accuracy rose from 69.3% to 85.2%,** macro F1 from 0.579 to 0.663.
3. **Training on Portuguese reviews also improved Danish:** 94.6% accuracy on Danish Trustpilot reviews, up from 92.8%. The model did not forget Danish; it got better at reviews in general.
4. **A cheap model gets part of the way:** embeddings plus logistic regression reached macro F1 0.647 in 5 minutes on a laptop.
5. **Trade-off:** the fine-tuned model rarely predicts neutral (3-star, 9% of data). For catching complaints this matters little.

## Three models on the same test set (6,983 comments)

| | Off-the-shelf XLM-T | Embeddings + logistic regression | Fine-tuned XLM-T |
| --- | --- | --- | --- |
| Macro F1 | 0.579 | 0.647 | **0.663** |
| Accuracy | 69.3% | 75.9% | **85.2%** |
| Negative recall | 0.638 | 0.729 | **0.897** |
| Negative precision | 0.687 | 0.779 | **0.800** |
| Positive F1 | 0.848 | 0.878 | **0.925** |
| Neutral F1 | 0.228 | **0.312** | 0.218 |

- Off-the-shelf: `cardiffnlp/twitter-xlm-roberta-base-sentiment`, trained on tweets in 8 languages.
- Quick model: `paraphrase-multilingual-MiniLM-L12-v2` embeddings with logistic regression (class_weight balanced); only the classifier learns.
- Fine-tuned: the same XLM-T model with all weights retrained on Olist reviews. 2 epochs, learning rate 2e-5, batch size 32, max length 128, mixed precision. Training time 5 min 45 s on a free T4 GPU.

### Training check

| Epoch | Training loss | Validation loss | Validation macro F1 |
| --- | --- | --- | --- |
| 1 | 0.403 | 0.412 | 0.592 |
| 2 | 0.351 | 0.404 | 0.662 |

Validation loss fell in both epochs: no sign of overfitting.

## Danish check (10,000 ScandiSent Trustpilot reviews, positive vs negative)

| | Off-the-shelf | Fine-tuned on Portuguese reviews |
| --- | --- | --- |
| Accuracy | 92.8% | **94.6%** |
| Macro F1 | 0.928 | **0.946** |

Fine-tuning on one language can make a model forget others. Here it improved Danish instead: what the model learned about how customers write reviews transferred across languages. One training run; the gain is modest but consistent with no forgetting.

## Limits

- Labels come from stars, which are noisy for mixed reviews (3 stars).
- One training run with default settings; results could vary slightly between runs.
- The neutral class could be improved with a class-weighted loss, at some cost to complaint detection.
- The Danish test is binary and balanced, so it is easier than the three-way Olist test.

## Model storage

Saved to Google Drive (`MyDrive/olist-review-sentiment`) and downloaded as `olist-review-sentiment.zip` for stage 6.

## Next

Stage 6: a tool a marketing or CX person can use to ask what customers complain about, in any language, using the fine-tuned model and the complaint themes.
