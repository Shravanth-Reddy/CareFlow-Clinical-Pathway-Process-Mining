{{ config(materialized='view', schema='week2') }}

-- One output row per eligible source row. No DISTINCT or deduplication.
select
    Case_ID,
    Activity_Name,
    Timestamp,
    End_Timestamp
from {{ ref('stg_event_log') }}
where Case_ID is not null
  and Activity_Name is not null
  and Timestamp is not null
