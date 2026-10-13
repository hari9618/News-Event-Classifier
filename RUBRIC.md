# Labelling rubric: insurable loss event (YES) vs not (NO)

## Question

I label a snippet **YES** when it describes an event that has already happened and could reasonably lead to an insurance loss or claim.

The key distinction is between an **actual event** and something that is only a forecast, warning, financial development, or potential future loss.

I am judging the event itself, not whether a particular insurer would definitely provide coverage.

## YES

Label **YES** when the snippet describes one or more of the following:

* **Physical damage:** Fire, flood, wildfire, hail, explosion, collapse, derailment, or similar events that damage property or infrastructure.
* **Bodily injury:** People are injured or killed as a result of an event.
* **Transport/asset casualties:** A vessel, aircraft, vehicle, or other insured asset experiences a casualty that could reasonably create a property, hull, machinery, salvage, or related claim, even if nobody is injured.
* **Business interruption:** An unexpected event, including a cyber or system failure, causes a meaningful interruption to operations.
* **A hazard that has already struck:** If an earthquake, storm, flood or other hazard has occurred and there is enough evidence that loss may have resulted, I label it YES even when the full damage assessment is still underway.

## NO

Label **NO** when the snippet is primarily:

* **A forecast, warning or outlook:** The hazard has not happened yet.
* **A precaution without confirmed loss:** For example, shutting down a pipeline because of an abnormal reading when there is no confirmed leak or damage.
* **An event with no meaningful loss reported:** A disruption or weather event where the snippet explicitly says there was no damage, injury or other loss.
* **Financial, market, regulatory, research or corporate news:** Share-price movements, funding announcements, regulation, academic studies, underwriting decisions, and similar items.
* **A historical/legal outcome rather than a new event:** For example, a court judgment relating to historical contamination.
* **Planned operational activity:** A scheduled upgrade or planned work that causes an interruption is not treated as a fortuitous loss event.

## Borderline cases

I use the following approach for cases where the evidence is incomplete:

* **No injuries or no spill does not automatically mean NO.** I look at whether the insured asset itself experienced a casualty.
* **Precaution vs actual damage:** A precautionary response without confirmed damage is NO; confirmed physical damage is YES.
* **Slow-onset hazards:** These can be YES once their effects are already occurring, rather than while they are only forecast.
* **Cyber incidents:** A confirmed operational interruption is YES. A security exposure with no confirmed loss is more difficult and is treated as LOW confidence.
* **Unverified reports:** I can still label the event YES if the reported event itself fits the definition, but I reduce confidence when the evidence is weak. I treat a single uncorroborated source, or an operator declining to confirm, as weak evidence and mark it LOW. Multiple independent sources reporting both casualties and damage can still support HIGH, even where the report is described as unverified.
* **Historical liability:** I treat a legal judgment about an old event as NO because this exercise is focused on near-real-time event detection rather than downstream legal/claims outcomes.

## Confidence

**HIGH** means the classification follows the rubric clearly and I would expect another analyst to reach the same conclusion.

**LOW** means the evidence is incomplete or the case sits close to a boundary in the rubric. Low-confidence items would be good candidates for human review in a production system.
