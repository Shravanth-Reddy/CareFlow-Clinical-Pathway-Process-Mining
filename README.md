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
