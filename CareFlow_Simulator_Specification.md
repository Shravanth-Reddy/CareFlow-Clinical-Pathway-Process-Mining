# CareFlow --- Synthetic Event Simulator Specification

## Purpose

This document records the design decisions for CareFlow Week 1, Steps
1--4, before implementation. CareFlow uses synthetic outpatient
department (OPD) visit data to test event-log validation, process
discovery, waiting-time analysis, and conformance checking.

The data is synthetic. Generated delays and deviations are test
scenarios, not evidence about real hospital performance.

## 1. Simulation Configuration

-   **Patient visits:** 1,000
-   **Simulated period:** 30 days
-   **Randomness:** Fixed random seed for reproducibility
-   **Raw event-log columns:** `Case_ID`, `Activity_Name`,
    `Start_Timestamp`, `End_Timestamp`
-   **Validation approach:** Strict validation; critical errors stop the
    run and are reported.

A case represents one patient visit. The same `Case_ID` is used for
every activity occurrence within that visit.

## 2. Hospital Workflow and Activity Catalogue

  Activity name           Description                            Usage
  ----------------------- -------------------------------------- ------------------------------
  `Registration`          Capture patient and visit details      Core activity
  `Triage`                Assess urgency and initial condition   Core activity
  `Doctor_Consultation`   Doctor examines the patient            Core activity
  `Diagnostic_Test`       Perform an ordered diagnostic test     Conditional
  `Review_Results`        Review diagnostic findings             Conditional
  `Discharge`             Complete the visit                     Expected completion activity

Reference pathway:

`Registration → Triage → Doctor_Consultation → Discharge`

Possible diagnostic pathway:

`Registration → Triage → Doctor_Consultation → Diagnostic_Test → Review_Results → Discharge`

These are reference patterns, not exhaustive templates. The simulator
will produce varied journeys. Activity names must remain standardized.
Repeated occurrences are allowed when they represent intended rework or
a loop-back.

## 3. Event-Log Schema

  Column              Meaning
  ------------------- ------------------------------------------------
  `Case_ID`           Unique identifier for one visit, e.g. `CF0001`
  `Activity_Name`     Standardized activity name
  `Start_Timestamp`   When the activity begins
  `End_Timestamp`     When the activity finishes

### Timing calculations

-   **Activity duration:** `End_Timestamp − Start_Timestamp`
-   **Waiting interval:**
    `Next activity Start_Timestamp − Previous activity End_Timestamp`

The four-column raw schema preserves activity duration and waiting
intervals separately. For PM4Py, a suitable event timestamp will be
derived during event-log preparation.

## 4. Journey-Generation Strategy

Use a **hybrid approach**:

1.  Select a plausible base pathway.
2.  Add randomized choices such as optional diagnostic activities.
3.  Generate activity durations and waits independently.
4.  Apply controlled deviations to selected cases or transitions.
5.  Validate the journey and the resulting event records.

This balances structured, interpretable pathways with enough variation
for process discovery. A fixed random seed makes a run reproducible when
the code and configuration are unchanged; it does not mean all patient
journeys are identical.

## 5. Waiting-Time Model

Use a mixed model with targeted bottleneck injection:

-   Ordinary waits are common, initially **5--20 minutes**.
-   Deliberately long waits are initially **30--90 minutes**.
-   A long wait may occur at **any transition between consecutive
    activities**.
-   One visit may contain multiple long waits.
-   Selected transitions receive deliberately injected delays so later
    analysis can be tested against known scenarios.

These are illustrative simulation ranges, not clinical benchmarks. A
long interval shows elapsed time between recorded activities; it does
not independently establish the cause of the delay.

## 6. Activity-Duration Model

Use weighted durations plus deliberately extended activities. Typical
durations should be more common than unusually long durations.

Initial illustrative ranges:

  Activity                Duration range
  ----------------------- ----------------
  `Registration`          5--15 minutes
  `Triage`                5--15 minutes
  `Doctor_Consultation`   10--30 minutes
  `Diagnostic_Test`       10--30 minutes

The initial extended-activity frequency is **8% of eligible
activities/visits**; the exact sampling unit and extended-duration range
must be made explicit in the implementation configuration before coding.

Activity duration and waiting time are separate measurements and must be
analyzed separately.

## 7. Controlled Deviations and Incomplete Visits

The simulator may introduce:

-   Registration rework.
-   Repeated diagnostic tests.
-   Returns to earlier activities.
-   Repeat consultations, including after diagnostic testing.
-   Selected skipped activities or unexpected activity sequences.
-   Incomplete recorded visits that end before `Discharge`.

Not every repeated activity or unusual path is necessarily an
inefficiency. For example, a repeat consultation after a test may be
clinically appropriate. Incomplete records do not by themselves prove
that a patient abandoned care.

Repeated activities must remain visible in the event log. Add a maximum
repetition/loop limit and a guaranteed stopping condition so journeys
cannot loop forever.

### Initial scenario frequencies

  ------------------------------------------------------------------------
  Scenario                         Initial frequency Intended sampling
                                                     unit
  --------------------- ---------------------------- ---------------------
  Long waiting interval                          15% Eligible activity
                                                     transitions

  Extended activity                               8% Eligible
  duration                                           activities/visits;
                                                     exact unit to be
                                                     configured

  Rework or loop-back                            10% Eligible visits

  Other pathway                                   5% Eligible visits
  deviation                                          

  Incomplete recorded                             3% Visits
  visit                                              
  ------------------------------------------------------------------------

These frequencies are configurable starting assumptions, not real
hospital statistics. Categories may overlap, so their percentages do not
need to sum to 100%. The simulator should retain scenario metadata
separately from the four-column raw event log, so analysis can be
evaluated against known injected scenarios without exposing those labels
as event-log features.

## 8. Event Ordering and Data-Quality Rules

-   Exactly 1,000 distinct visit IDs must be generated.
-   Every case must contain at least one activity record.
-   `Case_ID` and `Activity_Name` must not be missing.
-   Activity names must belong to the approved catalogue or be
    explicitly documented.
-   Start and end timestamps must be valid datetime values.
-   `Start_Timestamp` must be earlier than or equal to `End_Timestamp`.
-   Within a case, the next activity must not start before the previous
    activity ends. Negative waiting intervals are critical errors.
-   Events must fall within the configured 30-day simulation window.
-   Repeated activity names are permitted when generated intentionally;
    they must not be automatically deleted as duplicates.
-   Incomplete visits without `Discharge` are permitted when
    intentionally generated and must be identifiable through separate
    simulation metadata.
-   Records should be sorted by `Case_ID` and event time for
    readability, but correctness must not depend on original file row
    order.
-   Reproducibility should be tested using the same code, seed, and
    configuration.

### Strict validation policy

If a critical check fails, stop the pipeline, report the issue, and fix
the generator. Do not silently repair invalid timestamps, negative
waits, missing identifiers, or accidental records. Intentional scenarios
such as incomplete visits and loop-backs must be validated according to
their documented rules rather than rejected as errors.

## 9. Planned Implementation Sequence

1.  Finalize the exact configurable probabilities, eligible sampling
    units, and edge-case rules.
2.  Implement pathway generation in Python.
3.  Generate start/end timestamps and waiting intervals.
4.  Add controlled deviations and separate scenario metadata.
5.  Validate all generated journeys and event records.
6.  Export the raw event log, for example as CSV.
7.  Load the validated dataset into Google BigQuery.
8.  Configure dbt and create the initial model.

## 10. Decisions Still Requiring Explicit Configuration

Before implementation, specify:

-   The exact weighted sampling method for activity durations.
-   The extended-duration range for each activity.
-   How the 8% extended-duration rate is sampled.
-   How the 15% long-wait rate is applied to eligible transitions and
    how targeted bottlenecks are selected.
-   The exact rules and repetition limits for each deviation type.
-   Whether the 3% incomplete-visit rate is applied before or after
    other scenario selection.
-   The exact timestamp anchor and boundaries for the 30-day simulation
    window.
-   How tied timestamps are handled if they occur.

These are implementation details that must be settled explicitly rather
than left ambiguous.

## Status

**Design status:** The overall simulation strategy and initial settings
are agreed. The implementation-specific sampling rules listed above
remain to be finalized.

**No simulator code has been written as part of this specification.**
