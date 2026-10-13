"""Rule-based classifier for the insurable-loss-event task.

An ordered cascade rather than a bag-of-words score: the first rule that fires
decides the label, so every prediction carries the reason that produced it.
The rules are a deliberate approximation of RUBRIC.md, not a copy of it.

Usage: python classify.py [--input data/snippets.csv] [--output predictions.csv]
"""
import argparse
import csv
import re

# 1. Topics that are never a loss event, however hazard-like the vocabulary.
NON_EVENT = [
    (r"\bshares?\b|\bdowngrad|\banalysts?\b|\bpremiums?\b|\brenewals?\b|\bbrokers\b", "market/financial commentary"),
    (r"\braised \$|\bseries [a-e]\b|\bfunding\b", "corporate finance"),
    (r"\bstudy\b|\bacademic paper\b|\bresearch\b|\bmachine-learning\b", "research"),
    (r"\bconsultations?\b|\bregulations?\b|\brequirements\b|\bcourt ordered\b|\bunderwriting\b", "regulation/legal/policy"),
    (r"\bstrike ballot\b|\bfiled for administration\b", "labour/insolvency"),
]

# 2. Forward-looking language: a forecast is not an event.
FORECAST = r"\bforecast|\bpredict|\boutlook\b|\badvisory\b|red-flag|warnings? for"

# 3. Explicit statements that nothing was lost.
NO_LOSS = r"\bno (injuries|incidents|leak|oil spill|misuse|casualties|damage)\b|as a precaution|described it as routine"

# 4. A peril that insurance recognises.
HAZARD = (r"\bfire\b|\bblaze\b|\bexplosion\b|\bflood|\bstorm|\bhail|\bearthquake\b|\btsunami\b|\bwildfire"
          r"|\bderail|\bcollapse|\baground\b|\bransomware\b|\bcyber attack\b|\bdrought\b|\bsnowfall\b"
          r"|\bcracks?\b|\bspill\b|\bleak\b|\bsoftware fault\b|\bfailure\b|\blost engine power\b|\bemergency landing\b")

# 5. Evidence that the peril actually bit.
IMPACT = (r"\bdestroyed\b|\bdamage|\binjur|\bhospitalised\b|\bfatalities\b|\bcasualties\b|\bmissing\b|\bkilled\b"
          r"|\bevacuat|\brescue\b|\boffline\b|\bhalted\b|\bsuspended\b|\bwithout power\b|\bcancelled\b"
          r"|\bsubmerged\b|\brestrictions\b|\blevelled\b|\bassessments\b")


def classify(text):
    """Return (label, reason) for one snippet."""
    t = text.lower()
    for pattern, topic in NON_EVENT:
        if re.search(pattern, t):
            return "NO", f"non-event topic: {topic}"
    has_impact = bool(re.search(IMPACT, t))
    if re.search(FORECAST, t) and not has_impact:
        return "NO", "forward-looking hazard, no impact reported"
    if re.search(NO_LOSS, t):
        return "NO", "explicitly reports no loss / precautionary only"
    if re.search(HAZARD, t) and has_impact:
        return "YES", "peril present with reported impact"
    return "NO", "no peril-plus-impact evidence"


def main():
    parser = argparse.ArgumentParser(description="Regex baseline classifier.")
    parser.add_argument("--input", default="data/snippets.csv")
    parser.add_argument("--output", default="predictions.csv")
    args = parser.parse_args()

    rows = list(csv.DictReader(open(args.input, encoding="utf-8")))
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "predicted", "reason"])
        for r in rows:
            label, reason = classify(r["snippet"])
            w.writerow([r["id"], label, reason])
    print(f"wrote {args.output} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
