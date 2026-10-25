-- Compare full event multiplicities, including repeated case/activity/timestamp
-- combinations. An empty result means exact multiset parity.
with source_events as (
    select Case_ID, Activity_Name, Start_Timestamp as Timestamp, count(*) as n
    from {{ source('careflow_raw', 'event_log') }}
    group by 1, 2, 3
), output_events as (
    select Case_ID, Activity_Name, Timestamp, count(*) as n
    from {{ ref('fct_event_log') }}
    group by 1, 2, 3
)
select
    coalesce(s.Case_ID, o.Case_ID) as Case_ID,
    coalesce(s.Activity_Name, o.Activity_Name) as Activity_Name,
    coalesce(s.Timestamp, o.Timestamp) as Timestamp,
    s.n as source_multiplicity,
    o.n as output_multiplicity
from source_events s
full outer join output_events o
  on s.Case_ID = o.Case_ID
 and s.Activity_Name = o.Activity_Name
 and s.Timestamp = o.Timestamp
where coalesce(s.n, 0) != coalesce(o.n, 0)
