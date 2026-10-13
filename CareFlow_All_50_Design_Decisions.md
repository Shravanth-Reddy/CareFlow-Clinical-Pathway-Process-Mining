# CareFlow Simulator — Complete Design Decisions 1–50

**Project:** CareFlow — Clinical Pathway Process Mining  
**Design scope:** Week 1 synthetic OPD event-log simulator  
**Status:** Design decisions consolidated for review; no simulator code written  
**Purpose:** Create a reproducible synthetic event log for process discovery, waiting-time analysis, bottleneck investigation, and later conformance checking.

> **Important:** All durations, frequencies, pathway proportions, operating hours, and arrival patterns in this document are synthetic modelling assumptions. They are not measured hospital statistics or clinical recommendations.

---

# Part I — Workflow, data, and journey design

## Decision 1 — Select the healthcare workflow

**Finalized:** Model an outpatient department (OPD) patient visit.

The simulator represents one visit as a sequence of recorded activities. A `Case_ID` represents one visit, not a unique person across all possible visits.

The goal is to create event data for studying activity sequences, activity durations, waiting intervals, bottlenecks, and process deviations.

## Decision 2 — Define the activity catalogue

**Finalized:** Use these six standardized activity names.

| Activity | Meaning | Use |
|---|---|---|
| `Registration` | Capture patient and visit details | Core |
| `Triage` | Assess urgency and initial condition | Core |
| `Doctor_Consultation` | Doctor examines the patient | Core |
| `Diagnostic_Test` | Perform a diagnostic test | Conditional |
| `Review_Results` | Review diagnostic findings | Conditional |
| `Discharge` | Complete the visit | Expected completion |

Activity names must remain consistent throughout the dataset. Do not introduce undocumented names.

## Decision 3 — Define reference pathways

**Finalized:** Use a small set of plausible base pathways, but do not restrict all visits to fixed templates.

Direct reference pathway:

`Registration → Triage → Doctor_Consultation → Discharge`

Diagnostic reference pathway:

`Registration → Triage → Doctor_Consultation → Diagnostic_Test → Review_Results → Discharge`

The simulator will also create controlled variations, including a normal return to the doctor after results, rework, other deviations, and incomplete visits.

## Decision 4 — Define the raw event-log schema

**Finalized:** The raw event log must contain exactly four columns.

| Column | Meaning |
|---|---|
| `Case_ID` | Identifier for one visit, such as `CF0001` |
| `Activity_Name` | Standardized activity name |
| `Start_Timestamp` | When the activity begins |
| `End_Timestamp` | When the activity finishes |

Keep this schema unchanged. Scenario labels and ground truth belong in separate metadata files.

## Decision 5 — Define the time calculations

**Finalized:** Calculate activity duration and waiting time separately.

- **Activity duration:** `End_Timestamp − Start_Timestamp`
- **Waiting interval:** `Next activity Start_Timestamp − Previous activity End_Timestamp`

A long interval measures elapsed time between recorded activities; it does not, by itself, establish why the delay occurred.

## Decision 6 — Use varied journeys rather than a few rigid templates

**Finalized:** Use a hybrid pathway-generation strategy.

The simulator will:
1. Assign a baseline pathway.
2. Apply normal pathway variations where applicable.
3. Generate activity durations and waits separately.
4. Apply selected scenario injections.
5. Validate the resulting journey and timestamps.

This balances interpretable reference paths with enough variation for process discovery.

## Decision 7 — Define scenario categories and initial rates

**Finalized:** Use these starting frequencies.

| Scenario | Rate | Sampling unit |
|---|---:|---|
| Deliberately injected long wait | 15% | Eligible transitions; exact count is selected |
| Extended activity duration | 8% | Eligible activities, independently |
| Rework or loopback | 10% | Visits, independently |
| Other pathway deviation | 5% | Visits, independently |
| Incomplete visit | 3% | Visits, independently |

Scenario categories may overlap. Percentages do not need to sum to 100%. These rates are synthetic test settings.

## Decision 8 — Set the validation philosophy

**Finalized:** Use strict validation.

Critical errors must stop the pipeline and be reported. Do not silently repair missing IDs, invalid timestamps, negative waiting intervals, or accidental records. Intentional repeats and incomplete visits are allowed only when consistent with the documented scenario rules.

## Decision 9 — Choose ordinary activity-duration sampling

**Finalized:** Use triangular sampling for ordinary activity durations.

Each ordinary activity duration is sampled using a triangular distribution with a minimum, mode, and maximum. The mode is the midpoint of the ordinary range for each activity.

This makes the midpoint the most likely duration while allowing shorter and longer values within the range.

## Decision 10 — Choose extended activity-duration sampling

**Finalized:** Use uniform random sampling for extended activity durations.

When an activity is selected for extension, sample a whole-minute duration uniformly from that activity’s extended range. The ordinary duration is replaced by the extended duration; the two durations are not added together.

---

# Part II — Waiting times, deviations, and event-log preparation

## Decision 11 — Select transitions for targeted long waits

**Finalized:** Use hybrid selection.

Any eligible transition may receive a deliberately long wait, but selected primary bottleneck transitions receive higher selection weight. This allows delays elsewhere while still creating known bottleneck scenarios for later evaluation.

## Decision 12 — Choose primary bottleneck transitions

**Finalized:** Give extra selection weight to these three transitions:

1. `Triage → Doctor_Consultation`
2. `Doctor_Consultation → Diagnostic_Test`
3. `Diagnostic_Test → Review_Results`

A transition is eligible only when it actually appears in a generated visit. Long waits can still occur at other transitions.

## Decision 13 — Choose ordinary waiting-time sampling

**Finalized:** Use triangular sampling with:

- Minimum: **5 minutes**
- Mode: **10 minutes**
- Maximum: **20 minutes**

These are ordinary waits, separate from activity durations and deliberate long-wait injections.

## Decision 14 — Choose the sampling unit for extended durations

**Finalized:** Apply the 8% probability independently to each eligible activity.

A visit may have no extended activities, one extended activity, or multiple extended activities. Do not select entire visits first for this scenario.

## Decision 15 — Select visits for rework

**Finalized:** Each eligible visit independently has a **10% chance** of receiving rework or a loopback.

The number selected may vary around 10% of visits. Each selected visit will receive exactly one injected rework operation, as specified in Decision 32.

## Decision 16 — Select visits for other pathway deviations

**Finalized:** Each eligible visit independently has a **5% chance** of receiving another pathway deviation.

A selected visit receives exactly one other deviation operation, as specified in Decisions 33–34. This category is separate from rework, but a visit can receive both.

## Decision 17 — Select incomplete visits

**Finalized:** Each visit independently has a **3% chance** of being incomplete.

An incomplete visit typically ends without `Discharge`. The intended incomplete status and stopping point are stored in separate metadata, not added to the event log.

## Decision 18 — Choose the PM4Py event timestamp

**Finalized:** Use `End_Timestamp` as the event timestamp for PM4Py.

Preserve both start and end timestamps in the raw event log. Use them to calculate activity durations and waiting intervals. The PM4Py event log is a prepared representation; it does not replace the raw data.

## Decision 19 — Fix the simulation window

**Finalized:** Use a fixed, configurable start date, initially:

- Start inclusive: `2026-01-01 00:00:00`
- End exclusive: `2026-01-31 00:00:00`

This is a 30-calendar-day window. The configured start date can be changed without rewriting the simulator.

## Decision 20 — Define duration ranges for all activities

**Finalized:** Use the following ranges.

| Activity | Ordinary range | Ordinary triangular mode | Extended range |
|---|---:|---:|---:|
| `Registration` | 5–15 min | 10 min | 16–30 min |
| `Triage` | 5–15 min | 10 min | 16–30 min |
| `Doctor_Consultation` | 10–30 min | 20 min | 31–60 min |
| `Diagnostic_Test` | 10–30 min | 20 min | 31–60 min |
| `Review_Results` | 5–15 min | 10 min | 16–30 min |
| `Discharge` | 5–10 min | 7.5 min | 11–20 min |

Ordinary durations use triangular sampling with the midpoint as mode. Extended durations use uniform sampling within their extended ranges. The extension probability is 8% independently per eligible activity.

## Decision 21 — Handle tied timestamps

**Finalized:** Allow identical timestamps across different visits.

Within a single visit, activities must remain sequential and non-overlapping. We do not require globally unique timestamps. Repeated activity names are allowed when intentionally generated.

## Decision 22 — Define the arrival model

**Finalized:** Generate visit arrivals during OPD operating hours, with daily patient volumes allowed to vary.

The total remains exactly 1,000 visits across the simulation window.

## Decision 23 — Define OPD operating days and hours

**Finalized:** Monday–Saturday, **9:00 AM–5:00 PM**, with Sunday closed.

Registration starts must fall within the operating window. A visit that starts before 5 PM may finish after 5 PM, subject to the overall simulation-window boundary in Decision 37.

## Decision 24 — Define daily volume variation

**Finalized:** Use moderate daily patient-volume variation while maintaining exactly 1,000 visits overall.

The January 1–30, 2026 window contains 26 operating days under the Monday–Saturday schedule. Daily volumes vary around an average of approximately 38–39 visits per operating day.

## Decision 25 — Choose the intraday arrival pattern

**Finalized:** Use two daily arrival peaks, with a midday lull and lighter arrivals during the remaining hours.

The peak windows and weights are defined in Decisions 26–27.

## Decision 26 — Define the arrival periods

**Finalized:** Use these four periods within the 9 AM–5 PM operating window.

| Period | Time |
|---|---|
| Morning peak | 9:00–11:00 AM |
| Midday lull | 11:00 AM–2:00 PM |
| Afternoon peak | 2:00–4:00 PM |
| Late period | 4:00–5:00 PM |

These are synthetic arrival windows, not observed hospital patterns.

## Decision 27 — Set daily arrival weights

**Finalized:** Use these weights for each day’s allocated visits.

| Period | Share of daily visits |
|---|---:|
| Morning peak | 40% |
| Midday lull | 15% |
| Afternoon peak | 35% |
| Late period | 10% |
| **Total** | **100%** |

Because daily visit counts must be whole numbers, the implementation must use a deterministic integer-allocation and rounding rule that preserves each day’s allocated count.

## Decision 28 — Define the baseline pathway mix

**Finalized:** Use:

- **60% direct consultation**
- **40% diagnostic pathway**

These are baseline templates before normal variations and injected deviations.

## Decision 29 — Make baseline allocation exact

**Finalized:** Allocate exactly:

- **600 visits** to the direct baseline template
- **400 visits** to the diagnostic baseline template

Later pathway variations, rework, other deviations, and incomplete stopping points may change the final observed activity sequences. The exact split applies before modifications.

## Decision 30 — Allow a normal post-test return to the doctor

**Finalized:** Some diagnostic journeys may return to `Doctor_Consultation` after `Review_Results` as a normal pathway variation.

Example:

`Registration → Triage → Doctor_Consultation → Diagnostic_Test → Review_Results → Doctor_Consultation → Discharge`

This return is not automatically classified as rework or an anomaly.

## Decision 31 — Set the normal post-test return rate

**Finalized:** Independently select **20% of diagnostic-template visits** for a normal return to `Doctor_Consultation` after `Review_Results`, before other modifications.

With 400 baseline diagnostic visits, approximately 80 visits are expected to receive this variation, but the actual count can vary. This rate is a synthetic assumption.

## Decision 32 — Limit injected rework per selected visit

**Finalized:** Each visit selected for rework receives exactly one injected rework or loopback operation.

The selected operation can be:
1. Repeat an eligible activity.
2. Return to an earlier activity.
3. Repeat a diagnostic test.

The operation must preserve valid timestamps and must not create uncontrolled loops.

## Decision 33 — Limit other deviations per selected visit

**Finalized:** Each visit selected for another pathway deviation receives exactly one injected deviation operation.

Rework remains a separate scenario category. Since scenario selection is independent, a visit may receive both a rework operation and another deviation.

## Decision 34 — Choose other deviation types

**Finalized:** Use a balanced mix among selected other-deviation visits:

- **50%:** Skip one eligible activity or one coherent dependent sequence.
- **50%:** Change the order of two eligible adjacent activities, where valid.

Only apply an operation when the affected activities and resulting sequence are valid under the simulator rules. Do not force an invalid order just to create an anomaly.

## Decision 35 — Define allowed rework operations

**Finalized:** Rework can use one of these three operation types:

1. **Repeat an activity:** Repeat `Registration`, `Triage`, `Doctor_Consultation`, or `Diagnostic_Test`.
2. **Return to an earlier activity:** For example, return from `Doctor_Consultation` to `Triage` and then continue to consultation.
3. **Repeat a diagnostic test:** `Diagnostic_Test → Diagnostic_Test`.

Each selected visit receives one injected rework operation. Repeated activity names must remain in the event log and must not be deduplicated.

## Decision 36 — Define safe skip/reorder rules

**Finalized:** Apply other deviations only when the resulting journey remains coherent and timestamp-valid.

- `Diagnostic_Test` may be skipped when it is present in the diagnostic template.
- If skipping the test makes `Review_Results` invalid, remove the dependent review as part of the same coherent deviation operation.
- Reordering may swap two adjacent activities only when the resulting sequence is allowed by the simulator’s rules.
- Do not create overlapping activities, negative waits, missing identifiers, or undocumented activity names.

A dependent skip sequence counts as one injected operation.

## Decision 37 — Keep all activities inside the simulation window

**Finalized:** Every activity’s start and end timestamps must fit inside the 30-day window.

- Inclusive start: `2026-01-01 00:00:00`
- Exclusive end: `2026-01-31 00:00:00`

Never truncate an activity to force it inside the boundary. If a journey would cross the boundary, explicitly regenerate or adjust its schedule deterministically. If bounded attempts fail, stop and report an error rather than silently altering the data.

## Decision 38 — Define incomplete-visit stopping points

**Finalized:** An incomplete visit may end after one of these activities, when that activity exists in the generated journey:

- `Triage`
- `Doctor_Consultation`
- `Diagnostic_Test`
- `Review_Results`

The visit must not receive a `Discharge` event after its selected stopping point. Store the intended stopping point in `case_metadata.csv`. An incomplete record does not prove abandonment or poor care.

## Decision 39 — Separate ground-truth metadata from the event log

**Finalized:** Keep the raw event log and simulator ground truth in separate CSV files.

- `event_log.csv`: four-column raw event log.
- `case_metadata.csv`: one row per visit with visit-level information.
- `injection_log.csv`: one row per deliberately injected scenario.

The metadata is for evaluating the simulator and later analysis. Do not add scenario labels to the raw event log used as process-mining input.

## Decision 40 — Expand the injection metadata schema

**Finalized:** Use a minimal case metadata schema and an expanded injection log schema.

### `case_metadata.csv`

One row per visit:

- `Case_ID`
- `Baseline_Pathway`
- `Is_Incomplete`
- `Incomplete_End_Activity`

### `injection_log.csv`

One row per deliberately injected scenario:

- `Injection_ID`
- `Case_ID`
- `Scenario_Type`
- `Operation_Type`
- `Activity_Name`
- `From_Activity`
- `To_Activity`
- `Injected_Value`
- `Details`

`Injected_Value` stores the intended wait or activity duration in minutes where applicable. It may be blank for pathway operations. Blank fields are acceptable when a field does not apply to that scenario.

The injection log records deliberately injected scenarios, not every naturally occurring long wait.

## Decision 41 — Set primary bottleneck selection weight

**Finalized:** Give primary bottleneck transitions **3× selection weight** compared with other eligible transitions when selecting long-wait injections.

The weight is relative, not a guarantee that every run will produce exactly three times as many waits on those transitions.

## Decision 42 — Make the long-wait allocation exact

**Finalized:** Calculate 15% of all eligible transitions, round to a whole number, and select that number using the agreed 3× bottleneck weighting.

Select distinct eligible transitions so the same transition does not receive duplicate long-wait injections. The eligible-transition count depends on the generated journeys.

## Decision 43 — Sample long-wait durations

**Finalized:** Use triangular sampling for deliberately injected long waits:

- Minimum: **30 minutes**
- Mode: **45 minutes**
- Maximum: **90 minutes**

The overall target remains an exact 15% allocation of eligible transitions, rounded to a whole number, with 3× selection weight for primary bottlenecks.

## Decision 44 — Combine ordinary and injected long waits

**Finalized:** An injected long wait **replaces** the ordinary wait on the selected transition.

The final wait is a single value sampled from the 30–90-minute triangular distribution. Do not add the long-wait value to an ordinary 5–20-minute wait. This makes the intended injection directly comparable with the final observed interval.

---

# Part III — Final implementation and validation decisions

## Decision 45 — Apply extended durations by replacement

**Finalized:** If an eligible activity is selected for an extended duration, replace its ordinary duration with a uniformly sampled whole-minute duration from its extended range.

The ordinary triangular duration and extended uniform duration are not added together. Each selected activity gets one final duration. Record the intended duration in `injection_log.csv` with `Scenario_Type = Extended_Duration` and `Operation_Type = Extend_Activity`.

## Decision 46 — Set timestamp precision and event construction

**Finalized:** Use whole-minute durations and minute-resolution timestamps.

Use a consistent timestamp format such as `YYYY-MM-DD HH:MM:SS`, with seconds set to `00`.

For each visit:
1. Generate a registration start time within an allowed arrival period.
2. Sample the activity duration.
3. Calculate the activity end timestamp.
4. Sample the wait before the next activity.
5. Set the next activity’s start to the previous activity’s end plus that wait.
6. Continue until the journey ends.

For a transition selected for long-wait injection, use the injected long wait instead of the ordinary wait. Keep both raw timestamps and derive the PM4Py event timestamp from `End_Timestamp`.

## Decision 47 — Define stable IDs, sorting, and metadata linkage

**Finalized:** Use deterministic identifiers and sorting.

### Case IDs

Use one unique ID per visit:

`CF0001`, `CF0002`, …, `CF1000`

A case represents one visit.

### Injection IDs

Use unique injection IDs such as:

`INJ0001`, `INJ0002`, …

### Deterministic sorting

Sort `event_log.csv` by `Case_ID` and then `Start_Timestamp`. Sorting is for readability and reproducibility; correctness must not depend on original row order.

### Required outputs

`event_log.csv` — exactly four columns:
- `Case_ID`
- `Activity_Name`
- `Start_Timestamp`
- `End_Timestamp`

`case_metadata.csv`:
- `Case_ID`
- `Baseline_Pathway`
- `Is_Incomplete`
- `Incomplete_End_Activity`

`injection_log.csv`:
- `Injection_ID`
- `Case_ID`
- `Scenario_Type`
- `Operation_Type`
- `Activity_Name`
- `From_Activity`
- `To_Activity`
- `Injected_Value`
- `Details`

## Decision 48 — Define reproducibility settings

**Finalized:** Use fixed random seed `42` as the initial default, with the seed and simulation settings kept in one clearly named configuration section or file.

With the same code, seed, and configuration, the generated cases, scenario selections, timestamps, durations, and sorted CSV outputs should be identical.

Use a stable generation order and deterministic sorting. Do not depend on the current date or unordered iteration. A fixed seed makes the synthetic dataset reproducible; it does not make its assumptions real-world statistics.

## Decision 49 — Finalize end-of-window handling

**Finalized:** Keep every activity fully inside the configured simulation window; never truncate activity durations.

The valid window is `[2026-01-01 00:00:00, 2026-01-31 00:00:00)`.

If a proposed journey would cross the boundary:
1. Do not shorten an activity.
2. Do not move its end timestamp backward.
3. Deterministically regenerate or adjust the proposed schedule so the full visit fits.
4. If a bounded number of attempts fails, stop and report a clear error.

This is consistent with Decision 37 and reinforces the same boundary rule for implementation.

## Decision 50 — Define the final validation and release gate

**Finalized:** Stop on critical errors; never silently repair the dataset.

### Event-log validation

- Exactly 1,000 distinct case IDs.
- Every case contains at least one activity.
- Exactly four columns with the agreed names.
- No missing `Case_ID` or `Activity_Name`.
- Activity names belong to the documented catalogue.
- Timestamps parse successfully.
- `Start_Timestamp <= End_Timestamp` for every event.
- Every activity start and end is inside the simulation window.
- Within each case, activities are chronologically ordered and non-overlapping.
- Negative waiting intervals are prohibited.
- Repeated activities are allowed when generated intentionally and must not be automatically removed.
- Identical timestamps across different cases are allowed.

### Metadata validation

- `case_metadata.csv` contains exactly one row for each case.
- Every metadata `Case_ID` exists in the event log.
- Incomplete visits end without `Discharge` and have a valid `Incomplete_End_Activity`.
- Complete visits have `Is_Incomplete = False` and no incomplete stopping activity.

### Injection-log validation

- `Injection_ID` values are unique.
- Every injection references an existing `Case_ID`.
- Activity and transition references match the generated visit.
- Long-wait injection records match the final waiting interval on the affected transition.
- Extended-duration records match the generated activity duration.
- Rework and other-deviation records match the resulting activity sequence.
- No transition has more than one deliberate long-wait injection.
- Scenario labels remain outside the raw event log.

### Scenario and reproducibility validation

- Baseline allocation is exactly 600 direct-template visits and 400 diagnostic-template visits before modifications.
- The long-wait count equals 15% of eligible transitions, rounded to a whole number.
- Primary bottlenecks receive 3× selection weight during long-wait selection.
- Extended durations, rework, other deviations, and incomplete visits follow their agreed sampling rules.
- Two runs with identical code, seed, and configuration produce identical outputs after deterministic sorting and serialization.

**Failure policy:** If a critical check fails, stop the pipeline, report the issue, and fix the generator or configuration. Do not silently delete, deduplicate, or repair records.

---

# Consolidated configuration reference

| Setting | Final choice |
|---|---|
| Visits | Exactly 1,000 |
| Simulation window | January 1–30, 2026; January 31 midnight is exclusive |
| Operating days | Monday–Saturday; Sunday closed |
| OPD registration hours | 9 AM–5 PM |
| Arrival weights | Morning 40%, midday 15%, afternoon 35%, late 10% |
| Arrival periods | 9–11 AM, 11 AM–2 PM, 2–4 PM, 4–5 PM |
| Daily volumes | Moderate variation; exactly 1,000 visits overall |
| Baseline pathways | Exactly 600 direct, 400 diagnostic before modifications |
| Normal post-test return | 20% of diagnostic-template visits, selected independently |
| Ordinary waits | Triangular: 5 / 10 / 20 minutes |
| Injected long waits | Exact 15% of eligible transitions, rounded to a whole number |
| Primary bottleneck weighting | 3× |
| Long-wait duration | Triangular: 30 / 45 / 90 minutes |
| Extended activity probability | 8% independently per eligible activity |
| Rework probability | 10% independently per eligible visit; one operation if selected |
| Other deviation probability | 5% independently per eligible visit; one operation if selected |
| Other deviation operation mix | 50% skip, 50% reorder |
| Incomplete visit probability | 3% independently per visit |
| Ordinary activity durations | Triangular sampling; mode at range midpoint |
| Extended activity durations | Uniform sampling in extended range |
| PM4Py event timestamp | `End_Timestamp` |
| Raw event-log columns | `Case_ID`, `Activity_Name`, `Start_Timestamp`, `End_Timestamp` |
| Ground-truth metadata | Separate `case_metadata.csv` and `injection_log.csv` |
| Initial random seed | `42` |
| Validation | Strict; stop and report critical errors |

## Implementation sequence after review

1. Create the configuration and activity catalogue.
2. Generate the baseline arrivals and pathway templates.
3. Generate durations and waiting intervals.
4. Apply normal pathway variations and controlled scenario injections.
5. Write the three CSV outputs and their ground truth.
6. Run strict validation and a reproducibility check.
7. Only then proceed to the Week 1 BigQuery and dbt workflow.

**Current status:** All 50 decisions are documented here. Review the specification for any requested changes before we freeze it. No simulator code has been written.
