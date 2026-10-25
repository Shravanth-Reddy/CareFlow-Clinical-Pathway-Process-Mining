# CareFlow Week 2 Independent Audit & Mid-Project Review

## Audit findings and fixes

- **Medium — validation coverage gap.** The prior 10 tests did not enforce case-metadata uniqueness/coverage, incomplete-case retention, or valid start/end intervals. Added metadata key checks and two singular tests for output case coverage and source timestamp interval validity. The exact event-multiplicity reconciliation remains in place.
- **Low — export-test side effect.** tests/test_export.py previously used the default data/raw and data/metadata destinations, so running it could overwrite Week 1 CSV artifacts. Changed it to write through pytest tmp_path. The test itself was not run because it invokes the Week 1 generator.
- **Low — pathway-count ambiguity.** The prior report did not define whether 518/269/62 were partial or full paths. Independently recomputed from per-case sorted event arrays: they are counts of exact complete trace sequences, mutually exclusive as trace classes. The other 151 cases have other traces.
- **Medium — timezone provenance unresolved.** Simulator datetimes and CSV strings are naive. All 4,863 source CSV events match BigQuery when timestamps are rendered as UTC, but no ingestion code or job configuration exists in this repository. Preserve current values; confirm the intended timezone before local-time analysis.
- No source SQL defect, accidental join, deduplication, or raw-target collision was found. Before rebuilding, the target dataset contained only `stg_event_log` and `fct_event_log`, both views.

## Actual validation evidence

- Environment: Python 3.13.3, dbt Core 1.13.0-b1, BigQuery adapter 1.12.1, PM4Py 2.7.23.11, Graphviz 16.1.0.
- `dbt parse`: passed. `dbt compile`: passed. `dbt build`: passed (2 views, 15 data tests, no test failures). Standalone `dbt test`: passed (15/15).
- Raw sources remained tables with counts unchanged after build: `event_log` 4,863 rows / 1,000 cases; `case_metadata` 1,000 rows / 1,000 unique cases; `injection_log` 1,143 rows / 705 cases.
- Both output views contain 4,863 rows / 1,000 cases / 6 distinct activities. Reconciliation by `(Case_ID, Activity_Name, Start_Timestamp)` multiplicity: zero source-only keys, zero output-only keys, zero mismatches.
- Required fields had zero nulls; starts/ends had zero nulls; no negative or zero activity durations. Case event counts range from 2 to 8 (mean 4.863).
- Repeated activity groups: 161 `(Case_ID, Activity_Name)` groups and 328 events in the source and output. Metadata has 1,000 unique cases and 21 true `Is_Incomplete` flags; all 21 incomplete end-activity labels match their last observed event. No output/metadata case gaps.
- PM4Py discovered a **frequency DFG**, not a Petri net: 4,863 events, 1,000 cases, 6 activities, 13 directed activity edges. There were no within-case timestamp ties. PM4Py generated the DOT source and PNG via its DFG visualizer with Graphviz `dot`; the PNG was opened and inspected.

## Exact full-trace counts

These counts are exact entire event sequences, not partial-path counts. Each case belongs to one full-trace class; the three listed classes do not cover all cases.

1. Registration → Triage → Doctor_Consultation → Discharge: **518 cases**.
2. Registration → Triage → Doctor_Consultation → Diagnostic_Test → Review_Results → Discharge: **269 cases**.
3. Registration → Triage → Doctor_Consultation → Diagnostic_Test → Review_Results → Doctor_Consultation → Discharge: **62 cases**.

Other exact traces account for the remaining 151 cases. Loops are retained as observed and are not automatically labeled rework. Incomplete visits have no synthetic missing activities added.

## Timestamp semantics and remaining risk

The project brief specifies Indian local operating hours. src/careflow/config.py constructs naive datetimes; src/careflow/export.py writes %Y-%m-%d %H:%M:%S strings without timezone metadata. All 4,863 source CSV rows match the BigQuery values when TIMESTAMP values are rendered in UTC; Asia/Kolkata display is 05:30 later. BigQuery defines TIMESTAMP as an absolute instant and documents UTC as the default for zone-free CSV timestamps ([TIMESTAMP semantics](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types), [CSV load time zone](https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-csv)). No loader code or job configuration was found. The observed mapping is consistent with naive local clock values being interpreted as UTC. If those values are intended to represent India-local instants, the stored instants are 05:30 later than intended. This is an inference; the original loader behavior is unverified. PM4Py preserves the connector datetime64[us, UTC] values. Do not shift source timestamps without an authoritative decision.

There were no equal start timestamps within a case. The script rejects timezone-naive timestamps rather than guessing; its activity-name tie-break is for deterministic serialization only and does not imply clinical order. DFG edges are observed adjacency frequencies, not proof of clinically valid transitions.

## Remaining scope

Week 3 bottleneck analysis and BI dashboard; Week 4 conformance checking and dashboard refinement. These were not implemented.

## Re-run from the repository root

```powershell
.\.venv\Scripts\dbt.exe debug --project-dir careflow_dbt
.\.venv\Scripts\dbt.exe parse --project-dir careflow_dbt
.\.venv\Scripts\dbt.exe compile --project-dir careflow_dbt
.\.venv\Scripts\dbt.exe build --project-dir careflow_dbt
.\.venv\Scripts\dbt.exe test --project-dir careflow_dbt
.\.venv\Scripts\python.exe scripts\discover_process.py
Invoke-Item outputs\process_map.png
```

## Verification boundary

The Python simulator/export unit suite was not run because it invokes the Week 1 generator, which this audit was instructed not to run. The export test now directs generated CSVs to pytest tmp_path, so it no longer writes into data/raw or data/metadata. Its runtime behavior and the rest of the simulator unit suite remain unverified; dbt checks, live BigQuery reconciliation, and PM4Py discovery were run independently.
