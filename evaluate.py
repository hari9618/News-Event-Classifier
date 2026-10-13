"""Score every classifier against labels.csv.

Reports the confusion matrix, precision/recall/F1 on YES (the class the insurer cares
about), and accuracy split by my own labelling confidence. Writes metrics.json for the
web UI.

Usage: python evaluate.py
"""
import csv
import json
import os

SYSTEMS = [
    ("LLM (rubric prompt)", "llm_predictions.csv"),
    ("LLM (rubric v1, pre-amendment)", "llm_predictions_v1.csv"),
    ("LLM (no rubric, ablation)", "llm_naive_predictions.csv"),
    ("Rules baseline", "predictions.csv"),
]


def load(path):
    return {r["id"]: r for r in csv.DictReader(open(path, encoding="utf-8"))}


def score(gold, pred, snippets):
    missing = sorted(set(gold) - set(pred))
    if missing:
        raise SystemExit(f"predictions file is incomplete, missing ids: {missing}")

    tp = fp = fn = tn = 0
    disagreements = []
    by_conf = {"HIGH": [0, 0], "LOW": [0, 0]}   # [correct, total]

    for i in sorted(gold):
        g, p = gold[i]["label"], pred[i]["predicted"]
        if g == "YES" and p == "YES":
            tp += 1
        elif g == "NO" and p == "YES":
            fp += 1
        elif g == "YES" and p == "NO":
            fn += 1
        else:
            tn += 1

        bucket = by_conf[gold[i]["confidence"]]
        bucket[1] += 1
        bucket[0] += (g == p)

        if g != p:
            disagreements.append({
                "id": i,
                "mine": g,
                "classifier": p,
                "type": "false positive" if p == "YES" else "false negative",
                "reason": pred[i].get("reason", ""),
                "snippet": snippets[i]["snippet"],
            })

    n = len(gold)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "n": n,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "accuracy": (tp + tn) / n,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy_high_conf": by_conf["HIGH"][0] / by_conf["HIGH"][1],
        "high_conf_correct": by_conf["HIGH"][0], "high_conf_total": by_conf["HIGH"][1],
        "accuracy_low_conf": by_conf["LOW"][0] / by_conf["LOW"][1],
        "low_conf_correct": by_conf["LOW"][0], "low_conf_total": by_conf["LOW"][1],
        "disagreements": disagreements,
    }


def main():
    gold = load("labels.csv")
    snippets = load("data/snippets.csv")
    # Written analysis for the disagreements, surfaced in the UI alongside the numbers.
    notes = {}
    if os.path.exists("disagreement_notes.json"):
        notes = json.load(open("disagreement_notes.json", encoding="utf-8"))

    results = {}
    for name, path in SYSTEMS:
        if not os.path.exists(path):
            print(f"skipping {name}: {path} not found")
            continue
        m = results[name] = score(gold, load(path), snippets)
        for d in m["disagreements"]:
            d["notes"] = notes.get(d["id"])

        print(f"\n=== {name} ===")
        print(f"accuracy  {m['accuracy']:.3f}    precision {m['precision']:.3f}"
              f"    recall {m['recall']:.3f}    F1 {m['f1']:.3f}")
        print(f"confusion (YES = positive): TP={m['tp']} FP={m['fp']} FN={m['fn']} TN={m['tn']}")
        print(f"accuracy on my HIGH-confidence labels: "
              f"{m['high_conf_correct']}/{m['high_conf_total']} = {m['accuracy_high_conf']:.3f}")
        print(f"accuracy on my LOW-confidence labels:  "
              f"{m['low_conf_correct']}/{m['low_conf_total']} = {m['accuracy_low_conf']:.3f}")
        print(f"{len(m['disagreements'])} disagreements:")
        for d in m["disagreements"]:
            print(f"  {d['id']}  mine={d['mine']} classifier={d['classifier']} ({d['type']})")
            print(f"      {d['snippet'][:100]}...")

    json.dump(results, open("metrics.json", "w", encoding="utf-8"), indent=2)
    print("\nwrote metrics.json")


if __name__ == "__main__":
    main()
