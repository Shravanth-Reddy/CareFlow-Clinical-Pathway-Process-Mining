# CareFlow Python Package Guide

This document explains the Python code in [`src/careflow/`](./src/careflow/):

- [`config.py`](./src/careflow/config.py)
- [`check_config.py`](./src/careflow/check_config.py)
- [`scenarios.py`](./src/careflow/scenarios.py)
- [`simulator.py`](./src/careflow/simulator.py)
- [`validation.py`](./src/careflow/validation.py)
- [`export.py`](./src/careflow/export.py)
- [`__init__.py`](./src/careflow/__init__.py)

The package simulates outpatient clinical pathways, injects realistic process
variation, validates the generated data, and exports three CSV files.

## 1. End-to-end design

The intended flow is:

```text
config.py
    ↓
simulator.generate_baseline_visits()
    ├─ creates direct and diagnostic baseline pathways
    ├─ applies visit-level scenarios from scenarios.py
    ├─ selects long-wait transitions
    ├─ creates timestamped events
    └─ returns event log, visit metadata, long-wait selections,
       and injection records
    ↓
validation.validate_dataset(...)
    ↓
export.export_careflow_data(...)
    ├─ data/raw/event_log.csv
    ├─ data/metadata/case_metadata.csv
    └─ data/metadata/injection_log.csv
```

There is no database or web service in this package. The generated objects are
ordinary Python lists, dictionaries, sets, and `datetime` values until the
export step writes them to CSV.

## 2. `config.py`

File: [`config.py`](./src/careflow/config.py)

This module has no functions or classes. It is the single source of truth for
simulation settings. Other modules import these constants instead of
duplicating values.

### Simulation identity and time range

```python
PROJECT_NAME = "CareFlow"
RANDOM_SEED = 42
SIMULATION_START = datetime(2026, 1, 1, 0, 0, 0)
SIMULATION_END = datetime(2026, 1, 31, 0, 0, 0)
TOTAL_VISITS = 1_000
```

- `PROJECT_NAME` identifies the project.
- `RANDOM_SEED` makes random output repeatable.
- `SIMULATION_START` and `SIMULATION_END` bound the simulation dates.
- `TOTAL_VISITS` requests 1,000 generated cases.

The simulator treats the end date as exclusive when it builds operating dates,
so the loop includes dates before January 31, but not January 31 itself.

### Operating hours and baseline pathways

```python
OPENING_HOUR = 9
CLOSING_HOUR = 17
OPERATING_DAYS = 6
DIRECT_VISITS = 600
DIAGNOSTIC_VISITS = 400
```

The department operates Monday through Saturday from 09:00 to 17:00.
The baseline population contains 600 direct visits and 400 diagnostic visits.
These counts add to `TOTAL_VISITS`.

The two pathway templates are:

```text
Direct:
Registration → Triage → Doctor_Consultation → Discharge

Diagnostic:
Registration → Triage → Doctor_Consultation → Diagnostic_Test
            → Review_Results → Discharge
```

`DIRECT_PATHWAY` and `DIAGNOSTIC_PATHWAY` are lists. The simulator copies them
before modifying a particular visit, so one scenario does not alter the
template used by another visit.

### Scenario probabilities

```python
EXTENDED_ACTIVITY_PROBABILITY = 0.08
REWORK_PROBABILITY = 0.10
PATHWAY_DEVIATION_PROBABILITY = 0.05
INCOMPLETE_VISIT_PROBABILITY = 0.03
```

These represent independent probabilities:

- 8% for an extended activity duration.
- 10% for one repeated eligible activity.
- 5% for a pathway deviation.
- 3% for an incomplete visit.

Because the visit-level scenario checks are independent, one visit can receive
more than one scenario.

### Waiting and arrival configuration

`LONG_WAIT_PROPORTION = 0.15` requests long waits for 15% of eligible
transitions. `BOTTLENECK_WEIGHT = 3` makes configured bottleneck transitions
three times as likely to be selected as ordinary transitions.

`ARRIVAL_PERIOD_WEIGHTS` assigns the registration-arrival distribution:

| Period | Weight |
|---|---:|
| Morning | 0.40 |
| Midday | 0.15 |
| Afternoon | 0.35 |
| Late | 0.10 |

The weights sum to 1.0 and are used as relative probabilities, not as an
exact quota.

### Activity duration settings

Each `ACTIVITY_DURATIONS` tuple has this shape:

```text
(ordinary minimum, ordinary mode, ordinary maximum,
 extended minimum, extended maximum)
```

For example, `Registration: (5, 10, 15, 16, 30)` means ordinary durations are
sampled from 5–15 minutes with a mode of 10, while extended durations are
sampled uniformly from 16–30 minutes.

The ordinary duration uses a triangular distribution. The extended duration
uses a uniform integer distribution. `Discharge` has a mode of `7.5`, even
though the surrounding comment describes whole-minute durations; the simulator
rounds the result to an integer.

### Bottleneck and wait distributions

`BOTTLENECK_TRANSITIONS` contains these `(from_activity, to_activity)` pairs:

1. `Triage → Doctor_Consultation`
2. `Doctor_Consultation → Diagnostic_Test`
3. `Diagnostic_Test → Review_Results`

Ordinary waits use `(5, 10, 20)` as minimum, mode, and maximum. Long waits use
`(30, 45, 90)`. Both are sampled with a triangular distribution.

## 3. `check_config.py`

File: [`check_config.py`](./src/careflow/check_config.py)

This file is an executable configuration smoke check. It does not define any
functions.

When run, it:

1. Imports the core configuration values.
2. Prints the number of visits, pathway allocation, activity count, and both
   pathway templates.
3. Asserts that:
   ```python
   TOTAL_VISITS == DIRECT_VISITS + DIAGNOSTIC_VISITS
   ```
4. Asserts that there are exactly six configured activity types.
5. Prints a success message if both assertions pass.

The assertions raise `AssertionError` if the configuration is inconsistent.
This is a lightweight sanity check, not a complete validation of every
configuration value.

## 4. `scenarios.py`

File: [`scenarios.py`](./src/careflow/scenarios.py)

### `apply_visit_scenarios(case_id, pathway, rng)`

```python
apply_visit_scenarios(case_id, pathway, rng)
```

This function applies visit-level changes to one pathway.

#### Inputs

- `case_id`: identifier such as `CF0001`.
- `pathway`: a list of activity names.
- `rng`: a seeded `random.Random` instance.

#### Outputs

It returns a four-item tuple:

```text
(modified_pathway,
 is_incomplete,
 incomplete_end_activity,
 records)
```

- `modified_pathway`: a copied and potentially changed activity list.
- `is_incomplete`: whether the visit was truncated.
- `incomplete_end_activity`: the final activity for an incomplete visit, or
  an empty string.
- `records`: scenario metadata without `Injection_ID`; the simulator assigns
  IDs after all records have been collected.

#### Implementation logic

The function first copies the pathway. This prevents the caller's original
list from being modified accidentally.

##### Rework

If `rng.random() < REWORK_PROBABILITY`, it builds an eligible list containing
only activities present in the pathway:

```text
Triage
Doctor_Consultation
Diagnostic_Test
```

It randomly selects one eligible activity, finds its first index, and inserts
the same activity immediately after it. This creates exactly one additional
occurrence. It also records a `Repeat_Activity` injection.

##### Pathway deviation

If `rng.random() < PATHWAY_DEVIATION_PROBABILITY`, a second random decision
chooses between two branches.

For the first branch, the function attempts to remove
`Diagnostic_Test` and `Review_Results` together. These activities are treated
as a dependent sequence. If either is absent, the function falls back to
removing one eligible activity from `Triage` or `Doctor_Consultation`.

For the second branch, no approved adjacent reorder is implemented for the
current reference pathways. Therefore, it explicitly records a fallback
single-activity skip instead of silently pretending that a reorder occurred.

Each successful deviation appends either a `Skip_Sequence` or `Skip_Activity`
record.

##### Incomplete visit

The function independently tests `INCOMPLETE_VISIT_PROBABILITY`. If selected,
it chooses an endpoint from activities present in the pathway:

```text
Triage
Doctor_Consultation
Diagnostic_Test
Review_Results
```

It truncates the pathway immediately after the selected endpoint. This removes
all later activities, including `Discharge`, and records a
`Truncate_Pathway` injection.

If no eligible endpoint exists, the function resets `is_incomplete` to
`False`. This prevents metadata from claiming that a visit is incomplete when
no valid incomplete endpoint could be selected.

## 5. `simulator.py`

File: [`simulator.py`](./src/careflow/simulator.py)

This is the main generation module. It creates dates, visit pathways,
durations, waits, event timestamps, and injection records.

### `get_operating_dates()`

Returns all dates in the simulation window whose weekday is Monday through
Saturday.

Implementation:

1. Starts at `SIMULATION_START.date()`.
2. Iterates while the current date is before `SIMULATION_END.date()`.
3. Includes a date when `weekday() < 6`; Python uses Monday `0` through Sunday
   `6`.
4. Advances one day at a time.

The result is a list of `date` objects. The function raises no error if the
list is empty; `allocate_daily_visits` handles that case.

### `allocate_daily_visits(dates, total_visits, rng)`

Allocates exactly `total_visits` across the supplied operating dates.

Implementation:

1. Raises `ValueError` when no dates are provided.
2. Gives each date a random weight between `0.75` and `1.25`.
3. Converts each weight into an exact fractional visit count.
4. Floors each fractional count with `int`.
5. Calculates the number of visits still unallocated.
6. Sorts dates by the size of their discarded fractional parts.
7. Gives the remaining visits to dates with the largest fractional parts.

This is a largest-remainder allocation method. It guarantees that the returned
dictionary sums to exactly `total_visits`, while still producing moderate
random variation by date.

### `generate_arrival_time(date, rng, latest_minute=None)`

Generates a registration start time on a specified date.

The available periods are:

| Period | Start | End |
|---|---:|---:|
| Morning | 09:00 | 11:00 |
| Midday | 11:00 | 14:00 |
| Afternoon | 14:00 | 16:00 |
| Late | 16:00 | 17:00 |

The function:

1. Converts the closing hour to minutes from midnight.
2. Uses one minute before closing as the default latest possible start.
3. If `latest_minute` is supplied, caps it at the closing minute.
4. Removes periods whose start is already too late.
5. Selects a period using `ARRIVAL_PERIOD_WEIGHTS`.
6. Selects a whole minute within that period.
7. Combines the selected minute with the supplied date.

It raises `ValueError` if no period can fit before closing. In the main
generation flow, `latest_minute` is reduced by the visit's expected elapsed
duration so the entire visit can remain within operating hours.

### `generate_activity_duration(activity_name, rng)`

Generates one activity duration and reports whether it was extended.

The function unpacks the activity's five duration settings from
`ACTIVITY_DURATIONS`, then tests the extended-duration probability.

- Extended case: selects an integer uniformly between `extended_min` and
  `extended_max`.
- Ordinary case: samples a triangular distribution using the ordinary minimum,
  maximum, and mode, then rounds to a whole minute.

It returns:

```text
(duration_in_minutes, is_extended)
```

The caller uses `is_extended` to create an `Extended_Duration` injection record.

### Module demonstration block

The `if __name__ == "__main__":` block creates a seeded random generator and
prints one sample duration for each configured activity. It runs only when
`simulator.py` is executed directly, not when it is imported by another
module.

### `generate_waiting_time(rng, is_long_wait=False)`

Generates one waiting period.

- When `is_long_wait` is `False`, it uses the ordinary wait distribution.
- When `True`, it uses the long-wait distribution.

Both branches use `rng.triangular(minimum, maximum, mode)` and round the
result. The return value is an integer number of minutes.

### `create_activity_event(case_id, activity_name, start_time, rng)`

Creates one event dictionary.

Implementation:

1. Calls `generate_activity_duration`.
2. Adds the duration to `start_time`.
3. Builds a dictionary containing exactly:
   - `Case_ID`
   - `Activity_Name`
   - `Start_Timestamp`
   - `End_Timestamp`
4. Returns the dictionary and the extension flag.

It does not add waiting time. Waiting is inserted between events by
`generate_visit_timeline`.

### `select_long_wait_transitions(pathways, rng)`

Selects which pathway transitions receive long waits.

`pathways` is a mapping from case ID to its final, scenario-modified pathway.
For every adjacent activity pair, the function creates an eligible transition
tuple:

```text
(case_id, from_activity, to_activity, weight)
```

The weight is `BOTTLENECK_WEIGHT` for a configured bottleneck and `1`
otherwise.

The target number is:

```python
round(number_of_eligible_transitions * LONG_WAIT_PROPORTION)
```

Selection is weighted without replacement:

1. Copy all eligible transitions into `remaining`.
2. Calculate the sum of remaining weights.
3. Draw a random number between zero and that sum.
4. Walk through the candidates cumulatively until the draw is reached.
5. Add the selected transition's first three fields to `selected`.
6. Remove the chosen candidate.
7. Repeat until the target count is reached.

The function raises `ValueError` if the target exceeds the number of eligible
transitions. It returns a set of `(case_id, from_activity, to_activity)` tuples.

### `generate_baseline_visits()`

This is the top-level simulation generator.

It returns:

```text
(event_log, visits, long_wait_transitions, injection_records)
```

#### Step 1: initialize reproducible randomness

It creates `random.Random(RANDOM_SEED)`, so the complete generation sequence is
repeatable.

#### Step 2: allocate visit dates

It obtains operating dates and distributes exactly `TOTAL_VISITS` across them.
The date list is expanded so each generated case receives one assigned date.

#### Step 3: build and shuffle baseline pathways

It creates 600 copies of the direct template and 400 copies of the diagnostic
template, then shuffles the combined list.

Before visit-level scenarios are applied, each diagnostic pathway has a 20%
chance of receiving a normal return loop:

```text
... Review_Results → Doctor_Consultation → Discharge
```

The return loop is not represented as a scenario injection; it is stored in
the baseline pathway metadata.

#### Step 4: apply visit-level scenarios

For each date/pathway pair, it assigns a case ID such as `CF0001`, calls
`apply_visit_scenarios`, and stores metadata:

- final pathway
- baseline pathway type
- whether the baseline had a return loop
- incomplete status
- incomplete endpoint

The scenario records are appended to the global injection list.

#### Step 5: select long waits

It passes the final modified pathways to
`select_long_wait_transitions`. This is important: long waits are selected
after skips, repeats, and truncations, so selections correspond to actual
transitions that will appear in the event log.

#### Step 6: create each visit timeline

For each visit, it calls `generate_visit_timeline` using a temporary start time
at the opening hour. It measures the generated elapsed duration, then calls
`generate_arrival_time` with enough remaining time for the entire visit to
finish before closing.

All events are shifted by the difference between the temporary start and the
actual generated arrival time. The visit's `arrival_time` is then stored and
the events are added to `event_log`.

#### Step 7: finalize injection IDs and output

Injection records are assigned stable sequential IDs:

```text
INJ0001, INJ0002, ...
```

Events are sorted by case ID and start timestamp. Assertions confirm:

- the number of visits is `TOTAL_VISITS`;
- every visit has an event;
- event dictionaries contain exactly the four expected columns.

The four generated objects are then returned.

### `generate_visit_timeline(...)`

Creates the timestamped event sequence for one already-modified pathway.

If `long_wait_transitions` or `injection_records` is omitted, it replaces the
missing value with an empty set or disables injection recording as appropriate.

For each activity:

1. Calls `create_activity_event` at `current_start`.
2. Appends the event.
3. If the duration is extended, adds an `Extended_Duration` record containing
   the actual duration.
4. If another activity follows, constructs the transition tuple.
5. Checks whether that tuple was selected for a long wait.
6. Generates an ordinary or long wait.
7. If long, records a `Long_Wait` injection.
8. Sets the next activity's start to the current event's end plus the wait.

The returned event list is chronological and non-overlapping by construction.
The function records injections but does not assign `Injection_ID`; that is
done by `generate_baseline_visits` after all records exist.

## 6. `validation.py`

File: [`validation.py`](./src/careflow/validation.py)

This module validates the generated in-memory dataset and raises one combined
`ValueError` rather than silently accepting invalid data.

### Module constants

`EXPECTED_EVENT_COLUMNS` requires exactly these event fields:

```text
Case_ID, Activity_Name, Start_Timestamp, End_Timestamp
```

`ALLOWED_SCENARIOS` permits:

```text
Extended_Duration
Rework
Pathway_Deviation
Incomplete_Visit
Long_Wait
```

### `validate_dataset(event_log, visits, long_wait_transitions, injection_records)`

The function accumulates errors in an `errors` list and reports up to the first
25 in the final exception.

#### Check 1: visit totals and baseline allocation

It verifies:

- `len(visits) == TOTAL_VISITS`
- direct baseline count equals `DIRECT_VISITS`
- diagnostic baseline count equals `DIAGNOSTIC_VISITS`

Counts are calculated with `Counter` over each visit's
`baseline_pathway` field.

#### Check 2: event schema and values

It groups events by case using `defaultdict(list)` and checks every event:

- exactly four expected keys;
- known `Case_ID`;
- known activity;
- timestamp-like values exposing `strftime`;
- start is not after end;
- start and end are within the configured simulation window;
- neither timestamp is on Sunday;
- end time is not after the closing hour.

Rows with the wrong schema or unknown case are reported and skipped for the
remaining checks on that row.

#### Check 3: every visit has an event

It compares known visit IDs with the IDs found in the grouped event log and
adds an error for every missing case.

#### Check 4: chronology and overlap

Each case's events are sorted by start timestamp. Consecutive events are
compared. An error is recorded when a current event starts before the previous
event ends.

This detects overlapping intervals but does not reject an event that starts
exactly when the previous event ends.

#### Check 5: incomplete-visit metadata

For each visit with events, it finds the final activity:

- An incomplete visit may not end in `Discharge`.
- Its final activity must equal `incomplete_end_activity`.
- A complete visit must have an empty `incomplete_end_activity`.

This cross-check ensures that metadata and raw event data agree.

#### Check 6: injection records

Every injection record is checked for:

- a known case;
- an allowed scenario type;
- a non-empty `Injection_ID`;
- no duplicate injection ID.

#### Check 7: long-wait count

It filters injection records to `Scenario_Type == "Long_Wait"` and compares
that count with `len(long_wait_transitions)`. A mismatch indicates that a
selected transition was not recorded or an extra record was created.

#### Result or failure

If any errors exist, the function raises `ValueError` with a summary and the
first 25 messages.

If all checks pass, it returns a summary dictionary:

```python
{
    "visits": ...,
    "events": ...,
    "direct_visits": ...,
    "diagnostic_visits": ...,
    "injection_records": ...,
    "selected_long_waits": ...,
    "status": "PASS",
}
```

## 7. `export.py`

File: [`export.py`](./src/careflow/export.py)

This module converts generated Python data into CSV files.

### Column definitions

The three column lists establish stable output order:

- `EVENT_COLUMNS` for the raw event log.
- `METADATA_COLUMNS` for one row per case.
- `INJECTION_COLUMNS` for scenario and waiting-time records.

### `write_csv(file_path, columns, rows)`

Writes dictionaries to a CSV file.

Implementation:

1. Converts the path to a `Path` object.
2. Creates the parent directory if necessary.
3. Opens the file as UTF-8 with `newline=""`.
4. Creates a `csv.DictWriter` with the requested field order.
5. Uses `extrasaction="ignore"` so extra dictionary keys do not break export.
6. Writes the header and all rows.
7. Returns the `Path` used for the file.

### `export_careflow_data(event_log, visits, injection_records, raw_dir, metadata_dir)`

Exports all three datasets and returns their paths.

#### Event log

Before writing, each event's `datetime` values are converted to
`YYYY-MM-DD HH:MM:SS` strings. The output is written to:

```text
raw_dir/event_log.csv
```

#### Case metadata

The function converts the `visits` mapping into one row per case with:

- `Case_ID`
- baseline pathway
- incomplete flag
- incomplete endpoint

This is written to:

```text
metadata_dir/case_metadata.csv
```

#### Injection log

The collected injection records are written with the fixed injection columns
to:

```text
metadata_dir/injection_log.csv
```

The returned dictionary has keys `event_log`, `case_metadata`, and
`injection_log`, each pointing to its corresponding `Path`.

## 8. `__init__.py`

File: [`__init__.py`](./src/careflow/__init__.py)

This file is currently empty. Its purpose is package initialization.

With the project configured as a `src`-layout package, the file marks
`src/careflow` as the `careflow` package for normal Python tooling and makes
imports such as these possible:

```python
from careflow import simulator
from careflow.config import TOTAL_VISITS
```

It intentionally does not import or execute the simulator. That is useful
because importing `careflow` remains lightweight and does not generate files
or run a simulation automatically.

It can later be used to expose package-level metadata or selected public
functions, but no such public API is currently defined there.

## 9. Important data structures

### Event record

```python
{
    "Case_ID": "CF0001",
    "Activity_Name": "Registration",
    "Start_Timestamp": datetime(...),
    "End_Timestamp": datetime(...),
}
```

### Visit metadata

Each `visits[case_id]` dictionary contains:

```text
pathway
arrival_time
baseline_pathway
baseline_has_return_loop
is_incomplete
incomplete_end_activity
```

### Injection record

Scenario records contain the fields later written to `injection_log.csv`:

```text
Injection_ID
Case_ID
Scenario_Type
Operation_Type
Activity_Name
From_Activity
To_Activity
Injected_Value
Details
```

Scenario functions create every field except `Injection_ID`; the top-level
simulator adds that ID after all scenario and timeline records are collected.

## 10. Summary

The package separates concerns cleanly:

- `config.py` defines the simulation rules.
- `check_config.py` performs a small configuration smoke test.
- `scenarios.py` modifies individual pathways and records deviations.
- `simulator.py` generates reproducible clinical event data.
- `validation.py` checks structural, temporal, and metadata consistency.
- `export.py` writes stable CSV outputs.
- `__init__.py` establishes the Python package without side effects.
