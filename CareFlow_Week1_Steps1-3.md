# CareFlow: Week 1 Design --- Steps 1--3

## Step 1: Define the Hospital Workflow

CareFlow will simulate patient visits through a hospital outpatient
department (OPD). The purpose is to create synthetic event data that can
later be analyzed to discover patient pathways, measure waiting
intervals, and identify process deviations.

### Core activities

  Activity                Description
  ----------------------- ----------------------------------------
  `Registration`          Capture patient and visit details
  `Triage`                Assess urgency and initial condition
  `Doctor_Consultation`   Doctor examines the patient
  `Diagnostic_Test`       Perform a diagnostic test when ordered
  `Review_Results`        Review test results when applicable
  `Discharge`             Complete the visit

A simplified expected pathway is:

`Registration → Triage → Doctor_Consultation → Discharge`

A patient who needs a diagnostic test may follow a pathway such as:

`Registration → Triage → Doctor_Consultation → Diagnostic_Test → Review_Results → Discharge`

These are reference pathways, not the only pathways the simulator will
generate. Diagnostic tests and result reviews are conditional
activities.

## Step 2: Design the Event-Log Schema

The raw synthetic event log will use four columns:

  Column              Meaning
  ------------------- ----------------------------------------------------
  `Case_ID`           Identifier for one patient visit, such as `CF0001`
  `Activity_Name`     Standardized name of the activity
  `Start_Timestamp`   When the activity begins
  `End_Timestamp`     When the activity finishes

A case represents one visit, not necessarily one unique person across
all visits. All activity records belonging to the same visit share the
same `Case_ID`.

### Timestamp and data rules

-   `Case_ID` and `Activity_Name` must not be missing.
-   Activity names must be consistent; the same activity should not use
    multiple labels.
-   Start and end timestamps must be valid datetime values.
-   `Start_Timestamp` must be earlier than or equal to `End_Timestamp`.
-   Activities within a case must be chronologically consistent and
    sortable by timestamps.
-   Repeated activities are allowed when they represent an intentional
    loop-back or rework.
-   Accidental duplicate records should be avoided, but repeated
    activity names must not automatically be treated as duplicates.
-   Waiting intervals and activity durations will be measured
    separately.

### Timing calculations

**Activity duration**

`End_Timestamp − Start_Timestamp`

**Waiting time between consecutive activities**

`Next activity Start_Timestamp − Previous activity End_Timestamp`

A negative waiting interval should be flagged for investigation. A long
interval shows elapsed time between recorded activities, but does not by
itself explain the cause of the delay.

The raw dataset will retain both start and end timestamps. When using
PM4Py, we will prepare the event log with the event timestamp required
for process mining.

## Step 3: Design Diverse Patient Journeys

The simulator will generate varied patient journeys instead of relying
on only three fixed templates. Different cases may follow different
activity sequences, experience different activity durations and waiting
intervals, and contain selected process deviations.

### Journey variations

-   **Normal pathway:** Patient follows the expected sequence and
    completes the visit.
-   **Optional diagnostic pathway:** A diagnostic test and result review
    occur when applicable.
-   **Waiting-time variation:** A patient may wait between any two
    consecutive activities.
-   **Long waits:** Some transitions receive deliberately long waits;
    one visit may contain more than one long wait.
-   **Registration rework:** Registration may be repeated when details
    are incomplete.
-   **Loop-backs:** A patient may return to an earlier activity or
    repeat an activity.
-   **Other selected deviations:** Some journeys may skip an expected
    activity or use an unexpected sequence.
-   **Incomplete journeys:** A controlled number may end before
    `Discharge`, if retained in the final simulator rules.

Not every repeated activity or unusual pathway is necessarily an
inefficiency. For example, a second doctor consultation after a
diagnostic test may be clinically appropriate. The simulator's scenarios
are synthetic and are intended to test analysis methods, not to make
claims about a real hospital.

### Initial illustrative timing ranges

These are starting assumptions for simulation, not real hospital
benchmarks:

  Activity or interval               Initial range
  ---------------------------------- ----------------
  Registration duration              5--15 minutes
  Triage duration                    5--15 minutes
  Doctor consultation duration       10--30 minutes
  Diagnostic test duration           10--30 minutes
  Ordinary wait between activities   5--20 minutes
  Deliberately long wait             30--90 minutes

Waiting time is generated separately from activity duration and can
occur at any transition.

### Confirmed simulation settings

-   **Number of patient visits:** 1,000
-   **Simulated period:** 30 days
-   **Random seed:** Fixed, to make runs reproducible when the code and
    configuration remain the same

The exact probabilities for pathways, long waits, loop-backs, and
incomplete journeys are not finalized yet. They will be defined before
implementation and documented in the simulator configuration.

## How Steps 1--3 Connect

1.  The workflow defines the activities a patient may perform.
2.  The event-log schema defines how each activity occurrence is
    recorded.
3.  The journey-generation rules define how cases move through
    activities and how timing variation or deviations are introduced.
4.  The resulting synthetic records can then be validated and used in
    the later CareFlow pipeline.

**Current status:** Steps 1--3 are in the design phase. The Python
simulator has not yet been implemented.
