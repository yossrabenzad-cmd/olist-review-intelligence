"""Review snapshot: a one-page report for one webshop, from its review export.

What it shows (the free offer in the LinkedIn post):
  1. Top complaint themes, with numbers
  2. What customers love, as quotes for marketing
  3. AI visibility: what assistants answer when asked for shops like this one
  4. Three fixes, ranked by impact

Input: a CSV of reviews (a Trustpilot export works). If it has a star rating column,
1 to 2 stars count as complaints and 4 to 5 as praise. Without stars, the fine-tuned
sentiment model in models/olist-review-sentiment labels each review.

AI visibility is checked by hand (ask the assistants the prompts printed in the report)
and saved as a small JSON file, passed with --ai. Without it, the report lists the
prompts to run, so no result is ever invented. The JSON looks like this:
    {"date": "27 Oct 2026",
     "checks": [{"assistant": "ChatGPT", "prompt": "Hvor kan jeg købe tæpper online i Danmark?",
                 "mentioned": false, "note": "Named three other shops"}],
     "missing": ["No Danish product descriptions", "Few recent reviews"]}

Run from the project folder, with the virtual environment active:
    python src/snapshot.py reviews.csv --shop "Shop name" --city Copenhagen
    python src/snapshot.py reviews.csv --shop "Shop name" --ai ai_check.json
The report is saved in reports/snapshots/ (not published: not on the .gitignore list).
"""
import argparse
import html
import json
import re
from datetime import date
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE / "models" / "olist-review-sentiment"
OUT_DIR = BASE / "reports" / "snapshots"
MIN_THEME = 2          # a theme needs at least this many reviews to be shown

# Complaint themes: Danish and English word stems. A review can match several themes.
COMPLAINTS = {
    "No reply": r"svar|besvar|henvendelse|e-?mail|mails?\b|ringe|telefon|kontakt|reply|respon|answer|contact",
    "Bad customer service": r"kundeservice|service|uhøflig|uvenlig|arrogant|behandl|rude|unhelpful",
    "Money and refunds": r"penge|refu|tilbagebetal|retur|kreditnota|trukket|refund|money|return",
    "Late or missing delivery": r"lever(?:ing|et|er|ede|ancer)|forsink|ventetid|pakke|modtag|fragt|uger?\b|delivery|deliver|late|parcel|shipping",
    "Product not as described": r"kvalitet|defekt|virker ikke|i stykker|forkert|ødelagt|beskrivelse|broken|faulty|wrong|quality",
}
PRAISE = {
    "Fast delivery": r"hurtig levering|lynhurtig|hurtigt leveret|leveret hurtigt|fast delivery|quick delivery",
    "Helpful, friendly service": r"venlig|hjælpsom|kompetent|rådgivning|god service|super service|friendly|helpful",
    "Product quality": r"kvalitet|flot|lækker|god vare|fed|quality|beautiful|great product",
    "Price and value": r"pris|billig|værd|price|value|cheap",
    "Would recommend": r"anbefal|kommer (?:der )?(?:igen|tilbage)|recommend|again",
}
# One fix per complaint theme, written for a shop owner.
FIXES = {
    "No reply": "Answer every email and review within 24 hours, and say so on the contact page. "
                "A saved reply library and one daily check cover most shops.",
    "Bad customer service": "Write a short tone guide and 5 standard answers for the most common problems, "
                            "so every reply is polite and solves something.",
    "Money and refunds": "Publish a clear refund timeline (for example: refund within 5 working days) "
                         "and send an email when the refund is made.",
    "Late or missing delivery": "Send tracking automatically and a proactive email when an order is delayed, "
                                "before the customer has to ask.",
    "Product not as described": "Add real photos, measurements and material details to the top-returned products, "
                                "and use complaint words to fix the descriptions.",
}
AI_PROMPTS = [
    "Hvor kan jeg købe {category} online i Danmark?",
    "Hvad er de bedste webshops for {category} i {city}?",
    "Where can I buy {category} online in Denmark?",
    "Is {shop} a good place to buy {category}?",
]


# ---------- Reading and labelling ----------
def load(csv_path, text_col=None, stars_col=None):
    """Return a DataFrame with 'review' and, if available, 'stars'."""
    df = pd.read_csv(csv_path)
    if not text_col:
        text_cols = df.select_dtypes(include=["object", "string"]).columns
        if len(text_cols) == 0:
            raise ValueError("No text column found in the CSV.")
        text_col = max(text_cols, key=lambda c: df[c].astype(str).str.len().mean())
    if not stars_col:
        stars_col = next((c for c in df.columns
                          if re.search(r"star|rating|stjern|score", str(c), re.I)), None)
    out = pd.DataFrame({"review": df[text_col].astype(str).str.strip().str.strip('"')})
    if stars_col:
        out["stars"] = pd.to_numeric(df[stars_col], errors="coerce")
    out = out[out["review"].str.len() > 0].reset_index(drop=True)
    return out


def label(df, model=None):
    """Add 'sentiment' (negative, neutral, positive): from stars if present, else the model."""
    if "stars" in df and df["stars"].notna().mean() > 0.9:
        df["sentiment"] = pd.cut(df["stars"], [0, 2.5, 3.5, 5],
                                 labels=["negative", "neutral", "positive"]).astype(str)
        df["source"] = "star rating"
        return df
    if model is None:
        from transformers import pipeline
        model = pipeline("text-classification", model=str(MODEL_DIR),
                         truncation=True, max_length=256, top_k=None)
    scores = model(df["review"].tolist(), batch_size=32)
    df["sentiment"] = [max(s, key=lambda x: x["score"])["label"].lower() for s in scores]
    df["source"] = "fine-tuned model"
    return df


# ---------- Analysis ----------
def themes(texts, patterns):
    """Count how many reviews mention each theme, largest first."""
    low = texts.str.lower()
    rows, used = [], set()
    for name, pat in patterns.items():
        hit = low.str.contains(pat, regex=True)
        if hit.sum() >= MIN_THEME:
            rows.append({"theme": name, "n": int(hit.sum()),
                         "share": round(hit.mean() * 100, 1),
                         "example": shortest_good(texts[hit & ~texts.isin(used)])})
            used.add(rows[-1]["example"])
    return sorted(rows, key=lambda r: r["n"], reverse=True)


def shortest_good(texts, lo=40, hi=220):
    """A readable example: the shortest review between lo and hi characters."""
    ok = [t for t in texts if lo <= len(t) <= hi]
    return min(ok, key=len) if ok else (texts.iloc[0][:hi] if len(texts) else "")


def love_quotes(pos, n=3, skip=()):
    """Short, specific positive reviews, usable as marketing quotes."""
    cand = pos[pos.str.len().between(30, 160) & ~pos.isin(list(skip))]
    cand = cand[cand.str.lower().str.contains("|".join(PRAISE.values()), regex=True)]
    return cand.sort_values(key=lambda s: s.str.len()).head(n).tolist()


def analyse(df):
    neg = df.loc[df["sentiment"] == "negative", "review"].reset_index(drop=True)
    pos = df.loc[df["sentiment"] == "positive", "review"].reset_index(drop=True)
    comp = themes(neg, COMPLAINTS)
    praise = themes(pos, PRAISE)
    return {
        "n": len(df), "n_neg": len(neg), "n_pos": len(pos),
        "neg_share": round(len(neg) / len(df) * 100, 1) if len(df) else 0,
        "source": df["source"].iloc[0] if len(df) else "",
        "complaints": comp, "praise": praise,
        "quotes": love_quotes(pos, skip=[t["example"] for t in praise[:3]]),
        "fixes": [(t["theme"], t["n"], FIXES[t["theme"]]) for t in comp[:3]],
    }


# ---------- Report ----------
CSS = """
@page { size: A4; margin: 14mm; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font: 10.5pt/1.45 "Segoe UI", Arial, sans-serif; color: #1f2328; margin: 0; background: #fff; }
.page { max-width: 190mm; margin: 0 auto; padding: 8mm 0; }
header { display: flex; justify-content: space-between; align-items: flex-end;
         border-bottom: 2px solid #1f2328; padding-bottom: 6px; margin-bottom: 10px; }
h1 { font-size: 19pt; margin: 0; }
.meta { color: #59636e; font-size: 9pt; text-align: right; }
.kpis { display: flex; gap: 8px; margin: 8px 0 12px; }
.kpi { flex: 1; border: 1px solid #d1d9e0; border-radius: 6px; padding: 6px 10px; }
.kpi b { display: block; font-size: 16pt; }
.kpi b.txt { font-size: 11.5pt; line-height: 1.25; padding-top: 4px; }
.kpi span { color: #59636e; font-size: 8.5pt; }
h2 { font-size: 11.5pt; margin: 12px 0 6px; text-transform: uppercase; letter-spacing: .04em; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.bar { display: grid; grid-template-columns: 42mm 1fr 18mm; align-items: center; gap: 6px; margin: 3px 0; }
.track { background: #eef1f4; height: 9px; border-radius: 5px; overflow: hidden; }
.fill { height: 100%; background: #c0392b; }
.fill.pos { background: #2e7d4f; }
.num { text-align: right; font-variant-numeric: tabular-nums; color: #59636e; font-size: 9pt; }
.ex { color: #59636e; font-size: 8.5pt; font-style: italic; margin: 0 0 4px 0; }
blockquote { margin: 0 0 6px; padding: 4px 8px; border-left: 3px solid #2e7d4f; background: #f4f9f6; font-size: 9.5pt; }
ol { margin: 0; padding-left: 18px; } ol li { margin-bottom: 5px; }
.ai td, .ai th { border-bottom: 1px solid #e6eaef; padding: 3px 4px; font-size: 9pt; text-align: left; vertical-align: top; }
.ai { border-collapse: collapse; width: 100%; }
.todo { color: #8a6d00; }
footer { margin-top: 12px; border-top: 1px solid #d1d9e0; padding-top: 5px; color: #59636e; font-size: 8pt; }
"""


def e(s):
    return html.escape(str(s))


def bars(rows, base, cls=""):
    if not rows:
        return "<p class='ex'>Too few reviews to show themes.</p>"
    top = max(r["share"] for r in rows) or 1
    out = []
    for r in rows[:5]:
        out.append(f"<div class='bar'><div>{e(r['theme'])}</div>"
                   f"<div class='track'><div class='fill {cls}' style='width:{r['share'] / top * 100:.0f}%'></div></div>"
                   f"<div class='num'>{r['share']:.0f}% · {r['n']}</div></div>"
                   f"<p class='ex'>“{e(r['example'][:160])}”</p>")
    return f"<p class='ex' style='font-style:normal'>Share of {base} that mention each theme.</p>" + "".join(out)


def ai_section(ai, shop, city, category):
    if ai:
        rows = "".join(f"<tr><td>{e(r.get('assistant', ''))}</td><td>{e(r.get('prompt', ''))}</td>"
                       f"<td>{'Yes' if r.get('mentioned') else 'No'}</td><td>{e(r.get('note', ''))}</td></tr>"
                       for r in ai.get("checks", []))
        n = len(ai.get("checks", []))
        hits = sum(1 for r in ai.get("checks", []) if r.get("mentioned"))
        missing = "".join(f"<li>{e(m)}</li>" for m in ai.get("missing", []))
        return (f"<p><b>Recommended in {hits} of {n} answers</b> (checked {e(ai.get('date', ''))}).</p>"
                f"<table class='ai'><tr><th>Assistant</th><th>Question</th><th>{e(shop)}?</th><th>Who it named</th></tr>{rows}</table>"
                + (f"<p style='margin:6px 0 2px'><b>What's missing:</b></p><ul>{missing}</ul>" if missing else ""))
    prompts = "".join(f"<li>{e(p.format(shop=shop, city=city, category=category))}</li>" for p in AI_PROMPTS)
    return (f"<p class='todo'>To be checked by hand: ask ChatGPT these questions in a fresh chat, note whether "
            f"{e(shop)} is named and who is, then rerun with --ai.</p><ol>{prompts}</ol>")


def render(res, shop, city, category, ai=None, example=False):
    quotes = "".join(f"<blockquote>“{e(q)}”</blockquote>" for q in res["quotes"]) \
        or "<p class='ex'>No short positive quotes found.</p>"
    fixes = "".join(f"<li><b>{e(t)}</b> ({n} complaints). {e(f)}</li>" for t, n, f in res["fixes"]) \
        or "<li>Too few complaints to rank fixes.</li>"
    note = ("Example built on 200 anonymised Danish reviews from several businesses, not one shop. "
            if example else "")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Review snapshot: {e(shop)}</title><style>{CSS}</style></head><body><div class="page">
<header><div><h1>Review snapshot: {e(shop)}</h1><div class="meta" style="text-align:left">
What your customers complain about, what they love, and whether AI recommends you</div></div>
<div class="meta">{e(city)}<br>{date.today():%d %b %Y}</div></header>
<div class="kpis">
<div class="kpi"><b>{res['n']}</b><span>reviews analysed</span></div>
<div class="kpi"><b>{res['neg_share']:.0f}%</b><span>complaints ({res['n_neg']})</span></div>
<div class="kpi"><b>{res['n_pos']}</b><span>positive reviews</span></div>
<div class="kpi"><b class="txt">{e(res['complaints'][0]['theme']) if res['complaints'] else '–'}</b><span>top complaint</span></div>
</div>
<div class="grid">
<section><h2>1. Top complaints</h2>{bars(res['complaints'], 'complaints')}</section>
<section><h2>2. What customers love</h2>{bars(res['praise'][:3], 'positive reviews', 'pos')}
<p style="margin:8px 0 4px"><b>Quotes for your marketing</b></p>{quotes}</section>
</div>
<h2>3. Does AI recommend you?</h2>{ai_section(ai, shop, city, category)}
<h2>4. Three fixes, ranked by impact</h2><ol>{fixes}</ol>
<footer>{note}Sentiment from {e(res['source'])}; themes from Danish and English keywords, so a review can count
in more than one theme. Shares are of this export only.</footer>
</div></body></html>"""


def main():
    ap = argparse.ArgumentParser(description="One-page review snapshot for a webshop.")
    ap.add_argument("csv")
    ap.add_argument("--shop", required=True)
    ap.add_argument("--city", default="Copenhagen")
    ap.add_argument("--category", default="the products you sell")
    ap.add_argument("--text-col")
    ap.add_argument("--stars-col")
    ap.add_argument("--ai", help="JSON file with the hand-checked AI visibility results")
    ap.add_argument("--example", action="store_true", help="mark the report as an example")
    a = ap.parse_args()

    df = label(load(a.csv, a.text_col, a.stars_col))
    res = analyse(df)
    ai = json.loads(Path(a.ai).read_text(encoding="utf-8")) if a.ai else None
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", a.shop.lower()).strip("_")
    out = OUT_DIR / f"snapshot_{slug}.html"
    out.write_text(render(res, a.shop, a.city, a.category, ai, a.example), encoding="utf-8")
    print(f"{res['n']} reviews, {res['n_neg']} complaints. Saved: {out}")
    print("Open it in a browser and use Print > Save as PDF for the one-page version.")


if __name__ == "__main__":
    main()
