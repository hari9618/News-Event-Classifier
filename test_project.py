"""End-to-end checks on the deliverables. Run: python test_project.py"""
import csv, json, subprocess, sys

def load(p): return list(csv.DictReader(open(p, encoding="utf-8")))
ok, fail = 0, []
def check(name, cond, detail=""):
    global ok
    if cond: ok += 1; print(f"  PASS  {name}")
    else: fail.append(name); print(f"  FAIL  {name}  {detail}")

print("\n[1] labels.csv")
labels = load("labels.csv")
ids = [r["id"] for r in labels]
check("40 rows", len(labels) == 40, f"got {len(labels)}")
check("ids 01-40 unique and sorted", ids == sorted(ids) and len(set(ids)) == 40)
check("labels are YES/NO only", all(r["label"] in ("YES","NO") for r in labels))
check("confidence is HIGH/LOW only", all(r["confidence"] in ("HIGH","LOW") for r in labels))
check("every LOW has a justification",
      all(r["justification"].strip() for r in labels if r["confidence"]=="LOW"))
check("no HIGH carries a justification",
      not [r["id"] for r in labels if r["confidence"]=="HIGH" and r["justification"].strip()])

print("\n[2] user's frozen decisions are intact")
frozen = {"38":("NO","LOW"),"08":("YES","HIGH"),"11":("YES","HIGH"),"15":("NO","HIGH"),
          "25":("YES","HIGH"),"30":("NO","HIGH"),"26":("YES","LOW"),"09":("YES","LOW"),
          "39":("YES","HIGH")}
by_id = {r["id"]: r for r in labels}
for i,(lab,conf) in frozen.items():
    check(f"{i} = {lab}/{conf}", (by_id[i]["label"],by_id[i]["confidence"])==(lab,conf),
          f"got {by_id[i]['label']}/{by_id[i]['confidence']}")

print("\n[3] snippets and predictions align")
snips = load("data/snippets.csv")
check("40 snippets", len(snips) == 40)
check("snippet ids match label ids", {r["id"] for r in snips} == set(ids))
for f in ["llm_predictions.csv","llm_naive_predictions.csv","predictions.csv"]:
    rows = load(f)
    check(f"{f} has 40 rows", len(rows)==40, f"got {len(rows)}")
    check(f"{f} ids complete", {r['id'] for r in rows}=={r['id'] for r in snips})
    check(f"{f} labels valid", all(r["predicted"] in ("YES","NO") for r in rows))

print("\n[4] prompt is faithful to RUBRIC.md")
rubric = open("RUBRIC.md", encoding="utf-8").read().lower()
from prompt import SYSTEM_PROMPT, CATEGORIES, MODEL
p = SYSTEM_PROMPT.lower()
for clause in ["physical damage","bodily injury","business interruption","forecast",
               "precaution","planned operational activity","slow-onset","unverified"]:
    check(f"prompt carries rubric clause '{clause}'", clause in p)
check("no invented Y1-Y5/N1-N5 codes in prompt",
      not any(c in SYSTEM_PROMPT for c in ["Y1 ","Y2 ","N1 ","N2 ","N5 "]))
check("model is gpt-oss-120b", MODEL == "openai/gpt-oss-120b")
used = {r["category"] for r in load("llm_predictions.csv")}
check("all predicted categories are in the closed list", used <= set(CATEGORIES),
      f"stray: {used - set(CATEGORIES)}")

print("\n[5] metrics.json matches a fresh recomputation")
subprocess.run([sys.executable,"evaluate.py"], capture_output=True, check=True)
m = json.load(open("metrics.json", encoding="utf-8"))
main = m["LLM (rubric prompt)"]
gold = {r["id"]: r["label"] for r in labels}
pred = {r["id"]: r["predicted"] for r in load("llm_predictions.csv")}
tp = sum(1 for i in gold if gold[i]=="YES" and pred[i]=="YES")
fp = sum(1 for i in gold if gold[i]=="NO"  and pred[i]=="YES")
fn = sum(1 for i in gold if gold[i]=="YES" and pred[i]=="NO")
tn = sum(1 for i in gold if gold[i]=="NO"  and pred[i]=="NO")
check("confusion matrix recomputes", (main["tp"],main["fp"],main["fn"],main["tn"])==(tp,fp,fn,tn),
      f"json={(main['tp'],main['fp'],main['fn'],main['tn'])} recomputed={(tp,fp,fn,tn)}")
check("tp+fp+fn+tn == 40", tp+fp+fn+tn == 40)
prec = tp/(tp+fp) if tp+fp else 0
rec  = tp/(tp+fn) if tp+fn else 0
check("precision correct", abs(main["precision"]-prec) < 1e-9)
check("recall correct", abs(main["recall"]-rec) < 1e-9)
check("f1 correct", abs(main["f1"] - 2*prec*rec/(prec+rec)) < 1e-9)
check("accuracy correct", abs(main["accuracy"] - (tp+tn)/40) < 1e-9)
check("2 live disagreements reported", len(main["disagreements"])==2,
      str([d["id"] for d in main["disagreements"]]))
check("disagreements are 25/33",
      {d["id"] for d in main["disagreements"]}=={"25","33"})
check("each disagreement carries written analysis",
      all(d.get("notes") and all(k in d["notes"] for k in ("why","assessment","tells_us"))
          for d in main["disagreements"]))
v1 = m["LLM (rubric v1, pre-amendment)"]
check("v1 kept for the amendment comparison", v1["fn"] == 3 and v1["recall"] < main["recall"],
      f"v1 recall={v1['recall']} v2 recall={main['recall']}")

print("\n[6] documented numbers match metrics.json")
ev = open("EVALUATION.md", encoding="utf-8").read()
rd = open("README.md", encoding="utf-8").read()
for doc,name in [(ev,"EVALUATION.md"),(rd,"README.md")]:
    check(f"{name} states 95.0% accuracy", "95.0%" in doc)
    check(f"{name} states 90.0% recall", "90.0%" in doc or "90%" in doc)
check("EVALUATION.md states 100% precision", "100%" in ev)
check("EVALUATION.md states F1 94.7%", "94.7%" in ev)
check("EVALUATION.md quotes ablation 71.4%", "71.4%" in ev)
check("EVALUATION.md documents the v1 -> v2 experiment", "amendment experiment" in ev.lower())
check("EVALUATION.md analyses all 3 disagreements (2 live + 1 resolved)",
      all(f"snippet {i}" in ev for i in ["18","25","33"]))
for q in ["what the classifier said","More defensible","Where the weakness lies"]:
    check(f"EVALUATION.md uses required framing '{q}'", q.lower() in ev.lower())

print("\n[7] deliverables present")
import os
for f in ["RUBRIC.md","labels.csv","EVALUATION.md","README.md","prompt.py",
          "llm_classify.py","evaluate.py","app.py","static/index.html",".gitignore"]:
    check(f"{f} exists", os.path.exists(f))
check(".env is gitignored", ".env" in open(".gitignore", encoding="utf-8").read())

print("\n[8] API endpoints")
from fastapi.testclient import TestClient
from app import app
c = TestClient(app)
check("GET / serves UI", c.get("/").status_code == 200)
r = c.get("/api/metrics")
check("GET /api/metrics returns all 4 systems", r.status_code==200 and len(r.json())==4,
      str(list(r.json())))
r = c.post("/api/classify", json={"text":"A fire destroyed a warehouse in Rotterdam; two workers were injured."})
d = r.json()
if "error" in d:
    # Free-tier quota exhausted or no key: the endpoint must degrade cleanly, not crash.
    check("live API unavailable, handled cleanly", r.status_code == 200 and isinstance(d["error"], str),
          str(d))
    print(f"  SKIP  live classification (API unavailable: {d['error'][:60]}...)")
else:
    check("POST /api/classify returns YES for a fire", r.status_code==200 and d["label"]=="YES", str(d))
    check("response carries category + model", bool(d.get("category")) and bool(d.get("model")))
r = c.post("/api/classify", json={"text":"   "})
check("empty input handled", "error" in r.json())


print()
print("[9] robustness and generalisation")
import subprocess, tempfile, os as _os
tmp = tempfile.mkdtemp()
src = _os.path.join(tmp, "feed.csv"); dst = _os.path.join(tmp, "out.csv")
with open(src, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["id", "snippet"])
    w.writerow(["x1", "A fire destroyed a warehouse in Rotterdam; two workers were injured."])
    w.writerow(["x2", "Shares in a reinsurer fell 4% after an analyst downgrade."])
r = subprocess.run([sys.executable, "classify.py", "--input", src, "--output", dst],
                   capture_output=True, text=True)
check("regex classifier accepts --input/--output", r.returncode == 0, r.stderr[-200:])
if r.returncode == 0:
    out = load(dst)
    check("arbitrary ids preserved", [x["id"] for x in out] == ["x1", "x2"])
    check("fire=YES and market=NO on unseen text",
          (out[0]["predicted"], out[1]["predicted"]) == ("YES", "NO"))

check("requirements.txt lists groq and fastapi",
      all(k in open("requirements.txt", encoding="utf-8").read() for k in ("groq", "fastapi")))

import llm_classify
saved = llm_classify._CLIENT
class _Fake:
    class chat:
        class completions:
            @staticmethod
            def create(**kw):
                class M: content = '{"label":"maybe","confidence":"?","category":"x","reason":"y"}'
                class C: message = M()
                class R: choices = [C()]
                return R()
llm_classify._CLIENT = _Fake()
res = llm_classify.classify("anything")
check("invalid label falls back to NO", res["label"] == "NO", str(res))
check("invalid confidence falls back to LOW", res["confidence"] == "LOW", str(res))
llm_classify._CLIENT = saved


print()
print("[10] frontend javascript is valid")
import re as _re, shutil as _sh, subprocess as _sp, tempfile as _tf, os as _o
_html = open("static/index.html", encoding="utf-8").read()
_js = chr(10).join(_re.findall(r"<script>(.*?)</script>", _html, _re.S))
_node = _sh.which("node")
if _node:
    _f = _o.path.join(_tf.mkdtemp(), "c.js")
    open(_f, "w", encoding="utf-8").write(_js)
    _r = _sp.run([_node, "--check", _f], capture_output=True, text=True)
    check("page JavaScript parses (node --check)", _r.returncode == 0, _r.stderr[:200])
else:
    _bad = [i+1 for i, l in enumerate(_js.split(chr(10)))
            if (l.count(chr(34)) - l.count(chr(92)+chr(34))) % 2]
    check("no string literal spans a newline", not _bad, str(_bad))
for _fn in ["function parseCSV", "function pickFile", "async function runBatch",
            "async function classify", "function showDetail"]:
    check(f"defined: {_fn}", _fn in _js)

print(f"\n{'='*46}\n{ok} passed, {len(fail)} failed")
if fail: print("FAILED:", fail); sys.exit(1)
print("ALL CHECKS PASSED")
