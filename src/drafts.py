"""Review-to-Action Agent, piece 2: draft a Danish reply for each queued complaint.

For every complaint with status "new", a language model writes a short, polite reply.
Each draft then passes guardrail checks; a draft that fails is "flagged", never sent.
Drafts are only proposals: a human approves them in piece 3.

Two models:
  --model local  Qwen2.5-1.5B-Instruct on this laptop: no review text leaves the machine,
                 but its Danish is weak (tested: mixes in Norwegian and English).
  --model groq   gpt-oss-120b on Groq's free tier: much better Danish. Needs a free key
                 from console.groq.com, set once in PowerShell:  $env:GROQ_API_KEY = "..."
                 The review text is sent to Groq (it is public on Trustpilot anyway).

Run from the project folder, with the virtual environment active:
    python src/drafts.py --shop "Example Shop" --limit 10 --model groq
    python src/drafts.py --shop "Example Shop" --limit 10 --model groq --redo   (draft again)
"""
import argparse
import difflib
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from src.agent import DB_PATH, connect  # noqa: E402

LOCAL_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_WORDS = 90

SYSTEM = """Du svarer på en negativ anmeldelse på vegne af webshoppen {shop}. Skriv på korrekt dansk (ikke norsk, ikke engelsk).
Regler:
- Start med at takke for anmeldelsen (aldrig "anmodning"), og beklag oplevelsen.
- Nævn kort det konkrete problem med kundens egne ord, så kunden kan se, at vi har læst det. Nævn kun det, anmeldelsen faktisk siger.
- Hvis kunden også nævner noget positivt, så tak for det.
- Lov ALDRIG penge, refusion, rabat, kompensation eller en dato. Skriv i stedet, at vi gerne vil se på sagen.
- Opfind ingen fakta, og indrøm ingen fejl, vi ikke kender. Ingen ordrenumre, navne eller årsager.
- Bed kunden skrive til os med sit ordrenummer, så vi kan hjælpe.
- Højst 70 ord, ét afsnit, ingen emojis, ingen pladsholdere i [klammer].
- Slut med: "Venlig hilsen, {shop}"

Eksempel:
Anmeldelse: "Har ventet to uger på min pakke, og ingen svarer på mine mails."
Svar: "Tak for din anmeldelse, og undskyld, at du har ventet på både pakken og et svar. Sådan skal det ikke være. Skriv venligst til os med dit ordrenummer, så ser vi på din sag med det samme. Venlig hilsen, {shop}"

Svar kun med selve svaret."""

# Guardrails: what a draft must not contain, with the reason shown to the reviewer.
BLOCKED = {
    r"refunder|refusion|pengene tilbage|tilbagebetal": "promises a refund",
    r"rabat|kompensation|gratis|voucher|gavekort": "promises compensation",
    r"\b\d{1,2}[./]\d{1,2}\b|i morgen|inden for \d+": "promises a date or deadline",
    r"ordre(nummer|nr)?\.?\s*#?\d{3,}": "invents an order number",
    r"\[[^\]]*\]": "contains a [placeholder]",
    r"\banmodning": "calls the complaint a request",
    r"\b(takk|hjelpe|gjøre|kjøp\w*|ikkje|dere|deres hjelp)\b": "uses Norwegian",
    r"\b(happy|sorry|please|thank you|order)\b": "uses English",
}
# Cases a human must handle: fraud, police, lawyers, bank disputes, consumer complaints, threats.
ESCALATE = re.compile(r"svind|svindl|politi|advokat|indsigelse|forbrugerklage|retssag|sagsøg|anmeld(e|er|t) (jer|dem|firmaet)", re.I)

DANISH_HINT = re.compile(r"\b(og|ikke|vi|det|til|på|med|for|din|dig)\b", re.I)


def build_messages(review, themes, shop):
    return [{"role": "system", "content": SYSTEM.format(shop=shop)},
            {"role": "user", "content": f"Anmeldelse:\n{review}\n\nSvar:"}]


def check(draft, shop, review=""):
    """Return a list of problems; an empty list means the draft passed."""
    if not draft.strip():
        return ["empty draft"]
    problems = [why for pat, why in BLOCKED.items() if re.search(pat, draft, re.I)]
    if len(draft.split()) > MAX_WORDS:
        problems.append(f"longer than {MAX_WORDS} words")
    if len(DANISH_HINT.findall(draft)) < 3:
        problems.append("does not look Danish")
    if f"venlig hilsen, {shop.lower()}" not in re.sub(r"\s+", " ", draft.lower()):
        problems.append("missing the shop's sign-off")
    if review and difflib.SequenceMatcher(None, review.lower(), draft.lower()).ratio() > 0.5:
        problems.append("repeats the review")
    return problems


def local_llm():
    """Load the local model once; return a function messages -> text."""
    import torch
    from transformers import pipeline
    pipe = pipeline("text-generation", model=LOCAL_MODEL, dtype=torch.bfloat16)

    def generate(messages):
        out = pipe(messages, max_new_tokens=200, do_sample=False)
        return out[0]["generated_text"][-1]["content"].strip()
    return generate


def payload(messages):
    """Request body. Reasoning models think before they answer, so they need room and low effort."""
    body = {"model": GROQ_MODEL, "messages": messages, "temperature": 0.3, "max_tokens": 1500}
    if "gpt-oss" in GROQ_MODEL:
        body["reasoning_effort"] = "low"
    return body


def groq_llm():
    """Return a function messages -> text that calls Groq. The key comes from GROQ_API_KEY."""
    import requests
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise SystemExit('Set your key first, in PowerShell:  $env:GROQ_API_KEY = "your key"')

    def generate(messages):
        for attempt in range(RETRIES + 1):
            r = requests.post(GROQ_URL, timeout=60, headers={"Authorization": f"Bearer {key}"},
                              json=payload(messages))
            if r.status_code == 429 and attempt < RETRIES:      # free tier: tokens per minute used up
                time.sleep(retry_wait(r))
                continue
            if r.status_code != 200:
                raise DraftError(f"Groq said {r.status_code} for model '{GROQ_MODEL}': {r.text[:400]}\n"
                                 "If the model is not found, pick one from console.groq.com/docs/models and run:\n"
                                 '  $env:GROQ_MODEL = "openai/gpt-oss-120b"')
            return r.json()["choices"][0]["message"]["content"].strip()
    return generate


RETRIES = 5


def retry_wait(response):
    """Seconds to wait after a 429: Groq's retry-after header, or the 'try again in 2.3s' text, plus a margin."""
    header = response.headers.get("retry-after")
    if header:
        try:
            return float(header) + 1
        except ValueError:
            pass
    m = re.search(r"try again in ([0-9.]+)(ms|s)", response.text)
    if m:
        wait = float(m.group(1)) / (1000 if m.group(2) == "ms" else 1)
        return min(wait + 1, 65)
    return 20


class DraftError(Exception):
    """The model could not be reached. `results` holds the drafts saved before it stopped."""
    def __init__(self, message, results=None):
        super().__init__(message)
        self.results = results or []


def draft_queue(shop, limit=10, generate=None, db_path=DB_PATH, redo=False):
    """Draft replies for up to `limit` complaints. Returns the list of results.

    Normally only status "new"; with redo=True, also drafts already drafted or flagged
    (never approved or rejected ones: those are a human's decision).
    """
    generate = generate or local_llm()
    statuses = ("new", "drafted", "flagged") if redo else ("new",)
    results = []
    with connect(db_path) as con:
        rows = con.execute(
            "SELECT q.review_id, r.text, q.themes FROM queue q JOIN reviews r USING (review_id) "
            f"WHERE r.shop = ? AND q.status IN ({','.join('?' * len(statuses))}) "
            "ORDER BY r.first_seen, q.review_id LIMIT ?",
            (shop, *statuses, limit)).fetchall()
        for review_id, text, themes in rows:
            if ESCALATE.search(text):
                con.execute("UPDATE queue SET status = 'escalated', updated_at = ? WHERE review_id = ?",
                            (datetime.now().isoformat(timespec="seconds"), review_id))
                results.append({"review": text, "themes": themes, "draft": "",
                                "status": "escalated", "problems": ["needs a human: legal, fraud or police"]})
                continue
            try:
                draft = generate(build_messages(text, themes, shop))
            except Exception as e:
                con.commit()                      # keep every draft made before the failure
                raise DraftError(str(e), results) from e
            problems = check(draft, shop, text)
            status = "drafted" if not problems else "flagged"
            con.execute("UPDATE queue SET draft = ?, status = ?, updated_at = ? WHERE review_id = ?",
                        (draft, status, datetime.now().isoformat(timespec="seconds"), review_id))
            results.append({"review": text, "themes": themes, "draft": draft,
                            "status": status, "problems": problems})
            con.commit()
    return results


def main():
    ap = argparse.ArgumentParser(description="Draft Danish replies for queued complaints.")
    ap.add_argument("--shop", required=True)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--model", choices=["local", "groq"], default="local")
    ap.add_argument("--redo", action="store_true", help="draft again for drafted or flagged complaints")
    a = ap.parse_args()
    generate = groq_llm() if a.model == "groq" else local_llm()
    results = draft_queue(a.shop, a.limit, generate, redo=a.redo)
    for i, r in enumerate(results, 1):
        print(f"\n--- {i}. [{r['status']}] {r['themes']}")
        print(f"REVIEW: {r['review'][:200]}")
        print(f"DRAFT:  {r['draft']}")
        if r["problems"]:
            label = "ESCALATED" if r["status"] == "escalated" else "FLAGGED"
            print(f"{label}: {', '.join(r['problems'])}")
    ok = sum(r["status"] == "drafted" for r in results)
    esc = sum(r["status"] == "escalated" for r in results)
    print(f"\n{len(results)} complaints: {ok} drafts passed the checks, "
          f"{len(results) - ok - esc} flagged, {esc} escalated to a human.")


if __name__ == "__main__":
    main()
