# CareFlow — Clinical Pathway Process Mining

CareFlow is a synthetic healthcare event-log generation project developed as part of a Data Analyst internship. It simulates outpatient department (OPD) patient journeys, introduces controlled process variations, and generates structured datasets for process mining and healthcare workflow analysis.

The project is being developed in stages, with Python-based synthetic data generation completed as the first major milestone. BigQuery, dbt, PM4Py, and BI integration are planned for subsequent stages.

## Project Objectives

- Generate realistic synthetic OPD patient journeys.
- Represent normal clinical pathway variations and controlled process deviations.
- Simulate activity durations, waiting times, rework, and incomplete visits.
- Maintain a separate ground-truth record of injected scenarios.
- Validate the generated data before downstream processing.
- Prepare the datasets for process discovery, bottleneck analysis, and conformance checking.

## Current Milestone

**Milestone 1: Synthetic Data Simulator — Completed**

The Python simulator generates 1,000 synthetic OPD visits across January 2026, using a fixed random seed for reproducibility.

The baseline population contains:
- 600 direct-pathway visits.
- 400 diagnostic-pathway visits.
- Normal diagnostic return loops in a subset of diagnostic visits.
- Controlled scenario injections for extended activity durations, rework, pathway deviations, incomplete visits, and long waits.

The generated event log, case metadata, and injection log have been exported and cross-checked for consistency.

**Next milestone:** Configure Google BigQuery, load the generated data, and begin dbt-based data transformation.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Synthetic data generation and validation |
| CSV | Structured dataset storage and exchange |
| Google BigQuery | Planned cloud data warehouse |
| dbt | Planned data transformation and testing |
| PM4Py | Planned process discovery and process mining |
| Power BI / Looker | Planned process analytics dashboard |

## Project Structure

```text
CareFlow/
├── data/
│   ├── raw/
│   │   └── event_log.csv
│   └── metadata/
│       ├── case_metadata.csv
│       └── injection_log.csv
├── src/
│   └── careflow/
│       ├── __init__.py
│       ├── config.py
│       ├── simulator.py
│       ├── scenarios.py
│       ├── validation.py
│       └── export.py
├── tests/
│   ├── test_durations.py
│   ├── test_waiting_times.py
│   ├── test_activity_events.py
│   ├── test_visit_timeline.py
│   ├── test_long_wait_selection.py
│   ├── test_arrival_schedule.py
│   ├── test_baseline_generator.py
│   ├── test_validation.py
│   └── test_export.py
├── requirements.txt
└── README.md
```

*The tree represents the current intended project layout. Keep it aligned with the actual files in the repository as the project evolves.*

## Dataset Overview

The simulator produces three CSV files.

### 1. `event_log.csv`

Location: `data/raw/event_log.csv`

Contains the activity-level event log used for process mining.

| Column | Description |
|---|---|
| `Case_ID` | Unique identifier for a simulated OPD visit |
| `Activity_Name` | Activity performed during the visit |
| `Start_Timestamp` | Activity start time |
| `End_Timestamp` | Activity end time |

The raw event log contains exactly four columns. Scenario labels and other ground-truth information are stored separately.

### 2. `case_metadata.csv`

Location: `data/metadata/case_metadata.csv`

Contains visit-level ground truth.

| Column | Description |
|---|---|
| `Case_ID` | Visit identifier linked to the event log |
| `Baseline_Pathway` | Original direct or diagnostic pathway classification |
| `Is_Incomplete` | Indicates whether the simulated visit is incomplete |
| `Incomplete_End_Activity` | Activity where an incomplete journey ends |

### 3. `injection_log.csv`

Location: `data/metadata/injection_log.csv`

Records the controlled scenarios applied during simulation.

| Column | Description |
|---|---|
| `Injection_ID` | Unique scenario-record identifier |
| `Case_ID` | Visit affected by the scenario |
| `Scenario_Type` | Scenario category |
| `Operation_Type` | Operation used to inject the scenario |
| `Activity_Name` | Relevant activity, where applicable |
| `From_Activity` | Origin activity for a transition |
| `To_Activity` | Destination activity for a transition |
| `Injected_Value` | Duration or waiting-time value, where applicable |
| `Details` | Explanation of the injected scenario |

A visit can have multiple scenario records. Scenario categories are not mutually exclusive, and normal pathway variations are not automatically classified as anomalies.

## Simulated OPD Process

### Direct pathway

```text
Registration
    ↓
Triage
    ↓
Doctor_Consultation
    ↓
Discharge
```

### Diagnostic pathway

```text
Registration
    ↓
Triage
    ↓
Doctor_Consultation
    ↓
Diagnostic_Test
    ↓
Review_Results
    ↓
Discharge
```

A subset of diagnostic visits includes a normal return to `Doctor_Consultation` after `Review_Results`.

## Simulation Configuration

The main configuration is maintained in `src/careflow/config.py`.

| Parameter | Configuration |
|---|---|
| Total visits | 1,000 |
| Simulation window | January 1–30, 2026, inclusive |
| Operating days | Monday–Saturday |
| OPD hours | 9:00 AM–5:00 PM |
| Direct baseline visits | 600 |
| Diagnostic baseline visits | 400 |
| Random seed | 42 |
| Extended activity probability | 8% per eligible activity |
| Rework probability | 10% per eligible visit |
| Other pathway deviation probability | 5% per eligible visit |
| Incomplete visit probability | 3% per visit |
| Long-wait target | 15% of eligible transitions |
| Normal diagnostic return probability | 20% per diagnostic-template visit |

The simulator uses configured activity-duration distributions, ordinary waiting-time distributions, and longer waiting-time distributions for selected transitions. The random seed supports reproducible generation when the code, configuration, and execution environment remain unchanged.

## Data Validation

The project includes validation and test modules for the simulator's core functionality.

Checks cover:
- Required event-log columns and allowed activity names.
- Visit counts and baseline pathway counts.
- Timestamp validity and simulation-window boundaries.
- Chronological ordering and activity overlap within visits.
- Incomplete-visit consistency.
- Scenario-record references and unique injection IDs.
- Consistency between selected long waits and recorded long-wait scenarios.
- CSV schema and exported record counts.

These checks are part of the current validation layer. Additional validation will be introduced as the project progresses, including stricter operating-hour, scenario-probability, and transformation-level checks.

## Running the Project

Use Python 3.11 or newer as a starting point, subject to compatibility with the installed environment.

Activate the virtual environment in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Set the source directory for imports:

```powershell
$env:PYTHONPATH = "src"
```

Run the core simulator tests:

```powershell
python tests/test_durations.py
python tests/test_waiting_times.py
python tests/test_activity_events.py
python tests/test_visit_timeline.py
python tests/test_long_wait_selection.py
python tests/test_arrival_schedule.py
```

Run the integrated generator, validation, and export tests:

```powershell
python tests/test_baseline_generator.py
python tests/test_validation.py
python tests/test_export.py
```

The export workflow writes the three CSV files to their configured output directories.

## Roadmap

### Week 1 — Synthetic Data Generation and Data Engineering Setup

- [x] Implement the Python synthetic event-log simulator.
- [x] Generate direct and diagnostic baseline pathways.
- [x] Implement controlled scenario injection.
- [x] Generate event log, case metadata, and injection log.
- [x] Cross-check the generated CSV files.
- [ ] Configure Google BigQuery.
- [ ] Load the raw event log into BigQuery.
- [ ] Configure dbt and create the initial staging model.
- [ ] Run dbt data-quality tests and document the completed pipeline.

### Week 2 — Data Transformation and Process Discovery

- Normalize event data using dbt.
- Discover the observed process using PM4Py.
- Compare discovered pathways with the intended reference process.

### Week 3 — Waiting-Time Analysis and Dashboard

- Calculate waiting times between activities.
- Identify process bottlenecks and operational inefficiencies.
- Build a Power BI or Looker dashboard.

### Week 4 — Conformance Checking and Finalization

- Compare observed patient journeys against the expected pathway.
- Identify deviations and incomplete journeys.
- Interpret results and finalize the project documentation.

## Expected Outcome

CareFlow aims to demonstrate an end-to-end healthcare process-mining workflow, from controlled synthetic data generation to data transformation, process discovery, bottleneck analysis, conformance checking, and dashboard reporting.

The simulator provides the reproducible foundation for the remaining project stages.

# CareFlow — Week 2

CareFlow standardizes the observed hospital event data with dbt and discovers an observed process graph with PM4Py. Raw BigQuery relations are read-only. The normalized views are in the separate `careflow_week2` dataset.

## Architecture

- `careflow_dbt/models/sources.yml` declares the three raw relations in `careflow`.
- `stg_event_log` aliases raw `Start_Timestamp` directly to `Timestamp` and preserves `End_Timestamp`.
- `fct_event_log` exposes `Case_ID`, `Activity_Name`, `Timestamp`, and `End_Timestamp`. It filters only null required fields and does not deduplicate.
- The active dbt target dataset is `careflow`; the custom schema resolves to `careflow_week2`.
- dbt checks required fields, timestamp intervals, metadata/event case coverage, metadata key uniqueness, incomplete-case retention, and exact event multiplicities by case, activity, and source start timestamp.
- `scripts/discover_process.py` reads only `careflow_week2.fct_event_log`, creates a PM4Py EventLog, discovers a frequency directly-follows graph (DFG), and exports the DFG as PNG and Graphviz source through PM4Py's visualizer. A DFG represents observed adjacent-activity frequencies; it is not an Inductive Miner Petri net.

## Reproduce from Windows PowerShell

From the repository root, with the existing `.venv` and configured BigQuery OAuth credentials:

```powershell
.\.venv\Scripts\dbt.exe debug --project-dir careflow_dbt
.\.venv\Scripts\dbt.exe parse --project-dir careflow_dbt
.\.venv\Scripts\dbt.exe compile --project-dir careflow_dbt
.\.venv\Scripts\dbt.exe build --project-dir careflow_dbt
.\.venv\Scripts\dbt.exe test --project-dir careflow_dbt
.\.venv\Scripts\python.exe scripts\discover_process.py
Invoke-Item outputs\process_map.png
```

Python dependencies are recorded in `requirements.txt`. Install native Graphviz once with:

```powershell
winget install --id Graphviz.Graphviz --exact --accept-package-agreements --accept-source-agreements
```

The discovery script uses `dot` from `PATH`, `GRAPHVIZ_DOT`, or the standard `C:\Program Files\Graphviz\bin` location. Outputs and evidence are saved in `outputs\` and `reports\`.

## Verified audit results

- Raw sources before and after build: `event_log` 4,863 rows / 1,000 cases; `case_metadata` 1,000 rows; `injection_log` 1,143 rows. They remain BigQuery tables.
- Both normalized views contain 4,863 rows / 1,000 cases / 6 distinct activities. The source/output multiset comparison found zero source-only keys, output-only keys, or multiplicity mismatches.
- All 15 dbt data tests passed. Source and output each have 161 `(Case_ID, Activity_Name)` groups with repeated events (328 events in those groups). All 21 cases marked incomplete have observed events; their metadata end-activity labels match the last observed activity.
- PM4Py read 4,863 events across 1,000 cases and discovered 13 directly-follows edges. The displayed 518, 269, and 62 counts are exact, complete event-sequence counts for three distinct trace classes; they are not partial-path totals. Other traces account for 151 cases.
- Full CSV-to-BigQuery comparison: all 4,863 source events match when BigQuery timestamps are rendered in UTC.

## Timestamp and interpretation limits

The project brief defines the simulator operating clock as Indian local time. The Python generator uses naive datetimes and the CSV exporter writes timezone-free strings. All 4,863 CSV rows match the BigQuery source exactly when TIMESTAMP values are rendered in UTC; rendering those instants in Asia/Kolkata is 05:30 later. BigQuery defines TIMESTAMP as an absolute instant and documents UTC as the default for zone-free CSV timestamp loading ([TIMESTAMP semantics](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types), [CSV load time zone](https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-csv)). The repository has no ingestion code or load-job configuration. The observed mapping is consistent with naive local clock values being interpreted as UTC; if those clock values represent actual India-local instants, the stored instants are 05:30 later than intended. This is an inference, not proven loader behavior. Preserve the source instants and resolve the intended timestamp interpretation before time-of-day analysis. No within-case timestamp ties occurred; an activity-name tie-break in a future tie is serialization only, not clinical order.

The DFG describes observed event-to-event frequencies and does not prove clinical correctness. The return to consultation after results is not automatically classified as rework. Missing discharge events in incomplete visits are not fabricated. Bottleneck analysis, conformance checking, and BI dashboards remain future work.
