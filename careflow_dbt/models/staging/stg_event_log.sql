{{ config(materialized='view') }}

-- Retain source values and types. Timestamp deliberately comes from Start_Timestamp;
-- no timezone conversion or end-time substitution is performed here.
select
    Case_ID,
    Activity_Name,
    Start_Timestamp as Timestamp,
    End_Timestamp
from {{ source('careflow_raw', 'event_log') }}
