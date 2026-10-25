-- Fail if source event intervals are incomplete or have a negative duration.
select Case_ID, Activity_Name, Start_Timestamp, End_Timestamp
from {{ source('careflow_raw', 'event_log') }}
where Start_Timestamp is null
   or End_Timestamp is null
   or End_Timestamp < Start_Timestamp
