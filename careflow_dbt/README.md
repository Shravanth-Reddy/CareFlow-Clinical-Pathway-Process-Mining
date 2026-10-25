# CareFlow dbt project

The Week 2 dbt project declares read-only sources in BigQuery dataset `careflow` and builds two views in the isolated `careflow_week2` dataset:

- `stg_event_log`: preserves each source event and aliases `Start_Timestamp` directly as `Timestamp`.
- `fct_event_log`: normalized process-mining output with `Case_ID`, `Activity_Name`, and `Timestamp`.

The original dbt example models are disabled. The project-wide custom schema routes every enabled model to `careflow_week2`, keeping builds separate from raw tables.

Run from the repository root in Windows PowerShell:

```powershell
.\.venv\Scripts\dbt.exe debug --project-dir careflow_dbt
.\.venv\Scripts\dbt.exe build --project-dir careflow_dbt
```

The build runs required-field checks and `event_multiplicity_reconciliation`, which compares counts for each `(Case_ID, Activity_Name, Timestamp)` key against the raw source.
