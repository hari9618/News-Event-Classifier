"""Classify news snippets with a prompted LLM (Groq, openai/gpt-oss-120b).

    python llm_classify.py                     # rubric prompt -> llm_predictions.csv
    python llm_classify.py --naive             # no rubric (ablation) -> llm_naive_predictions.csv
    python llm_classify.py --input feed.csv --output out.csv

The input file needs an `id` column and a `snippet` column; nothing else is assumed, so the
same script runs over a real news feed without modification.
"""
import argparse
import csv
import json
import os
import sys
import time

from dotenv import load_dotenv
from groq import Groq

from prompt import MODEL, NAIVE_SYSTEM_PROMPT, SYSTEM_PROMPT, user_prompt

load_dotenv(".env")

_CLIENT = None


def get_client():
    """Build the Groq client, accepting either spelling of the key.

    Created lazily rather than at import time so that importing this module (app.py does)
    never fails just because a key is absent.
    """
    key = os.getenv("GROQ_API_KEY") or os.getenv("Groq_API_KEY")
    if not key:
        raise RuntimeError(
            "No Groq API key found. Create a .env file containing GROQ_API_KEY=<your key>."
        )
    return Groq(api_key=key)


def classify(snippet, system_prompt=SYSTEM_PROMPT, retries=6):
    """Classify one snippet. Returns dict with label, confidence, category, reason.

    temperature=0 and seed=0 make the output as stable as this endpoint allows, though not
    perfectly reproducible - measured in EVALUATION.md section 3.
    """
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = get_client()

    for attempt in range(retries):
        try:
            response = _CLIENT.chat.completions.create(
                model=MODEL,
                temperature=0,
                seed=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt(snippet)},
                ],
            )
            out = json.loads(response.choices[0].message.content)
            break
        except Exception:
            # Free-tier rate limits are per-minute, so a useful backoff has to be measured in
            # tens of seconds, not milliseconds. One failure should not abandon a whole batch.
            if attempt == retries - 1:
                raise
            time.sleep(min(60, 5 * 2 ** attempt))

    # Never trust the model's formatting: validate against the allowed values.
    label = str(out.get("label", "")).strip().upper()
    confidence = str(out.get("confidence", "")).strip().upper()
    return {
        "label": label if label in ("YES", "NO") else "NO",
        "confidence": confidence if confidence in ("HIGH", "LOW") else "LOW",
        "category": str(out.get("category", "")).strip(),
        "reason": str(out.get("reason", "")).strip(),
    }


def main():
    # Windows consoles default to cp1252 and the model can return characters it cannot
    # encode (e.g. a non-breaking hyphen), which would otherwise kill the run mid-way.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Classify snippets with the rubric prompt.")
    parser.add_argument("--naive", action="store_true",
                        help="drop the rubric from the prompt (ablation baseline)")
    parser.add_argument("--input", default="data/snippets.csv",
                        help="CSV with an id column and a snippet column")
    parser.add_argument("--output", default=None,
                        help="where to write predictions (defaults by mode)")
    args = parser.parse_args()

    system_prompt = NAIVE_SYSTEM_PROMPT if args.naive else SYSTEM_PROMPT
    out_path = args.output or (
        "llm_naive_predictions.csv" if args.naive else "llm_predictions.csv"
    )

    rows = list(csv.DictReader(open(args.input, encoding="utf-8")))
    if not rows or "id" not in rows[0] or "snippet" not in rows[0]:
        raise SystemExit(f"{args.input} must have id and snippet columns")

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "predicted", "confidence", "category", "reason"])
        for r in rows:
            out = classify(r["snippet"], system_prompt)
            w.writerow([r["id"], out["label"], out["confidence"], out["category"], out["reason"]])
            print(f"{r['id']}  {out['label']:3}  {out['confidence']:4}  "
                  f"{out['category']:33}  {out['reason']}")

    print()
    print(f"wrote {out_path} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
