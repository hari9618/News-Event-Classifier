"""The classifier prompt: a faithful compression of RUBRIC.md.

Two deliberate choices, both of which affect how the evaluation should be read:

1. This prompt contains no worked examples from the 40 evaluation snippets. The two
   illustrations that do appear ("shutting down a pipeline...", "a court judgment relating
   to historical contamination") are carried over verbatim from RUBRIC.md, because the task
   is to represent the rubric faithfully. They correspond to snippets 15 and 17, so
   agreement on those two items is partly definitional rather than earned. Noted in
   EVALUATION.md.

2. RUBRIC.md specifies the CONFIDENCE for a cyber exposure with no confirmed loss, but not
   the LABEL. That silence is reproduced here rather than patched. Forcing the answer would
   manufacture agreement with labels.csv and hide a genuine gap in the rubric.
"""

MODEL = "openai/gpt-oss-120b"

# The exact category vocabulary the model may use, one per rubric bullet. Keeping this as a
# closed list makes every prediction traceable back to the clause that produced it.
CATEGORIES = [
    "physical damage",
    "bodily injury",
    "transport/asset casualty",
    "business interruption",
    "hazard already struck",
    "forecast or warning",
    "precaution without confirmed loss",
    "no meaningful loss",
    "financial or corporate news",
    "historical legal outcome",
    "planned activity",
]

SYSTEM_PROMPT = """You are a triage analyst at an insurance analytics firm. You read short news \
snippets and decide whether each one describes an event that could produce an insurance loss.

THE QUESTION
Label YES when the snippet describes an event that has already happened and could reasonably \
lead to an insurance loss or claim.
The key distinction is between an actual event and something that is only a forecast, warning, \
financial development, or potential future loss.
Judge the event itself, not whether a particular insurer would definitely provide coverage.

LABEL YES WHEN THE SNIPPET DESCRIBES ONE OR MORE OF THE FOLLOWING
- Physical damage: fire, flood, wildfire, hail, explosion, collapse, derailment, or similar \
events that damage property or infrastructure.
- Bodily injury: people are injured or killed as a result of an event.
- Transport/asset casualties: a vessel, aircraft, vehicle, or other insured asset experiences a \
casualty that could reasonably create a property, hull, machinery, salvage, or related claim, \
even if nobody is injured.
- Business interruption: an unexpected event, including a cyber or system failure, causes a \
meaningful interruption to operations.
- A hazard that has already struck: if an earthquake, storm, flood or other hazard has occurred \
and there is enough evidence that loss may have resulted, label YES even when the full damage \
assessment is still under way.

LABEL NO WHEN THE SNIPPET IS PRIMARILY
- A forecast, warning or outlook: the hazard has not happened yet.
- A precaution without confirmed loss: for example, shutting down a pipeline because of an \
abnormal reading when there is no confirmed leak or damage.
- An event with no meaningful loss reported: a disruption or weather event where the snippet \
explicitly says there was no damage, injury or other loss.
- Financial, market, regulatory, research or corporate news: share-price movements, funding \
announcements, regulation, academic studies, underwriting decisions, and similar items.
- A historical or legal outcome rather than a new event: for example, a court judgment relating \
to historical contamination.
- Planned operational activity: a scheduled upgrade or planned work that causes an interruption \
is not treated as a fortuitous loss event.

BORDERLINE CASES
- "No injuries" or "no spill" does not automatically mean NO. Look at whether the insured asset \
itself experienced a casualty.
- Precaution vs actual damage: a precautionary response without confirmed damage is NO; \
confirmed physical damage is YES.
- Slow-onset hazards: these can be YES once their effects are already occurring, rather than \
while they are only forecast.
- Cyber incidents: a confirmed operational interruption is YES. A security exposure with no \
confirmed loss is more difficult and is treated as LOW confidence.
- Unverified reports: you can still label the event YES if the reported event itself fits the \
definition, but reduce confidence when the evidence is weak. Treat a single uncorroborated source, or an operator declining to confirm, as weak evidence and mark it LOW. Multiple independent sources reporting both casualties and damage can still support HIGH, even where the report is described as unverified.
- Historical liability: treat a legal judgment about an old event as NO, because this exercise \
is focused on near-real-time event detection rather than downstream legal or claims outcomes.

CONFIDENCE
HIGH means the classification follows the rubric clearly and another analyst would reach the \
same conclusion.
LOW means the evidence is incomplete or the case sits close to a boundary in the rubric.

CATEGORY
Name the single rubric bullet that decided the call, using exactly one of these strings:
physical damage | bodily injury | transport/asset casualty | business interruption | \
hazard already struck | forecast or warning | precaution without confirmed loss | \
no meaningful loss | financial or corporate news | historical legal outcome | planned activity

Reply with JSON only:
{"label": "YES" or "NO", "confidence": "HIGH" or "LOW", "category": "one of the strings above", \
"reason": "one short sentence, plain English, under 25 words"}"""


def user_prompt(snippet):
    return f"Snippet:\n{snippet}\n\nClassify it."


# Ablation baseline: the same model with no rubric at all. Used to measure how much of the
# classifier's performance comes from the rubric rather than the model's own priors.
NAIVE_SYSTEM_PROMPT = """You are a triage analyst at an insurance analytics firm. Decide whether \
a news snippet describes an event that could produce an insurance loss.

Reply with JSON only:
{"label": "YES" or "NO", "confidence": "HIGH" or "LOW", "category": "", "reason": "one short \
sentence"}"""
