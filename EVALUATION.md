# Evaluation

**Classifier:** `openai/gpt-oss-120b` on Groq, `temperature=0`, `seed=0`, with `RUBRIC.md`
compressed into the system prompt (`prompt.py`). Note that this does not make the run fully
reproducible — see §3.
**Reference labels:** `labels.csv` — mine, applied from `RUBRIC.md` and frozen before the
classifier was run. They were not edited afterwards.
**Reproduce:** `python llm_classify.py && python llm_classify.py --naive && python evaluate.py`

## 1. Headline numbers

n = 40. YES (insurable loss event) is the positive class.

### Main classifier — LLM + rubric

|  | Actual YES | Actual NO |
|---|---|---|
| **Predicted YES** | TP 18 | FP 0 |
| **Predicted NO** | FN 2 | TN 20 |

| Metric | Value |
|---|---|
| Accuracy | 95.0% |
| Precision | 100% |
| Recall | 90.0% |
| F1 | 94.7% |

### All systems

| System | Accuracy | Precision | Recall | F1 | FP | FN |
|---|---|---|---|---|---|---|
| **LLM + rubric v2 (main)** | **95.0%** | **100%** | **90.0%** | **94.7%** | 0 | 2 |
| LLM + rubric v1 (pre-amendment) | 92.5% | 100% | 85.0% | 91.9% | 0 | 3 |
| LLM, no rubric (ablation) | 80.0% | 71.4% | 100% | 83.3% | 8 | 0 |
| Rules baseline (regex) | 90.0% | 100% | 80.0% | 88.9% | 0 | 4 |

v1 and v2 differ only in the rubric: v2 adds the source-strength rule described in §4. Same
model, same code, same labels.

## 2. Which numbers matter, and why

**Not accuracy.** This set is 50/50 by construction. Real news traffic is perhaps 1–2% loss
events, so a classifier that answered NO to everything would score ~98% accuracy on live data
and detect nothing. Accuracy is reported because the set is balanced, and should be dropped
the moment this touches production.

**Recall first, precision second.** The product is early warning, so a miss is the expensive
error (argued in §7). On that measure the main classifier's 85.0% recall is the weak spot, not
its perfect precision.

**The ablation is the most informative comparison, and it does not say what I expected.**
Removing the rubric from the prompt moves precision 100% → 71.4% and recall 90.0% → 100%.

So the rubric is doing real work — it eliminates all eight false positives, and every one is a
case the rubric explicitly addresses (04 strike ballot, 14 forecast, 15 precaution, 17 court
judgment, 21 snowfall with no incidents, 24 routine flaring, 30 planned works, 38 exposure with
no misuse). Without it the model treats any *potential future* loss as a loss event.

**But the rubric buys that precision by making the model conservative, and it pays for it in
recall — which is the error type this product cares about more.** Both remaining misses are
cases where the rubric gave the model a NO-clause to reach for. That is a finding against my own
rubric rather than a model defect, and §4 shows what happened when I acted on it.

**The confidence output was unusable in v1, and the rubric amendment fixed it.** In v1 the model
returned HIGH on all 40 items, never once LOW, including on the three it got wrong — so routing
LOW-confidence items to human review could not be driven by the model at all. In v2 it returns
LOW on exactly two items, 09 and 39, which are precisely the two unverified-sourcing snippets the
amendment was about. Making one clause more specific turned a dead signal into a working one.

**My confidence labels carry signal too.** The classifier agrees with 33/34 of my HIGH-confidence
labels (97.1%) but only 5/6 of my LOW ones (83.3%). Both remaining disagreements sit on rows I had
flagged LOW. Disagreement concentrates where I said the rubric was thin.

**What these numbers cannot support.** With 40 items, one flipped label moves recall by 5 points.
The 95% interval around 90.0% recall runs roughly 68%–99%. The v1→v2 gain is one snippet: real and
explainable, but not separable from noise at this sample size. These are debugging signals, not
performance estimates.

## 3. Reproducibility (measured, not assumed)

Temperature 0 is **not** deterministic on this endpoint. Running the identical v1 prompt over the
identical 40 snippets three times, with `temperature=0` and `seed=0`, gives:

| Run | Accuracy | Precision | Recall | F1 | False negatives |
|---|---|---|---|---|---|
| 1 | 92.5% | 100% | 85.0% | 91.9% | 18, 25, 33 |
| 2 | 95.0% | 100% | 90.0% | 94.7% | 25, 33 |
| 3 | 92.5% | 100% | 85.0% | 91.9% | 18, 25, 33 |

**Label stability: 39/40 (97.5%).** Exactly one snippet flips between runs — **18**, the cargo
plane, which came back NO / YES / NO. Everything else is stable, and the free-text `reason`
field varies in wording throughout without changing any other verdict.

This matters twice over. First, headline accuracy on this set has a genuine ±2.5 point run-to-run
spread, so quoting 92.5% to three significant figures would be false precision — at n=40 a single
unstable item is 2.5 points. The committed `llm_predictions.csv` is the majority outcome across
the three runs and the numbers throughout this document come from it.

Second, and more usefully: **the one item the model cannot decide is the same item §6 identifies
as having two applicable rubric clauses and no precedence rule between them.** The instability is
not random noise sprayed across the set; it is concentrated precisely where my rubric is
ambiguous. That is independent evidence for the diagnosis in Disagreement 1, arrived at by a
different route than reading the model's reasoning.

In production I would not tolerate a classifier whose verdict depends on the run. The fix is the
rubric edit in §6 rather than a sampling change: an item that is genuinely 50/50 under the
written criteria should be *routed to a human*, not resolved by whichever way the sampler falls.
Failing that, majority vote over three calls converts the instability into an explicit
low-confidence signal, at three times the cost.

## 4. The amendment experiment: fixing the rubric, not the model

Separately from the classifier's disagreements, I re-derived all 40 labels from the rubric as a
check on myself, and found one place where two of my own labels rested on a distinction the
rubric never stated.

**Snippets 09 and 39 are both unverified reports, and I had scored their confidence
differently.** 09 (Chilean mine collapse) is LOW; 39 (Yemen flash floods) is HIGH, even though 39
explicitly says "details are unverified". My reasoning was that 09 rests on a single eyewitness
with the operator declining to confirm, whereas 39 has multiple local sources reporting both
fatalities and damage. I still think that is right, but the rubric only said "reduce confidence
when the evidence is weak", which does not distinguish one uncorroborated source from several
independent ones. A second analyst reading my rubric could reasonably have marked 39 LOW.

**The amendment.** I added one sentence to the unverified-reports clause:

> Treat a single uncorroborated source, or an operator declining to confirm, as weak evidence and
> mark it LOW. Multiple independent sources reporting both casualties and damage can still
> support HIGH, even where the report is described as unverified.

Then I mirrored it into the prompt and re-ran all 40 snippets. Nothing else changed — same model,
same code, same labels, same temperature and seed. `llm_predictions_v1.csv` (before) and
`llm_predictions.csv` (after) are both committed, so the comparison is reproducible.

| | v1 (before) | v2 (after) |
|---|---|---|
| Accuracy | 92.5% | **95.0%** |
| Recall | 85.0% | **90.0%** |
| F1 | 91.9% | **94.7%** |
| Precision | 100% | 100% |
| Misses | 18, 25, 33 | 25, 33 |
| Items marked LOW by the model | 0 of 40 | 09 and 39 |

**Two things moved, and the second is the more interesting.**

First, snippet 18 (the cargo plane) flipped from NO to YES and became correct, lifting recall
five points. That is the item §3 shows was unstable across runs, so I would not claim the
amendment alone deterministically fixed it — one snippet at n=40 is within the noise I measured.
The honest reading is that a more specific rubric made a borderline call tip the right way.

Second, and not something I predicted: **the amendment repaired the confidence signal.** In v1
the model returned HIGH on all 40 items and never used LOW, which made the whole
route-uncertain-items-to-a-human design unimplementable. In v2 it returns LOW on exactly two
snippets — 09 and 39 — which are precisely the two the amended clause is about. One sentence of
extra specificity in a clause about *evidence strength* turned a dead signal into a working one.

**Where it still disagrees with me.** The model marks 39 LOW; I have it HIGH. So it accepted the
"single uncorroborated source is weak" half of my rule and not the "multiple independent sources
can support HIGH" half. That is a fair challenge: my distinction between one source and several
is a judgement about how much corroboration is enough, and the amendment states it without
justifying it. I would keep my label and add the reasoning to the rubric, but I note that the
model, reading only my words, was more cautious than I was.

**The finding I would put in front of an underwriter:** across everything tried here — a regex
baseline, a prompted LLM, an ablation, and a rubric amendment — *the single change that most
improved the classifier was editing one sentence of the rubric.* Recall moved 85% → 90% and a
broken confidence signal started working, with no change to the model, the code, or the labels.
This is an analyst-time problem more than an ML problem, which is also the argument in answer (c)
for where the tuning effort should go.

## 5. Two honesty caveats on the headline score

**Partial circularity.** I wrote the rubric, labelled from it, then compressed the same rubric
into the prompt. Part of the 92.5% measures prompt-to-rubric fidelity rather than correctness.
The ablation is less contaminated, because the naive prompt inherits none of my reasoning.

**Two agreements are definitional, not earned.** `RUBRIC.md` illustrates two of its NO clauses
with near-verbatim descriptions of snippets in the evaluation set — "shutting down a pipeline
because of an abnormal reading when there is no confirmed leak" (15) and "a court judgment
relating to historical contamination" (17). The prompt reproduces the rubric faithfully, so it
carries those illustrations with it, and the classifier's correct calls on 15 and 17 are
therefore partly given to it. This is a side-effect of the brief asking the rubric to handle
the awkward cases *found in this data*. No other evaluation snippet appears in the prompt.

## 6. The three disagreements

The shipped classifier (v2) has two live disagreements with my labels, 25 and 33, both false
negatives. I analyse those two, plus snippet 18 — which v1 got wrong and the rubric amendment
resolved — because a disagreement I diagnosed and then fixed shows more than a third static one.
For each: what the classifier said, what I said, which is more defensible, why, and where the
weakness actually lies.

Ordered most to least clear-cut.

---

### Disagreement 1 (live) — snippet 25 (Italian drought, irrigation restrictions)

> "A historic drought has left reservoir levels in northern Italy at 30% of capacity, prompting
> irrigation restrictions for farmers."

- **Classifier predicted:** NO — category *no meaningful loss*, reasoning "Drought caused
  restrictions but no reported damage, injury, or loss."
- **My label:** YES / HIGH.
- **More defensible:** mine, clearly. This is the weakest of the classifier's calls, and it is
  unchanged between v1 and v2.
- **Why:** two independent reasons. First, the rubric's slow-onset clause is directly on point —
  "Slow-onset hazards: these can be YES once their effects are already occurring, rather than
  while they are only forecast" — and the effects are unambiguously already occurring, since
  restrictions are in force and reservoirs are at 30%. Second, the classifier invoked the *no
  meaningful loss* clause, but that clause requires the snippet to explicitly state there was no
  loss ("where the snippet explicitly says there was no damage, injury or other loss"). Snippet
  25 says nothing of the kind. The classifier applied a clause whose own precondition is not
  met — it read absence of a stated loss as a statement of no loss. Commercially, drought with
  enforced irrigation restrictions is exactly what crop and parametric agricultural covers
  respond to.
- **Where the weakness lies: primarily the classifier, secondarily the rubric's structure.** The
  misapplication is the model's. But the rubric made it easy: the slow-onset rule lives under
  *Borderline cases* at the bottom rather than in the YES list, so a reader working top-down
  hits *no meaningful loss* first and stops. **Fix: promote slow-onset hazards to a full YES
  bullet, and tighten the *no meaningful loss* clause to require an explicit negative statement
  in the text.**

---

### Disagreement 2 (live) — snippet 33 (dam in Laos showing cracks)

> "A dam in Laos showed cracks after heavy rain and authorities evacuated downstream villages as
> a precaution; engineers are assessing the structure."

- **Classifier predicted:** NO — category *precaution without confirmed loss*, reasoning "Cracks
  observed but no confirmed failure, damage, or loss reported."
- **My label:** YES / LOW.
- **More defensible:** mine, on the rubric as written — but this is genuinely contested and I
  am the least certain here of the three.
- **Why:** the rubric's borderline rule states "a precautionary response without confirmed
  damage is NO; confirmed physical damage is YES." Cracks in a dam *are* confirmed physical
  damage to the insured structure, and engineering/property covers respond to damage to the
  asset, not only to its total failure. Evacuation costs are also already being incurred. The
  classifier's reading collapses "damage" into "loss has crystallised": nothing has failed, the
  assessment is ongoing, and if the dam holds there may be no claim.
- **Where the weakness lies: the rubric.** The whole disagreement turns on an ambiguity in the
  word "damage" that my rubric never resolves — does the damage test apply to *the asset*
  (cracks qualify) or to *a resulting loss* (nothing yet)? Both readings are available in the
  current text, which is why two careful readers split. **Fix: define "confirmed physical
  damage" as damage to the insured asset itself, independent of whether a claim has
  crystallised — and add the WATCH tier this case argues for, since forcing 33 into a binary
  discards the fact that it is a live situation worth re-checking tomorrow.**

---

### Disagreement 3 (resolved) — snippet 18 (cargo plane, emergency landing after engine fire warning)

> "A cargo plane made an emergency landing in Anchorage after an engine fire warning; the
> aircraft landed safely with no injuries."

- **Classifier predicted (v1):** NO — category *precaution without confirmed loss*, reasoning
  "Emergency landing due to warning, no confirmed damage or injury reported."
- **Classifier predicts (v2, after the amendment):** YES — category *transport/asset casualty*,
  reasoning "Emergency landing due to engine fire warning likely caused aircraft damage, a hull
  claim." It now agrees with me.
- **My label:** YES / LOW.
- **More defensible:** mine, but narrowly. This was the closest of the three.
- **Why:** the rubric's *transport/asset casualties* clause covers "a vessel, aircraft, vehicle
  or other insured asset [that] experiences a casualty that could reasonably create a property,
  hull, machinery, salvage, or related claim, even if nobody is injured." An unscheduled
  engine-warning landing reliably produces a boroscope inspection, often an engine change, plus
  diversion, repositioning and cargo-handling costs. Those are aviation claims, and they do not
  depend on injuries. The classifier's counter-argument is legitimate though: an engine fire
  *warning* can be a false indication, and no damage is confirmed in the text. If the warning
  was spurious the costs may fall below any deductible.
- **Where the weakness lies: the rubric.** Both clauses genuinely apply — this is an asset
  casualty *and* a precautionary response with no confirmed damage — and the rubric provided no
  precedence rule to decide which wins. Neither reading was a misreading, which is exactly why
  §3 found this the one snippet whose label was unstable across identical runs: the model was
  genuinely on the fence because my rubric left it there.
- **What happened when I acted on it.** The v2 amendment did not target this clause at all, yet
  18 resolved in my favour anyway — a more precise rubric tipped a borderline call. I am
  deliberately *not* claiming the amendment fixed it: §3 shows 18 flipping between identical v1
  runs, so one observation cannot separate the amendment from noise. **The precedence rule I
  proposed — the asset-casualty clause outranks the precaution clause whenever the asset itself
  has undergone an unplanned event, with "precaution" reserved for an untouched asset as in 15 —
  is still the right fix, and is still unshipped.** It would also settle snippet 33 below.

---

---

**A related observation on an agreement.** The rules baseline gets snippet 30 (Felixstowe crane
upgrade) right for the wrong reason: my rubric says NO because planned works are not fortuitous,
but the regex says NO only because "software upgrade" is missing from its hazard list. Reword it
to "a crane fault" and it flips to YES while the correct answer stays NO. The LLM cited *planned
activity* — the right reason. Checking the reasoning field, not just the label, is what exposes
this; agreement on the label alone is not evidence the logic is sound.

## 7. Answers to the three assessment questions

### (a) Where does the classifier disagree with you?

Covered in §6: snippets 25 and 33 (live) and 18 (resolved by the rubric amendment), all false
negatives. Where the fault lies: **one classifier error (25), two rubric gaps (18, 33)** — and
the two rubric gaps are the same underlying issue, that the rubric does not say what happens when
a snippet satisfies a YES clause and a NO clause at the same time. §4 shows what happened when I
repaired a different under-specified clause: recall rose and the confidence signal started
working, which is the evidence that the remaining gaps are worth closing.

### (b) What is wrong with using your own labels as ground truth, and what would you do in production?

They are not ground truth. They are one analyst's reading of a rubric that the same analyst
wrote, then used to prompt the classifier. Specific defects:

1. **No independent check.** Nobody has tested whether a second analyst would agree with me. On
   the six LOW rows I would not confidently bet on my own consistency a week from now.
2. **The awkward calls are conventions, not facts.** 17 (historical liability) and 30 (planned
   works) are NO because I drew the scope boundary there. An underwriter could reasonably draw
   it elsewhere and every number above would move.
3. **The rubric was written after seeing the data.** The brief asks for exactly that, but it
   means the rubric is fitted to these 40 items and its clauses have never faced an unseen one.
4. **No claims feedback.** The commercially meaningful label is "did this produce a notified
   loss", knowable only months later. I am labelling a proxy and validating against the proxy.

**In production:** two analysts label independently, measure Cohen's kappa, a third adjudicates;
every adjudication becomes a dated rubric amendment so the standard evolves in the open; a
frozen gold set that never touches prompt development plus a separate dev set for iteration
(right now there is one set and I have already looked at it); monthly re-labelling of a live
traffic sample to catch drift, since news vocabulary moves faster than rubrics; and eventually
joining flagged events to actual claims notifications to test whether the proxy is worth
anything.

### (c) At 100,000 items a day, which error type matters more, and what would you tune?

**False negatives, decisively.** The product is early warning. A miss is a silent failure: no
alert fires, nobody knows to look, and the insurer learns about it when the claim arrives — by
which point the value of knowing early (reserving, reinsurance notification, adjusters
mobilised, exposure checked against the book) has gone. A false positive costs an analyst about
thirty seconds of reading.

The arithmetic: at a 1% base rate, 100,000 items/day holds ~1,000 real events. The main
classifier's 90% recall would still miss ~100 every day, ~36,000 a year. Precision is a staffing
question: even at 71% precision (the ablation) the queue is ~1,400 items/day. That asymmetry is
also why I would not optimise F1 — it weights the two errors equally, and here they are not.

**What I would tune, in order:**

1. **Close the two rubric gaps found in §6 before touching anything else.** Add the precedence
   rule (asset-casualty beats precaution) and promote the slow-onset clause. Those two edits
   target all three misses and cost nothing at inference time. This is the highest-value change
   available and it is an analyst edit, not an engineering one.
2. **Rebalance the prompt toward recall.** The ablation proves the rubric currently trades
   recall for precision. Since we would rather over-flag, I would add an explicit instruction:
   when a snippet plausibly satisfies both a YES and a NO clause, return YES with LOW
   confidence. Then re-measure — I would expect recall toward 100% at some precision cost, which
   is the trade we want.
3. **Move to a numeric confidence score.** v2 emits LOW on just two items, so the signal now
   exists but is far too coarse to place an operating point on. Ask for a 0–100 score instead of a
   HIGH/LOW token, plot precision against recall, and set the threshold where recall meets an
   agreed floor (I would argue ≥95%). Report the precision at that recall as the cost and let the
   business accept or reject the resulting review load.
4. **Weight errors by severity.** Missing a hailstorm damaging "thousands of vehicles" is not
   equivalent to missing a towage claim. Weight recall by expected severity — peril type, and
   whether an exposure concentration sits in the affected region — running a permissive
   threshold on high-severity perils and a stricter one on the long tail. The same weighting
   prioritises the review queue rather than merely filling it.
5. **Control cost at volume.** 100,000 LLM calls/day is real money and latency. The regex
   baseline holds 100% precision on this set, so it can front the pipeline: auto-accept its YES
   calls and send only the remainder to the LLM. That is a cost argument, not an accuracy one,
   and it needs re-validating on real traffic before anyone relies on it.

**Where false positives would start to matter:** if alerts triggered automatic downstream action
— reserving, reinsurance notification, client communication. They should not. Keep a human
between the classifier and any outbound action until precision is measured on real traffic
rather than on 40 snippets.
