-- Require metadata/event case coverage in both directions and retain events for
-- every case marked incomplete. The exact event multiset test separately verifies
-- that every event within each represented case is preserved.
with metadata_cases as (
    select Case_ID, Is_Incomplete
    from {{ source('careflow_raw', 'case_metadata') }}
), output_cases as (
    select distinct Case_ID
    from {{ ref('fct_event_log') }}
)
select
    m.Case_ID,
    case when m.Is_Incomplete then 'incomplete_case_without_events'
         else 'metadata_case_without_events' end as issue
from metadata_cases m
left join output_cases o using (Case_ID)
where o.Case_ID is null
union all
select
    o.Case_ID,
    'event_case_without_metadata' as issue
from output_cases o
left join metadata_cases m using (Case_ID)
where m.Case_ID is null
